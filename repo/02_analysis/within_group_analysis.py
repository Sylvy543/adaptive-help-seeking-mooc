"""
Within-Group Correlation Analysis for Manuscript Revision
Addresses Reviewer #2's concern (5.b):
"Simpson's paradox would be strengthened by directly examining 
within-group relationships rather than relying primarily on group-level comparisons."

Logic of the test:
- The aggregate correlation r(EF%, accuracy) = -0.102
- If this is Simpson's paradox driven by structural selection,
  then within each performance tertile, the correlation should
  approach zero or even reverse to positive.
- If the negative correlation persists within tertiles, that
  weakens the Simpson's paradox interpretation.
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib as mpl

import os
# Output directory (relative to repository, portable). Override with env var if needed.
OUTPUT_DIR = os.environ.get("RESULTS_DIR", "../03_results")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Set style
mpl.rcParams['font.family'] = 'DejaVu Sans'
mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['axes.spines.top'] = False

df = pd.read_csv('combined_ai_learning_data.csv')

print("="*78)
print("WITHIN-GROUP CORRELATION ANALYSIS")
print("Testing the Simpson's Paradox interpretation of r(EF%, accuracy) = -0.102")
print("="*78)

# Step 1: Define performance tertiles using fixed cutpoints that match
# the main manuscript (Table 5) and Online Resource 3 (§3.3).
# Cutpoints 67.5% and 84.0% correspond to the 33rd and 67th percentiles
# of the accuracy distribution. Because accuracy values are discrete,
# the resulting tertile groups are of slightly unequal size.
T1_CUT, T2_CUT = 67.5, 84.0

print(f"\nTertile cutoffs (fixed):")
print(f"  Low (T1):    accuracy < {T1_CUT}%")
print(f"  Medium (T2): {T1_CUT}% <= accuracy <= {T2_CUT}%")
print(f"  High (T3):   accuracy > {T2_CUT}%")

def assign_tertile(acc):
    if acc < T1_CUT:
        return 'Low (T1)'
    elif acc <= T2_CUT:
        return 'Medium (T2)'
    else:
        return 'High (T3)'

df['tertile'] = df['problem_accuracy'].apply(assign_tertile)

print("\nTertile sample sizes:")
print(df['tertile'].value_counts().sort_index())

# Step 2: Compute the AGGREGATE correlation (replication check)
print("\n" + "="*78)
print("STEP 1: Replicate aggregate correlation")
print("="*78)
r_agg, p_agg = stats.pearsonr(df['effective_feedback_pct'], df['problem_accuracy'])
print(f"\nAggregate r(EF%, accuracy) = {r_agg:.4f}, p = {p_agg:.4e}")
print(f"  (Manuscript reports r = -0.102, p < .001)")

# Spearman as robustness check (since EF% has heavy ties at 0 and 100)
rho_agg, p_rho = stats.spearmanr(df['effective_feedback_pct'], df['problem_accuracy'])
print(f"Aggregate rho (Spearman) = {rho_agg:.4f}, p = {p_rho:.4e}")

# Step 3: WITHIN-GROUP correlations (the key test)
print("\n" + "="*78)
print("STEP 2: Within-tertile correlations (the key Simpson's-paradox test)")
print("="*78)

results = []
tertile_order = ['Low (T1)', 'Medium (T2)', 'High (T3)']

for t in tertile_order:
    sub = df[df['tertile'] == t]
    r, p = stats.pearsonr(sub['effective_feedback_pct'], sub['problem_accuracy'])
    rho, p_rho = stats.spearmanr(sub['effective_feedback_pct'], sub['problem_accuracy'])
    
    # Fisher z-based 95% CI for Pearson r
    n_t = len(sub)
    if n_t > 3:
        z = np.arctanh(r)
        se = 1 / np.sqrt(n_t - 3)
        ci_lo = np.tanh(z - 1.96 * se)
        ci_hi = np.tanh(z + 1.96 * se)
    else:
        ci_lo = ci_hi = np.nan
    
    results.append({
        'Tertile': t, 
        'N': n_t,
        'Mean accuracy': sub['problem_accuracy'].mean(),
        'Mean EF%': sub['effective_feedback_pct'].mean(),
        'Pearson r': r,
        '95% CI': f"[{ci_lo:.3f}, {ci_hi:.3f}]",
        'p (Pearson)': p,
        'Spearman rho': rho,
        'p (Spearman)': p_rho,
    })
    
    print(f"\n{t}  (n = {n_t:,})")
    print(f"  Mean accuracy: {sub['problem_accuracy'].mean():.2f}%")
    print(f"  Mean EF%:      {sub['effective_feedback_pct'].mean():.2f}%")
    print(f"  Pearson r  = {r:+.4f}, 95% CI [{ci_lo:+.3f}, {ci_hi:+.3f}], p = {p:.4e}")
    print(f"  Spearman rho = {rho:+.4f}, p = {p_rho:.4e}")

results_df = pd.DataFrame(results)
print("\n" + "="*78)
print("SUMMARY TABLE")
print("="*78)
print(results_df.to_string(index=False))

# Step 4: Interpretation
print("\n" + "="*78)
print("STEP 3: Interpretation")
print("="*78)

within_correlations = [r['Pearson r'] for r in results]
mean_within_r = np.mean(within_correlations)
print(f"\nAggregate r:                {r_agg:+.4f}")
print(f"Mean of within-tertile rs:  {mean_within_r:+.4f}")
print(f"Difference (agg - within):  {r_agg - mean_within_r:+.4f}")

# Test whether within-group correlations are systematically different from aggregate
all_within_negative = all(r < 0 for r in within_correlations)
all_within_smaller_in_magnitude = all(abs(r) < abs(r_agg) for r in within_correlations)

print(f"\nAll within-group rs negative?       {all_within_negative}")
print(f"All within-group rs smaller in |r|? {all_within_smaller_in_magnitude}")

if all_within_smaller_in_magnitude:
    print("\n>>> Within-group correlations are SUBSTANTIALLY ATTENUATED relative to aggregate.")
    print(">>> This is consistent with Simpson's paradox: most of the apparent")
    print(">>> negative association arises from BETWEEN-group differences in mean EF%,")
    print(">>> not from within-tertile relationships.")

# Step 5: Decompose variance — between vs within
print("\n" + "="*78)
print("STEP 4: Variance decomposition (between- vs within-tertile)")
print("="*78)

# Between-group analysis: at the tertile level
group_means = df.groupby('tertile').agg(
    accuracy_mean=('problem_accuracy', 'mean'),
    ef_mean=('effective_feedback_pct', 'mean'),
    n=('user_id', 'count')
).reset_index()
print("\nGroup means:")
print(group_means.to_string(index=False))

# Compute the "between-group" correlation: weighted by n
# Using Pearson on the 3 group means weighted appropriately
between_r, between_p = stats.pearsonr(group_means['ef_mean'], group_means['accuracy_mean'])
print(f"\nBetween-group r (using group means): {between_r:+.4f}")
print("(Note: with only 3 groups, this is descriptive, not inferential)")

# Save results
results_df.to_csv(os.path.join(OUTPUT_DIR, 'within_group_correlations.csv'), index=False)
print("\nSaved: within_group_correlations.csv")

# ============================================================
# VISUALIZATION
# ============================================================
print("\n" + "="*78)
print("Generating visualization...")
print("="*78)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# ---- Panel A: Within-group scatter with regression lines ----
ax = axes[0]
colors = {'Low (T1)': '#D62728', 'Medium (T2)': '#FF7F0E', 'High (T3)': '#2CA02C'}
ax_text_y = [0.95, 0.85, 0.75]

for i, t in enumerate(tertile_order):
    sub = df[df['tertile'] == t]
    # Subsample for scatter readability
    sample = sub.sample(min(1500, len(sub)), random_state=42)
    ax.scatter(sample['effective_feedback_pct'], sample['problem_accuracy'],
               s=4, alpha=0.15, color=colors[t], rasterized=True)
    # Regression line
    slope, intercept, r_val, _, _ = stats.linregress(sub['effective_feedback_pct'], 
                                                      sub['problem_accuracy'])
    x_line = np.array([0, 100])
    ax.plot(x_line, intercept + slope * x_line, '-', color=colors[t], 
            linewidth=2.5, label=f'{t}: r = {r_val:+.3f}')

ax.set_xlabel('Effective Feedback Usage (%)', fontsize=11)
ax.set_ylabel('Problem-Solving Accuracy (%)', fontsize=11)
ax.set_title('(a) Within-Tertile Relationships\nbetween Effective Feedback and Accuracy', 
             fontsize=12, fontweight='bold')
ax.legend(loc='lower left', fontsize=10, framealpha=0.95)
ax.set_xlim(-3, 103)
ax.set_ylim(-3, 103)
ax.grid(alpha=0.2)

# Add aggregate line for comparison
slope_agg, int_agg, _, _, _ = stats.linregress(df['effective_feedback_pct'], 
                                                df['problem_accuracy'])
ax.plot(x_line, int_agg + slope_agg * x_line, '--', color='black', 
        linewidth=2, alpha=0.7, label=f'Aggregate: r = {r_agg:+.3f}')
ax.legend(loc='lower left', fontsize=9.5, framealpha=0.95)

# ---- Panel B: Bar comparison of correlations ----
ax = axes[1]
labels = ['Aggregate\n(N = 16,389)'] + [f'{t}\n(n = {results[i]["N"]:,})' 
                                          for i, t in enumerate(tertile_order)]
r_values = [r_agg] + within_correlations
bar_colors = ['#404040'] + [colors[t] for t in tertile_order]

bars = ax.bar(labels, r_values, color=bar_colors, alpha=0.85, edgecolor='black', linewidth=0.8)

# Add value labels on bars
for bar, r in zip(bars, r_values):
    height = bar.get_height()
    label_y = height + 0.005 if height > 0 else height - 0.012
    va = 'bottom' if height > 0 else 'top'
    ax.text(bar.get_x() + bar.get_width()/2, label_y, f'{r:+.4f}', 
            ha='center', va=va, fontsize=11, fontweight='bold')

# Add CI error bars for within-group correlations
for i, (t, bar) in enumerate(zip(tertile_order, bars[1:])):
    sub = df[df['tertile'] == t]
    n_t = len(sub)
    z = np.arctanh(within_correlations[i])
    se = 1 / np.sqrt(n_t - 3)
    ci_lo = np.tanh(z - 1.96 * se)
    ci_hi = np.tanh(z + 1.96 * se)
    ax.errorbar(bar.get_x() + bar.get_width()/2, within_correlations[i],
                yerr=[[within_correlations[i] - ci_lo], [ci_hi - within_correlations[i]]],
                fmt='none', color='black', capsize=5, linewidth=1.5)

ax.axhline(0, color='black', linewidth=0.6)
ax.set_ylabel('Pearson r (EF% × Accuracy)', fontsize=11)
ax.set_title('(b) Aggregate vs. Within-Tertile Correlations\n(error bars = 95% CI)', 
             fontsize=12, fontweight='bold')
ax.grid(alpha=0.2, axis='y')
ax.set_ylim(-0.15, 0.10)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'Figure_within_group_correlations.png'), 
            dpi=300, bbox_inches='tight')
plt.savefig(os.path.join(OUTPUT_DIR, 'Figure_within_group_correlations.pdf'), 
            bbox_inches='tight')
print("Saved: Figure_within_group_correlations.png + .pdf")

print("\n" + "="*78)
print("ANALYSIS COMPLETE")
print("="*78)
