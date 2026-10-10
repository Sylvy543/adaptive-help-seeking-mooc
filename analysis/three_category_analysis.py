"""OR4 strict-accuracy refresh; inputs are read-only; results have no student IDs."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from scipy import stats

import argparse
ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);args=ap.parse_args()
SOURCE=args.root.resolve()/'revision_round2'
HERE=args.root.resolve()/'online_resources/Online_Resource_4_Three_Category_Results';HERE.mkdir(parents=True,exist_ok=True)
path = SOURCE / 'run02_outputs/strict_student_model_data.csv'
s = pd.read_csv(path)
assert len(s) == 16389 and s.user_id.nunique() == len(s)
assert s.ai_frequency.sum() == 85815
assert (s.strict_valid_records > 0).all()
np.testing.assert_allclose(s.strict_accuracy_pct, 100*s.strict_correct_records/s.strict_valid_records)
specs = [
    ('Knowledge Graph Navigation', 'kg_pct', 'kg_count', 'kg_pct'),
    ('Other Process-level (MOOCCubeX concept search and Aminer academic search)', 'other_process_pct', 'other_process_count', 'other_process_pct'),
    ('Task-level (neutral feature mapping)', 'task_pct_neutral', 'task_count_neutral', 'task_pct'),
    ('Self-Regulation (historical author mapping)', 'selfreg_pct_neutral', 'selfreg_count_neutral', 'selfreg_pct'),
    ('Self-level (entertainment chatbot and poetry)', 'self_pct_neutral', 'self_count_neutral', 'self_pct'),
]
for _, v, c, _ in specs:
    assert np.isfinite(s[v]).all() and s[v].between(0,100).all()
    np.testing.assert_allclose(s[v],100*s[c]/s.ai_frequency,atol=1e-12)
assert (s[[c for _,_,c,_ in specs]].sum(axis=1)+s.other_count_neutral == s.ai_frequency).all()
s['tertile'] = np.select([s.strict_accuracy_pct < 67.5, s.strict_accuracy_pct <= 84], ['Low (T1)', 'Medium (T2)'], default='High (T3)')
assert s.groupby('tertile').size().to_dict() == {'Low (T1)':5540,'Medium (T2)':5467,'High (T3)':5382}
zcrit = stats.norm.ppf(.975)
corr, tests, groups = [], [], []
oldcorr = pd.read_csv(SOURCE/'run02_outputs/strict_student_correlations.csv')
oldtests = pd.read_csv(SOURCE/'run04b_outputs/tertile_comparisons_v2.csv').set_index('variable')
oldgroups = pd.read_csv(SOURCE/'run02_outputs/strict_tertiles.csv').set_index('strict_tertile')
mult = pd.read_csv(SOURCE/'run04c_outputs/multiplicity_v3.csv')
for label, v, c, short in specs:
    x, y = s[v].to_numpy(), s.strict_accuracy_pct.to_numpy()
    # Explicit t-distribution p-values reproduce run04c. Pearson coefficient
    # independently checked against scipy; avoid replacing Spearman CI by Fisher z.
    r = float(np.corrcoef(x,y)[0,1])
    rho = float(stats.spearmanr(x,y).statistic)
    np.testing.assert_allclose(r, stats.pearsonr(x,y).statistic,atol=1e-14)
    p = lambda r: float(2*stats.t.sf(abs(r)*np.sqrt((len(s)-2)/(1-r*r)),len(s)-2))
    cil, cih = np.tanh(np.arctanh(r)+np.array([-1,1])*zcrit/np.sqrt(len(s)-3))
    corr.append({'Category':label,'variable':v,'n':len(s),'Mean %':float(x.mean()),'SD %':float(x.std(ddof=1)),
        'r (Pearson)':r,'95% CI lo (Pearson)':float(cil),'95% CI hi (Pearson)':float(cih),
        'p (Pearson; unadjusted)':p(r),'rho (Spearman)':rho,'p (Spearman; unadjusted)':p(rho),
        'Outcome':'strict_accuracy_pct','Pearson CI method':'Fisher z; 95%',
        'p method':'two-sided t distribution, df=n-2; Spearman asymptotic',
        'Share denominator':'all AI interactions per student, including Other'})
    a = s.loc[s.tertile=='Low (T1)',v].to_numpy()
    b = s.loc[s.tertile=='High (T3)',v].to_numpy()
    n1,n2=len(a),len(b); va,vb=a.var(ddof=1),b.var(ddof=1)
    diff=float(a.mean()-b.mean()); se=np.sqrt(va/n1+vb/n2)
    df=(va/n1+vb/n2)**2/((va/n1)**2/(n1-1)+(vb/n2)**2/(n2-1))
    t=diff/se; pval=float(2*stats.t.sf(abs(t),df)); margin=stats.t.ppf(.975,df)*se
    sp=np.sqrt(((n1-1)*va+(n2-1)*vb)/(n1+n2-2))
    g=(1-3/(4*(n1+n2)-9))*diff/sp
    gse=np.sqrt((n1+n2)/(n1*n2)+g*g/(2*(n1+n2-2)))
    independent=stats.ttest_ind(a,b,equal_var=False)
    np.testing.assert_allclose([t,pval],[independent.statistic,independent.pvalue],rtol=1e-10)
    tests.append({'Category':label,'variable':v,'n_low':n1,'n_high':n2,'Low mean (%)':float(a.mean()),'Low SD (pp)':float(a.std(ddof=1)),
        'High mean (%)':float(b.mean()),'High SD (pp)':float(b.std(ddof=1)),
        'Diff (L-H; pp)':diff,'Diff 95% CI lo (pp)':float(diff-margin),'Diff 95% CI hi (pp)':float(diff+margin),
        'Welch t (L-H)':float(t),'Welch df':float(df),'p (two-sided; unadjusted)':pval,
        'Hedges g (L-H)':float(g),'g 95% CI lo':float(g-zcrit*gse),'g 95% CI hi':float(g+zcrit*gse),
        'Outcome for grouping':'strict_accuracy_pct','Low definition':'strict accuracy < 67.5%', 'High definition':'strict accuracy > 84%',
        'Difference direction':'Low minus High','g CI method':'pooled SD; J=1-3/(4*(n_low+n_high)-9); analytic normal CI'})
    if v in oldtests.index:
        ref=oldtests.loc[v]
        np.testing.assert_allclose([diff,g,pval,-(diff+margin),-(diff-margin)],[-ref.mean_diff,-ref.hedges_g,ref.p,ref.mean_diff_ci_low,ref.mean_diff_ci_high],rtol=1e-10,atol=1e-12)
    for method, val in [('pearson',r),('spearman',rho)]:
        ref=mult[(mult.source=='correlation')&(mult.variable==v)&(mult.method==method)]
        if len(ref):
            assert len(ref)==1
            np.testing.assert_allclose([val,p(val)],[ref.iloc[0]['stat'],ref.iloc[0].raw_p],rtol=1e-10,atol=1e-14)

for label, definition in [('Low (T1)','strict accuracy < 67.5%'),('Medium (T2)','67.5% <= strict accuracy <= 84%'),('High (T3)','strict accuracy > 84%')]:
    q=s[s.tertile==label]
    row={'tertile':label,'n':len(q),'strict_accuracy_mean_pct':float(q.strict_accuracy_pct.mean()),'strict_accuracy_sd_pp':float(q.strict_accuracy_pct.std(ddof=1))}
    for _,v,_,short in specs:
        row[short]=float(q[v].mean()); row[short+'_sd_pp']=float(q[v].std(ddof=1))
    row['other_unclassified_pct']=float(q.other_pct_neutral.mean())
    row['group_definition']=definition
    row['Share denominator']='all AI interactions per student, including Other'
    np.testing.assert_allclose(sum(row[short] for *_,short in specs)+row['other_unclassified_pct'],100,atol=1e-10)
    ref=oldgroups.loc[label.split()[0]]
    np.testing.assert_allclose([row['n'],row['strict_accuracy_mean_pct'],row['kg_pct'],row['other_process_pct'],row['task_pct']], [ref['n'],ref.accuracy,ref.kg_pct,ref.other_process_pct,ref.task_pct],atol=1e-12)
    groups.append(row)

payload={'three_category_correlations.csv':corr,'three_category_tertiles.csv':groups,'three_category_ttests.csv':tests}
(HERE/'statistics.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False))
(HERE/'verification.json').write_text(json.dumps({'input':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'n':len(s),'group_n':[5540,5467,5382],'checks':'unique users; strict-accuracy reconstruction; category count/share reconciliation; run02 means; run04b effects and CIs; run04c correlation statistics and p-values; scipy independent Welch test','raw_p_only':True},indent=2))
print('Verified 5 correlation rows, 3 group rows, and 5 Welch comparisons.')
print([(r['variable'],r['r (Pearson)']) for r in corr])

for name,rows in payload.items():pd.DataFrame(rows).to_csv(HERE/name,index=False)
