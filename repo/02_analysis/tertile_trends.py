"""
tertile_trends.py
==================
Reproduces manuscript Table 5 ("AI Usage Patterns and Learning Indicators
Across Performance Tertiles") in full: tertile means, standard deviations,
and the linear-trend coefficient (beta, SE, t, p) for every row of the table.

This script supersedes the earlier predominantly_usage_trends.py: the three
"Usage Patterns" rows computed by that script are a subset of the eleven
rows produced here.

Operationalisation:
  - Runs on the full analytic sample (N = 16,389), consistent with Table 5.
  - Performance tertiles are defined by FIXED accuracy cutpoints at 67.5%
    and 84.0% (the 33rd and 67th percentiles), matching the manuscript:
        Low    = problem_accuracy < 67.5
        Medium = 67.5 <= problem_accuracy <= 84.0
        High   = problem_accuracy > 84.0
  - Tertile rank is coded 1 (Low) / 2 (Medium) / 3 (High).
  - "Predominantly" indicators use a > 70% threshold on the corresponding
    usage percentage; "Mixed / Balanced" is the complement (neither
    process_pct nor task_pct exceeds 70%).

Method:
  For each row variable, an OLS linear regression of the variable on the
  1/2/3 tertile rank. The reported beta is the change per tertile step,
  in the variable's original units (percentage points for percentage
  variables, raw units otherwise).

Input:
  ../combined_ai_learning_data.csv (16,389 students, prepared by the
  main analysis pipeline that pre-dates this revision)

Output:
  tertile_trends_results.csv  — one row per Table 5 variable, with the
                                tertile means, SDs, and beta / SE / t / p
  tertile_trends_summary.txt  — human-readable summary

Usage:
  python tertile_trends.py
"""

import pandas as pd
import numpy as np
from scipy.stats import linregress
import os

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
INPUT_PATH = "combined_ai_learning_data.csv"  # adjust if path differs
CUT_LOW = 67.5                   # accuracy cutpoint: Low / Medium
CUT_HIGH = 84.0                  # accuracy cutpoint: Medium / High
PREDOMINANT_THRESHOLD = 70       # > 70% of interactions = predominant
OUTPUT_DIR = os.environ.get("RESULTS_DIR", "../03_results")
os.makedirs(OUTPUT_DIR, exist_ok=True)
RESULTS_CSV = os.path.join(OUTPUT_DIR, "tertile_trends_results.csv")
SUMMARY_TXT = os.path.join(OUTPUT_DIR, "tertile_trends_summary.txt")

# -----------------------------------------------------------------------------
# LOAD DATA
# -----------------------------------------------------------------------------
df = pd.read_csv(INPUT_PATH)
print(f"Loaded {len(df):,} students from {INPUT_PATH}")

# -----------------------------------------------------------------------------
# DEFINE PERFORMANCE TERTILES (fixed cutpoints, matching Table 5)
# -----------------------------------------------------------------------------
def tertile_rank(accuracy):
    if accuracy < CUT_LOW:
        return 1
    elif accuracy <= CUT_HIGH:
        return 2
    else:
        return 3

df["tertile"] = df["problem_accuracy"].apply(tertile_rank)
sizes = df["tertile"].value_counts().sort_index()
print(f"Tertile sizes — Low: {sizes[1]:,}  Medium: {sizes[2]:,}  High: {sizes[3]:,}")

# Derive the three "Usage Patterns" indicators (0-100 scale)
df["pred_process"] = (df["process_pct"] > PREDOMINANT_THRESHOLD).astype(float) * 100
df["pred_task"] = (df["task_pct"] > PREDOMINANT_THRESHOLD).astype(float) * 100
df["pred_mixed"] = (
    (df["process_pct"] <= PREDOMINANT_THRESHOLD)
    & (df["task_pct"] <= PREDOMINANT_THRESHOLD)
).astype(float) * 100

# -----------------------------------------------------------------------------
# TABLE 5 ROW SPECIFICATION
# (section label, display name, column in df)
# -----------------------------------------------------------------------------
ROWS = [
    ("Sample & Performance", "Problem Accuracy %", "problem_accuracy"),
    ("Sample & Performance", "Problems Attempted", "total_problems"),
    ("AI Usage Quantity",    "AI Frequency",       "ai_frequency"),
    ("AI Usage Quantity",    "AI Frequency (Mdn)", "ai_frequency"),
    ("AI Usage Character",   "Process Feedback %", "process_pct"),
    ("AI Usage Character",   "Task Feedback %",    "task_pct"),
    ("AI Usage Character",   "Self-Regulation %",  "self_reg_pct"),
    ("AI Usage Character",   "Self Feedback %",    "self_pct"),
    ("AI Usage Character",   "Effective Feedback %", "effective_feedback_pct"),
    ("Usage Patterns",       "Predominantly Process", "pred_process"),
    ("Usage Patterns",       "Predominantly Task",    "pred_task"),
    ("Usage Patterns",       "Mixed / Balanced",      "pred_mixed"),
]


