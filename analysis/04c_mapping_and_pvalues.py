# Portable revision pipeline. Run via python run.py reproduce.
"""04c: restore archived five-category coding and correct correlation p-values.

Only reads previous outputs and archived coding records. New outputs are written
to run04c_outputs. This is a post-hoc sensitivity analysis, not construct validation.
"""
from pathlib import Path
import json
import hashlib
import platform
import warnings
import numpy as np
import pandas as pd
import scipy
from scipy import stats
from statsmodels.stats.multitest import multipletests

VERSION = '2026-09-18-04c-v1'
# Feature, Coder 1, Coder 2, recorded adjudication/consensus (before author remapping).
MAPPING = [
    ('知识图谱点击','Process','Process','Process'),
    ('预设问答','Task','Task','Task'),
    ('来自mooccube','Task','Task','Task'),
    ('来自图灵机器人','Self-Regulation','Self','Self'),
    ('来自baidu','Task','Task','Task'),
    ('来自baike','Task','Task','Task'),
    ('作诗','Other','Other','Other'),
    ('来自Faq','Other','Other','Other'),
    ('来自Aminer','Task','Process','Process'),
    ('助教回答','Other','Task','Other'),
    ('飘窗回答','Process','Process','Process'),
    ('cannot_answer','Other','Other','Other'),
    ('问助教','Other','Other','Other'),
    ('加减乘除','Other','Other','Other'),
    ('脏问题','Other','Other','Other'),
    ('来自课程信息','Other','Other','Other'),
]

def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')

def fisher_ci(r, n):
    if n <= 3 or abs(r) >= 1:
        return [None, None]
    return np.tanh(np.arctanh(r) + np.array([-1, 1])*stats.norm.ppf(.975)/np.sqrt(n-3)).tolist()

def paired_spearman_ci(x, y, count, seed, label):
    """Percentile paired-row bootstrap, recomputing average ranks each time."""
    rng = np.random.default_rng(seed)
    x, y = np.asarray(x, float), np.asarray(y, float)
    values = []
    for b in range(count):
        idx = rng.integers(0, len(x), len(x))
        a, c = stats.rankdata(x[idx]), stats.rankdata(y[idx])
        a -= a.mean()
        c -= c.mean()
        den = np.sqrt(np.dot(a,a)*np.dot(c,c))
        if den > 0:
            values.append(float(np.dot(a,c)/den))
        if (b+1) % 1000 == 0:
            print(f'  {label}: bootstrap {b+1}/{count}', flush=True)
    if len(values) < .99*count:
        raise ValueError(f'{label}: too many undefined bootstrap resamples')
    ci = np.percentile(values, [2.5,97.5]).tolist()
    return ci, len(values)

def correlation(st, variable, method):
    z = st[[variable, 'strict_accuracy_pct']].dropna()
    if len(z) <= 500 or z[variable].nunique() < 2:
        raise ValueError(f'{variable}: insufficient sample/variation for planned test')
    x, y = z[variable].to_numpy(), z.strict_accuracy_pct.to_numpy()
    result = stats.spearmanr(x,y,alternative='two-sided') if method == 'spearman' else stats.pearsonr(x,y)
    r, p = float(result.statistic), float(result.pvalue)
    if not np.isfinite([r,p]).all():
        raise ValueError(f'{variable}/{method}: nonfinite result')
    return r, p, len(z)

