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
PER_SCORE = 1.0
SYS_PROMPT = """你是中医临床专家，本题为多选题，输出全部正确大写字母，英文逗号分隔，仅输出字母，无多余文字"""
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

def calc_score(pred, std):
    # 多选题Jaccard比例计分
    std_set = set(std)
    pred_set = set(pred)
    inter = std_set & pred_set
    if len(inter) == 0:
        return 0.0
    ratio = len(inter) / max(len(std_set), len(pred_set))
    return round(ratio * PER_SCORE, 4)

def llm_api_call(client, prompt):
    # 云端API推理，简易重试
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role":"system","content":SYS_PROMPT},{"role":"user","content":prompt}],
            temperature=0, max_tokens=256, extra_body={"enable_thinking":False}
        )
        return resp.choices[0].message.strip()
    except Exception as e:
        print(f"[API Fail] {e}")
        time.sleep(1)
        return "ERROR"

# 本地模型替换接口
def llm_local_call(local_model, prompt):
    try:
        # 此处填入vLLM/Transformers本地推理代码
        return local_model.generate(prompt).strip()
    except Exception as e:
        print(f"[Local Model Fail] {e}")
        return "ERROR"

def build_prompt(item):
    # 拼接多选题题干
    opt_str = "\n".join(item["options"])
    return f"【多选题】{item['question']}\n【选项】{opt_str}\n仅输出答案字母："

if __name__ == "__main__":
    # 捕获文件、JSON解析异常
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            case_list = json.load(f)
    except FileNotFoundError:
        print(f"[File Load Fail] File {DATA_PATH} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"[Json Parse Fail] {DATA_PATH} invalid json format")
        sys.exit(1)
    print(f"Total test items: {len(case_list)}")

    # 初始化API客户端
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    total_get = 0.0
    total_max = 0.0
    full_correct = 0
    partial = 0
    wrong = 0

    # 核心评测循环
    for case in case_list:
        cid = case["case_id"]
        std_ans = case["answer"]
        std_list = std_ans if isinstance(std_ans, list) else [std_ans]

        prompt = build_prompt(case)
        model_out = llm_api_call(client, prompt)
        pred_list = parse_ans(model_out)

        score = calc_score(pred_list, std_list)
        total_get += score
        total_max += PER_SCORE

        if score == PER_SCORE:
            full_correct += 1
        elif score > 0:
            partial += 1
        else:
            wrong += 1

        print(f"ID:{cid} | Raw:{model_out} | Pred:{pred_list} | Std:{std_list} | Score:{score}")
        time.sleep(REQ_DELAY)

    # 控制台输出汇总
    accuracy = (total_get / total_max) * 100 if total_max > 0 else 0
    print("========================================")
    print(f"Total Score: {total_get}/{total_max}")
    print(f"Accuracy: {accuracy:.2f}%")
    print(f"Full Correct: {full_correct} | Partial Score: {partial} | Wrong: {wrong}")
    print("========================================")