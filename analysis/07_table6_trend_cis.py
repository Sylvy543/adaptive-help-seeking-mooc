# Portable revision pipeline. Run via python run.py reproduce.
"""Stage 7: CIs for the Section 4.3 group comparison and Table 6 trend betas.

Reviewer 7, comment 9 (report CIs more regularly). Reads only
run02_outputs/strict_student_model_data.csv. Writes run07_outputs.

Definitions fixed at 2026-09-21, before execution:

1. Section 4.3 group comparison. Groups defined exactly as in the
   manuscript: high-effectiveness users = historical effective-feedback
   share >= 70% (effective_feedback_pct, the historical composite), low =
   < 70%. PRIMARY outcome: strict_accuracy_pct (strict is_correct).
   The historical accuracy outcome (historical_accuracy_pct) is computed
   as a provenance check against the round-1 manuscript values
   (t = -10.35, d = -0.17, means 72.29 vs 75.79). Welch's t-test; mean
   difference with Welch 95% CI (primary); Hedges g with analytic 95% CI
   (secondary), matching the run04b effect-size convention.

2. Table 6 tertile trend CIs. Tertiles use the revision pipeline cut
   points (strict_accuracy_pct < 67.5 / <= 84; identical to run02/run04,
   giving n = 5,540 / 5,467 / 5,382). Trend is an OLS of the row variable
   on the tertile index (1, 2, 3) with HC3 covariance; beta is the
   per-tertile-step slope in the row's original units (percentage-point
   rows stay in percentage points; the two "Predominantly > 70%" rows are
   analysed as binary 0/1 variables and their slope is multiplied by 100
   to express percentage points, matching the manuscript's units).
   Rows mirror manuscript Table 6, using the historical five-category
   counts already present in the student dataset so the existing table
   can be updated in place; strict accuracy is the outcome row.
   Historical accuracy trend is included for provenance comparison only.

3. Multiplicity: these exploratory rows report unadjusted p values. They
   do not add tests to either the archived 48-test or 60-test BH family.
"""
import argparse, json, platform, warnings
from pathlib import Path
import numpy as np
import pandas as pd

VERSION = '2026-09-21-v1'
TERTILE_CUTS = (67.5, 84.0)

