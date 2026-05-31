"""
Inter-Rater Reliability Analysis — Author-Final Mapping
=========================================================
Companion to compute_irr.py. Reports a second Cohen's kappa under the
author-final classification scheme described in Online Resource 1,
Appendix A.

The five features that both coders unanimously classified as "Other"
under the codebook's strict five-category definition are programmatically
remapped here to the closest Hattie-Timperley level (per Appendix A.2):
    - Poetry Composition        → Self (FS)
    - From FAQ                  → Self-Regulation (FR)
    - Ask TA (Human)            → Self-Regulation (FR)
    - Arithmetic Calculator     → Task (FT)
    - From Course Information   → Task (FT)

Three additional features (System Cannot Answer, Inappropriate Input,
TA Answer Browser) are kept as "Other" and excluded from the down-stream
four-level shares (Appendix A.3).

The reclassification of From MOOCCube from coders' consensus (Task) to
Process (Appendix A.4) is a theoretical author judgement and is not
programmatically applied here; it is documented in the manuscript
(Section 3.4.3) and Appendix A.4.

The raw five-category kappa reported in compute_irr.py is unchanged and
remains the primary inter-rater reliability statistic reported in
Section 3.4.4. This script provides a transparency check on the
classification scheme actually used in the down-stream analyses.
"""

import pandas as pd
import numpy as np
from openpyxl import load_workbook
from sklearn.metrics import cohen_kappa_score, confusion_matrix
import warnings
import os

# Output directory (relative to repository, portable). Override with env var if needed.
OUTPUT_DIR = os.environ.get("RESULTS_DIR", "../03_results")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# IRR input materials directory
IRR_DIR = os.environ.get("IRR_DIR", "../04_irr_materials")

warnings.filterwarnings('ignore')

# ============================================================
# Author-final mapping rules (per Online Resource 1, Appendix A.2)
# Keys are feature item numbers (1-16); values are the target HT level
# only when the coder's raw classification was "Other / Not Applicable".
# If a coder did not write "Other" for a given feature, their raw label
# is preserved unchanged.
# ============================================================
OTHER_TO_HT_MAPPING = {
    7:  "Self (FS)",                 # Poetry Composition
    8:  "Self-Regulation (FR)",      # From FAQ
    13: "Self-Regulation (FR)",      # Ask TA (Human)
    14: "Task (FT)",                 # Arithmetic Calculator
    16: "Task (FT)",                 # From Course Information
}

# Features whose "Other" classifications are NOT mapped (kept as Other,
# excluded from the four-level shares); listed here for documentation only.
EXCLUDED_AS_OTHER = {
    10: "TA Answer Browser",
    12: "System Cannot Answer",
    15: "Inappropriate Input (Filtered)",
}

# ============================================================
# STEP 1: Load both coders' raw five-category ratings
# ============================================================
def load_codings(filepath, coder_name):
    """Extract the 16 item ratings from a coding sheet."""
    wb = load_workbook(filepath, data_only=True)
    ws = wb['Coding Sheet']

    ratings = []
    for row in range(1, ws.max_row + 1):
        item = ws.cell(row=row, column=1).value
        if isinstance(item, int):
            feature_zh = ws.cell(row=row, column=2).value
            feature_en = ws.cell(row=row, column=3).value
            classification = ws.cell(row=row, column=8).value
            notes = ws.cell(row=row, column=9).value

            if classification:
                ratings.append({
                    'item_id': item,
                    'feature_zh': feature_zh,
                    'feature_en': feature_en,
                    'classification_raw': classification.strip(),
                    'notes': notes.strip() if notes else ''
                })
    return pd.DataFrame(ratings)

print("="*78)
print("INTER-RATER RELIABILITY — AUTHOR-FINAL MAPPING")
print("="*78)
print("\nCompanion to compute_irr.py.")
print("See Online Resource 1, Appendix A for full documentation.\n")

coder1 = load_codings(os.path.join(IRR_DIR, 'Coding_Sheet_Coder1.xlsx'), 'Coder 1')
coder2 = load_codings(os.path.join(IRR_DIR, 'Coding_Sheet_Coder2.xlsx'), 'Coder 2')

print(f"Coder 1 ratings: {len(coder1)} items")
print(f"Coder 2 ratings: {len(coder2)} items")

