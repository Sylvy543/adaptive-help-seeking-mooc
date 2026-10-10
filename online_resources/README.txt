Online Resources for the manuscript
Adaptive Help-Seeking in AI-Enhanced MOOCs: Evidence from Large-Scale Learning Analytics
Submitted to: Education and Information Technologies (Springer)
Revision package: 9 October 2026

This archive contains the seven Online Resources referenced in the revised manuscript. Each resource retains its manuscript number. Folders contain English explanatory notes and numerical data; the original bilingual coding materials are retained. OR5, OR6 and OR7 each contain one Excel workbook and one README. OR5 contains four named data worksheets; OR6 and OR7 list their data worksheets in Contents. Separate CSV versions of these tables are provided in the code repository, not duplicated in these three Online Resource folders.

Online Resource 1 — Coding Manual, including Appendix A on classification provenance, author mappings and the coder-anchored alternative.
[Online_Resource_1_Coding_Manual.docx]

Online Resource 2 — Original independent ratings of 16 features by two coders. The workbooks are unchanged from round 1. Their frequencies refer to all 108,351 AI interactions, not the 85,815 interactions in the main analytic sample. The accompanying README distinguishes original ratings from adjudications and subsequent author mappings.
[Online_Resource_2_Coder_Ratings/]

Online Resource 3 — Strict-accuracy sensitivity report for KG Navigation classification, including Other-denominator checks, the coder-anchored comparison, group summaries and the revised figure (Section 4.6; related results in Section 4.7.2).
[Online_Resource_3_Sensitivity_Analysis_Report.docx]

Online Resource 4 — Feature-decomposition correlations, fixed-group descriptions, Welch comparisons and the complete per-student feature breakdown reported in Section 4.7.2.
[Online_Resource_4_Three_Category_Results/]

Online Resource 5 — Revised student-course model input with a full-sample inclusion flag and field dictionary; also the complete 16,389-student historical-versus-strict accuracy comparison and its summaries (Sections 3.4.1 and 4.7.3).
[Online_Resource_5_user_course_accuracy/OR5_Accuracy_Data.xlsx; Online_Resource_5_README.txt]

Online Resource 6 — Course-model estimates, variance components, corrected diagnostics and leave-one-course-out sensitivity, including the three Self-Regulation coefficient sign changes (Sections 4.7.3–4.7.4 and 5.5).
[Online_Resource_6_Model_Diagnostics/]

Online Resource 7 — Final 48-test and separate 60-test multiple-testing tables; classification and count/share sensitivity; within-accuracy-group, response-record-stratified, subsample and weighted checks; additional reported operationalisations; full student-level analysis input.
[Online_Resource_7_Robustness_Results/]

READING AND REPRODUCTION
Excel workbooks and CSV files preserve the statistical values; Excel exports retain floating-point precision. Some CSV files use a UTF-8 byte-order mark for compatibility. Percentages are generally on a 0–100 scale unless a field is explicitly a proportion. Definitions and units are given in each resource's README. Excel display formats do not change stored values; use the worksheet headers when exporting for code. OR5 worksheet names are listed in its README; OR6 and OR7 also provide Contents sheets with their original CSV filenames. Keep student and student-course units distinct. The strict_accuracy_pct field in the course input is student-level, whereas accuracy/accuracy_pct is course-cell accuracy used by the course model.

All inferential analyses are exploratory. The two reported BH families are separate, and confidence intervals are marginal rather than simultaneous. Raw p values in additional tables are not automatically included in those families. Older withdrawn dispersion-rescaled standard errors, Fisher-z Spearman intervals and superseded multiplicity tables are not distributed as final results.

SOURCE_MANIFEST.csv records the source pipeline outputs and transformations for newly curated numerical files; its worksheet column locates tables consolidated into OR5/OR6/OR7 workbooks. PACKAGE_CHECKSUMS.sha256 records the final archive files, excluding itself. These support traceability and file integrity, not an additional scientific validation claim.

For the original analysis code, see the code repository identified in Section 3.5 of the manuscript. The supplementary package does not replace the raw MOOCCubeX source data or the analysis scripts.
