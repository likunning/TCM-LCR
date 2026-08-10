# -*- coding: utf-8 -*-
import json
import time
import sys

# ========== 硬编码配置区 =========
DATA_PATH = ""
MODEL_NAME = ""
BASE_URL = ""
API_KEY = ""
REQ_DELAY = 0.3
PER_SCORE = 1.0
SYS_PROMPT = "你是中医专家，仅输出A-E单个大写字母，禁止额外文字"
# =====================================

# 导入OpenAI客户端并校验依赖
try:
    from openai import OpenAI
except ImportError:
    print("缺失依赖：pip install openai")
    sys.exit(1)

def parse_ans(raw):
    # 清洗模型输出文本，只保留A-E有效选项
    raw = raw.strip().upper()
    # 统一各类分隔符替换为英文逗号
    for s in ["、", "，", " ", ".", ";"]:
        raw = raw.replace(s, ",")
    res = [x.strip() for x in raw.split(",") if x.strip() in "ABCDE"]
    return list(set(res))

def calc_score(pred, std):
    # 打分规则：预测选项与标准答案完全匹配得满分，否则0分
    return PER_SCORE if set(pred) == set(std) else 0.0

def llm_api_call(client, prompt):
    # 云端API调用函数，出现异常简单等待后返回错误标识
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role":"system","content":SYS_PROMPT},{"role":"user","content":prompt}],
            temperature=0, max_tokens=256, extra_body={"enable_thinking":False}
        )
        return resp.choices[0].message.strip()
    except Exception as e:
        print(f"[接口调用失败] {e}")
        time.sleep(1)
        return "ERROR"

# 本地模型推理函数
def llm_local_call(local_model, prompt):
    try:
        # 此处填入vllm/transformers本地生成代码
        return local_model.generate(prompt).strip()
    except Exception as e:
        print(f"[本地模型调用失败] {e}")
        return "ERROR"

def build_prompt(item):
    # 拼接题目与选项
    opt_str = "\n".join(item["options"])
    return f"【题目】{item['question']}\n【选项】{opt_str}\n仅输出答案字母："

if __name__ == "__main__":
    # 加载数据集，捕获文件不存在、JSON格式错误异常
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

    # 初始化云端API客户端
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    total_get = 0.0    
    total_max = 0.0    
    correct_num = 0   

    # 核心评测循环
    for case in case_list:
        cid = case["case_id"]
        std_ans = case["answer"]
        # 兼容字符串、列表两种标准答案格式
        std_list = std_ans if isinstance(std_ans, list) else [std_ans]

        prompt = build_prompt(case)
        model_out = llm_api_call(client, prompt)
        pred_list = parse_ans(model_out)

        score = calc_score(pred_list, std)
        total_get += score
        total_max += PER_SCORE
        if score == PER_SCORE:
            correct_num += 1

        print(f"ID:{cid} | Raw:{model_out} | Pred:{pred_list} | Std:{std_list} | Score:{score}")
        time.sleep(REQ_DELAY)

    # 控制台输出最终汇总结果
    accuracy = (total_get / total_max) * 100 if total_max > 0 else 0
    print("========================================")
    print(f"Total Score: {total_get}/{total_max}")
    print(f"Accuracy: {accuracy:.2f}%")
    print(f"Correct Items: {correct_num}/{len(case_list)}")
    print("========================================")