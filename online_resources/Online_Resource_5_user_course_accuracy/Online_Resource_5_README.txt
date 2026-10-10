Online Resource 5 — Student-by-course data for the revised analyses
Manuscript: Adaptive Help-Seeking in AI-Enhanced MOOCs: Evidence from Large-Scale Learning Analytics
Prepared: 7 October 2026; expanded: 8 October 2026; workbook packaging updated: 9 October 2026

FILE AND SCOPE
OR5_Accuracy_Data.xlsx is the delivered data file. It contains four worksheets:
1. User-course accuracy — the 2,496-row student-course model input.
2. Student comparison — the 16,389-row historical-versus-strict accuracy comparison.
3. Definition summary — the full-student outcome-definition summary.
4. Correlation comparison — associations under the two outcome definitions.
The four tables are consolidated in this workbook; separate CSV files are not included in this OR5 folder. The code repository provides the corresponding CSV tables for scripted reproduction.

The User-course accuracy worksheet contains 2,496 student-by-course cells (2,092 students; 461 courses) from the revised analysis input strict_course_model_data.csv. This replaces the earlier 143,385-row OR5 extract as the data accompanying the revised course-level analyses.

The original 24 columns and their numerical values are retained. One column, included_primary_model, is added, giving 25 columns in total. Identifiers and row order are retained to support linkage with the analysis code. Floating-point precision is retained; accuracy is not rounded to two decimal places.

Each row represents one student in one course. Only response records with valid binary correctness (0 or 1) and an unambiguous unique-course linkage contribute to the course-cell counts. The course cells are merged with the revised student-level AI usage data. AI feature measures describe each student's overall observed AI use, not use measured separately within each course; these measures therefore repeat across a student's course rows.

FINAL MODEL SAMPLE
included_primary_model = 1 if n_records >= 5, and 0 otherwise.
Selecting included_primary_model == 1 gives 1,983 cells, 1,708 students and 396 courses, matching the full-sample crossed linear model. The other 513 cells remain in this file so the threshold can be reproduced. This flag identifies the full-sample inclusion rule, not the reduced samples used in course-exclusion or other sensitivity checks.

IMPORTANT DISTINCTION BETWEEN OUTCOMES
accuracy and accuracy_pct both measure STUDENT-BY-COURSE accuracy: 100 * n_correct / n_records. The crossed linear model uses accuracy as its outcome.

strict_accuracy_pct is the STUDENT-LEVEL OVERALL strict accuracy merged into the course table. It is not the course-cell outcome and must not replace accuracy in the course model.

historical_accuracy_pct is the STUDENT-LEVEL OVERALL historical accuracy, retained for audit purposes. It is not used as the outcome of the revised course model.

FIELD DEFINITIONS
user_id: Student identifier retained from the analysis input; a string.
course_id: Course identifier retained from the analysis input; a string.
n_records: Number of valid binary response records in this student-course cell. This counts response records, not necessarily distinct questions.
n_correct: Number of those records with correctness equal to 1.
accuracy_pct: Course-cell strict accuracy on a 0–100 scale; equals 100 * n_correct / n_records.
strict_accuracy_pct: Student-level overall strict accuracy on a 0–100 scale; retained for reference, not the course-model outcome.
historical_accuracy_pct: Student-level overall historical accuracy on a 0–100 scale; retained for audit, not the course-model outcome.
ai_frequency: Student-level total AI interaction count.
log_ai_frequency: Natural logarithm of 1 + ai_frequency.
kg_pct: Student-level KG Navigation share of all AI interactions, on a 0–100 scale.
other_process_pct: Student-level MOOCCubeX concept-search and Aminer academic-search share of all AI interactions, on a 0–100 scale.
task_pct_neutral: Student-level Task-feature share under the neutral feature grouping, on a 0–100 scale.
selfreg_pct_neutral: Student-level Self-Regulation share under the neutral feature grouping, on a 0–100 scale; this retains the historical author-level Self-Regulation assignments, not the strictly coder-anchored alternative.
self_pct_neutral: Student-level Self-feature share under the neutral feature grouping, on a 0–100 scale.
other_pct_neutral: Student-level unclassified Other share under the neutral feature grouping, on a 0–100 scale; distinct from other_process_pct.
kg_count: Student-level KG Navigation interaction count.
other_process_count: Student-level MOOCCubeX concept-search and Aminer academic-search interaction count.
accuracy: Course-cell strict accuracy on a 0–100 scale; equals accuracy_pct and is the crossed linear model outcome.
success_prop: Course-cell success proportion on a 0–1 scale; n_correct / n_records.
n_failure: Number of incorrect binary response records in the course cell; n_records - n_correct.
kg_pct10: kg_pct / 10.
other_process_pct10: other_process_pct / 10.
task_pct_neutral10: task_pct_neutral / 10.
selfreg_pct_neutral10: selfreg_pct_neutral / 10.
included_primary_model: Integer inclusion flag, 1 for n_records >= 5 and 0 otherwise.

SHARES AND SCALING
All feature-share denominators include all of a student's AI interactions, including unclassified Other. The six shares kg_pct, other_process_pct, task_pct_neutral, selfreg_pct_neutral, self_pct_neutral and other_pct_neutral sum to 100, subject to floating-point precision.

