"""
Inter-Rater Reliability Analysis
=================================
Computes Cohen's kappa between two independent coders' classifications of
the 16 AI features in the user-xiaomu.json dataset, using the Hattie & 
Timperley (2007) feedback framework.
"""

import pandas as pd
import numpy as np
from openpyxl import load_workbook
from sklearn.metrics import cohen_kappa_score, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# STEP 1: Load both coders' ratings
# ============================================================
def load_codings(filepath, coder_name):
    """Extract the 16 item ratings from a coding sheet."""
    wb = load_workbook(filepath, data_only=True)
    ws = wb['Coding Sheet']
    
    ratings = []
    for row in range(1, ws.max_row + 1):
        item = ws.cell(row=row, column=1).value
        if isinstance(item, int):  # actual data rows have integer item numbers
            feature_zh = ws.cell(row=row, column=2).value
            feature_en = ws.cell(row=row, column=3).value
            classification = ws.cell(row=row, column=8).value
            notes = ws.cell(row=row, column=9).value
            
            if classification:
                ratings.append({
                    'item_id': item,
                    'feature_zh': feature_zh,
                    'feature_en': feature_en,
                    'classification': classification.strip(),
                    'notes': notes.strip() if notes else ''
                })
    
    return pd.DataFrame(ratings)

print("="*78)
print("INTER-RATER RELIABILITY ANALYSIS")
print("="*78)

coder1 = load_codings('/home/claude/analysis/Coding_Sheet_Coder1.xlsx', 'Coder 1')
coder2 = load_codings('/home/claude/analysis/Coding_Sheet_Coder2_v2.xlsx', 'Coder 2')

print(f"\nCoder 1 ratings: {len(coder1)} items")
print(f"Coder 2 ratings: {len(coder2)} items")

# Merge for comparison
merged = coder1.merge(coder2, on=['item_id', 'feature_zh', 'feature_en'], 
                     suffixes=('_c1', '_c2'))
print(f"Merged: {len(merged)} items\n")

# ============================================================
# STEP 2: Compute Cohen's kappa
# ============================================================
print("="*78)
print("STEP 1: Cohen's Kappa")
print("="*78)

ratings1 = merged['classification_c1'].tolist()
ratings2 = merged['classification_c2'].tolist()

# Define category order (so the matrix has a stable structure)
all_categories = sorted(set(ratings1 + ratings2))
print(f"\nCategories observed: {all_categories}")

kappa = cohen_kappa_score(ratings1, ratings2, labels=all_categories)
print(f"\nCohen's κ = {kappa:.4f}")

# Interpretation
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

# Percent agreement
agreement_count = sum(1 for r1, r2 in zip(ratings1, ratings2) if r1 == r2)
percent_agreement = agreement_count / len(ratings1) * 100
print(f"\nRaw percent agreement: {agreement_count}/{len(ratings1)} = {percent_agreement:.1f}%")

# 95% CI for kappa using bootstrap
print("\nBootstrapping 95% CI for kappa...")
np.random.seed(42)
n_boot = 10000
boot_kappas = []
n = len(ratings1)
for _ in range(n_boot):
    indices = np.random.choice(n, n, replace=True)
    r1_boot = [ratings1[i] for i in indices]
    r2_boot = [ratings2[i] for i in indices]
    try:
        k = cohen_kappa_score(r1_boot, r2_boot)
        if not np.isnan(k):
            boot_kappas.append(k)
    except:
        pass

ci_lower = np.percentile(boot_kappas, 2.5)
ci_upper = np.percentile(boot_kappas, 97.5)
print(f"  95% bootstrap CI: [{ci_lower:.3f}, {ci_upper:.3f}]")

# ============================================================
# STEP 3: Disagreement analysis
# ============================================================
print("\n" + "="*78)
print("STEP 2: Disagreement Analysis")
print("="*78)

merged['agreement'] = merged['classification_c1'] == merged['classification_c2']
disagreements = merged[~merged['agreement']]
agreements = merged[merged['agreement']]

print(f"\nAgreed items: {len(agreements)}")
print(f"Disagreed items: {len(disagreements)}")

if len(disagreements) > 0:
    print("\n--- DISAGREEMENT DETAILS ---")
    for _, row in disagreements.iterrows():
        print(f"\nItem #{row['item_id']}: {row['feature_zh']} ({row['feature_en']})")
        print(f"  Coder 1: {row['classification_c1']}")
        print(f"  Coder 2: {row['classification_c2']}")
        if row['notes_c1']:
            print(f"  C1 notes: {row['notes_c1']}")
        if row['notes_c2']:
            print(f"  C2 notes: {row['notes_c2']}")

# ============================================================
# STEP 4: Confusion matrix
# ============================================================
print("\n" + "="*78)
print("STEP 3: Confusion Matrix")
print("="*78)

cm = confusion_matrix(ratings1, ratings2, labels=all_categories)
cm_df = pd.DataFrame(cm, index=[f'C1: {c}' for c in all_categories], 
                          columns=[f'C2: {c}' for c in all_categories])
print(f"\n{cm_df.to_string()}")

# ============================================================
# STEP 5: Save side-by-side comparison
# ============================================================
print("\n" + "="*78)
print("STEP 4: Side-by-side ratings (sorted by frequency)")
print("="*78)

# Add frequency from item ordering for context
# Item numbers in coding sheet correspond to frequency rank
side_by_side = merged[['item_id', 'feature_zh', 'feature_en', 
                       'classification_c1', 'classification_c2', 'agreement']].copy()
side_by_side.columns = ['Item', 'Feature (CN)', 'Feature (EN)', 
                        'Coder 1', 'Coder 2', 'Agreed?']

# Save to CSV
side_by_side.to_csv('/home/claude/analysis/irr_side_by_side.csv', index=False)
print("\nSaved: irr_side_by_side.csv")

print("\n" + side_by_side.to_string(index=False))

# ============================================================
# STEP 6: Summary stats and decision support
# ============================================================
print("\n" + "="*78)
print("SUMMARY")
print("="*78)
print(f"""
N items coded: {len(merged)}
Cohen's κ: {kappa:.4f} (95% CI [{ci_lower:.3f}, {ci_upper:.3f}])
Agreement: {agreement_count}/{len(ratings1)} ({percent_agreement:.1f}%)
Interpretation: {interp}

Items requiring adjudication: {len(disagreements)}
""")

# Save key statistics for the report
with open('/home/claude/analysis/irr_key_stats.txt', 'w') as f:
    f.write(f"Inter-Rater Reliability Analysis Summary\n")
    f.write(f"="*60 + "\n\n")
    f.write(f"N items coded: {len(merged)}\n")
    f.write(f"Cohen's kappa: {kappa:.4f}\n")
    f.write(f"95% bootstrap CI: [{ci_lower:.3f}, {ci_upper:.3f}]\n")
    f.write(f"Raw agreement: {agreement_count}/{len(ratings1)} = {percent_agreement:.1f}%\n")
    f.write(f"Interpretation: {interp}\n\n")
    f.write(f"Disagreed items ({len(disagreements)}):\n")
    for _, row in disagreements.iterrows():
        f.write(f"  Item #{row['item_id']} ({row['feature_zh']}): "
                f"C1={row['classification_c1']} vs C2={row['classification_c2']}\n")

print("Saved: irr_key_stats.txt")
