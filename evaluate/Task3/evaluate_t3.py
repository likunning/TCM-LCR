# -*- coding: utf-8 -*-

import json
import time
import sys

# ========== Hardcode Config =========
DATA_PATH = ""
MODEL_NAME = ""
BASE_URL = ""
API_KEY = ""
REQ_DELAY = 0.3
PER_SCORE = 1.0  # 所有单选/多选统一单题满分1分
SYS_PROMPT = """你是中医临床专家，单选仅输出单个大写字母，多选英文逗号分隔字母，无任何多余文字"""
# 题型区分标识
SINGLE_TYPE = "illness_change"
# =====================================

try:
    from openai import OpenAI
except ImportError:
    print("Dep missing: pip install openai")
    sys.exit(1)

def parse_ans(raw):
    # 清洗输出，仅保留A-E有效选项
    raw = raw.strip().upper()
    for s in ["、", "，", " ", ".", "；", ";"]:
        raw = raw.replace(s, ",")
    res = [x.strip() for x in raw.split(",") if x.strip() in "ABCDE"]
    return list(set(res))

def calc_score(q_type, pred, std):
    """统一满分1分，单选完全匹配得1，多选Jaccard比例计分"""
    std_set = set(std)
    pred_set = set(pred)
    if q_type == SINGLE_TYPE:
        return PER_SCORE if pred_set == std_set else 0.0
    # 多选Jaccard规则
    inter = std_set & pred_set
    if len(inter) == 0:
        return 0.0
    ratio = len(inter) / max(len(std_set), len(pred_set))
    return round(ratio * PER_SCORE, 4)

def llm_api_call(client, prompt):
    # 云端API推理，简易单次重试
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role":"system","content":SYS_PROMPT},{"role":"user","content":prompt}],
            temperature=0,
            max_tokens=256,
            extra_body={"enable_thinking":False}
        )
        return resp.choices[0].message.strip()
    except Exception as e:
        print(f"[API Fail] {e}")
        time.sleep(1)
        return "ERROR"

# 本地模型替换接口，仅修改此函数即可
def llm_local_call(local_model, prompt):
    try:
        # 填入vLLM/transformers本地推理代码
        return local_model.generate(prompt).strip()
    except Exception as e:
        print(f"[Local Model Fail] {e}")
        return "ERROR"

def build_prompt(bg, q):
    opt_str = "\n".join(q["options"])
    tip = "（单选题）" if q["type"] == SINGLE_TYPE else "（多选题）"
    return f"""【病案背景】
{bg}
【题目】{tip}
{q['question']}
【选项】
{opt_str}
仅输出答案字母："""

if __name__ == "__main__":
    # 捕获文件、JSON加载异常
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            case_list = json.load(f)
    except FileNotFoundError:
        print(f"[File Load Fail] File {DATA_PATH} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"[Json Parse Fail] {DATA_PATH} invalid json format")
        sys.exit(1)
    print(f"Total case records: {len(case_list)}")

    # 初始化API客户端
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    # 全局总分统计
    total_got = 0.0
    total_max = 0.0

    # 主循环遍历每条医案记录
    for case in case_list:
        cid = case["case_id"]
        fid = case["form_id"]
        bg_text = case["background"]

        # 遍历本条所有题目
        for q in case["questions"]:
            qt = q["type"]
            std_ans = q["answer"]
            std_list = std_ans if isinstance(std_ans, list) else [std_ans]

            prompt = build_prompt(bg, q)
            model_out = llm_api_call(client, prompt)
            pred_list = parse_ans(model_out)

            score = calc_score(qt, pred_list, std_list)
            # 全局汇总分数
            total_got += score
            total_max += PER_SCORE

            print(f"Case{cid}-{fid} | Qtype:{qt} Raw:{model_out} Pred:{pred_list} Score:{score}")
            time.sleep(REQ_DELAY)

    # 输出全局总览
    global_acc = (total_got / total_max) * 100 if total_max > 0 else 0
    print("========================================")
    print("【全局总览】")
    print(f"总得分：{total_got:.2f} / {total_max:.0f}")
    print(f"全局综合正确率：{global_acc:.2f} %")
    print("========================================")