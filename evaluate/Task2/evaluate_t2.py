# -*- coding: utf-8 -*-

import json
import time
import sys

# ========== 编码配置区 =========
DATA_PATH = ""
MODEL_NAME = ""
BASE_URL = ""
API_KEY = ""
REQ_DELAY = 0.3
SYS_PROMPT = "你是资深中医医师，根据完整多诊病案写300-400字病机叙述摘要，仅输出正文无多余文字"
BERT_MODEL = ""
# =====================================

# 依赖库导入校验
try:
    from openai import OpenAI
except ImportError:
    print("缺失依赖：pip install openai")
    sys.exit(1)
try:
    from rouge_chinese import Rouge
    import jieba
except ImportError:
    print("缺失依赖：pip install rouge-chinese jieba")
    sys.exit(1)
try:
    from bert_score import score
except ImportError:
    print("缺失依赖：pip install bert-score torch")
    sys.exit(1)

rouge = Rouge()

def split_cn_text(text):
    # 使用jieba对中文文本分词，适配rouge输入格式
    words = jieba.lcut(text.strip())
    return " ".join(words)

def calc_rouge_metrics(pred, ref):
    # 计算ROUGE-1、ROUGE-2、ROUGE-L的F值，并求三者平均值
    pred_seg = split_cn_text(pred)
    ref_seg = split_cn_text(ref)
    # 预测或参考文本为空时全部指标置0，避免库报错
    if not pred_seg or not ref_seg:
        return 0.0, 0.0, 0.0, 0.0
    res = rouge.get_scores(pred_seg)[0]
    r1 = round(res["rouge-1"]["f"], 4)
    r2 = round(res["rouge-2"]["f"], 4)
    rl = round(res["rouge-l"]["f"], 4)
    rouge_avg = round((r1 + r2 + rl) / 3, 4)
    return r1, r2, rl, rouge_avg

def calc_bert_f(pred, ref):
    # 基于中文BERT-wwm计算语义相似度F分数
    P, R, F = score([pred], [ref], model_type=BERT_MODEL, lang="zh")
    return round(float(F[0]), 4)

def calc_task3_final(rouge_avg, bert_f):
    # 官方综合得分计算公式
    return round(0.5 * (rouge_avg + bert_f), 4)

def llm_api_call(client, prompt):
    # 云端API接口调用，单次异常等待重试
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role":"system","content":SYS_PROMPT},{"role":"user","content":prompt}],
            temperature=0,
            max_tokens=1024,
            extra_body={"enable_thinking":False}
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[接口调用失败] {e}")
        time.sleep(1)
        return "ERROR_OUTPUT"

# 本地模型推理函数
def llm_local_call(local_model, prompt):
    try:
        return local_model.generate(prompt).strip()
    except Exception as e:
        print(f"[本地模型调用失败] {e}")
        return "ERROR_OUTPUT"

def build_prompt(bg, ins):
    # 拼接病案背景与答题要求，构造用户提问
    return f"""【完整多诊医案】
{bg}
【答题要求】
{ins}
直接输出摘要："""

if __name__ == "__main__":
    # 捕获文件不存在、JSON格式错误两类异常
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            case_list = json.load(f)
    except FileNotFoundError:
        print(f"[文件加载失败] File {DATA_PATH} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"[JSON解析失败] {DATA_PATH} invalid json format")
        sys.exit(1)
    print(f"Total test items: {len(case_list)}")

    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    all_final_scores = []

    for case in case_list:
        cid = case["case_id"]
        bg_text = case["background"]
        instr = case["instruction"]
        ref_text = case["reference_answer"]

        prompt = build_prompt(bg_text, instr)
        model_out = llm_api_call(client, prompt)

        # 计算本条所有评测指标
        r1, r2, rl, rouge_avg = calc_rouge_metrics(model_out, ref_text)
        bert_f = calc_bert_f(model_out, ref_text)
        s_task3 = calc_task3_final(rouge_avg, bert_f)

        all_final_scores.append(s_task3)
        print(f"ID:{cid} | R1:{r1} R2:{r2} RL:{rl} ROUGE_AVG:{rouge_avg} BERT_F:{bert_f} S_task3:{s_task3}")
        time.sleep(REQ_DELAY)

    # 计算全部病案综合平均分
    global_avg = sum(all_final_scores) / len(all_final_scores) if len(all_final_scores) > 0 else 0
    print("========================================")
    print(f"Global Average S_task3: {global_avg:.4f}")
    print("========================================")