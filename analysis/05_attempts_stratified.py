# Portable revision pipeline. Run via python run.py reproduce.
"""Stage 5: attempts-stratified robustness analyses (Reviewer 7, comment 13).

Reviewer 7: "Further robustness analyses or a more suitable statistical model
is needed when problem accuracy is aggregated across students with wildly
disparate amounts of attempted problems."

Reads only run02_outputs (strict_student_model_data.csv,
strict_course_model_data.csv). Writes run05_outputs. Never modifies source
files or earlier-stage outputs.

Definitions fixed at 2026-09-21, before execution:

1. Attempts variable. n_attempts = strict_valid_records, the number of
   response records per student. The raw per-record `attempts` field is NOT
   summed (per-record correctness for retries is not recoverable; 21,987 of
   1,468,220 AI-user response rows have attempts > 1). This matches the
   Online Resource 5 / run02 convention that cell n_records counts records.

2. Strata (fixed cut points, not data-dependent quartiles):
   1-9, 10-19, 20-49, >=50 records. Per stratum: descriptive statistics and
   within-stratum correlations of the six headline usage variables with
   strict_accuracy_pct. Pearson CI: Fisher z. Spearman CI within strata:
   completed by stage08 paired-row bootstrap; these interval fields remain
   empty until that step. No Fisher-z interval on ranks is used.

3. Subsample analyses:
   a. attempts >= 20 subsample (author-chosen sensitivity threshold; the
      reviewer requested robustness to disparate attempt counts without
      naming a specific cut-off).
   b. Median split (median computed from data and reported; groups
      <= median vs > median).
   On each: Pearson (Fisher z CI) for all six headline variables; Spearman
   with paired row-level bootstrap percentile CI (B=10,000, seed=20260921)
   for the two reviewer-focus variables (kg_pct, effective_feedback_pct);
   Stage08 supplies Spearman bootstrap intervals for the rest. Plus OLS with HC3
   covariance in the run02 specification
   (strict_accuracy_pct ~ kg_pct10 + log_ai_frequency).

4. Weighted analyses (student level, weights = strict_valid_records):
   - Weighted Pearson correlation of each headline variable with
     strict_accuracy_pct; CI by paired row-level bootstrap (B=10,000,
     seed=20260921), resampling students and carrying weights.
   - WLS in the run02 student specification with HC3 covariance.

5. Cell-level check (student-course cells, N=1,983 with n_records>=5):
   composition OLS with student-clustered covariance (run02 specification)
   refitted on cells with n_records >= 10 and >= 20. This checks whether the
   course-cell composition results rest on low-record cells. The crossed
   user/course model remains primary and is not refitted here (MixedLM does
   not support frequency weights; the subsample OLS is the documented
   robustness check).

6. Multiplicity: the archived 60-test selection is exploratory and separate
   from the 48-test revision family. Stage08 itemises its 36 subsample
   correlations and 24 model terms; no additional tests enter this family.
"""
import argparse, json, platform, traceback, warnings
from pathlib import Path
import numpy as np
import pandas as pd

VERSION='2026-09-21-v1'
BOOT_B=10000
BOOT_SEED=20260921
Z=1.959963984540054
STRATA=[(1,9,'1-9'),(10,19,'10-19'),(20,49,'20-49'),(50,None,'>=50')]
HEADLINE=[('effective_feedback_pct','Historical EF share'),
          ('kg_pct','KG Navigation share'),
          ('kg_count','KG Navigation count'),
          ('other_process_pct','Other Process share'),
          ('task_pct_neutral','Task-feature share'),
          ('ai_frequency','AI interaction count')]
FOCUS={'kg_pct','effective_feedback_pct'}
OLS_FML='strict_accuracy_pct ~ kg_pct10 + log_ai_frequency'
CELL_FML='accuracy ~ kg_pct10 + other_process_pct10 + task_pct_neutral10 + selfreg_pct_neutral10 + log_ai_frequency'

def write_json(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str),encoding='utf-8')

