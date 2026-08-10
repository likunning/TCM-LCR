# -*- coding: utf-8 -*-

import json
import time
import sys

# ========== 编码配置区 =========
# 1. 生成模型配置
GEN_DATA_PATH = ""
GEN_MODEL_NAME = ""
GEN_BASE_URL = ""
GEN_API_KEY = ""
GEN_DELAY = 0.5
GEN_SYS_PROMPT = "你是资深中医，根据病案给出规范处方及思路，仅输出正文无多余文字"

# 2. 双评分模型配置
JUDGE1_NAME = ""
JUDGE1_URL = ""
JUDGE1_KEY = ""

JUDGE2_NAME = ""
JUDGE2_URL = ""
JUDGE2_KEY = ""

# 评分维度
DIM_MAX = {"纵向病情演变把握":40, "处方质量":35, "阐释质量":25}
TOTAL_FULL = 100
SCORE_JSON_TPL = '''{"case_id":"","scores":{"纵向病情演变把握":{"score":0,"max":40},"处方质量":{"score":0,"max":35},"阐释质量":{"score":0,"max":25}},"total_score":0}'''
SCORE_SYS = f"""
【任务背景】
本评测考察模型是否能够像一名合格的临床带教医师/进修医生一样，读懂一份多诊次的中医病案（第一诊、第二诊、第三诊……），并在此基础上，根据病情的动态演变，为"当前诊次"开出合理、连贯、与前几诊治疗逻辑相衔接的处方，同时清晰阐释处方背后的辨证思路。这与"从零开始辨证"不同，重点考察模型对病情纵向演变（症状变化、舌脉变化、疗效反馈、病机转化）的把握能力，以及处方调整（增、减、换、守方）是否合理。

【评分维度与标准】（满分100分）

一、纵向病情演变把握（满分40分）
考察参评模型是否准确抓住了从既往诊次到本诊之间的关键病情变化，包括但不限于：症状的缓解或加重、舌象脉象的变化、二便/饮食/睡眠等兼症变化、前诊治疗的反馈效果，并据此判断病机的转化方向（如邪去正显、由实转虚、由湿转燥、由瘀转虚等）。
- 36-40分：精准捕捉全部或几乎全部关键纵向变化点，病机转化判断与专家一致或高度接近；
- 26-35分：捕捉到大部分关键变化点，病机判断基本合理，有轻微遗漏或偏差；
- 16-25分：仅捕捉到部分变化点，病机把握不完整或存在明显偏差；
- 6-15分：对纵向变化的把握非常有限，基本停留在本诊症状的静态辨证；
- 0-5分：完全未体现纵向理解，等同于孤立看待本诊病情。

二、处方质量（满分35分）
考察参评模型给出的处方是否与其自身判断的病机相符，是否体现了合理的"守方-加减-转方"逻辑（该守的守、该减的减、该加的加、该转的转），药物configuration、剂量、炮制方法是否符合中医临床常规，是否存在明显不合理配伍或与病机矛盾的用药。不要求与参考处方逐一对应，但核心治法方向、主要药物类别应基本吻合或有充分医理支持。
- 31-35分：处方与病机高度吻合，加减变化合理精准，用药规范；
- 21-30分：处方总体合理，治法方向正确，个别药物或剂量可商榷；
- 11-20分：处方部分合理，但与病机存在一定脱节，或加减逻辑不清；
- 5-10分：处方与病机明显不符，或基本照搬前诊未做合理调整（或调整无据）；
- 0-4分：处方存在明显禁忌、内在矛盾或与病情严重不符。

三、阐释质量（满分25分）
考察参评模型对处方思路的阐释是否清晰、有中医理论依据，逻辑是否自洽，是否说明了"为什么调整/为什么维持"，是否体现了对君臣佐使、治法治则的合理表达，语言是否符合中医专业表达习惯。
- 21-25分：阐释逻辑清晰、层次分明，理法方药论述透彻，专业表达规范；
- 14-20分：阐释基本清晰合理，但深度或条理性略有不足；
- 7-13分：阐释较为浅显或部分牵强，理法方药对应关系不够清楚；
- 1-6分：阐释混乱、空泛，或与处方脱节；
- 0分：未作有效阐释。
仅输出裸JSON，无任何多余字符，模板：{SCORE_JSON_TPL}，total_score为三项分数总和。"""
# ==========================================

