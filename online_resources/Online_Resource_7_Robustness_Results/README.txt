Online Resource 7 — Classification, operationalisation and response-record sensitivity analyses
Manuscript: Adaptive Help-Seeking in AI-Enhanced MOOCs: Evidence from Large-Scale Learning Analytics
Revision package: 8 October 2026

WORKBOOK ORGANISATION
All 19 numerical tables formerly supplied as separate CSV files are now worksheets in OR7_Robustness_Results.xlsx. The Contents worksheet lists the tables and original CSV filenames. All table headers, rows and values are retained; this consolidation does not change analyses, inference or multiple-testing families. Displayed decimal places are for reading only; stored numeric precision is retained to Excel's floating-point precision.

Each numerical worksheet begins with its original column headers in row 1. For use with the original analysis scripts, export the required worksheet as CSV with the original filename shown in Contents, preserving numeric precision and empty values. Do not export the Contents worksheet as analysis data.

中文：本资源现在只有一份Excel工作簿和本说明文件。原来的CSV均已合并为独立工作表，可从Contents目录查找。合并未改变统计结果；OR7的48项与60项检验仍是两张独立工作表。用程序复现时，可按Contents中的原文件名导出所需工作表。


SCOPE
This resource supplies the final exploratory multiple-testing tables and numerical robustness results cited in Sections 3.5 and 4.7. It combines already completed corrected outputs. The 48-test revision family and the separate 60-test response-record sensitivity family are retained separately. No single correction across every analysis in the paper is implied, and no new tests are inserted into either archived family.

All student-level outcomes use strict accuracy: 100 times correct binary response records divided by valid binary response records. Unless a denominator sensitivity is explicitly named, feature shares use all AI interactions per student, including unclassified Other. The full student-level sample is N = 16,389. The feature-level usage variables retain the neutral/historical operational assignments documented in OR1; the separate coder-anchored alternative uses the complete raw-consensus/adjudication mapping.

READING THE MULTIPLE-TESTING TABLES
worksheet "BH family 48" — The final 48 explicitly selected exploratory tests from run04c, including student correlations, selected student OLS terms, AI terms in the crossed and binomial course models, and selected low–high comparisons. raw_p and bh_q are reported together. reviewer_focus is an annotation of the KG-share question, not a designation of a confirmatory test.
worksheet "BH family 60" — The separate stage-local set of 60 tests for response-record robustness, itemised in run08 without changing the original run05 family. This is the exact archived selection, including the model terms listed in the file; it does not include every supplementary correlation or every new packaging summary.
Both sets of q values were independently recalculated from their respective full lists of raw p values and verified during packaging. Do not recalculate q after filtering the table or merge the two lists into one family without explicitly changing the analysis.
The KG-share and Task-feature-share low–high comparisons have q < .001. Other Process share's comparison has q = .00203868; the KG-count comparison has q = .15341877. In the crossed model, the Other Process term has q approximately .053. These statements concern different tests and must not be interchanged.

FULL-SAMPLE CLASSIFICATION AND OPERATIONALISATION
worksheet "Full sample correlations" — 28 unique Pearson/Spearman correlations in the 48-test family, combining final point estimates and corrected p/q with the valid confidence intervals. Pearson intervals use Fisher z. Spearman intervals use paired-student percentile bootstrap with ranks recomputed in every resample, B = 10,000. Seed/method information is retained in the source-method columns or in worksheet "Coder anchored correlations". Spearman tests use large-sample asymptotic p values, not bootstrap p values; intervals and p values come from different procedures. Pearson p values use the conventional two-sided parametric test. Confidence intervals are marginal 95% intervals, not simultaneous or BH-adjusted intervals.
For monotone transformations, log count has the same Spearman result as raw count, so the duplicate test is not listed again. log_kg_count refers to ln(1 + kg_count); kg_any indicates at least one KG interaction.
historical_ef = 100 * (historical process_count + self_reg_count) / ai_frequency.
kg_moved_to_task = historical_ef - kg_pct, with all other historical assignments and the denominator unchanged.
historical_other_share = 100 * other_count / ai_frequency; this is a standalone predictor, not an effective-feedback numerator.
historical_ef_excluding_other_denominator = 100 * (process_count + self_reg_count) / (ai_frequency - other_count). It is undefined for 52 all-Other students, giving N = 16,337. Other is not added to the numerator.
restored_process_selfreg_pct and restored_other_pct use the complete coder-anchored mapping. Under that mapping Self-Regulation has no interactions, so Process + Self-Regulation equals Process. The composite Pearson r is -.112865, compared with historical r = -.102695. This is a complete-mapping comparison and does not isolate one feature's reassignment.

