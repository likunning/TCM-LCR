# TCM-LCR
## Project Introduction
TCM-LCR benchmark comes with supporting evaluation datasets and lightweight prototype evaluation scripts.

## Project Directory Structure
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

## Directory Explanation
- `data/`: The full official benchmark dataset of TCM-LCR, including annotated data for four subtasks;
- `evaluate/`: Supporting prototype evaluation scripts for TCM-LCR, with built-in standardized evaluation rules, scoring logic and metric calculation implementations.

## License
Please refer to the `LICENSE` file in the root directory for detailed license terms.