try:
    from openai import OpenAI
except ImportError:
    print("Dep missing: pip install openai")
    sys.exit(1)

# ---------------- Step1 生成模块 ----------------
def gen_llm_call(client, prompt):
    try:
        resp = client.chat.completions.create(
            model=GEN_MODEL_NAME,
            messages=[{"role":"system","content":GEN_SYS_PROMPT},{"role":"user","content":prompt}],
            temperature=0, max_tokens=2048, extra_body={"enable_thinking":False}
        )
        return resp.choices[0].message.strip()
    except Exception as e:
        print(f"[Gen API Fail] {e}")
        time.sleep(1)
        return "GEN_ERROR"

def build_gen_prompt(bg, q):
    return f"""患者诊疗记录：{bg}\n问题：{q}"""

# ---------------- Step2 双评分模块 ----------------
def judge_call(j_client, j_model, sys_p, usr_p):
    try:
        resp = j_client.chat.completions.create(
            model=j_model,
            messages=[{"role":"system","content":sys_p},{"role":"user","content":usr_p}],
            temperature=0, max_tokens=2048
        )
        raw = resp.choices[0].message.strip()
        # 清洗JSON
        start = raw.find("{")
        end = raw.rfind("}")
        clean_json = raw[start:end+1] if start!=-1 and end!=-1 else "{}"
        score_data = json.loads(clean_json)
        return float(score.get("total_score", 0) for score in score_data["scores"].values())
    except Exception as e:
        print(f"[Judge API Fail] {e}")
        return 0.0

def build_judge_prompt(case_bg, case_q, pred_text, ref):
    return f"""病案：{case_bg}\n考题：{case_q}\n模型回答：{pred_text}\n专家标准：{ref}"""

if __name__ == "__main__":
    # 加载原始病案
    try:
        with open(GEN_DATA_PATH, "r", encoding="utf-8") as f:
            case_list = json.load(f)
    except FileNotFoundError:
        print(f"[File Load Fail] {GEN_DATA_PATH} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"[Json Parse Fail] Invalid file")
        sys.exit(1)
    print(f"Total test cases: {len(case_list)}")

    # 初始化生成模型客户端
    gen_client = OpenAI(base_url=GEN_BASE_URL, api_key=GEN_API_KEY)
    # 初始化两个独立评分客户端
    j1_client = OpenAI(base_url=JUDGE1_URL, api_key=JUDGE1_KEY)
    j2_client = OpenAI(base_url=JUDGE2_URL, api_key=JUDGE2_KEY)

    all_avg_total = []
    # 主循环：先生成答案，再双模型打分
    for case in case_list:
        cid = case["case_id"]
        bg = case["background"]
        q = case["question"]
        ref = case["reference_answer"]

        # Step1 生成模型输出
        gen_prompt = build_gen_prompt(bg, q)
        pred_out = gen_llm_call(gen_client, gen_prompt)
        print(f"Case {cid} Generated Finish")
        time.sleep(GEN_DELAY)

        # Step2 两个打分模型分别评分
        judge_prompt = build_judge_prompt(bg, q, pred_out, ref)
        s1 = judge_call(j1_client, JUDGE1_NAME, SCORE_SYS, judge_prompt)
        s2 = judge_call(j2_client, JUDGE2_NAME, SCORE_SYS, judge_prompt)
        case_avg = (s1 + s2) / 2
        all_avg_total.append(case_avg)
        print(f"Case {cid} Avg Score(Judge1={s1:.2f}, Judge2={s2:.2f}) = {case_avg:.2f}")

    # 输出全局所有病案平均分
    global_avg = sum(all_avg_total) / len(all_avg_total) if len(all_avg_total) > 0 else 0
    print("========================================")
    print(f"All Cases Average Final Score: {global_avg:.2f} / {TOTAL_FULL}")
    print("========================================")