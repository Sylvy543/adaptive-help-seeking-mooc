# Adaptive Help-Seeking in AI-Enhanced MOOCs — Analysis Code

This repository contains the analysis code and intermediate result files for the manuscript:

> **Adaptive Help-Seeking in AI-Enhanced MOOCs: Evidence from Large-Scale Learning Analytics**
> Submitted to *Education and Information Technologies* (Springer)

The repository archives all code used to produce the empirical findings reported in the manuscript, including the four robustness analyses introduced in revision (within-group correlations, three-category decomposition, multilevel modelling, and inter-rater reliability of the feedback classification).

## Citation

If you use this code, please cite the manuscript as:

```
Sen Ye,Fuyun Song. (2026). Adaptive help-seeking in AI-enhanced MOOCs: Evidence from
large-scale learning analytics. Education and Information Technologies. [DOI to be added]
```

A persistent DOI for the code archive is available via Zenodo: `[DOI to be added at acceptance]`

## Data source

The analysis uses the publicly available [MOOCCubeX dataset](https://github.com/THU-KEG/MOOCCubeX), specifically:

- `relations/user-xiaomu.json` — 108,351 AI assistant interactions
- `relations/user-problem.json` — 22.45 GB of problem-attempt records
- `entities/problem.json` — Problem metadata (1.29 GB)
- `entities/course.json` — Course metadata (44.7 MB)

The MOOCCubeX dataset is **not** redistributed in this repository; users should obtain it directly from the source. Once downloaded, place the files in a directory at the path expected by the data extraction scripts (configurable in `01_data_extraction/01_inspect_files.py`).

## Repository structure

```
.
├── README.md                          (this file)
├── LICENSE                            (MIT)
├── requirements.txt                   (Python dependencies)
├── .gitignore
│
├── 01_data_extraction/                Build the analytic dataset from raw MOOCCubeX
│   ├── README.md
│   ├── 01_inspect_files.py            Initial dataset inspection
│   ├── 01b_inspect_linkage.py         Verify problem→course linkage structure
│   ├── 01c_verify_id_match.py         Confirm ID-matching strategy
│   ├── 01d_deeper_inspection.py       Sample-level diagnostics
│   └── 02_extract_user_course_accuracy.py
│                                       Final extraction → user_course_accuracy.csv
│
├── 02_analysis/                       Robustness analyses (response to peer review)
│   ├── README.md
│   ├── within_group_analysis.py       Within-tertile correlations (Section 4.6.1)
│   ├── three_category_analysis.py     KG / Other Process / Task split (Section 4.6.2)
│   ├── multilevel_analysis.py         Mixed-effects with course as RE (Section 4.6.3)
│   └── compute_irr.py                 Cohen's kappa for feedback classification
│                                       (Section 3.4)
│
├── 03_results/                        Output files used by the manuscript
│   ├── within_group_correlations.csv
│   ├── three_category_correlations.csv
│   ├── three_category_tertiles.csv
│   ├── three_category_ttests.csv
│   ├── multilevel_results_summary.csv
│   ├── multilevel_key_stats.txt
│   ├── irr_side_by_side.csv
│   └── irr_key_stats.txt
│
└── 04_irr_materials/                  Inter-rater reliability materials
    ├── Coding_Manual.docx             Codebook used by both coders
    ├── Coding_Sheet_Coder1.xlsx       Coder 1 independent classifications
    └── Coding_Sheet_Coder2.xlsx       Coder 2 independent classifications
```

## How to reproduce the analyses

### Prerequisites

- Python 3.9 or higher
- Approximately 50 GB of free disk space (for the raw MOOCCubeX files)
- The Python packages listed in `requirements.txt`

```bash
pip install -r requirements.txt
```

### Step 1 — Obtain the data

Download the MOOCCubeX dataset (see "Data source" above) and place the relevant files in a working directory. The data extraction scripts assume a structure like:

```
data/
└── MOOCCubeX/
    ├── relations/
    │   ├── user-xiaomu.json
    │   ├── user-problem.json
    │   └── user-video.json
    └── entities/
        ├── problem.json
        ├── course.json
        ├── concept.json
        └── user.json
```

You will also need the main analytic dataset `combined_ai_learning_data.csv` (16,389 rows, one per student), which is constructed from `user-xiaomu.json` and a subset of `user-problem.json`. The construction script for this file is not included here because it is part of the original analysis pipeline that predates this revision; the file itself is treated as input to the four robustness analyses below.

### Step 2 — Build the (user × course) accuracy dataset

Required only for the multilevel analysis.

```bash
cd 01_data_extraction/
python 01_inspect_files.py          # diagnostic; verifies file paths
python 01b_inspect_linkage.py       # confirms problem→exercise→course linkage
python 01c_verify_id_match.py       # confirms ID-matching strategy
python 02_extract_user_course_accuracy.py
```

This produces `user_course_accuracy.csv` (143,385 rows, one per `(user, course)` cell), used by the multilevel analysis.

### Step 3 — Run the four robustness analyses

```bash
cd 02_analysis/

python within_group_analysis.py     # Section 4.6.1
python three_category_analysis.py   # Section 4.6.2
python multilevel_analysis.py       # Section 4.6.3
python compute_irr.py               # Section 3.4 (requires Coding_Sheet_Coder*.xlsx)
```

Each script writes its result files to `03_results/` (existing files in the repository) and produces a figure (`Figure_*.png`/`.pdf`) corresponding to the figures in the manuscript.

### Step 4 — Verify against the archived results

The expected outputs are archived in `03_results/`. Re-running the scripts on the same input data should reproduce these files identically.

## Key empirical findings (for reference)

The convergent finding across all three statistical robustness analyses is that the aggregate negative correlation between effective feedback usage and accuracy (*r* = −.102) is a between-group structural pattern, not a within-context effect:

| Analysis | Key result |
|---|---|
| Within-tertile correlation | All three tertile-internal correlations near zero (Low: *r* = +.008; Medium: *r* = +.006; High: *r* = −.020) |
| Three-category decomposition | Knowledge Graph Navigation drives the aggregate correlation (KG: *r* = −.107; other process-level: *r* = −.013; self-regulation: *r* = +.006) |
| Multilevel modelling | EF% effect on accuracy disappears (b = +.002, *p* = .85) once course is partialled out (ICC = .394) |
| Inter-rater reliability | Cohen's κ = .716 across two independent coders, 13 of 16 features with full agreement |

## License

The code in this repository is released under the MIT License (see `LICENSE`). The MOOCCubeX dataset is governed by its own license; users must comply with that license when using the data.

## Contact

Issues and questions about reproducing the analyses are welcome via the GitHub Issues system.

For substantive questions about the manuscript, please contact the corresponding author (details in the published paper).

## Acknowledgements

We thank the MOOCCubeX team at Tsinghua University for making the dataset publicly available, and the two graduate student coders whose blind classification of AI features supported the inter-rater reliability analysis.

The robustness analyses in this repository were added in response to constructive peer review, and we thank the reviewers for the methodological suggestions that motivated each one.