def write_json(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

def hedges_g(d1, d2):
    n1, n2 = len(d1), len(d2)
    sp = np.sqrt(((n1 - 1) * d1.var(ddof=1) + (n2 - 1) * d2.var(ddof=1)) / (n1 + n2 - 2))
    d = (d1.mean() - d2.mean()) / sp
    j = 1 - 3 / (4 * (n1 + n2) - 9)
    g = j * d
    se = np.sqrt((n1 + n2) / (n1 * n2) + g ** 2 / (2 * (n1 + n2 - 2)))
    return float(g), float(g - 1.959963984540054 * se), float(g + 1.959963984540054 * se)

def group_compare(df, group_col, outcome):
    hi = df.loc[df[group_col], outcome].dropna()
    lo = df.loc[~df[group_col], outcome].dropna()
    from scipy import stats as sst
    t, p = sst.ttest_ind(hi, lo, equal_var=False)
    diff = hi.mean() - lo.mean()
    se = np.sqrt(hi.var(ddof=1) / len(hi) + lo.var(ddof=1) / len(lo))
    dfree = se ** 4 / ((hi.var(ddof=1) / len(hi)) ** 2 / (len(hi) - 1) + (lo.var(ddof=1) / len(lo)) ** 2 / (len(lo) - 1))
    tcrit = sst.t.ppf(0.975, dfree)
    g, glo, ghi = hedges_g(hi, lo)
    return {'outcome': outcome, 'n_high': len(hi), 'n_low': len(lo),
            'mean_high': float(hi.mean()), 'sd_high': float(hi.std(ddof=1)),
            'mean_low': float(lo.mean()), 'sd_low': float(lo.std(ddof=1)),
            'mean_diff': float(diff), 'diff_ci_low': float(diff - tcrit * se), 'diff_ci_high': float(diff + tcrit * se),
            'welch_t': float(t), 'welch_df': float(dfree), 'p': float(p),
            'hedges_g': g, 'g_ci_low': glo, 'g_ci_high': ghi}

def trend_beta(df, ycol, pct_binary=False):
    z = df[['tertile_idx', ycol]].dropna()
    import statsmodels.formula.api as smf
    r = smf.ols(f'{ycol} ~ tertile_idx', data=z).fit(cov_type='HC3')
    ci = r.conf_int().loc['tertile_idx']
    scale = 100.0 if pct_binary else 1.0
    return {'variable': ycol, 'n': int(r.nobs), 'beta_per_step': float(r.params['tertile_idx'] * scale),
            'se': float(r.bse['tertile_idx'] * scale),
            'ci_low': float(ci[0] * scale), 'ci_high': float(ci[1] * scale),
            'p': float(r.pvalues['tertile_idx']),
            'units': 'percentage points per tertile step' if pct_binary else 'original units per tertile step'}

def main(root):
    root = Path(root).expanduser().resolve()
    inp = root / 'revision_round2/run02_outputs'
    out = root / 'revision_round2/run07_outputs'; out.mkdir(exist_ok=True)
    src = inp / 'strict_student_model_data.csv'
    if not src.is_file():
        raise FileNotFoundError('Run stage 2 first: ' + str(src))
    st = pd.read_csv(src)
    print('Script', VERSION, 'Python', platform.python_version(), flush=True)

    summary = {'version': VERSION, 'status': 'STARTED', 'n_student': len(st),
               'definitions': {
                   'group_split': 'historical effective_feedback_pct >= 70% (manuscript definition)',
                   'tertiles': 'strict_accuracy_pct < 67.5 / <= 84 (run02/run04 convention)',
                   'trend': 'OLS on tertile index (1,2,3), HC3 covariance; binary rows scaled x100',
                   'effect_size': 'mean difference + Welch CI (primary); Hedges g + analytic CI (secondary)'},
               'results': {}, 'notes': [
                   'Exploratory, unadjusted p values; not added to the separate 48-test or 60-test BH families.',
                   'Historical-outcome rows are provenance checks against the round-1 manuscript, not new claims.']}

    # ---- 1. Section 4.3 group comparison ----
    st['high_ef'] = st.effective_feedback_pct >= 70
    cmp_rows = [group_compare(st, 'high_ef', 'strict_accuracy_pct'),
                group_compare(st, 'high_ef', 'historical_accuracy_pct')]
    pd.DataFrame(cmp_rows).to_csv(out / 'section43_group_comparison.csv', index=False)
    summary['results']['section43'] = cmp_rows
    hist = cmp_rows[1]
    print(f"4.3 provenance check (historical outcome): t={hist['welch_t']:.2f} "
          f"(manuscript -10.35), means {hist['mean_high']:.2f} vs {hist['mean_low']:.2f} "
          f"(manuscript 72.29 vs 75.79)", flush=True)

    # ---- 2. Table 6 tertiles + trend CIs ----
    st['tertile'] = np.select([st.strict_accuracy_pct < TERTILE_CUTS[0],
                               st.strict_accuracy_pct <= TERTILE_CUTS[1]], ['Low', 'Medium'], default='High')
    st['tertile_idx'] = st.tertile.map({'Low': 1, 'Medium': 2, 'High': 3})
    # Historical five-category shares (mirror manuscript Table 6 rows).
    st['process_pct_hist'] = 100 * st.process_count / st.ai_frequency
    st['task_pct_hist'] = 100 * st.task_count / st.ai_frequency
    st['selfreg_pct_hist'] = 100 * st.self_reg_count / st.ai_frequency
    st['self_pct_hist'] = 100 * st.self_count / st.ai_frequency
    st['pred_process'] = (st.process_pct_hist > 70).astype(float)
    st['pred_task'] = (st.task_pct_hist > 70).astype(float)
    st['mixed_balanced'] = ((st.pred_process == 0) & (st.pred_task == 0)).astype(float)

    rows = [('strict_accuracy_pct', False), ('historical_accuracy_pct', False),
            ('strict_valid_records', False), ('ai_frequency', False),
            ('process_pct_hist', False), ('task_pct_hist', False),
            ('selfreg_pct_hist', False), ('self_pct_hist', False),
            ('effective_feedback_pct', False),
            ('kg_pct', False), ('other_process_pct', False),
            ('task_pct_neutral', False), ('selfreg_pct_neutral', False),
            ('pred_process', True), ('pred_task', True), ('mixed_balanced', True)]
    # Per-tertile descriptives for the replacement table.
    desc = (st.groupby('tertile', observed=False)
              .agg(n=('user_id', 'size')))
    table_rows = []
    for ycol, is_bin in rows:
        means = st.groupby('tertile', observed=False)[ycol].agg(['mean', 'std', 'count'])
        row = {'variable': ycol}
        for t in ('Low', 'Medium', 'High'):
            m = means.loc[t]
            row[f'{t.lower()}_n'] = int(m['count'])
            if is_bin:
                row[f'{t.lower()}_pct'] = float(100 * m['mean'])
            else:
                row[f'{t.lower()}_mean'] = float(m['mean'])
                row[f'{t.lower()}_sd'] = float(m['std'])
        row.update({k: v for k, v in trend_beta(st, ycol, is_bin).items() if k not in ('variable', 'n')})
        table_rows.append(row)
    tbl = pd.DataFrame(table_rows)
    tbl.to_csv(out / 'table6_tertile_trends.csv', index=False)
    summary['results']['table6'] = {'tertile_n': {t: int(desc.loc[t, 'n']) for t in ('Low', 'Medium', 'High')},
                                    'trends': table_rows}
    print('Table 6 tertile n:', summary['results']['table6']['tertile_n'], flush=True)

    summary['status'] = 'COMPLETE_REVIEW_REQUIRED'
    write_json(out / 'run07_summary.json', summary)
    print('Outputs:', out)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=str(Path(__file__).resolve().parents[1]/'outputs'))
    args = ap.parse_args()
    main(args.root)
