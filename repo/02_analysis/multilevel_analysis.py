"""
Multilevel Modeling Analysis
=============================
Addresses Reviewer #2 Comment 2.b:
"Students are nested within courses, which may differ in AI feature exposure,
instructional design, assessment difficulty. Not accounting for this structure
(e.g., via multilevel modelling) limits the ability to attribute observed 
patterns solely to learner behavior."

Strategy:
- Build a long-format dataset where each row is a (user, course) cell
- Each row has: user-level AI feature usage (% KG, % task, % EF) + course-level 
  accuracy
- Fit mixed-effects models with course_id as random intercept
- Compare with single-level model to show how much course-level variance there is
- Report ICC (intraclass correlation) and the partialled-out fixed effects
"""

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.formula.api as smf
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# STEP 1: Build merged long-format dataset
# ============================================================
print("="*78)
print("STEP 1: Building merged long-format dataset")
print("="*78)

uc = pd.read_csv('user_course_accuracy.csv')
ai = pd.read_csv('combined_ai_learning_data.csv')

# Also load three-category data (KG, OtherProcess, Task split)
three_cat = pd.read_csv('per_user_three_categories.csv')

# Merge: each row is a (user, course) cell, with user-level AI features attached
merged = uc.merge(ai[['user_id', 'effective_feedback_pct', 'process_pct', 
                       'task_pct', 'self_reg_pct', 'self_pct', 
                       'ai_frequency', 'ai_frequency_log',
                       'num_courses']], on='user_id', how='inner')
merged = merged.merge(three_cat[['user_id', 'kg_pct', 'other_process_pct', 
                                  'task_pct', 'selfreg_pct']], 
                      on='user_id', how='inner', suffixes=('_orig', '_new'))

print(f"Merged rows (user × course cells): {len(merged):,}")
print(f"  Unique users:   {merged['user_id'].nunique():,}")
print(f"  Unique courses: {merged['course_id'].nunique():,}")

# Filter: require at least 5 attempts per user-course cell to ensure 
# meaningful accuracy estimates
merged_filt = merged[merged['n_attempts'] >= 5].copy()
print(f"\nAfter filtering n_attempts >= 5: {len(merged_filt):,} cells")
print(f"  Unique users:   {merged_filt['user_id'].nunique():,}")
print(f"  Unique courses: {merged_filt['course_id'].nunique():,}")

# Use accuracy_pct from user-course (not the user-level aggregate from ai)
merged_filt['accuracy'] = merged_filt['accuracy_pct']
merged_filt['ef_pct'] = merged_filt['effective_feedback_pct']

# Save for later
merged_filt.to_csv('/home/claude/analysis/multilevel_long_format.csv', index=False)
print(f"\nSaved: multilevel_long_format.csv")

# ============================================================
# STEP 2: Single-level (OLS) model for baseline
# ============================================================
print("\n" + "="*78)
print("STEP 2: Baseline single-level OLS regression")
print("="*78)

ols1 = smf.ols('accuracy ~ ef_pct', data=merged_filt).fit()
print("\nModel: accuracy ~ effective_feedback_pct")
print(f"  Coefficient on ef_pct: {ols1.params['ef_pct']:+.4f} (SE = {ols1.bse['ef_pct']:.4f})")
print(f"  t = {ols1.tvalues['ef_pct']:.2f}, p = {ols1.pvalues['ef_pct']:.4e}")
print(f"  R² = {ols1.rsquared:.4f}")

# Convert coefficient to standardized to compare with correlation
sd_x = merged_filt['ef_pct'].std()
sd_y = merged_filt['accuracy'].std()
beta_std = ols1.params['ef_pct'] * sd_x / sd_y
print(f"  Standardized β = {beta_std:+.4f}")
print(f"  (For comparison: aggregate user-level r = -0.102)")

# ============================================================
# STEP 3: Empty (intercept-only) mixed model — compute ICC
# ============================================================
print("\n" + "="*78)
print("STEP 3: Empty mixed model (intercept only) — computing ICC")
print("="*78)

