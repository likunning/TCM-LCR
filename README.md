# TCM-LCR 中医纵向临床推理评测基准
## 项目简介
TCM-LCR（中医纵向临床推理评测基准），本项目内置配套评测数据集与轻量化评测原型脚本，针对中医大模型的临床辨证、病案理解、诊疗逻辑推演能力进行标准化量化测评。

## 项目目录结构
```
├── data/
│   ├── Task1/
│   │   ├── TCM_T1_mutiple_v1.json
│   │   └── TCM_T1_single_v1.json
│   ├── Task2/
│   │   └── TCM_T2_abstract_v1.json
│   ├── Task3/
│   │   └── TCM_T3_coherence_v1.json
│   └── Task4/
│       └── TCM_T4_prescription_v1.json
├── evaluate/
│   ├── Task1/
│   │   ├── evaluate_t1_multiple.py
│   │   └── evaluate_t1_single.py
│   ├── Task2/
│   │   └── evaluate_t2.py
│   ├── Task3/
│   │   └── evaluate_t3.py
│   └── Task4/
│       └── evaluate_t4.py
├── .gitignore
├── LICENSE
└── README.md
```

## 目录释义
- `data/`：TCM-LCR 整套官方评测基准数据集，包含四大细分任务标注数据；
- `evaluate/`：TCM-LCR 配套评测原型脚本，内置标准化评测规则、打分逻辑与指标计算实现。

## 开源协议
详细协议内容查阅项目根目录内 `LICENSE` 文件。

