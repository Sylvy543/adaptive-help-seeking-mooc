# Adaptive Help Seeking in AI Enhanced MOOCs

This repository accompanies the revised manuscript **Adaptive Help-Seeking in AI-Enhanced MOOCs: Evidence from Large-Scale Learning Analytics**. It supplies the final analysis inputs, executable Python analyses, coding materials, archived results and figures. It supersedes the earlier repository that used historical accuracy and a course-only primary model.

All analyses are observational and exploratory. The primary course-context model is the crossed student/course linear mixed model. The fixed-course binomial model is a sensitivity analysis. A negative aggregate association does not establish a causal effect or a Simpson mechanism; the performance bands are defined on the outcome itself.

## Run the final analyses

Use Python 3.13.5 for the tested environment. Start a terminal in this repository folder, then run:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run.py verify
python run.py reproduce
```

On Windows, activate with `.venv\Scripts\activate` instead. Use the same Python interpreter for installation and execution. The supplied requirements pin the packages tested for this release; they do not install Python itself.

The `verify` command checks file integrity and key data/statistical controls without refitting. The `reproduce` command rebuilds the strict analysis variables from the supplied derived inputs, refits models, runs all retained diagnostics and the full 10,000-resample bootstrap checks, curates final OR4–OR7 tables, compares all final tables with their references, and redraws the figures. It does not substitute archived coefficients or bootstrap intervals for newly computed results. Allow several minutes or longer depending on hardware.

Outputs go to `outputs/`, with progress and warnings in `outputs/logs/`. Final numerical tables are in `outputs/online_resources/`; the machine-readable comparison is `outputs/comparison.json`. Neither archived reference results nor input files are overwritten. Repeated runs overwrite generated output files in the selected output directory; use `--work /path/to/new/output` to keep runs separate.

## Files and scope

| Location | Contents |
|---|---|
| `run.py` | Command-line entry point |
| `analysis/` | Raw reconstruction, strict models, diagnostics, sensitivity analyses, IRR and final table generation |
| `data/inputs/` | Audited student counts, feature counts, unique-course binary response counts and historical feature mapping |
| `materials/` | OR1 coding manual, unchanged OR2 coder workbooks, adjudications and OR3 report |
| `online_resources/` | Submission-format Online Resources package (OR1–OR7) mirrored for reviewer access; content identical to `materials/` and the CSV tables |
| `results/reference/online_resources/` | Final OR4–OR7 numerical tables as CSVs, with field dictionaries |
| `results/reference/pipeline/` | Supporting archived stage results for checking and figure reconstruction |
| `figures/published/` | Author-supplied latest Figure 1–6 and OR3 Figure 1, in PNG and PDF |
| `figures/scripts/` | Portable redraw scripts |
| `docs/ANALYSIS_MAP.md` | Manuscript/OR-to-code mapping and stage order |
| `docs/VALIDATION.md` | Validation actually performed for this release |
| `CHECKSUMS.sha256` | Checksums for distributed files, excluding itself and generated outputs |

The submission OR5–OR7 workbooks and the CSV tables here represent the same datasets. Separate CSVs are intentional in the code repository so scripts do not require manual Excel export. OR5 has four CSVs; OR6 has 15; OR7 has 19. Original worksheet labels and CSV names are mapped in `docs/WORKSHEET_MAP.csv`. The repository also includes all four OR4 CSVs. Filenames containing `attempts` refer to **valid binary response-record counts**, not the sum of the raw `attempts` field or a count of unique questions.

## Definitions that affect reproduction

- Student strict accuracy is `100 * strict_correct_records / strict_valid_records`. Historical accuracy is retained only for comparison.
- Course-cell `accuracy` and `accuracy_pct` are `100 * n_correct / n_records`. The repeated student-level `strict_accuracy_pct` field is not the course-cell outcome.
- The main student sample contains 16,389 students and 85,815 AI interactions. The course input has 2,496 cells; `n_records >= 5` selects 1,983 cells, 1,708 students and 396 courses.
- Feature shares include unclassified Other in their denominator. Historical author, neutral feature and complete coder-anchored mappings are distinct. Four Baike-variant interactions retain their historical Process assignment only where that historical mapping is intended.
- Fixed performance bands are Low `<67.5%`, Medium `67.5%–84%` inclusive, and High `>84%`, with 5,540/5,467/5,382 students. They approximate thirds but are not newly estimated exact terciles.
- The 48-test and 60-test BH families remain separate. Confidence intervals are marginal, not BH-adjusted or simultaneous. Spearman intervals use paired-row bootstrap with ranks recomputed; Pearson intervals use Fisher z where specified.
- LOCO excludes the ten largest Pearson-contributing courses one at a time, not all 396 courses. Only the near-zero Self-Regulation coefficient changes sign, in three exclusions.
- Variance shares of about 38.6% course, 21.1% student and 40.3% residual are conditional shares of estimated variance components, not proportions of total observed outcome variance.
- OR4 Welch differences are Low minus High; OR7's selected comparison table is High minus Low. Opposite signs are intentional.

## Rebuild from raw data

Raw MOOCCubeX files are not redistributed. Obtain them from the dataset maintainers at [MOOCCubeX](https://github.com/THU-KEG/MOOCCubeX), then run:

```bash
python run.py raw --raw-dir /path/to/MOOCCubeX --work outputs/raw_run
python run.py reproduce --from-raw --work outputs/raw_run
```

Expected layout:

```text
MOOCCubeX/
  relations/user-xiaomu.json
  relations/user-problem.json
  entities/problem.json
  entities/course.json
```

If the response log is stored elsewhere, add `--responses /path/to/user-problem.json`. The reconstruction scans the complete response file, uses binary correctness and unique problem-to-course links, and retains response records rather than deduplicating user–question pairs. It writes SHA256 hashes of the scanned raw files. The supplied `feature_mapping_audit.csv` records the historical tag mapping; unknown feature labels fail explicitly. The code targets the dataset used for the paper, not arbitrary later dataset versions.

## Figures

The exact supplied final figures are in `figures/published/`. Run `python run.py figures` to redraw from archived numerical inputs without refitting, or `python run.py reproduce` to draw from newly computed outputs. Drawn image pixels, font metrics and PDF metadata can differ across systems and from manually adjusted publication layouts; agreement is assessed on numerical data and labels rather than byte-identical images. The redraw scripts do not overwrite the supplied publication files.

## Corrections and interpretation

Withdrawn dispersion-rescaled cluster-robust standard errors, the old effective-feedback numerator that added Other, and Fisher-z Spearman intervals are not final outputs. Stage03 no longer computes the withdrawn standard errors. Stage04 retains only its valid alternative OLS models. Stage05 leaves non-bootstrap Spearman intervals pending; stage08 computes their final bootstrap intervals and the curator inserts them. Intermediate 44-test selection in stage04b is completed and corrected to the final 48-test family by stage04c. Use the curated `online_resources` tables when reporting results.

Warnings from statistical fits are retained in logs and diagnostic tables. A completed fit does not establish construct validity or a causal mechanism. Small numerical differences can arise from numerical libraries; comparison tolerances are documented in `tools/compare_results.py`.

## Attribution and license

Analysis code retains the original repository's GPL-3.0 license; see `LICENSE`. The MOOCCubeX source data remain subject to their original terms. This local archive does not create a new dataset or publication DOI. Cite the manuscript using its actual author list and publication details when available.
