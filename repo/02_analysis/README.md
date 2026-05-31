# 02_analysis

The robustness and trend analyses introduced in revision in response to peer review. Each script is self-contained and produces both result files (in `../03_results/`); some also produce figures (PNG and PDF). Each script corresponds to a specific subsection of the manuscript.

## Scripts

### `within_group_analysis.py` — Section 4.7.1

Tests whether the aggregate negative correlation between effective feedback usage and accuracy (*r* = −.102) is observable within each performance tertile, or whether it is purely a between-group structural pattern. **Reviewer 2 specifically recommended this analysis to test the Simpson's paradox interpretation.**

**Key finding**: All three within-tertile correlations are near zero (Low: *r* = +.008; Medium: *r* = +.005; High: *r* = −.018), versus the aggregate −.102. The mean within-tertile *r* is −.002. The between-tertile correlation is −.881. Confirms that the aggregate correlation is structural.

**Inputs**: `combined_ai_learning_data.csv`
**Outputs**: `within_group_correlations.csv`, `Figure_within_group_correlations.{png,pdf}`

### `three_category_analysis.py` — Section 4.7.2

Decomposes the original "Process-level feedback" category to test whether the aggregate correlation is feature-specific or category-general. The decomposition separates Knowledge Graph Navigation from Other Process-level features (MOOCCube concept search, Aminer academic search), and reports each of the five feedback categories (KG Navigation, Other Process, Task-level, Self-Regulation, Self-level) against accuracy.

**Key finding**: The aggregate negative correlation is concentrated in Knowledge Graph (KG) Navigation specifically (*r* = −.107), while Other Process shows no significant correlation (*r* = −.013). Across all feedback levels, usage proportions form a consistent gradient with respect to accuracy: process-level engagement is negatively correlated (Process %: *r* = −.121), whereas the more self-directed and task-oriented levels are positively correlated (Self-Regulation: *r* = +.055; Self-level: *r* = +.033; Task-level: *r* = +.097; all *p* < .001), consistent with performance-based differential selection across feedback levels. KG Navigation accounts for 80.9% of process-level interactions in aggregate (total KG interactions / total process interactions), with a per-user mean share of 77.82% and a per-user median of 100%.

**Inputs**: `combined_ai_learning_data.csv`, `merged_three_category.csv` (per-user five-category breakdown provided in the `02_analysis/` directory)
**Outputs**: `three_category_correlations.csv`, `three_category_tertiles.csv`, `three_category_ttests.csv`, `Figure_three_category_analysis.{png,pdf}`

### `multilevel_analysis.py` — Section 4.7.3

Fits linear mixed-effects models with course as a random intercept on a long-format dataset of (user × course) accuracy cells. Tests whether the EF→accuracy relationship is robust to controlling for course-level variance.

**Key finding**: ICC = .394 (39.4% of accuracy variance is between-course). The OLS coefficient on EF% (b = −.056, *p* < .001) reduces to b = +.002 (*p* = .85) after partialling out course. The negative relationship vanishes once course-level variance is accounted for.

**Inputs**: `combined_ai_learning_data.csv`, `per_user_three_categories.csv` (provided in the `02_analysis/` directory), `user_course_accuracy.csv` (not included in this repository; either build via `01_data_extraction/` or use the copy provided as Online Resource 5 with the manuscript submission)
**Outputs**: `multilevel_results_summary.csv`, `multilevel_key_stats.txt`, `multilevel_long_format.csv`

### `compute_irr.py` — Section 3.4.4

Computes Cohen's kappa between two independent coders' classifications of the 16 distinct AI features, using the Hattie & Timperley (2007) feedback framework. Reports the κ point estimate, a 95% bootstrap confidence interval (10,000 resamples), the raw percent agreement, and a per-item disagreement table.

**Key finding**: κ = .716, 95% bootstrap CI [.417, 1.000], 13 of 16 items agreed (81.2%). Substantial agreement (Landis & Koch, 1977). Three disagreements (Turing Bot, Aminer, TA Answer Browser) were resolved by adjudication.