# ============================================================
# STEP 2: Apply author-final mapping
# ============================================================
def apply_author_mapping(item_id, raw_label):
    """If coder wrote 'Other', remap to HT level per Appendix A.2.
       Otherwise, return raw label unchanged."""
    if raw_label.lower().startswith("other"):
        if item_id in OTHER_TO_HT_MAPPING:
            return OTHER_TO_HT_MAPPING[item_id]
        # Excluded "Other" features stay as Other
        return "Other"
    return raw_label

coder1['classification_final'] = coder1.apply(
    lambda r: apply_author_mapping(r['item_id'], r['classification_raw']), axis=1)
coder2['classification_final'] = coder2.apply(
    lambda r: apply_author_mapping(r['item_id'], r['classification_raw']), axis=1)

# Merge for comparison
merged = coder1.merge(coder2, on=['item_id', 'feature_zh', 'feature_en'],
                     suffixes=('_c1', '_c2'))
print(f"Merged: {len(merged)} items\n")

# ============================================================
# STEP 3: Compute Cohen's kappa under author-final mapping
# ============================================================
print("="*78)
print("STEP 1: Cohen's Kappa (Coder 1 vs Coder 2, author-final mapping)")
print("="*78)

ratings1_final = merged['classification_final_c1'].tolist()
ratings2_final = merged['classification_final_c2'].tolist()

all_categories = sorted(set(ratings1_final + ratings2_final))
print(f"\nCategories observed: {all_categories}")

kappa = cohen_kappa_score(ratings1_final, ratings2_final, labels=all_categories)
print(f"\nCohen's κ (author-final): {kappa:.4f}")

if kappa > 0.81:
    interp = "almost perfect agreement (Landis & Koch, 1977)"
elif kappa > 0.61:
    interp = "substantial agreement (Landis & Koch, 1977)"
elif kappa > 0.41:
    interp = "moderate agreement (Landis & Koch, 1977)"
elif kappa > 0.21:
    interp = "fair agreement (Landis & Koch, 1977)"
else:
    interp = "slight agreement (Landis & Koch, 1977)"

print(f"Interpretation: {interp}")

agreement_count = sum(1 for a, b in zip(ratings1_final, ratings2_final) if a == b)
percent_agreement = agreement_count / len(ratings1_final) * 100
print(f"\nRaw percent agreement: {agreement_count}/{len(ratings1_final)} = {percent_agreement:.1f}%")

# Bootstrap 95% CI
print("\nBootstrapping 95% CI for author-final κ...")
np.random.seed(42)
n_boot = 10000
boot_kappas = []
n = len(ratings1_final)
for _ in range(n_boot):
    indices = np.random.choice(n, n, replace=True)
    r1_boot = [ratings1_final[i] for i in indices]
    r2_boot = [ratings2_final[i] for i in indices]
    try:
        k = cohen_kappa_score(r1_boot, r2_boot)
        if not np.isnan(k):
            boot_kappas.append(k)
    except Exception:
        pass

ci_lower = np.percentile(boot_kappas, 2.5)
ci_upper = np.percentile(boot_kappas, 97.5)
print(f"  95% bootstrap CI: [{ci_lower:.3f}, {ci_upper:.3f}]")

# ============================================================
# STEP 4: Coder vs author-final classification
# ============================================================
# The "author-final classification" is, by construction, the consensus
# of both coders after Other-mapping plus the three adjudicated items.
# For the adjudicated items we use the consensus reported in the
# manuscript (Section 3.4.4):
#   - From Turing Bot  → Self (FS)
#   - From Aminer      → Process (FP)
#   - TA Answer Browser → Other (excluded)
# Plus the one author reclassification (Appendix A.4):
#   - From MOOCCube    → Process (FP)   [coders had consensus Task]
# ============================================================

print("\n" + "="*78)
print("STEP 2: Each Coder vs. Author-Final Classification")
print("="*78)

ADJUDICATED = {
    4:  "Self (FS)",                  # Turing Bot
    9:  "Process (FP)",               # Aminer
    10: "Other",                      # TA Answer Browser (excluded)
}
AUTHOR_RECLASSIFIED = {
    3:  "Process (FP)",               # From MOOCCube
}