def fisher_ci(r,n):
    if n<=3 or r is None or abs(r)>=1: return [None,None]
    z=np.arctanh(r); se=1/np.sqrt(n-3)
    return [float(np.tanh(z-Z*se)),float(np.tanh(z+Z*se))]

def pearson_row(df,x,y):
    z=df[[x,y]].dropna(); n=len(z)
    if n<4: return {'variable':x,'method':'pearson','n':n,'r':None,'ci_low':None,'ci_high':None,'p':None,'ci_method':None}
    r=float(z[x].corr(z[y])); ci=fisher_ci(r,n)
    from scipy import stats as sst
    p=float(sst.pearsonr(z[x],z[y]).pvalue)
    return {'variable':x,'method':'pearson','n':n,'r':r,'ci_low':ci[0],'ci_high':ci[1],'p':p,'ci_method':'Fisher z'}

def _rank(v):
    from scipy import stats as sst
    return sst.rankdata(v)

def spearman_row(df,x,y,boot=False,rng=None):
    z=df[[x,y]].dropna(); n=len(z)
    if n<4: return {'variable':x,'method':'spearman','n':n,'r':None,'ci_low':None,'ci_high':None,'p':None,'ci_method':None}
    from scipy import stats as sst
    rx,ry=_rank(z[x].to_numpy(float)),_rank(z[y].to_numpy(float))
    r=float(np.corrcoef(rx,ry)[0,1])
    p=float(sst.spearmanr(z[x],z[y]).pvalue)
    if boot:
        xv,yv=z[x].to_numpy(float),z[y].to_numpy(float)
        stats=np.empty(BOOT_B)
        for b in range(BOOT_B):
            idx=rng.integers(0,n,n)
            stats[b]=np.corrcoef(_rank(xv[idx]),_rank(yv[idx]))[0,1]
        lo,hi=np.percentile(stats,[2.5,97.5])
        return {'variable':x,'method':'spearman','n':n,'r':r,'ci_low':float(lo),'ci_high':float(hi),'p':p,
                'ci_method':f'paired row bootstrap, B={BOOT_B}, seed={BOOT_SEED}'}
    ci=[None,None]  # Populated by stage08 paired-row bootstrap.
    return {'variable':x,'method':'spearman','n':n,'r':r,'ci_low':ci[0],'ci_high':ci[1],'p':p,
            'ci_method':'Pending stage08 paired-row bootstrap'}

def wcorr(x,y,w):
    c=np.cov(x,y,aweights=w)
    return float(c[0,1]/np.sqrt(c[0,0]*c[1,1]))

def weighted_row(df,x,y,rng):
    z=df[[x,y,'n_attempts']].dropna(); n=len(z)
    if n<4: return {'variable':x,'method':'weighted_pearson','n':n,'r':None,'ci_low':None,'ci_high':None,'ci_method':None}
    xv,yv,wv=z[x].to_numpy(float),z[y].to_numpy(float),z['n_attempts'].to_numpy(float)
    r=wcorr(xv,yv,wv)
    stats=np.empty(BOOT_B)
    for b in range(BOOT_B):
        idx=rng.integers(0,n,n)
        stats[b]=wcorr(xv[idx],yv[idx],wv[idx])
    lo,hi=np.percentile(stats,[2.5,97.5])
    return {'variable':x,'method':'weighted_pearson','n':n,'r':r,'ci_low':float(lo),'ci_high':float(hi),
            'ci_method':f'paired row bootstrap with weights, B={BOOT_B}, seed={BOOT_SEED}','weight':'n_attempts (strict_valid_records)'}