The neutral feature grouping is the grouping used by the revised feature-level course models. It is not the strictly coder-anchored alternative documented in OR1. In particular, the four-record Baike-variant difference from the historical Process/Task mapping is already represented in the supplied variables. Do not recompute or substitute a different mapping when reproducing these models.

A one-unit increase in a variable ending in pct10 represents 10 percentage points of usage share. log_ai_frequency is not divided by 10. The model includes four shares and omits the combined Self/Other remainder, so share coefficients describe conditional compositional associations.

REPRODUCING THE SAMPLE
Python/pandas:
    import pandas as pd
    df = pd.read_excel('OR5_Accuracy_Data.xlsx',
                       sheet_name='User-course accuracy',
                       dtype={'user_id': str, 'course_id': str})
    assert (df['included_primary_model'] == (df['n_records'] >= 5).astype(int)).all()
    d = df.loc[df['included_primary_model'] == 1].copy()
    assert (len(d), d['user_id'].nunique(), d['course_id'].nunique()) == (1983, 1708, 396)
    d['all_group'] = 1

The crossed linear model's fixed-effects formula is:
    accuracy ~ kg_pct10 + other_process_pct10 + task_pct_neutral10 + selfreg_pct_neutral10 + log_ai_frequency

The original statsmodels specification uses groups='all_group', re_formula='0', vc_formula={'user': '0+C(user_id)', 'course': '0+C(course_id)'}, use_sparse=True, and REML. The constant all_group is constructed in the code; it is not an additional grouping variable in the source data. See the accompanying analysis code for optimizer settings and diagnostics.

The binomial fixed-course sensitivity specification uses n_correct and n_failure as its two-column response, course fixed effects and student-clustered covariance. Do not use rounded accuracy as binomial counts or fit the crossed linear model to success_prop without changing the interpretation and scaling.

PROVENANCE AND VERIFICATION
Source: run02_outputs/strict_course_model_data.csv from the revised analysis results.
This source was checked against the corresponding project copy. The export preserves all original fields and numerical values and adds only included_primary_model. Checks covered unique student-course keys, finite numeric values, response counts, accuracy reconstruction, logarithms, share denominators, 10-percentage-point scaling, repeated student-level covariates and the final sample sizes. This packaging step does not rerun or alter the fitted models.

使用说明（中文）
1. 本 OR5 以 OR5_Accuracy_Data.xlsx 和本 README 一并交付；四张数据表已合并为四个工作表，无需另附旧 CSV。课程数据位于 User-course accuracy 工作表，全体学生比较及其汇总位于另外三个工作表。
2. 保留全部 2,496 行；included_primary_model=1 的 1,983 行才是正文主模型的完整样本。
3. accuracy / accuracy_pct 是学生×课程准确率；strict_accuracy_pct 是学生总体准确率。多层模型必须使用前者。
4. 特征比例仍是学生总体 AI 使用比例，并非每门课程内单独测得的比例。
5. 所有原始分析字段保留，未改动统计结果；新增的只有模型纳入标记。数值导入时请保留精度，不要将显示的小数位数写回数据。


FULL-STUDENT OUTCOME-DEFINITION COMPARISON (SECTION 3.4.1)
Three additional worksheets in OR5_Accuracy_Data.xlsx document the historical-versus-strict outcome comparison separately from the student-course model table:
Student comparison — One row for each of the 16,389 students. historical_response_records and historical_correct_records reproduce the historical counts; strict_valid_records and strict_correct_records reproduce the binary-correctness definition. Both accuracies are on a 0–100 scale. strict_minus_historical_pp is strict accuracy minus historical accuracy; accuracy_changed is 1 when the underlying integer count ratios differ and 0 otherwise. user_id links to the student-level feature input in OR7.
Definition summary — Equal-student-weight summary: 1,064 students (6.49216%) differ, mean signed difference -0.16541007 percentage points, median 0.0. These correspond to the manuscript's 6.5%, -0.17 and 0.0. Do not reproduce this summary by averaging student-course rows, which duplicate some students and contain only the course-linkable subset.
Correlation comparison — Historical and strict outcomes compared for AI frequency, historical effective-feedback share, KG share, Other Process share and Task-feature share, with each predictor held fixed. The directions and approximate magnitudes of these five zero-order associations are retained. Pearson p values are unadjusted and Pearson intervals are marginal Fisher-z 95% intervals. Spearman values are point estimates without intervals or p values in this table. This limited comparison supports stability of these aggregate associations; it does not claim that every fitted model or subgroup result is identical under both outcomes and does not alter the multiple-testing families in OR7.

另外三个工作表覆盖正文第3.4.1节所说的全体学生比较。2,496行课程表与16,389行学生比较表各有用途，请保留二者。变化人数按精确整数比例比较计算，避免把浮点舍入误差误记为准确率变化。

PACKAGE TRACEABILITY
The archive-root SOURCE_MANIFEST.csv identifies OR5_Accuracy_Data.xlsx and each of its four worksheet names. PACKAGE_CHECKSUMS.sha256 records the workbook and accompanying README as delivered files. Check hashes from the archive root with: shasum -a 256 -c PACKAGE_CHECKSUMS.sha256
