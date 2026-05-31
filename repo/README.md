# Adaptive Help-Seeking in AI-Enhanced MOOCs — Analysis Code

This repository contains the analysis code and intermediate result files for the manuscript:

> **Adaptive Help-Seeking in AI-Enhanced MOOCs: Evidence from Large-Scale Learning Analytics**
> Submitted to *Education and Information Technologies* (Springer)

The repository archives all code used to produce the empirical findings reported in the manuscript, including the analyses added or revised in response to peer review (within-group correlations, three-category decomposition, multilevel modelling, inter-rater reliability of the feedback classification, dose-response trend analysis, and tertile trends).

## Citation

If you use this code, please cite the manuscript as:

```
[Author(s)]. (2026). Adaptive help-seeking in AI-enhanced MOOCs: Evidence from
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

## Data availability
This study draws on the MOOCCubeX dataset (https://github.com/THU-KEG/MOOCCubeX). The raw behavioural files (`user-xiaomu.json`, `user-problem.json`) are not redistributed here; they can be obtained directly from MOOCCubeX.
The following derived datasets support the analyses in this repository:

- `combined_ai_learning_data.csv` — the main analytic dataset (16,389 students), used by the analysis scripts in `02_analysis/`. The code that constructs this file from `user-xiaomu.json` predates the present revision and is not included in this repository; the dataset itself is therefore provided directly, in the `02_analysis/` directory, so that the `02_analysis/` scripts can be run without it.
- `merged_three_category.csv` and `per_user_three_categories.csv` — per-user feature breakdowns derived from `user-xiaomu.json` according to the coding manual, used by `three_category_analysis.py` and `multilevel_analysis.py` respectively. Both are provided directly in the `02_analysis/` directory.
- `user_course_accuracy.csv` — the student-by-course dataset used by the multilevel analysis. This file is not redistributed in this repository. Two ways to obtain it: (a) download the copy provided as supplementary material with the manuscript submission (recommended for exact reproduction of the multilevel results), or (b) regenerate it from scratch by downloading `user-problem.json`, `problem.json`, and `course.json` from MOOCCubeX and running the scripts in `01_data_extraction/` in numerical order. Either way, place the file in the `02_analysis/` directory before running `02_analysis/multilevel_analysis.py`.

## Repository structure

```
.
├── README.md                          (this file)
├── LICENSE                            (GPL-3.0)
├── requirements.txt                   (Python dependencies)
├── .gitignore
│
├── 01_data_extraction/                Build the (user × course) accuracy dataset from raw MOOCCubeX
│   ├── README.md
│   ├── 01_inspect_files.py            Initial dataset inspection
│   ├── 01b_inspect_linkage.py         Verify problem→course linkage structure
│   ├── 01c_verify_id_match.py         Confirm ID-matching strategy
│   ├── 01d_deeper_inspection.py       Sample-level diagnostics
│   └── 02_extract_user_course_accuracy.py
│                                       Final extraction → user_course_accuracy.csv
│
├── 02_analysis/                       Analysis scripts (response to peer review)
│   ├── README.md
│   ├── combined_ai_learning_data.csv      Main analytic dataset (16,389 students; see Data availability)
│   ├── merged_three_category.csv          Per-user five-category breakdown (input to three_category_analysis.py)
│   ├── per_user_three_categories.csv      Per-user category shares (input to multilevel_analysis.py)
│   ├── within_group_analysis.py       Within-tertile correlations (Section 4.7.1)
│   ├── three_category_analysis.py     KG / Other Process / Task split (Section 4.7.2)
│   ├── multilevel_analysis.py         Mixed-effects with course as RE (Section 4.7.3)
│   ├── compute_irr.py                 Cohen's kappa for feedback classification (Section 3.4.4)
│   ├── dose_response_trends.py        Dose-response / threshold trends (Section 4.4)
│   ├── (user_course_accuracy.csv)         Not redistributed; input to multilevel_analysis.py; build via 01_data_extraction/ or obtain as supplementary material
│   └── tertile_trends.py              Reproduces Table 5 (tertile trends, Section 4.5)
│
├── 03_results/                        Output files used by the manuscript
│   ├── within_group_correlations.csv
│   ├── three_category_correlations.csv
│   ├── three_category_tertiles.csv
│   ├── three_category_ttests.csv
│   ├── multilevel_results_summary.csv
│   ├── multilevel_key_stats.txt
│   ├── multilevel_long_format.csv
│   ├── irr_side_by_side.csv
│   ├── irr_key_stats.txt
│   ├── dose_response_trends_results.csv
│   ├── dose_response_trends_summary.txt
│   ├── tertile_trends_results.csv
│   ├── tertile_trends_summary.txt
│   ├── Figure_within_group_correlations.png
│   ├── Figure_within_group_correlations.pdf
│   ├── Figure_three_category_analysis.png
│   └── Figure_three_category_analysis.pdf
│
└── 04_irr_materials/                  Inter-rater reliability materials
    ├── README.md
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

You will also need the derived datasets described under Data availability below. 

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

### Step 3 — Run the analysis scripts

```bash
cd 02_analysis/

python within_group_analysis.py     # Section 4.7.1
python three_category_analysis.py   # Section 4.7.2
python multilevel_analysis.py       # Section 4.7.3
python compute_irr.py               # Section 3.4 (requires Coding_Sheet_Coder*.xlsx)
python dose_response_trends.py      # Section 4.4
python tertile_trends.py            # Section 4.5
```

Each script writes its result files to 03_results/; most also produce a figure (Figure_*.png/.pdf) corresponding to the figures in the manuscript.

### Step 4 — Verify against the archived results

The expected outputs are archived in `03_results/`. Re-running the scripts on the same input data should reproduce these files identically.

## Key empirical findings (for reference)

The convergent finding across all the statistical robustness analyses is that the aggregate negative correlation between effective feedback usage and accuracy (*r* = −.102) is a between-group structural pattern, not a within-context effect:

| Analysis | Key result |
|---|---|
| Within-tertile correlation | All three tertile-internal correlations near zero (Low: *r* = +.008; Medium: *r* = +.005; High: *r* = −.018) |
| Three-category decomposition | The aggregate correlation is concentrated in Knowledge Graph Navigation (KG: *r* = −.107; other process-level: *r* = −.013); across all feedback levels a consistent gradient emerges (Self-Regulation: *r* = +.055; Self-level: *r* = +.033; Task-level: *r* = +.097), consistent with performance-based differential selection |
| Multilevel modelling | EF% effect on accuracy disappears (*b* = +.002, *p* = .85) once course is partialled out (*ICC* = .394) |
| Inter-rater reliability | Cohen's κ = .716 across two independent coders, 13 of 16 features with full agreement |

## License

The code in this repository is released under the GPL-3.0 License (see `LICENSE`), consistent with the upstream MOOCCubeX dataset. The MOOCCubeX dataset itself is governed by its own license; users must comply with that license when using the data.

## Contact

Issues and questions about reproducing the analyses are welcome via the GitHub Issues system.

For substantive questions about the manuscript, please contact the corresponding author (details in the published paper).

## Acknowledgements

We thank the MOOCCubeX team at Tsinghua University for making the dataset publicly available.

The robustness analyses in this repository were added in response to constructive peer review, and we thank the reviewers for the methodological suggestions that motivated each one.