def main(root, boot_b=None):
    global BOOT_B
    if boot_b: BOOT_B=int(boot_b)
    root=Path(root).expanduser().resolve()
    inp=root/'revision_round2/run02_outputs'; out=root/'revision_round2/run05_outputs'; out.mkdir(exist_ok=True)
    needed=['strict_student_model_data.csv','strict_course_model_data.csv','run02_summary.json']
    miss=[x for x in needed if not (inp/x).is_file()]
    if miss: raise FileNotFoundError('Run stage 2 first. Missing: '+', '.join(miss))
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    print('Script',VERSION,'Python',platform.python_version(),'statsmodels',sm.__version__,'BOOT_B',BOOT_B,flush=True)
    st=pd.read_csv(inp/'strict_student_model_data.csv')
    cell=pd.read_csv(inp/'strict_course_model_data.csv')
    required=['user_id','ai_frequency','strict_valid_records','strict_accuracy_pct','effective_feedback_pct',
              'kg_pct','kg_count','other_process_pct','task_pct_neutral','log_ai_frequency','kg_pct10']
    missing=sorted(set(required)-set(st.columns))
    if missing: raise ValueError('Student input missing columns: '+', '.join(missing))
    if st.user_id.duplicated().any(): raise ValueError('Duplicate student keys.')
    if not (st.strict_valid_records>0).all(): raise ValueError('Nonpositive attempts found.')
    st=st.rename(columns={'strict_valid_records':'n_attempts'})
    rng=np.random.default_rng(BOOT_SEED)
    summary={'version':VERSION,'status':'STARTED','n_student':len(st),
             'attempts_variable':'n_attempts = strict_valid_records (response records; raw per-record attempts field not summed)',
             'boot_B':BOOT_B,'boot_seed':BOOT_SEED,'results':{},'models':[],
             'notes':['The 60-test response-record family is exploratory and separate from the 48-test revision family. Raw p and BH q are reported side by side.',
                      'Weighted analyses weight students by strict_valid_records.',
                      'The crossed user/course mixed model is not refitted here (MixedLM has no frequency weights); cell-level subsample OLS with student-clustered covariance is the documented check.']}

    # ---- 1. attempts distribution ----
    a=st.n_attempts
    dist={'min':int(a.min()),'p25':float(a.quantile(.25)),'median':float(a.median()),'mean':float(a.mean()),
          'p75':float(a.quantile(.75)),'p90':float(a.quantile(.90)),'p99':float(a.quantile(.99)),'max':int(a.max()),
          'n_ge20':int((a>=20).sum()),'pct_ge20':float(100*(a>=20).mean())}
    summary['results']['attempts_distribution']=dist
    print('Attempts distribution:',dist,flush=True)

    # ---- 2. strata table ----
    strata_rows=[]; strata_corr=[]
    for lo,hi,label in STRATA:
        d=st[(st.n_attempts>=lo)&(st.n_attempts<=hi if hi is not None else True)]
        strata_rows.append({'stratum':label,'n_students':len(d),
            'accuracy_mean':float(d.strict_accuracy_pct.mean()),'accuracy_sd':float(d.strict_accuracy_pct.std()),
            'attempts_mean':float(d.n_attempts.mean()),'ai_frequency_mean':float(d.ai_frequency.mean()),
            'kg_pct_mean':float(d.kg_pct.mean()),'ef_pct_mean':float(d.effective_feedback_pct.mean())})
        for x,_label in HEADLINE:
            for m in ('pearson','spearman'):
                row=(pearson_row if m=='pearson' else spearman_row)(d,x,'strict_accuracy_pct')
                row['stratum']=label; strata_corr.append(row)
    pd.DataFrame(strata_rows).to_csv(out/'attempts_strata_descriptives.csv',index=False)
    pd.DataFrame(strata_corr).to_csv(out/'attempts_strata_correlations.csv',index=False)
    summary['results']['strata']={'cuts':[s[2] for s in STRATA],'n_per_stratum':{r['stratum']:r['n_students'] for r in strata_rows}}
    print('Strata table done:',{r['stratum']:r['n_students'] for r in strata_rows},flush=True)

    # ---- 3. subsample analyses ----
    med=float(st.n_attempts.median())
    subsamples={'attempts_ge20':st[st.n_attempts>=20],
                'attempts_le_median':st[st.n_attempts<=med],
                'attempts_gt_median':st[st.n_attempts>med]}
    sub_corr=[]
    for sname,d in subsamples.items():
        for x,_label in HEADLINE:
            row=pearson_row(d,x,'strict_accuracy_pct'); row['subsample']=sname; sub_corr.append(row)
            row=spearman_row(d,x,'strict_accuracy_pct',boot=(x in FOCUS),rng=rng); row['subsample']=sname; sub_corr.append(row)
        print('Subsample correlations done:',sname,'n=',len(d),flush=True)
    pd.DataFrame(sub_corr).to_csv(out/'attempts_subsample_correlations.csv',index=False)
    summary['results']['median_split']={'median_attempts':med,
        'n_le_median':int((st.n_attempts<=med).sum()),'n_gt_median':int((st.n_attempts>med).sum())}

    # ---- 4. weighted correlations ----
    wrows=[]
    for x,_label in HEADLINE:
        wrows.append(weighted_row(st,x,'strict_accuracy_pct',rng))
        print('Weighted correlation done:',x,flush=True)
    pd.DataFrame(wrows).to_csv(out/'attempts_weighted_correlations.csv',index=False)

    # ---- 5. models: subsample OLS, WLS, cell-level subsample OLS ----
    model_rows=[]
    def fit_record(name, fit):
        print('Fitting:',name,flush=True)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            try:
                r=fit()
                ci=r.conf_int()
                for term in r.params.index:
                    model_rows.append({'model':name,'term':term,'estimate':float(r.params[term]),
                        'se':float(r.bse[term]),'ci_low':float(ci.loc[term,0]),'ci_high':float(ci.loc[term,1]),
                        'p':float(r.pvalues[term]),'nobs':float(r.nobs)})
                info={'model':name,'nobs':float(r.nobs),'converged':bool(getattr(r,'converged',True)),'error':None}
            except Exception as e:
                info={'model':name,'error':repr(e),'traceback':traceback.format_exc()}
            info['warnings']=list(dict.fromkeys(str(w.message) for w in caught))
        summary['models'].append(info)
        pd.DataFrame(model_rows).to_csv(out/'attempts_models.csv',index=False)
        write_json(out/'run05_summary.json',summary)
        print('Finished:',name,'error=',info.get('error'),flush=True)

    for sname,d in subsamples.items():
        fit_record(f'student_ols_kg_share__{sname}',
                   (lambda dd: lambda: smf.ols(OLS_FML,data=dd).fit(cov_type='HC3'))(d))
    fit_record('student_wls_kg_share__weight_attempts',
               lambda: smf.wls(OLS_FML,data=st,weights=st.n_attempts.astype(float)).fit(cov_type='HC3'))
    dc=cell[cell.n_records>=5].copy()
    for thr in (10,20):
        dd=dc[dc.n_records>=thr]
        fit_record(f'cell_ols_composition__n_records_ge{thr}',
                   (lambda dd: lambda: smf.ols(CELL_FML,data=dd).fit(cov_type='cluster',cov_kwds={'groups':dd.user_id}))(dd))

    # ---- 6. stage-local multiplicity view ----
    pvals=[r['p'] for r in sub_corr+wrows if r.get('p') is not None]+[r['p'] for r in model_rows]
    pvals=np.array([p for p in pvals if p is not None and np.isfinite(p)])
    if len(pvals):
        order=np.argsort(pvals); q=np.empty_like(pvals); m=len(pvals)
        prev=1.0
        for i in range(m-1,-1,-1):
            prev=min(prev,pvals[order[i]]*m/(i+1)); q[order[i]]=prev
        summary['results']['multiplicity']={'stage_local_family_size':int(m),'min_raw_p':float(pvals.min()),
            'n_raw_p_lt_0.05':int((pvals<0.05).sum()),'n_bh_q_lt_0.05':int((q<0.05).sum()),
            'note':'60-test family retained separately from the 48-test family; stage08 itemises the same tests'}

    summary['status']='COMPLETE_REVIEW_REQUIRED' if not any(x.get('error') or x.get('warnings') for x in summary['models']) else 'REVIEW_REQUIRED'
    write_json(out/'run05_summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2,default=str))
    print('Outputs:',out)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]/'outputs'))
    ap.add_argument('--boot',default=None,help='override bootstrap B (testing only; default 10000)')
    args=ap.parse_args()
    main(args.root,args.boot)