**Inputs**: `Coding_Sheet_Coder1.xlsx`, `Coding_Sheet_Coder2.xlsx` (in `../04_irr_materials/`)
**Outputs**: `irr_side_by_side.csv`, `irr_key_stats.txt` (no figure is produced by this script; Figure 1 in the manuscript was prepared manually)

### `compute_irr_author_final.py` — Section 3.4.4 (companion to compute_irr.py)

Reports a second κ under the author-final classification scheme documented
in Online Resource 1, Appendix A. The script remaps each coder's "Other"
classifications to the closest Hattie–Timperley level per Appendix A.2,
then recomputes κ.

**Key finding**: κ (author-final, Coder 1 vs Coder 2) = .743, 95% bootstrap
CI similar to raw. Mean κ (coders vs author-final classification) = .796.
The author-final reliability is equal to or slightly higher than the raw
five-category κ = .716.

**Inputs**: `Coding_Sheet_Coder1.xlsx`, `Coding_Sheet_Coder2.xlsx`
**Outputs**: `irr_author_final_side_by_side.csv`, `irr_author_final_key_stats.txt`

### `dose_response_trends.py` — Section 4.4 (RQ3)

Tests linear dose-response and quadratic threshold effects of AI usage intensity on accuracy, using OLS polynomial trend regression on the seven ordered usage bands.

**Key finding**: Neither the linear trend (β = 0.12, *p* = .45) nor the quadratic term (β = −0.01, *p* = .92) is significant, consistent with the one-way ANOVA (*F*(6, 16382) = 1.22, *p* = .29). No dose-response or threshold relationship.

**Inputs**: `combined_ai_learning_data.csv`
**Outputs**: `dose_response_trends_results.csv`, `dose_response_trends_summary.txt`

### `tertile_trends.py` — Section 4.5 (RQ4) / Table 5

Reproduces manuscript Table 5 in full: tertile means, SDs, and the linear-trend coefficient (β, SE, t, p) for all eleven row variables across performance tertiles. Tertiles use fixed accuracy cutpoints at 67.5% and 84.0%. Supersedes the earlier `predominantly_usage_trends.py`.

**Key finding**: Ten of the eleven trends are significant at *p* < .001; only the AI Frequency trend is non-significant (β = +0.17, *p* = .37).

**Inputs**: `combined_ai_learning_data.csv`
**Outputs**: `tertile_trends_results.csv`, `tertile_trends_summary.txt`

## Running

Each script is independent and can be run in any order. From the repository root:

```bash
cd 02_analysis/
python within_group_analysis.py
python three_category_analysis.py
python multilevel_analysis.py
python compute_irr.py
python dose_response_trends.py
python tertile_trends.py
```

Each script prints progress to stdout. Total runtime for all six: approximately 5–10 minutes on a modern laptop.

## Where the figures end up

Each script that produces a figure writes it to its working directory. Manuscript figures are numbered in order of appearance in the text, so the figure numbers below differ from the order in which the scripts are listed in this README:

| Script | Manuscript location | Figure number |
|---|---|---|
| `within_group_analysis.py` | Section 4.7.1 | Figure 4 |
| `three_category_analysis.py` | Section 4.7.2 | Figure 5 |

Figures not produced by scripts in this directory:
- **Figure 1** (IRR summary, Section 3.4.4) was prepared manually; `compute_irr.py` produces the underlying statistics (κ, CI, agreement table) but no figure.
- **Figures 2 and 3** (Sections 4.2 and 4.4) are generated by the original analysis pipeline that predates this revision.
- **Figure 6** (Section 4.7.3) was prepared manually; `multilevel_analysis.py` produces the underlying statistics (ICC, fixed-effect coefficients in `multilevel_results_summary.csv` and `multilevel_key_stats.txt`) but no figure.

## Reproducibility note

All analyses use REML estimation where applicable, and all bootstrap CIs use a fixed random seed (`np.random.seed(42)`). Re-running on the same input data will reproduce the archived results in `../03_results/` exactly.