def stars(p):
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    return "ns"


# -----------------------------------------------------------------------------
# COMPUTE TERTILE STATISTICS AND LINEAR TREND FOR EACH ROW
# -----------------------------------------------------------------------------
results = []
for section, name, col in ROWS:
    is_median = name.endswith("(Mdn)")
    if is_median:
        # Median row: report tertile medians only; no SD, no trend test
        meds = df.groupby("tertile")[col].median()
        results.append({
            "Section": section,
            "Variable": name,
            "Low mean": round(meds[1], 2),
            "Low SD": np.nan,
            "Medium mean": round(meds[2], 2),
            "Medium SD": np.nan,
            "High mean": round(meds[3], 2),
            "High SD": np.nan,
            "beta": np.nan,
            "SE": np.nan,
            "t": np.nan,
            "p": np.nan,
            "p_label": "",
            "significance": "",
        })
        continue
    means = df.groupby("tertile")[col].mean()
    sds = df.groupby("tertile")[col].std()
    x = df["tertile"].values.astype(float)
    y = df[col].values.astype(float)
    slope, intercept, r, p, se = linregress(x, y)
    t = slope / se
    results.append({
        "Section": section,
        "Variable": name,
        "Low mean": round(means[1], 2),
        "Low SD": round(sds[1], 2),
        "Medium mean": round(means[2], 2),
        "Medium SD": round(sds[2], 2),
        "High mean": round(means[3], 2),
        "High SD": round(sds[3], 2),
        "beta": round(slope, 2),
        "SE": round(se, 3),
        "t": round(t, 2),
        "p": p if p > 1e-300 else 0.0,  # underflow guard
        "p_label": "< 1e-300" if p < 1e-300 else f"{p:.2e}",
        "significance": stars(p),
    })

results_df = pd.DataFrame(results)
results_df.to_csv(RESULTS_CSV, index=False)
print(f"Results saved to: {RESULTS_CSV}")

# -----------------------------------------------------------------------------
# WRITE HUMAN-READABLE SUMMARY
# -----------------------------------------------------------------------------
with open(SUMMARY_TXT, "w") as f:
    f.write("Tertile Trend Analysis — Manuscript Table 5\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Input file:        {INPUT_PATH}\n")
    f.write(f"Total sample:      N = {len(df):,}\n")
    f.write(f"Tertile cutpoints: {CUT_LOW} and {CUT_HIGH} (problem_accuracy)\n")
    f.write(f"Tertile sizes:     Low = {sizes[1]:,}, "
            f"Medium = {sizes[2]:,}, High = {sizes[3]:,}\n")
    f.write(f"Predominant cutoff: usage percentage > {PREDOMINANT_THRESHOLD}\n")
    f.write("Method:            OLS linear regression on tertile rank (1/2/3)\n\n")

    f.write("Row statistics (mean [SD] per tertile; linear trend):\n\n")
    current_section = None
    for r in results:
        if r["Section"] != current_section:
            current_section = r["Section"]
            f.write(f"  [{current_section}]\n")
        if pd.isna(r["p"]):
            f.write(f"    {r['Variable']:24s} "
                    f"Low {r['Low mean']:8.2f}  Med {r['Medium mean']:8.2f}  "
                    f"High {r['High mean']:8.2f}  (median row; no trend test)\n")
            continue
        p_str = "< .001" if r["p"] < 0.001 else f"= {r['p']:.3f}"
        f.write(f"    {r['Variable']:24s} "
                f"Low {r['Low mean']:8.2f} ({r['Low SD']:.2f})  "
                f"Med {r['Medium mean']:8.2f} ({r['Medium SD']:.2f})  "
                f"High {r['High mean']:8.2f} ({r['High SD']:.2f})  "
                f"beta = {r['beta']:+.2f}, SE = {r['SE']:.3f}, "
                f"t = {r['t']:+.2f}, p {p_str}  {r['significance']}\n")

    f.write("\nNote: *** p < .001, ** p < .01, * p < .05. The AI Frequency\n")
    f.write("linear trend is the only non-significant row.\n")

print(f"Summary saved to: {SUMMARY_TXT}")
print("\n" + "=" * 78)
print("Analysis complete.")
print("=" * 78)
