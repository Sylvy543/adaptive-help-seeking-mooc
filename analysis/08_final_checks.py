# Portable revision pipeline. Run via python run.py reproduce.
"""Stage 8: reproducibility patch — itemised multiplicity, Spearman bootstrap
CIs, archived Tukey / operationalisation / trend results.

Reads only run02_outputs and run05_outputs. Writes run08_outputs. Never
modifies earlier-stage outputs.

Definitions fixed at 2026-09-28, before execution:

1. Spearman bootstrap CIs for run05 rows that used the Fisher-z-on-ranks
   approximation (withdrawn convention, mirroring the 04b withdrawal):
   all strata Spearman rows (4 strata x 6 variables) and the non-focus
   subsample Spearman rows (3 subsamples x 4 non-focus variables).
   Paired row-level bootstrap, ranks recomputed per resample, B=10,000,
   seed=20260928. The run05 rows already computed with bootstrap (the two
   reviewer-focus variables) are NOT recomputed.

2. Itemised run05 stage-local family (60 tests = 36 subsample correlations
   with p + 24 model-coefficient rows, intercepts included as fitted).
   Raw p and Benjamini-Hochberg q side by side; reproduction check against
   run05_summary.json aggregate counts (60 tests, 47 raw p < .05).

3. Archived strict-outcome results cited in Sections 4.2/4.4:
   - partial correlation controlling total problems; log frequency;
     frequency dichotomised at >=2, >=5, >=10; high-performance
     classification (accuracy >= 80%); completion of >= 50 problems;
     excluding frequency > 100 — each with r, Fisher-z CI, p.
   - Tukey HSD over the seven usage-frequency groups (all 21 pairs).
   - Seven-group linear and quadratic trends with HC3 covariance.

4. The 05 script's Fisher-z Spearman CIs for strata/subsample rows are
   superseded by item (1); the withdrawal is recorded in run08_summary.json.
"""
import argparse, json, platform, warnings
from pathlib import Path
import numpy as np
import pandas as pd

VERSION = '2026-09-28-v1'
BOOT_B = 10000
BOOT_SEED = 20260928
Z = 1.959963984540054