worksheet "Coder feature mapping" — The 16 base features, raw coder classifications, consensus/adjudication basis and restored categories, with main-sample counts.
worksheet "Coder student counts" — One row per student under that alternative. Category totals are Task = 28,957; Process = 44,655; Self-Regulation = 0; Self = 4,577; Other = 7,626; total = 85,815. The denominator is unchanged and all 16,389 students are retained.
worksheet "Coder anchored correlations" — The four correlations introduced by this sensitivity check, including confidence intervals, bootstrap seeds and q values from the full 48-test family. Do not correct these four rows alone.
worksheet "Alternative OLS" — HC3 OLS coefficients for log KG count and any KG use, controlling for log AI frequency. This retained run04 output was not among the withdrawn correlation intervals or multiplicity tables. Unadjusted p values are provided; only the specifically selected focal tests occur in family48.
worksheet "High minus low comparisons" — The five selected raw-unit comparisons in family48, with Welch intervals and secondary Hedges g intervals. Direction is HIGH MINUS LOW, as in the analysis source. OR4's category table uses LOW MINUS HIGH. Signs of differences and effect sizes reverse under that change of orientation; p values do not. OR4 also includes additional Self-Regulation/Self comparisons that are not automatically added to family48.
worksheet "Within accuracy groups" — Historical effective-feedback share versus strict accuracy within the fixed Low/Medium/High groups. Low <67.5%; Medium 67.5–84.0% inclusive; High >84.0%. Group sizes are 5,540/5,467/5,382. Pearson correlations are approximately .0083/.0047/-.0171. The groups are defined by the outcome: range restriction and between-group structure cannot be distinguished by these conditional correlations alone. Spearman values here are point estimates only; no new bootstrap interval or multiple-testing family is introduced for this packaging table.

RESPONSE-RECORD SENSITIVITY
Here 'attempts' means strict_valid_records, the number of valid binary response records for a student. It is not the sum of the raw per-record attempts field and does not necessarily count distinct questions.
worksheet "Record strata descriptives" — Strata 1–9, 10–19, 20–49 and >=50 contain 3,185, 2,394, 4,054 and 6,756 students.
worksheet "Record strata correlations" — Pearson and Spearman results for all six headline variables in the four strata. Superseded Fisher-z-on-ranks intervals have been replaced with the run08 paired-row bootstrap intervals.
worksheet "Record subsample correlations" — The >=20-record subset (N = 10,810) and median-split subsets <=36 (N = 8,656) and >36 (N = 7,733). The valid original paired-row intervals are retained, and the remaining Spearman intervals are replaced with run08 bootstrap intervals. Coefficients and raw p values retain their original interpretation.
worksheet "Record bootstrap intervals" — The 36 run08 bootstrap replacements, B = 10,000 and seed = 20260928. The six already bootstrapped EF/KG-share subsample intervals in run05 use seed = 20260921 and remain in worksheet "Record subsample correlations". Together these cover all Spearman intervals in the two correlation tables.
worksheet "Record weighted correlations" — Weighted Pearson correlations using strict_valid_records as student weights, with paired-row bootstrap intervals (B = 10,000, seed = 20260921). No p value is supplied in this file. Weighting changes the estimand relative to equal-student weighting.
worksheet "Record sensitivity models" — Student OLS/WLS models use HC3 covariance. Course-cell OLS sensitivity models at n_records >=10 and >=20 use student-clustered covariance; these contain 1,682 and 1,322 cells. These are not weighted or refitted crossed mixed models. The crossed model was not weighted in these analyses.

