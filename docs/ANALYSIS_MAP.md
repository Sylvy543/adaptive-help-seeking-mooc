# Analysis map

| Manuscript or resource | Implementation | Final results |
|---|---|---|
| Strict accuracy, §3.4.1; OR5 | `rebuild_inputs.py`, `02_strict_models.py`, `curate_online_resources.py` | Four OR5 tables, including exact integer-ratio change flags |
| Raw coding agreement, §3.4.4; OR1–2 | `compute_irr.py` | `run06_outputs/run06_summary.json`; κ=.716, 13/16 agreements |
| Deterministic author remapping; OR1 A.5 | `compute_irr_author_final.py` | `run09_outputs/author_final_irr.json`; .743/.668/.755, mean .712 |
| Frequency checks, §4.2/4.4 | `08_final_checks.py` | OR7 frequency operationalisations, HC3 trends and Tukey comparisons |
| High/low historical EF share, §4.3 | `07_table6_trend_cis.py` | `run07_outputs/section43_group_comparison.csv`; strict and historical outcome comparisons |
| Performance trends, §4.5/Table 6 | `07_table6_trend_cis.py` | `run07_outputs/` |
| KG classification sensitivity, §4.6; OR3 | `04b_corrections.py`, `04c_mapping_and_pvalues.py`, `OR3_recompute_and_plot.py` | OR7 correlations; regenerated OR3 descriptive tables and figure |
| Within-performance groups, §4.7.1 | `curate_online_resources.py` | OR7 within-group table |
| Feature decomposition, §4.7.2; OR4 | `three_category_analysis.py`, `curate_online_resources.py` | Four OR4 CSVs |
| Coder-anchored sensitivity | `04c_mapping_and_pvalues.py` | OR7 feature mapping, student counts and correlations |
| Crossed model, §4.7.3 | `02_strict_models.py` | OR6 fixed effects and conditional variance components |
| Course diagnostics/LOCO, §4.7.4/5.5 | `03_diagnostics.py`, `03b_diagnostics_patch.py` | OR6 diagnostics; ten exclusions and three near-zero sign changes |
| Single-course-per-student sensitivity | `04b_corrections.py` | OR6 single-course two-optimizer recheck |
| Response-record robustness, §4.7.5 | `05_attempts_stratified.py`, `08_final_checks.py` | OR7 stratified, subsample and weighted results |
| Multiple testing | `04c_mapping_and_pvalues.py`, `08_final_checks.py` | Separate OR7 48-test and 60-test tables |

All filenames in the implementation column are under `analysis/`. Stage numbers retain their original provenance; the runner supplies their working directories in dependency order. Stage03b supersedes the narrow stage03 profile interpretation. Stage04b produces an intermediate unique-test list; stage04c supplies final p/q values. Stage08 completes the Spearman intervals. Only after these dependencies finish does the curator build final OR tables.

Publication figures 1–6 are copied from the author-supplied latest fig folder; OR3 Figure 1 is supplied with them. Their hashes are in the repository checksums. Raw coder workbooks are unchanged; the OR1 manual includes explicitly labelled revision notes and author mapping explanations.

Intermediate stage outputs are diagnostic work products. A stage's historical summary may describe its local test list or correction step; it does not supersede the final 48/60-family definitions. Data tables contain student or student-course units as documented in each resource README.