def write_json(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

def fisher_ci(r, n):
    if n <= 3 or abs(r) >= 1:
        return [None, None]
    z = np.arctanh(r); se = 1 / np.sqrt(n - 3)
    return [float(np.tanh(z - Z * se)), float(np.tanh(z + Z * se))]

def bh_q(pvals):
    p = np.asarray(pvals, float); m = len(p)
    order = np.argsort(p); q = np.empty(m); prev = 1.0
    for i in range(m - 1, -1, -1):
        prev = min(prev, p[order[i]] * m / (i + 1)); q[order[i]] = prev
    return q

def spearman_boot_ci(xv, yv, rng, B=BOOT_B):
    from scipy import stats as sst
    n = len(xv); stats = np.empty(B)
    for b in range(B):
        idx = rng.integers(0, n, n)
        rx, ry = sst.rankdata(xv[idx]), sst.rankdata(yv[idx])
        rx -= rx.mean(); ry -= ry.mean()
        den = np.sqrt(np.dot(rx, rx) * np.dot(ry, ry))
        stats[b] = np.dot(rx, ry) / den if den > 0 else np.nan
    stats = stats[np.isfinite(stats)]
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return float(lo), float(hi), len(stats)

def main(root, boot_b=None):
    B = int(boot_b) if boot_b else BOOT_B
    root = Path(root).expanduser().resolve()
    rev = root / 'revision_round2'
    inp2, inp5 = rev / 'run02_outputs', rev / 'run05_outputs'
    out = rev / 'run08_outputs'; out.mkdir(exist_ok=True)
    for f in [inp2/'strict_student_model_data.csv', inp5/'attempts_strata_correlations.csv',
              inp5/'attempts_subsample_correlations.csv', inp5/'attempts_models.csv',
              inp5/'run05_summary.json']:
        if not f.is_file():
            raise FileNotFoundError(str(f))
    print('Script', VERSION, 'Python', platform.python_version(), 'B =', B, flush=True)
    st = pd.read_csv(inp2/'strict_student_model_data.csv')
    y = st.strict_accuracy_pct.astype(float)
    summary = {'version': VERSION, 'status': 'STARTED', 'boot_B': B, 'boot_seed': BOOT_SEED,
               'results': {}, 'notes': [
                   'run05 strata/subsample Spearman CIs computed with Fisher-z-on-ranks are SUPERSEDED by the bootstrap CIs in spearman_bootstrap_cis.csv.',
                   'Stage-local BH family for run05 is itemised in run05_family60_itemized.csv; family composition unchanged from run05 (60 tests).']}
    rng = np.random.default_rng(BOOT_SEED)

    # ---- 1. Spearman bootstrap CIs for run05 Fisher-z rows ----
    HEADLINE = ['effective_feedback_pct', 'kg_pct', 'kg_count', 'other_process_pct',
                'task_pct_neutral', 'ai_frequency']
    FOCUS = {'kg_pct', 'effective_feedback_pct'}  # already bootstrapped in run05
    st['n_attempts'] = st.strict_valid_records
    STRATA = [(1, 9, '1-9'), (10, 19, '10-19'), (20, 49, '20-49'), (50, None, '>=50')]
    med = float(st.n_attempts.median())
    subgroups = {}
    for lo, hi, lab in STRATA:
        subgroups[f'strata:{lab}'] = st[(st.n_attempts >= lo) & (st.n_attempts <= hi if hi is not None else True)]
    subgroups['subsample:attempts_ge20'] = st[st.n_attempts >= 20]
    subgroups['subsample:attempts_le_median'] = st[st.n_attempts <= med]
    subgroups['subsample:attempts_gt_median'] = st[st.n_attempts > med]
    rows = []
    for gname, d in subgroups.items():
        for var in HEADLINE:
            if gname.startswith('subsample') and var in FOCUS:
                continue  # run05 already used bootstrap for these
            z = d[[var, 'strict_accuracy_pct']].dropna()
            from scipy import stats as sst
            r, p = sst.spearmanr(z[var], z.strict_accuracy_pct)
            lo, hi, n_valid = spearman_boot_ci(z[var].to_numpy(float),
                                               z.strict_accuracy_pct.to_numpy(float), rng, B)
            rows.append({'group': gname, 'variable': var, 'n': len(z), 'spearman_r': float(r),
                         'ci_low': lo, 'ci_high': hi, 'p': float(p),
                         'ci_method': f'paired row bootstrap, B={B}, seed={BOOT_SEED}',
                         'valid_resamples': n_valid})
            print('bootstrap done:', gname, var, flush=True)
    pd.DataFrame(rows).to_csv(out/'spearman_bootstrap_cis.csv', index=False)
    summary['results']['spearman_bootstrap'] = {'rows': len(rows)}

    # ---- 2. itemised run05 family ----
    sub = pd.read_csv(inp5/'attempts_subsample_correlations.csv')
    mdl = pd.read_csv(inp5/'attempts_models.csv')
    tests = []
    for r in sub.itertuples():
        if np.isfinite(r.p):
            tests.append({'source': 'subsample_correlation', 'group': r.subsample,
                          'variable': r.variable, 'method': r.method, 'raw_p': float(r.p)})
    for r in mdl.itertuples():
        if np.isfinite(r.p):
            tests.append({'source': 'model_coefficient', 'group': r.model,
                          'variable': r.term, 'method': 'ols_wls', 'raw_p': float(r.p)})
    tf = pd.DataFrame(tests)
    tf['bh_q'] = bh_q(tf.raw_p.to_numpy())
    tf = tf.sort_values('raw_p').reset_index(drop=True)
    tf.to_csv(out/'run05_family60_itemized.csv', index=False)
    s5 = json.loads((inp5/'run05_summary.json').read_text(encoding='utf-8'))
    expected = s5['results']['multiplicity']
    check = {'n_tests': len(tf), 'n_raw_p_lt_0.05': int((tf.raw_p < .05).sum()),
             'n_bh_q_lt_0.05': int((tf.bh_q < .05).sum()),
             'run05_summary_claims': {'family_size': expected['stage_local_family_size'],
                                      'n_raw_p_lt_0.05': expected['n_raw_p_lt_0.05'],
                                      'n_bh_q_lt_0.05': expected['n_bh_q_lt_0.05']},
             'match': len(tf) == expected['stage_local_family_size'] and
                      int((tf.raw_p < .05).sum()) == expected['n_raw_p_lt_0.05'] and
                      int((tf.bh_q < .05).sum()) == expected['n_bh_q_lt_0.05']}
    summary['results']['family_itemization'] = check
    print('family check:', check, flush=True)

    # ---- 3a. Section 4.2 operationalisations (strict) ----
    import statsmodels.formula.api as smf
    from scipy import stats as sst
    x = st.ai_frequency.astype(float)
    logx = np.log1p(x)
    def prow(xv, yv):
        r, p = sst.pearsonr(xv, yv); lo, hi = fisher_ci(r, len(xv))
        return {'r': float(r), 'ci_low': lo, 'ci_high': hi, 'p': float(p), 'n': len(xv)}
    # partial correlation controlling total problems
    # 2026-09-30 fix: partial r with 1 control variable uses df = n-3 (not n-2);
    # Fisher-z CI uses n-4. r itself unchanged; p shift is in the 4th decimal.
    cx = st.total_problems.astype(float)
    rx = x - np.polyval(np.polyfit(cx, x, 1), cx)
    ry = y - np.polyval(np.polyfit(cx, y, 1), cx)
    r_par = float(np.corrcoef(rx, ry)[0, 1])
    n_par = len(st)
    t_par = r_par * np.sqrt((n_par - 3) / (1 - r_par**2))
    p_par = float(2 * sst.t.sf(abs(t_par), n_par - 3))
    z_par = np.arctanh(r_par); se_par = 1 / np.sqrt(n_par - 4)
    lo, hi = float(np.tanh(z_par - Z * se_par)), float(np.tanh(z_par + Z * se_par))
    op = [{'analysis': 'pearson_frequency', **prow(x, y)},
          {'analysis': 'partial_frequency_given_problems', 'r': float(r_par), 'ci_low': lo, 'ci_high': hi, 'p': float(p_par), 'n': len(st)},
          {'analysis': 'log_frequency', **prow(logx, y)},
          {'analysis': 'dichotomised_ge2', **prow((x >= 2).astype(float), y)},
          {'analysis': 'dichotomised_ge5', **prow((x >= 5).astype(float), y)},
          {'analysis': 'dichotomised_ge10', **prow((x >= 10).astype(float), y)},
          {'analysis': 'high_perf_ge80pct', **prow(x, (y >= 80).astype(float))},
          {'analysis': 'completion_ge50_problems', **prow(x, (st.total_problems >= 50).astype(float))},
          {'analysis': 'exclude_freq_gt100', **prow(x[x <= 100], y[x <= 100])}]
    pd.DataFrame(op).to_csv(out/'section42_operationalisations.csv', index=False)
    summary['results']['section42'] = op

    # ---- 3b. Tukey HSD, seven groups (strict) ----
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    labels7 = ['1', '2-5', '6-10', '11-20', '21-50', '51-100', '>100']
    g7 = pd.cut(st.ai_frequency, [0, 1, 5, 10, 20, 50, 100, 10**9], labels=labels7)
    tk = pairwise_tukeyhsd(y, g7)
    tk_df = pd.DataFrame(tk.summary().data[1:], columns=tk.summary().data[0])
    tk_df.to_csv(out/'section44_tukey.csv', index=False)
    maxrow = tk_df.loc[tk_df.meandiff.astype(float).abs().idxmax()]
    summary['results']['tukey'] = {'n_pairs': len(tk_df), 'any_reject': bool(tk_df.reject.astype(bool).any()),
        'max_abs_pair': {'group1': str(maxrow.group1), 'group2': str(maxrow.group2),
                         'meandiff': float(maxrow.meandiff), 'p_adj': float(maxrow['p-adj'])}}

    # ---- 3c. Seven-group trends with HC3 ----
    d7 = st.assign(g7i=g7.cat.codes + 1)
    rl = smf.ols('strict_accuracy_pct ~ g7i', data=d7).fit(cov_type='HC3')
    rq = smf.ols('strict_accuracy_pct ~ g7i + I(g7i**2)', data=d7).fit(cov_type='HC3')
    def term_row(model_name, fit, term):
        ci = fit.conf_int().loc[term]
        return {'model': model_name, 'term': term, 'beta': float(fit.params[term]),
                'se': float(fit.bse[term]), 'ci_low': float(ci[0]), 'ci_high': float(ci[1]),
                'p': float(fit.pvalues[term]), 'nobs': float(fit.nobs), 'cov': 'HC3'}
    trends = [term_row('seven_group_linear', rl, 'g7i'),
              term_row('seven_group_quadratic', rq, 'g7i'),
              term_row('seven_group_quadratic', rq, 'I(g7i ** 2)')]
    pd.DataFrame(trends).to_csv(out/'section44_trends_hc3.csv', index=False)
    summary['results']['trends_hc3'] = trends
    # ANOVA for completeness
    groups7 = [st[g7 == g].strict_accuracy_pct for g in labels7]
    F, pa = sst.f_oneway(*groups7)
    grand = y.mean()
    eta2 = sum(len(g) * (g.mean() - grand)**2 for g in groups7) / ((y - grand)**2).sum()
    summary['results']['anova7'] = {'F': float(F), 'df': [6, len(st) - 7], 'p': float(pa), 'eta2': float(eta2)}

    summary['status'] = 'COMPLETE_REVIEW_REQUIRED'
    write_json(out/'run08_summary.json', summary)
    print(json.dumps(summary['results'], ensure_ascii=False, indent=2, default=str)[:2000])
    print('Outputs:', out)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=str(Path(__file__).resolve().parents[1]/'outputs'))
    ap.add_argument('--boot', default=None, help='override bootstrap B (testing only; default 10000)')
    args = ap.parse_args()
    main(args.root, args.boot)