print("\nFitting accuracy ~ 1 + (1 | course_id)...")
empty_model = smf.mixedlm("accuracy ~ 1", data=merged_filt, 
                          groups=merged_filt['course_id']).fit(reml=True)
print(empty_model.summary())

var_course = float(empty_model.cov_re.iloc[0, 0])
var_resid = float(empty_model.scale)
icc = var_course / (var_course + var_resid)

print(f"\nVariance components:")
print(f"  Between-course variance:  {var_course:.2f}")
print(f"  Within-course variance:   {var_resid:.2f}")
print(f"  ICC (course-level):       {icc:.4f}  ({icc*100:.1f}% of total variance)")

if icc > 0.10:
    print(f"\n  >>> ICC = {icc:.3f} indicates SUBSTANTIAL course-level clustering.")
    print(f"      Multilevel modelling is justified.")
elif icc > 0.05:
    print(f"\n  >>> ICC = {icc:.3f} indicates modest course-level clustering.")
else:
    print(f"\n  >>> ICC = {icc:.3f} is low. Course clustering is minor.")

# ============================================================
# STEP 4: Mixed model with EF% as fixed effect
# ============================================================
print("\n" + "="*78)
print("STEP 4: Mixed model — accuracy ~ EF% + (1 | course_id)")
print("="*78)

print("\nFitting accuracy ~ ef_pct + (1 | course_id)...")
mlm_ef = smf.mixedlm("accuracy ~ ef_pct", data=merged_filt, 
                     groups=merged_filt['course_id']).fit(reml=True)
print(mlm_ef.summary())

# Compare fixed effect to OLS
print(f"\nComparison of EF% coefficient:")
print(f"  OLS (no clustering):       {ols1.params['ef_pct']:+.4f} (SE = {ols1.bse['ef_pct']:.4f})")
print(f"  Mixed (course as RE):      {mlm_ef.fe_params['ef_pct']:+.4f} (SE = {mlm_ef.bse_fe['ef_pct']:.4f})")

# ============================================================
# STEP 5: Mixed model with KG% specifically
# ============================================================
print("\n" + "="*78)
print("STEP 5: Mixed model — accuracy ~ KG% + (1 | course_id)")
print("="*78)

print("\nFitting accuracy ~ kg_pct + (1 | course_id)...")
mlm_kg = smf.mixedlm("accuracy ~ kg_pct", data=merged_filt, 
                     groups=merged_filt['course_id']).fit(reml=True)
print(mlm_kg.summary())

# ============================================================
# STEP 6: Mixed model with three categories simultaneously
# ============================================================
print("\n" + "="*78)
print("STEP 6: Mixed model — three categories simultaneously")
print("="*78)

# Use kg_pct, other_process_pct, task_pct_new (from three-category data)
print("\nFitting accuracy ~ kg_pct + other_process_pct + task_pct_new + (1 | course_id)...")
mlm_three = smf.mixedlm("accuracy ~ kg_pct + other_process_pct + task_pct_new",
                        data=merged_filt, 
                        groups=merged_filt['course_id']).fit(reml=True)
print(mlm_three.summary())

# ============================================================
# STEP 7: Build summary results table
# ============================================================
print("\n" + "="*78)
print("STEP 7: Summary results table")
print("="*78)

results_summary = []

def add_row(model_name, predictor, coef, se, p, df=None):
    z = coef / se if se > 0 else 0
    results_summary.append({
        'Model': model_name,
        'Predictor': predictor,
        'Coefficient': f"{coef:+.4f}",
        'SE': f"{se:.4f}",
        'z': f"{z:.2f}",
        'p': f"{p:.4f}" if p >= 0.0001 else f"< .001",
    })

# OLS
add_row("OLS (no clustering)", "EF%", ols1.params['ef_pct'], 
        ols1.bse['ef_pct'], ols1.pvalues['ef_pct'])

# MLM with EF%
add_row("Mixed (RE: course)", "EF%", mlm_ef.fe_params['ef_pct'],
        mlm_ef.bse_fe['ef_pct'], mlm_ef.pvalues['ef_pct'])

