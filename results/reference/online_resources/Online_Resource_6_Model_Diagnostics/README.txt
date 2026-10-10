Online Resource 6 — Course-model diagnostics and leave-one-course-out sensitivity
Manuscript: Adaptive Help-Seeking in AI-Enhanced MOOCs: Evidence from Large-Scale Learning Analytics
Revision package: 8 October 2026

PURPOSE AND PRINCIPAL FINDINGS
This resource documents the course-model diagnostics and leave-one-course-out (LOCO) sensitivity referred to in Sections 4.7.3–4.7.4 and 5.5. The crossed student/course linear model remains the principal course-context analysis; the binomial fixed-course model is a sensitivity specification. Both use the full model sample of 1,983 student-course cells, 1,708 students and 396 courses selected by n_records >= 5 in OR5.

The crossed model partitions its estimated variance components into approximately 38.6% course, 21.1% student and 40.3% residual components, conditional on its fixed effects. These percentages are shares of the sum of estimated variance components, not shares of the total observed outcome variance. None of its five AI terms survives correction in the 48-test exploratory family supplied in OR7; the nominal Other Process association has p approximately .029 and q approximately .053.

The binomial sensitivity fit converged, with Pearson dispersion 10.01165. Excluding 22 courses identified by extreme success proportions or large course dummy coefficients left dispersion at 10.05615. Thus, excluding those courses did not resolve the overdispersion. The mean squared Pearson residual rises from 1.40077 in 5–9-record cells to 19.84643 in cells with at least 100 records. These diagnostics do not establish the source of overdispersion.

LOCO excludes, one at a time, the ten courses with the highest contributions to the full-sample sum of squared Pearson residuals. It does not exclude every one of the 396 courses. All ten fits converged. The ten courses account for 72.1773% of the full-sample Pearson sum; a large contribution depends partly on course size and does not itself identify an abnormal course.

Sign changes occur only for the Self-Regulation percentage coefficient, in three of the ten exclusions: C_737592, C_707456 and C_947252. Its full-sample estimate is -0.00209307 (p = .950519), already close to zero. KG Navigation, Other Process, Task-feature and log AI frequency retain their signs in all ten exclusions. LOCO dispersion ranges from 7.88700 to 11.07659. These are coefficient-stability checks, not evidence of causal effects or of statistical significance.

FILES
crossed_model_fixed_effects.csv — Six fixed-effect rows, including the intercept, from the crossed linear model. Outcome: course-cell accuracy on a 0–100 scale. bh_q_family48 is taken from the original 48-test family; it is blank for the intercept, which is outside that family. These are not q values recalculated over the rows of this file.
crossed_model_variance_components.csv — Course, student (labelled user in the source) and residual components and their conditional shares.
binomial_full_sample_coefficients.csv — Five AI terms from the patched full-sample binomial fit. Estimates are log-odds coefficients; se_cluster and the intervals use student-clustered robust covariance.
diagnostic_summary.csv — Sample sizes and retained dispersion summaries.
loco_sensitivity.csv — One row per excluded course, with convergence, warnings, dispersion, estimates, standardized changes and sign-change flags.
loco_sign_change_summary.csv — One row per AI term, with the full-sample reference, count/list of sign-changing exclusions and coefficient range.
high_contribution_courses.csv — All 396 courses ranked by Pearson contribution. The first ten define the LOCO exclusions. mean_success is the unweighted mean of cell success proportions within the course; separated is the source's extreme-mean flag, not an independent proof of separation.
extreme_courses.csv — The 22 courses selected for the separate extreme-course exclusion check. Selection is the union of mean cell success > .995 or < .005 and absolute fitted course dummy coefficient > 15. This set differs from the LOCO course set.
binomial_refit_comparison.csv — Full versus extreme-course-excluded coefficients and unadjusted p values for the five AI terms.
dispersion_by_cell_size.csv — Cells grouped by number of valid binary response records, with mean squared Pearson residuals.
optimizer_stability.csv — Five optimizers for each of the two course-only random-intercept linear specifications; not five refits of the crossed model. Retained warnings must be read alongside estimates and convergence.
extended_variance_profile_course_mixed_course_random.csv — Extended profile for the course-only composition model.
extended_variance_profile_course_mixed_kg_course_random.csv — Extended profile for the course-only KG specification. In both profile files the grid extends toward small positive variances; it does not evaluate a literal zero-variance point and should not be presented as a formal boundary test.
course_random_vs_crossed.csv — Fixed-effect comparison between the course-only composition model and crossed model.
single_course_recheck.csv — A separate sensitivity analysis choosing one eligible cell per student: the cell with the largest n_records, ties broken by the smallest course_id. This yields 1,708 cells. L-BFGS and BFGS estimates/intervals are close; the L-BFGS singular-covariance warning is retained rather than suppressed. This is not LOCO.

VARIABLES AND UNITS
The feature percentages and AI frequency describe overall student usage and repeat across that student's course cells. They are not within-course AI-use measurements. See OR5 for the field dictionary and the distinction between course-cell accuracy and student-level strict_accuracy_pct.
kg_pct10, other_process_pct10, task_pct_neutral10 and selfreg_pct_neutral10 are percentages divided by 10, so each unit is 10 percentage points of usage share. log_ai_frequency is ln(1 + ai_frequency). Linear-model estimates are accuracy percentage points; binomial estimates are log odds and are not numerically comparable to linear coefficients.
Each LOCO change_in_se_units is (excluded-course estimate minus full-sample estimate) / full-sample student-clustered standard error. Positive/negative signs therefore refer to movement relative to that full-sample coefficient.
Empty fields indicate unavailable or inapplicable values, not zero. Boolean columns retain their source values. Marginal confidence intervals are not simultaneous or BH-adjusted intervals.

CORRECTIONS AND PROVENANCE
This package retains the original student-clustered covariance for the binomial model. The earlier dispersion_scaled_terms.csv and the scaled_terms block in the original run03 summary were withdrawn because they rescaled standard errors that were already cluster-robust; neither is included here. The earlier narrow profile grids are superseded by the extended grids. A high Pearson contribution does not identify an abnormal course, and the cause of overdispersion remains undetermined.
Sources: final run02 model estimates/status; run03 diagnostics and the 03b patch; run04b single-course recheck. See docs/OR_TABLE_SOURCES.csv for the reproduction recipe and source hashes, and CHECKSUMS.sha256 for distributed-file integrity. python run.py reproduce refits and validates the models against these reference results.

中文使用说明
本资源对应课程模型诊断与留一课程敏感性分析。查看结论先读本说明；三次符号变化的课程名单见 loco_sign_change_summary.csv；各次排除结果见 loco_sensitivity.csv。LOCO仅针对Pearson贡献最大的10门课程。切勿把线性模型的准确率百分点系数与二项模型的log-odds系数混用。