def build_author_final(merged_row):
    item = merged_row['item_id']
    if item in AUTHOR_RECLASSIFIED:
        return AUTHOR_RECLASSIFIED[item]
    if item in ADJUDICATED:
        return ADJUDICATED[item]
    # Otherwise, both coders agreed after mapping; use either
    return merged_row['classification_final_c1']

merged['author_final'] = merged.apply(build_author_final, axis=1)
author_final_labels = merged['author_final'].tolist()

kappa_c1_vs_final = cohen_kappa_score(ratings1_final, author_final_labels)
kappa_c2_vs_final = cohen_kappa_score(ratings2_final, author_final_labels)
mean_kappa = (kappa_c1_vs_final + kappa_c2_vs_final) / 2

agree_c1 = sum(1 for a, b in zip(ratings1_final, author_final_labels) if a == b)
agree_c2 = sum(1 for a, b in zip(ratings2_final, author_final_labels) if a == b)

print(f"\nCoder 1 vs author-final: κ = {kappa_c1_vs_final:.4f}, agree {agree_c1}/{len(merged)}")
print(f"Coder 2 vs author-final: κ = {kappa_c2_vs_final:.4f}, agree {agree_c2}/{len(merged)}")
print(f"Mean κ (coders vs author-final): {mean_kappa:.4f}")

# ============================================================
# STEP 5: Side-by-side display
# ============================================================
print("\n" + "="*78)
print("STEP 3: Side-by-side (raw vs author-final)")
print("="*78)

display_cols = merged[['item_id', 'feature_zh', 'feature_en',
                       'classification_raw_c1', 'classification_final_c1',
                       'classification_raw_c2', 'classification_final_c2',
                       'author_final']].copy()
display_cols.columns = ['Item', 'Feature (CN)', 'Feature (EN)',
                        'C1 raw', 'C1 final', 'C2 raw', 'C2 final',
                        'Author-final']

display_cols.to_csv(os.path.join(OUTPUT_DIR, 'irr_author_final_side_by_side.csv'),
                    index=False)
print("\nSaved: irr_author_final_side_by_side.csv")
print("\n" + display_cols.to_string(index=False))

# ============================================================
# STEP 6: Summary stats
# ============================================================
print("\n" + "="*78)
print("SUMMARY — AUTHOR-FINAL κ")
print("="*78)
print(f"""
N items coded: {len(merged)}
Cohen's κ (Coder 1 vs Coder 2, author-final mapping): {kappa:.4f}
  95% bootstrap CI: [{ci_lower:.3f}, {ci_upper:.3f}]
  Raw agreement: {agreement_count}/{len(ratings1_final)} ({percent_agreement:.1f}%)
  Interpretation: {interp}

Coder 1 vs author-final classification: κ = {kappa_c1_vs_final:.4f}
Coder 2 vs author-final classification: κ = {kappa_c2_vs_final:.4f}
Mean (coders vs author-final): κ = {mean_kappa:.4f}

Reference statistic (from compute_irr.py): κ_raw (5-category) = .716
""")

with open(os.path.join(OUTPUT_DIR, 'irr_author_final_key_stats.txt'), 'w') as f:
    f.write("Inter-Rater Reliability — Author-Final Mapping\n")
    f.write("=" * 60 + "\n\n")
    f.write("Companion to compute_irr.py / irr_key_stats.txt.\n")
    f.write("See Online Resource 1, Appendix A for full documentation.\n\n")
    f.write(f"N items coded: {len(merged)}\n\n")
    f.write(f"Cohen's κ (Coder 1 vs Coder 2, author-final): {kappa:.4f}\n")
    f.write(f"  95% bootstrap CI: [{ci_lower:.3f}, {ci_upper:.3f}]\n")
    f.write(f"  Raw agreement: {agreement_count}/{len(ratings1_final)} = {percent_agreement:.1f}%\n")
    f.write(f"  Interpretation: {interp}\n\n")
    f.write(f"Coder 1 vs author-final: κ = {kappa_c1_vs_final:.4f}, agree {agree_c1}/{len(merged)}\n")
    f.write(f"Coder 2 vs author-final: κ = {kappa_c2_vs_final:.4f}, agree {agree_c2}/{len(merged)}\n")
    f.write(f"Mean (coders vs author-final): κ = {mean_kappa:.4f}\n\n")
    f.write(f"Reference (5-category raw, from compute_irr.py): κ = .716\n")

print("Saved: irr_author_final_key_stats.txt")