def main(root, bootstrap_n=10000, seed=20260918):
    root = Path(root).expanduser().resolve()
    rev = root/'revision_round2'
    repo = Path(__file__).resolve().parents[1]
    inputs = {
        'students': rev/'run02_outputs/strict_student_model_data.csv',
        'features': rev/'run01_outputs/feature_counts_long.csv',
        'family': rev/'run04b_outputs/multiplicity_v2.csv',
        'ratings': repo/'materials/irr_side_by_side.csv',
        'adjudication': repo/'materials/adjudications.md',
    }
    for p in inputs.values():
        if not p.is_file():
            raise FileNotFoundError(p)
    if bootstrap_n < 1000:
        raise ValueError('Use at least 1000 bootstrap replicates; planned value is 10000.')
    out = rev/'run04c_outputs'
    out.mkdir(exist_ok=True)
    summary = {'version':VERSION, 'status':'STARTED', 'environment':{
        'python':platform.python_version(), 'numpy':np.__version__,
        'pandas':pd.__version__, 'scipy':scipy.__version__}, 'inputs':{},
        'definitions':{
            'mapping':'Raw coder consensus plus documented adjudication; no subsequent author remapping.',
            'coding_scope':'Function-level coding sensitivity only; does not establish feedback content or construct validity.',
            'new_composite':'100 * (restored Process + restored Self-Regulation) / ALL AI interactions',
            'new_other':'100 * restored Other / ALL AI interactions; Other is never in the composite numerator',
            'legacy_denominator':'04b ef_mapped_only retained under explicit historical-denominator label only',
            'spearman_p':'scipy.stats.spearmanr two-sided large-sample asymptotic p; not bootstrap/permutation p',
            'pearson_p':'scipy.stats.pearsonr conventional two-sided parametric p; not a distribution-free test',
            'new_ci':'Pearson Fisher z; Spearman paired-row percentile bootstrap',
            'family':'44 explicitly selected 04b tests + 4 new mapping correlations; exploratory BH across 48. Not all historical analyses.',
            'intervals':'Marginal 95% intervals, not simultaneous or BH-adjusted intervals',
            'sampling':'Student-level correlations/bootstrap assume independent student rows; no causal interpretation',
        }}
    for name,p in inputs.items():
        summary['inputs'][name] = {'path':str(p), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    write_json(out/'run04c_summary.json',summary)
    try:
        mapping = pd.DataFrame(MAPPING, columns=['base_feature','coder1','coder2','restored_category'])
        raw = pd.read_csv(inputs['ratings'])
        raw['base_feature'] = raw['Feature (CN)'].str.replace(r'\s+','',regex=True)
        if len(raw) != 16 or raw.base_feature.duplicated().any():
            raise ValueError('Archived rating table is not 16 unique functions.')
        decode = {'Process (FP)':'Process','Task (FT)':'Task','Self-Regulation (FR)':'Self-Regulation',
                  'Self (FS)':'Self','Other / Not Applicable':'Other'}
        raw = raw.set_index('base_feature')
        if set(raw.index) != set(mapping.base_feature):
            raise ValueError('Unexpected feature names in archived ratings.')
        for row in mapping.itertuples():
            if decode.get(raw.loc[row.base_feature,'Coder 1']) != row.coder1 or decode.get(raw.loc[row.base_feature,'Coder 2']) != row.coder2:
                raise ValueError(f'Rating mismatch: {row.base_feature}')
        recorded = inputs['adjudication'].read_text(encoding='utf-8')
        for statement in ['Turing Bot (FR vs FS → adjudicated to FS)',
                          'Aminer (FT vs FP → adjudicated to FP)',
                          'TA Answer Browser (Other vs FT → adjudicated to Other)']:
            if statement not in recorded:
                raise ValueError('Archived adjudication changed: '+statement)
        mapping['basis'] = np.where(mapping.coder1==mapping.coder2, 'raw coder agreement','documented adjudication')
        mapping['source'] = np.where(mapping.coder1==mapping.coder2,
            'materials/irr_side_by_side.csv','materials/adjudications.md')
        st = pd.read_csv(inputs['students'],dtype={'user_id':str})
        fc = pd.read_csv(inputs['features'],encoding='utf-8-sig',dtype={'user_id':str})
        if st.user_id.isna().any() or st.user_id.duplicated().any() or not (st.ai_frequency>0).all():
            raise ValueError('Invalid student keys or denominators.')
        if fc[['user_id','base_feature','n_interactions']].isna().any().any():
            raise ValueError('Missing feature data.')
        if not ((fc.n_interactions>=0)&(fc.n_interactions%1==0)).all():
            raise ValueError('Invalid feature counts.')
        if set(fc.base_feature)-set(mapping.base_feature):
            raise ValueError('Unmapped recorded features.')
        counts = fc.pivot_table(index='user_id',columns='base_feature',values='n_interactions',aggfunc='sum',fill_value=0)
        counts = counts.reindex(index=st.user_id,columns=mapping.base_feature)
        if counts.isna().any().any() or not np.array_equal(counts.sum(axis=1).to_numpy(),st.ai_frequency.to_numpy()):
            raise ValueError('Feature totals do not match student AI totals.')
        mapping['interactions_main_sample'] = mapping.base_feature.map(counts.sum(axis=0))
        mapping.to_csv(out/'restored_feature_mapping.csv',index=False,encoding='utf-8-sig')
        category_counts = pd.DataFrame({'user_id':st.user_id.to_numpy()})
        for cat in ['Task','Process','Self-Regulation','Self','Other']:
            cols = mapping.loc[mapping.restored_category==cat,'base_feature'].tolist()
            category_counts[cat] = counts[cols].sum(axis=1).to_numpy()
        if not np.array_equal(category_counts.iloc[:,1:].sum(axis=1).to_numpy(),st.ai_frequency.to_numpy()):
            raise ValueError('Restored categories do not sum to AI total.')
        st['restored_process_selfreg_pct'] = 100*(category_counts['Process']+category_counts['Self-Regulation'])/st.ai_frequency
        st['restored_other_pct'] = 100*category_counts['Other']/st.ai_frequency
        st['historical_ef'] = 100*(st.process_count+st.self_reg_count)/st.ai_frequency
        st['kg_moved_to_task'] = 100*(st.process_count-st.kg_count+st.self_reg_count)/st.ai_frequency
        st['other_share'] = 100*st.other_count/st.ai_frequency
        st['ef_mapped_only'] = 100*(st.process_count+st.self_reg_count)/(st.ai_frequency-st.other_count).replace(0,np.nan)
        st['log_kg_count'] = np.log1p(st.kg_count)
        st['kg_any'] = (st.kg_count>=1).astype(int)
        category_counts['ai_frequency'] = st.ai_frequency.to_numpy()
        for c in ['strict_accuracy_pct','restored_process_selfreg_pct','restored_other_pct']:
            category_counts[c] = st[c].to_numpy()
        category_counts.to_csv(out/'restored_student_counts.csv',index=False)
        summary['mapping_checks'] = {'ratings_agreements':int((mapping.coder1==mapping.coder2).sum()),
            'documented_disagreements':int((mapping.coder1!=mapping.coder2).sum()),
            'n_students':len(st), 'all_totals_match':True,
            'new_denominator_exclusions':0,
            'category_interactions':{cat:int(category_counts[cat].sum()) for cat in ['Task','Process','Self-Regulation','Self','Other']}}
        print('DATA CHECKS PASSED. Restored mapping:',flush=True)
        print(mapping[['base_feature','coder1','coder2','restored_category']].to_string(index=False),flush=True)
        tests = pd.read_csv(inputs['family'])
        if len(tests)!=44 or tests.duplicated(['source','variable','method']).any():
            raise ValueError('Expected the reviewed 44 unique tests from 04b.')
        updates = []
        for idx,row in tests.iterrows():
            tests.loc[idx,'p_method'] = 'retained fitted-model/Welch p from 04b'
            if row.source != 'correlation':
                continue
            r,p,n = correlation(st,row.variable,row.method)
            if not np.isclose(r,row.stat,rtol=1e-9,atol=1e-12):
                raise ValueError(f'Correlation changed unexpectedly: {row.variable}/{row.method}')
            tests.loc[idx,'stat'],tests.loc[idx,'raw_p'] = r,p
            tests.loc[idx,'p_method'] = 'scipy.stats.'+('spearmanr asymptotic' if row.method=='spearman' else 'pearsonr parametric')
            updates.append({'variable':row.variable,'method':row.method,'n':n,'old_p':float(row.raw_p),'new_p':p})
        # Rename legacy Other measures; do not silently relabel them as restored coding.
        renames = {'other_share':'historical_other_share','ef_mapped_only':'historical_ef_excluding_other_denominator'}
        tests['variable'] = tests.variable.replace(renames)
        new_rows, result_rows = [], []
        for offset,v in enumerate(['restored_process_selfreg_pct','restored_other_pct']):
            print('New mapping analysis:',v,flush=True)
            ci_s,valid = paired_spearman_ci(st[v],st.strict_accuracy_pct,bootstrap_n,seed+offset,v)
            for method in ['pearson','spearman']:
                r,p,n = correlation(st,v,method)
                ci = fisher_ci(r,n) if method=='pearson' else ci_s
                result_rows.append({'variable':v,'method':method,'n':n,'r':r,'raw_p':p,
                    'ci_low':ci[0],'ci_high':ci[1],
                    'ci_method':'Fisher z' if method=='pearson' else 'paired row percentile bootstrap; ranks recomputed',
                    'bootstrap_valid':None if method=='pearson' else valid,
                    'seed':None if method=='pearson' else seed+offset})
                new_rows.append({'source':'correlation','variable':v,'method':method,'stat':r,'raw_p':p,
                    'group':'student_correlation','reviewer_focus':False,
                    'p_method':'scipy.stats.'+('spearmanr asymptotic' if method=='spearman' else 'pearsonr parametric')})
        tests = pd.concat([tests,pd.DataFrame(new_rows)],ignore_index=True)
        if len(tests)!=48 or tests.duplicated(['source','variable','method']).any():
            raise ValueError('Expected 48 unique listed hypotheses.')
        if not np.isfinite(tests.raw_p).all() or not tests.raw_p.between(0,1).all():
            raise ValueError('Invalid p-values.')
        tests['bh_q'] = multipletests(tests.raw_p.to_numpy(),method='fdr_bh')[1]
        tests['family_id'] = '04c_selected_exploratory_48'
        tests.to_csv(out/'multiplicity_v3.csv',index=False)
        results = pd.DataFrame(result_rows).merge(tests[['source','variable','method','bh_q']].query("source == 'correlation'").drop(columns='source'),on=['variable','method'],validate='one_to_one')
        results.to_csv(out/'restored_mapping_sensitivity.csv',index=False)
        pd.DataFrame(updates).to_csv(out/'correlation_pvalue_changes.csv',index=False)
        summary['results'] = {'mapping_sensitivity':results.to_dict('records'),
            'family_size':len(tests),'correlation_pvalues_updated':len(updates),
            'existing_models_refitted':0,'existing_bootstrap_rerun':False}
        # pandas may represent missing numeric metadata as NaN; serialize strict JSON.
        summary['results']['mapping_sensitivity'] = json.loads(results.to_json(orient='records',force_ascii=False,double_precision=15))
        summary['status'] = 'COMPLETE_REVIEW_REQUIRED'
        print(results.to_string(index=False),flush=True)
        print('Finished. Outputs:',out,flush=True)
    except Exception as exc:
        summary['status'] = 'FAILED'
        summary['error'] = repr(exc)
        raise
    finally:
        write_json(out/'run04c_summary.json',summary)

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]/'outputs'))
    args = ap.parse_args()
    main(args.root)
