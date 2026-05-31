# 04_irr_materials

The materials used for the inter-rater reliability analysis of the AI feature classification.

## Contents

| File | Description |
|---|---|
| `Coding_Manual.docx` | The structured codebook, distributed to both coders before independent classification. Defines the five categories (Task / Process / Self-Regulation / Self / Other-or-Not-Applicable), provides decision rules, and includes 3 calibration items (not in the analysis set) for training. Appendix A (added post-hoc) documents all author-level mapping, exclusion, and reclassification decisions used in Table 1 and downstream analyses, together with reconstructed κ statistics |
| `Coding_Sheet_Coder1.xlsx` | Coder 1's independent ratings of the 16 distinct AI features |
| `Coding_Sheet_Coder2.xlsx` | Coder 2's independent ratings |

## Procedure summary

Two graduate student coders, blind to the study hypotheses and not co-authors of this work, independently classified each of the 16 distinct AI features in the consolidated `user-xiaomu.json` question_type set. Both coders were native Chinese speakers from social science backgrounds. Following a one-hour training session (using the calibration items in `Coding_Manual.docx`), the coders worked alone on the 16 actual items without further discussion.

Inter-rater agreement was quantified using Cohen's kappa, computed by `02_analysis/compute_irr.py`. Disagreements on three items were resolved through discussion in a structured adjudication meeting; the consensus classification is used in all reported analyses.

For complete transparency on the chain from coders' five-category ratings to the four-level structure used in the downstream analyses, the post-hoc mapping decisions (five "Other" features mapped to Hattie–Timperley levels, three "Other" features excluded, and one feature reclassified from coders' consensus) are documented in `Coding_Manual.docx`, Appendix A. A second κ statistic under the author-final mapping scheme is reproduced by `02_analysis/compute_irr_author_final.py`.

## Reproducing the IRR statistics

```bash
cd ../02_analysis/
python compute_irr.py                  # raw five-category κ
python compute_irr_author_final.py     # author-final κ
```

The script reads `Coding_Sheet_Coder1.xlsx` and `Coding_Sheet_Coder2.xlsx` from this directory and produces:

- κ = .716 (95% bootstrap CI [.417, 1.000])
- 13 / 16 items agreed (81.2%)
- Three disagreements: Turing Bot (FR vs FS → adjudicated to FS), Aminer (FT vs FP → adjudicated to FP), TA Answer Browser (Other vs FT → adjudicated to Other)

## Coders' independence

The coding sheets here are unmodified versions exactly as the coders submitted them. No post-hoc edits were made to either coder's classifications. The adjudicated final classification is reported separately in the manuscript Table 1, and is not stored in this directory (since it is the consensus classification, not the coders' independent work). The full chain from coders' independent five-category ratings to the four-level structure used in Table 1, including all author-level decisions, is documented in `Coding_Manual.docx`, Appendix A.

## Note on language

Both coding sheets present feature names in Chinese (the original question_type values from MOOCCubeX) alongside English glosses. This was intended to ensure the coders worked from the original data, not from translation.