ADDITIONAL REPORTED CHECKS AND INPUT
worksheet "Frequency operationalisations" — Nine frequency/outcome operationalisations supporting Section 4.2, including partial/log/dichotomised frequency and restricted-sample checks; these rows do not define a new BH family.
worksheet "Frequency trends" — Linear and quadratic seven-group trend coefficients with HC3 intervals; these are unadjusted p values.
worksheet "Frequency Tukey" — All 21 pairwise comparisons among seven frequency groups; p-adj is the Tukey-adjusted p value, not a BH q value. No pair rejects at the reported level.
worksheet "Student analysis input" — The complete 16,389-row student input underlying these analyses. All original analysis fields are retained, including historical audit fields. strict_accuracy_pct is the revised student-level outcome; historical_accuracy_pct and problem_accuracy are historical fields. The full field dictionary is described below and in OR4/OR5.

STUDENT INPUT FIELD DICTIONARY
user_id: student identifier, a string.
ai_frequency: total student AI interaction count; log_ai_frequency: ln(1 + ai_frequency).
total_problems, correct_problems, problem_accuracy: historical response-record denominator, historical correct count and historical percentage accuracy, respectively; historical_accuracy_pct is recomputed from those historical counts.
strict_valid_records, strict_correct_records, strict_accuracy_pct: binary-response denominator, count with is_correct = 1 and revised percentage accuracy.
accuracy_change: strict_accuracy_pct minus historical_accuracy_pct, in percentage points.
task_count, process_count, self_reg_count, self_count, other_count: historical author-mapping interaction counts; their sum is ai_frequency.
effective_feedback_pct: historical Process plus Self-Regulation count divided by all AI interactions, multiplied by 100.
kg_count, other_process_count: counts of KG Navigation and of MOOCCubeX concept search plus Aminer academic search.
task_count_neutral, selfreg_count_neutral, self_count_neutral, other_count_neutral: neutral feature-group counts; together with kg_count and other_process_count they sum to ai_frequency_neutral, equal to ai_frequency.
kg_pct, other_process_pct, task_pct_neutral, selfreg_pct_neutral, self_pct_neutral, other_pct_neutral: corresponding counts divided by all AI interactions, multiplied by 100. These six shares sum to 100.
kg_pct10: kg_pct / 10. Counts and shares are distinct operationalisations.
The four Baike-variant interactions explain the historical versus neutral Process/Task difference documented in OR1; neither scheme should be confused with the complete coder-anchored alternative.

NUMERICAL AND INTERPRETIVE NOTES
Empty fields are unavailable or inapplicable values, not zero. Some very small model p values are recorded as 0.0 because of numerical underflow; this is not a literal probability of zero. Avoid replacing the stored scientific-notation values with rounded values for analysis.
All analyses are observational and exploratory. Outcome-defined groups, usage shares and response-record strata do not identify causal learning effects. The preserved interval estimates assume the sampling/resampling units stated in the source analyses. No family-wide or simultaneous confidence interval is claimed.
The withdrawn run04 keep_other composite, Fisher-z Spearman intervals, old multiplicity tables and simple-average-denominator Cohen d comparisons are excluded. The 48-test and 60-test families remain separate, superseding earlier summary wording suggesting a combined family.
SOURCE_MANIFEST.csv at the archive root records the source files, hashes and explicit interval replacements. Packaging does not refit the archived statistical models.

中文使用说明
正文引用的48项检验见 worksheet "BH family 48"，60项检验见 worksheet "BH family 60"，两者不能混为一组。全样本相关及其最终区间、p/q见 worksheet "Full sample correlations"。按作答记录数量分层及子样本结果中的Spearman区间已经统一采用有效的bootstrap版本。组间差值请留意方向：本资源保留原分析“高组减低组”，OR4使用“低组减高组”。