# MLM with KG%
add_row("Mixed (RE: course)", "KG%", mlm_kg.fe_params['kg_pct'],
        mlm_kg.bse_fe['kg_pct'], mlm_kg.pvalues['kg_pct'])

# Three-cat mixed model
for var in ['kg_pct', 'other_process_pct', 'task_pct_new']:
    add_row("Mixed three-cat", var, mlm_three.fe_params[var],
            mlm_three.bse_fe[var], mlm_three.pvalues[var])

results_df = pd.DataFrame(results_summary)
print("\n", results_df.to_string(index=False))
results_df.to_csv('/home/claude/analysis/multilevel_results_summary.csv', index=False)

# ============================================================
# STEP 8: Variance decomposition for the EF model
# ============================================================
print("\n" + "="*78)
print("STEP 8: Variance decomposition for the EF model")
print("="*78)

# Empty model variance components
var_course_empty = float(empty_model.cov_re.iloc[0, 0])
var_resid_empty = float(empty_model.scale)

# EF model variance components
var_course_ef = float(mlm_ef.cov_re.iloc[0, 0])
var_resid_ef = float(mlm_ef.scale)

# Variance explained
delta_total = (var_course_empty + var_resid_empty) - (var_course_ef + var_resid_ef)
print(f"\nTotal residual variance:")
print(f"  Empty model:    {var_course_empty + var_resid_empty:.2f}")
print(f"  EF% added:      {var_course_ef + var_resid_ef:.2f}")
print(f"  Reduction:      {delta_total:.2f} ({delta_total/(var_course_empty+var_resid_empty)*100:.2f}%)")

print(f"\nBetween-course variance:")
print(f"  Empty model:    {var_course_empty:.2f}")
print(f"  EF% added:      {var_course_ef:.2f}")

print(f"\nWithin-course variance (residual):")
print(f"  Empty model:    {var_resid_empty:.2f}")
print(f"  EF% added:      {var_resid_ef:.2f}")

# Save key statistics for the report
with open('/home/claude/analysis/multilevel_key_stats.txt', 'w') as f:
    f.write(f"N (user-course cells) = {len(merged_filt):,}\n")
    f.write(f"N (users) = {merged_filt['user_id'].nunique():,}\n")
    f.write(f"N (courses) = {merged_filt['course_id'].nunique():,}\n\n")
    f.write(f"Empty model (intercept only):\n")
    f.write(f"  Var(course) = {var_course_empty:.4f}\n")
    f.write(f"  Var(resid)  = {var_resid_empty:.4f}\n")
    f.write(f"  ICC         = {icc:.4f}\n\n")
    f.write(f"OLS model:\n")
    f.write(f"  EF%: b = {ols1.params['ef_pct']:.4f}, SE = {ols1.bse['ef_pct']:.4f}, p = {ols1.pvalues['ef_pct']:.4e}\n\n")
    f.write(f"Mixed model with EF%:\n")
    f.write(f"  EF%: b = {mlm_ef.fe_params['ef_pct']:.4f}, SE = {mlm_ef.bse_fe['ef_pct']:.4f}, p = {mlm_ef.pvalues['ef_pct']:.4e}\n\n")
    f.write(f"Mixed model with KG%:\n")
    f.write(f"  KG%: b = {mlm_kg.fe_params['kg_pct']:.4f}, SE = {mlm_kg.bse_fe['kg_pct']:.4f}, p = {mlm_kg.pvalues['kg_pct']:.4e}\n\n")
    f.write(f"Mixed model with three categories:\n")
    for v in ['kg_pct', 'other_process_pct', 'task_pct_new']:
        f.write(f"  {v}: b = {mlm_three.fe_params[v]:.4f}, SE = {mlm_three.bse_fe[v]:.4f}, p = {mlm_three.pvalues[v]:.4e}\n")

print("\nSaved: multilevel_key_stats.txt")
print("\n" + "="*78)
print("MULTILEVEL ANALYSIS COMPLETE")
print("="*78)
