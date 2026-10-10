# Portable revision pipeline. Run via python run.py reproduce.
"""Stage 4b: corrections to run04, scope limited to five items.

Reads run02_outputs and student-level data. Writes run04b_outputs. Never
modifies earlier outputs. No new model families are introduced.

Corrections (run04 items withdrawn and replaced):

1. keep_other WITHDRAWN. Adding other_count to the composite numerator assumed
   Other is effective feedback, which is exactly the mapping under dispute.
   Replaced by two separate, explicit-denominator measures:
   - other_share     = 100 * other_count / ai_frequency
                       (Other reported standalone; not mapped to any feedback level)
   - ef_mapped_only  = 100 * (process_count + self_reg_count) / (ai_frequency - other_count)
                       (composite share among level-mapped interactions only)
   The kg_moved_to_task composite is unchanged (denominator stays ai_frequency).

2. Spearman CIs: Fisher z approximation WITHDRAWN (unverified under heavy ties
   and binary variables). Replaced by paired row-level bootstrap over students,
   recomputing Spearman (average ranks) inside every resample. B=10,000,
   seed=20260918. Pearson CIs keep Fisher z.

3. Multiplicity: the run04 table claimed to include run02 student models but
   did not, and double-counted one Spearman test under monotone transforms
   (count vs log count). Replaced by an explicit unique-test list (44 tests;
   see UNIQUE TEST LIST in the summary). No test is designated primary or
   confirmatory: all are post-hoc revision analyses. KG share is flagged as
   the reviewer-focus indicator only. Raw p and Benjamini-Hochberg q reported
   side by side over the full family.

4. Effect sizes: raw-unit mean differences with Welch 95% CIs are the primary
   report. Hedges g (pooled SD weighted by group size, small-sample correction)
   with an analytic 95% CI is secondary. run04 cohens_d (simple-average
   denominator, no CI) WITHDRAWN.

5. Single-course model warning: the reduced-sample fit is a different sample
   and does not inherit the run03 diagnosis. Rechecked once with BFGS (stable
   across optimizers in run03); estimates and CIs compared against the L-BFGS
   fit. The full five-optimizer battery is not repeated.
"""
import argparse, json, platform, warnings
from pathlib import Path
import numpy as np
import pandas as pd

VERSION='2026-09-18-v1b'
BOOT_B=10000
BOOT_SEED=20260918
TERTILE_CUTS=(67.5,84.0)
TERTILE_VARS=['ai_frequency','kg_pct','kg_count','other_process_pct','task_pct_neutral']
COMPOSITION_FML='accuracy ~ kg_pct10 + other_process_pct10 + task_pct_neutral10 + selfreg_pct_neutral10 + log_ai_frequency'
AI_TERMS=['kg_pct10','other_process_pct10','task_pct_neutral10','selfreg_pct_neutral10','log_ai_frequency']

def write_json(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str),encoding='utf-8')

def fisher_ci(r,n):
    if n<=3 or abs(r)>=1: return [None,None]
    z=np.arctanh(r); se=1/np.sqrt(n-3)
    return [float(np.tanh(z-1.959963984540054*se)),float(np.tanh(z+1.959963984540054*se))]

def rank_avg(a):
    """Average (mid) ranks, tie-aware. Validated against scipy.stats.rankdata."""
    a=np.asarray(a,float); n=len(a)
    sorter=np.argsort(a,kind='stable')
    sa=a[sorter]
    change=np.empty(n,dtype=bool); change[0]=True
    change[1:]=sa[1:]!=sa[:-1]
    bounds=np.flatnonzero(np.r_[change,True])
    avg=(bounds[:-1]+bounds[1:]+1)/2.0
    ranks=np.empty(n); ranks[sorter]=np.repeat(avg,np.diff(bounds))
    return ranks

def spearman_boot(x,y,B,seed):
    """Paired row-level bootstrap CI for Spearman correlation."""
    x=np.asarray(x,float); y=np.asarray(y,float); n=len(x)
    rx=rank_avg(x); ry=rank_avg(y)
    r_obs=float(np.corrcoef(rx,ry)[0,1])
    rng=np.random.default_rng(seed)
    boots=np.empty(B)
    for b in range(B):
        idx=rng.integers(0,n,n)
        rb_x=rank_avg(x[idx]); rb_y=rank_avg(y[idx])
        sx=rb_x-rb_x.mean(); sy=rb_y-rb_y.mean()
        denom=np.sqrt((sx*sx).sum()*(sy*sy).sum())
        boots[b]=float((sx*sy).sum()/denom) if denom>0 else np.nan
    boots=boots[np.isfinite(boots)]
    lo,hi=np.percentile(boots,[2.5,97.5])
    return r_obs,float(lo),float(hi),int(len(boots))

def main(root):
    root=Path(root).expanduser().resolve()
    inp=root/'revision_round2/run02_outputs'; out=root/'revision_round2/run04b_outputs'; out.mkdir(exist_ok=True)
    needed=['strict_student_model_data.csv','strict_course_model_data.csv','model_coefficients.csv']
    miss=[x for x in needed if not (inp/x).is_file()]
    if miss: raise FileNotFoundError('Run stage 2 first. Missing: '+', '.join(miss))
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    from scipy import stats as sstats
    print('Script',VERSION,'Python',platform.python_version(),'statsmodels',sm.__version__,flush=True)

    # Validate the tie-aware ranker once against scipy before any bootstrap.
    probe=np.array([1.0,2.0,2.0,3.0,3.0,3.0,4.0,0.0,0.0,5.0])
    assert np.allclose(rank_avg(probe),sstats.rankdata(probe)), 'rank_avg disagrees with scipy.rankdata'
    print('rank_avg validated against scipy.stats.rankdata',flush=True)

    st=pd.read_csv(inp/'strict_student_model_data.csv')
    co=pd.read_csv(inp/'strict_course_model_data.csv')
    base=pd.read_csv(inp/'model_coefficients.csv')
    summary={'version':VERSION,'status':'STARTED','corrections':[
        'run04 keep_other (Other in the composite numerator) WITHDRAWN; replaced by other_share (standalone) and ef_mapped_only (mapped-interactions denominator).',
        'run04 Fisher-z Spearman CIs WITHDRAWN; replaced by paired row-level bootstrap (B=10000, seed=20260918).',
        'run04 multiplicity.csv WITHDRAWN; replaced by an explicit unique-test list (44 tests), no primary/confirmatory designation.',
        'run04 tertile cohens_d (simple-average denominator, no CI) WITHDRAWN; raw mean difference + Welch CI primary, Hedges g + analytic CI secondary.',
        'Single-course model rechecked once with BFGS instead of inheriting the run03 diagnosis.'],
        'results':{}}

    # Composite definitions (denominators explicit).
    five=st[['task_count','process_count','self_reg_count','self_count','other_count']].sum(axis=1)
    if not (five==st.ai_frequency).all(): raise ValueError('Five-category counts do not sum to ai_frequency.')
    st['historical_ef']=100*(st.process_count+st.self_reg_count)/st.ai_frequency
    st['kg_moved_to_task']=100*(st.process_count-st.kg_count+st.self_reg_count)/st.ai_frequency
    st['other_share']=100*st.other_count/st.ai_frequency
    mapped_denom=st.ai_frequency-st.other_count
    st['ef_mapped_only']=np.where(mapped_denom>0,
        100*(st.process_count+st.self_reg_count)/mapped_denom.replace(0,np.nan),np.nan)
    n_undefined=int((mapped_denom<=0).sum())
    st['log_kg_count']=np.log1p(st.kg_count.astype(float))
    st['kg_any']=(st.kg_count>=1).astype(int)
    if not np.isfinite(st['other_share']).all():
        raise ValueError('Nonfinite other_share.')
    # ef_mapped_only is undefined for students whose recorded interactions are
    # all Other; they are excluded pairwise and n is reported explicitly.

    # ---- Fix 1: Other mapping, corrected ----
    rows=[]
    for v in ['other_share','ef_mapped_only']:
        z=st[[v,'strict_accuracy_pct']].dropna(); n=len(z)
        rp=float(z[v].corr(z.strict_accuracy_pct)); cp=fisher_ci(rp,n)
        rows.append({'variable':v,'method':'pearson','n':n,'r':rp,'ci_low':cp[0],'ci_high':cp[1]})
        rs=float(z[v].rank().corr(z.strict_accuracy_pct.rank()))
        rows.append({'variable':v,'method':'spearman','n':n,'r':rs,'ci_low':None,'ci_high':None,
            'note':'CI from paired bootstrap; see spearman_bootstrap_cis.csv'})
    pd.DataFrame(rows).to_csv(out/'other_mapping_sensitivity.csv',index=False)
    summary['results']['other_mapping']={'rows':rows,
        'ef_mapped_only_undefined_n':n_undefined,
        'note':'ef_mapped_only undefined (all-Other interactions) for these students; excluded pairwise, n reported per row.'}
    print('Other mapping (corrected) done',flush=True)

    # ---- Fix 2: paired bootstrap Spearman CIs for the unique correlation set ----
    # Spearman is invariant to strictly monotone transforms: log-count Spearman
    # is the SAME test as count Spearman and is listed once (as the count).
    corr_specs=[('ai_frequency','AI interaction count',True),('log_ai_frequency','log AI interaction count',False),
        ('historical_ef','Historical EF share',True),('kg_pct','KG Navigation share',True),
        ('kg_count','KG Navigation count',True),('log_kg_count','log KG count',False),
        ('kg_any','KG any use',True),('kg_moved_to_task','KG moved to Task composite',True),
        ('other_share','Other share (standalone)',True),('ef_mapped_only','EF share, mapped denominator',True),
        ('other_process_pct','Other Process share',True),('other_process_count','Other Process count',True),
        ('task_pct_neutral','Task-feature share',True)]
    boot_rows=[]
    for i,(v,label,do_spearman) in enumerate(corr_specs):
        z=st[[v,'strict_accuracy_pct']].dropna(); n=len(z)
        rp=float(z[v].corr(z.strict_accuracy_pct)); cp=fisher_ci(rp,n)
        row={'variable':v,'label':label,'n':n,'pearson_r':rp,'pearson_ci_low':cp[0],'pearson_ci_high':cp[1],
             'pearson_ci_method':'Fisher z'}
        if do_spearman:
            r_s,lo,hi,b_eff=spearman_boot(z[v].to_numpy(),z.strict_accuracy_pct.to_numpy(),BOOT_B,BOOT_SEED+i)
            row.update(spearman_r=r_s,spearman_ci_low=lo,spearman_ci_high=hi,
                spearman_ci_method=f'paired row bootstrap, B={b_eff}, seed={BOOT_SEED+i}')
        else:
            base_v='ai_frequency' if v=='log_ai_frequency' else 'kg_count'
            row.update(spearman_r=None,spearman_ci_low=None,spearman_ci_high=None,
                spearman_ci_method=f'same test as {base_v} Spearman (monotone invariance); not duplicated')
        boot_rows.append(row)
        print(f'  bootstrap {i+1}/{len(corr_specs)}: {v}',flush=True)
    pd.DataFrame(boot_rows).to_csv(out/'spearman_bootstrap_cis.csv',index=False)
    summary['results']['correlation_cis']=boot_rows

    # ---- Fix 3: explicit unique-test list and BH over the full family ----
    tests=[]
    def add(source,variable,method,stat,p,group):
        tests.append({'source':source,'variable':variable,'method':method,'stat':float(stat),'raw_p':float(p),'group':group})
    for row in boot_rows:
        n=row['n']
        zp=np.arctanh(min(abs(row['pearson_r']),0.9999999))*np.sqrt(n-3)
        add('correlation',row['variable'],'pearson',row['pearson_r'],2*sstats.norm.sf(abs(zp)),'student_correlation')
        if row['spearman_r'] is not None:
            zs=np.arctanh(min(abs(row['spearman_r']),0.9999999))*np.sqrt(n-3)
            add('correlation',row['variable'],'spearman',row['spearman_r'],2*sstats.norm.sf(abs(zs)),'student_correlation')
    # Student OLS focal terms only; the control term log_ai_frequency is listed once.
    focal=[('student_ols_log_frequency','log_ai_frequency'),('student_ols_kg_share','kg_pct10'),
           ('student_ols_kg_count','kg_count')]
    for mdl,term in focal:
        r=base[(base.model==mdl)&(base.term==term)].iloc[0]
        add(mdl,term,'ols_hc3',r.estimate,r.p,'student_ols')
    for v in ['log_kg_count','kg_any']:
        r=smf.ols(f'strict_accuracy_pct ~ {v} + log_ai_frequency',data=st).fit(cov_type='HC3')
        add(f'student_ols_{v}',v,'ols_hc3',float(r.params[v]),float(r.pvalues[v]),'student_ols')
    # Course-level: only the two finally reported models contribute AI terms.
    for mdl in ['course_mixed_crossed_user_course','course_binomial_fixed_course']:
        for t in AI_TERMS:
            r=base[(base.model==mdl)&(base.term==t)].iloc[0]
            add(mdl,t,'mixed' if 'mixed' in mdl else 'glm_binomial',r.estimate,r.p,'course_model')
    # Tertile comparisons (Welch), computed below; placeholder filled after.
    # ---- Fix 4: effect sizes with proper definitions ----
    st['strict_tertile']=pd.Categorical(np.select(
        [st.strict_accuracy_pct<TERTILE_CUTS[0],st.strict_accuracy_pct<=TERTILE_CUTS[1]],
        ['Low','Medium'],default='High'),categories=['Low','Medium','High'],ordered=True)
    lo=st[st.strict_tertile=='Low']; hi=st[st.strict_tertile=='High']
    tert=[]
    for v in TERTILE_VARS:
        a,b=lo[v].astype(float),hi[v].astype(float)
        n1,n2=len(a),len(b); v1,v2=a.var(ddof=1),b.var(ddof=1)
        diff=float(b.mean()-a.mean())
        se=float(np.sqrt(v1/n1+v2/n2))
        dfree=float((v1/n1+v2/n2)**2/((v1/n1)**2/(n1-1)+(v2/n2)**2/(n2-1)))
        tcrit=float(sstats.t.ppf(0.975,dfree)); tstat=diff/se
        sp=float(np.sqrt(((n1-1)*v1+(n2-1)*v2)/(n1+n2-2)))  # pooled SD
        d=diff/sp; J=1-3/(4*(n1+n2)-9); g=J*d
        se_g=float(np.sqrt((n1+n2)/(n1*n2)+g**2/(2*(n1+n2-2))))
        tert.append({'variable':v,'n_low':n1,'n_high':n2,'mean_low':float(a.mean()),'mean_high':float(b.mean()),
            'mean_diff':diff,'mean_diff_ci_low':diff-tcrit*se,'mean_diff_ci_high':diff+tcrit*se,
            'welch_df':dfree,'p':float(2*sstats.t.sf(abs(tstat),dfree)),
            'hedges_g':float(g),'g_ci_low':float(g-1.959963984540054*se_g),'g_ci_high':float(g+1.959963984540054*se_g),
            'effect_note':'primary: raw mean difference + Welch CI; secondary: Hedges g (pooled SD) + analytic CI'})
        add('tertile_high_vs_low',v,'welch',diff,float(2*sstats.t.sf(abs(tstat),dfree)),'tertile')
    pd.DataFrame(tert).to_csv(out/'tertile_comparisons_v2.csv',index=False)
    summary['results']['tertile_comparisons']=tert
    print('Tertile effect sizes done',flush=True)

    tdf=pd.DataFrame(tests)
    if tdf.duplicated(['variable','method','source']).any(): raise ValueError('Duplicate tests in family list.')
    pvals=tdf.raw_p.to_numpy(); order=np.argsort(pvals); ranked=pvals[order]; m=len(pvals)
    q=np.empty(m); prev=1.0
    for i in range(m-1,-1,-1):
        prev=min(prev,ranked[i]*m/(i+1)); q[i]=prev
    bh=np.empty(m); bh[order]=q
    tdf['bh_q']=bh
    tdf['reviewer_focus']=tdf.variable.eq('kg_pct')
    tdf.to_csv(out/'multiplicity_v2.csv',index=False)
    summary['results']['multiplicity']={'family_size':int(m),
        'designation':'all post-hoc revision analyses; NO primary or confirmatory test; KG share flagged as reviewer focus only',
        'groups':tdf.groupby('group').size().to_dict()}
    print('Unique-test family size =',m,flush=True)

    # ---- Fix 5: single-course model rechecked once with BFGS ----
    d=co[co.n_records>=5].copy()
    d=d.sort_values(['user_id','n_records','course_id'],ascending=[True,False,True])
    one=d.drop_duplicates('user_id',keep='first').copy()
    recheck=[]
    for method in ['lbfgs','bfgs']:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            r=sm.MixedLM.from_formula(COMPOSITION_FML,groups='course_id',re_formula='1',data=one).fit(
                reml=True,method=method,maxiter=2000,disp=False)
        ci=r.conf_int()
        rec={'optimizer':method,'converged':bool(r.converged),'course_var':float(np.asarray(r.cov_re)[0,0]),
             'residual_var':float(r.scale),'warnings':[str(w.message) for w in caught]}
        for t in AI_TERMS:
            rec[t+'_est']=float(r.params[t]); rec[t+'_ci_low']=float(ci.loc[t,0]); rec[t+'_ci_high']=float(ci.loc[t,1])
        recheck.append(rec)
        print('  single-course recheck',method,'converged=',rec['converged'],'warn=',len(rec['warnings']),flush=True)
    rc=pd.DataFrame(recheck); rc.to_csv(out/'single_course_recheck.csv',index=False)
    diff={}
    for t in AI_TERMS:
        diff[t]={'est_abs_diff':float(abs(recheck[0][t+'_est']-recheck[1][t+'_est'])),
                 'ci_low_abs_diff':float(abs(recheck[0][t+'_ci_low']-recheck[1][t+'_ci_low'])),
                 'ci_high_abs_diff':float(abs(recheck[0][t+'_ci_high']-recheck[1][t+'_ci_high']))}
    summary['results']['single_course_recheck']={'runs':recheck,'lbfgs_vs_bfgs':diff,
        'note':'one additional optimizer (BFGS, stable in run03), not the full battery'}

    summary['status']='STAGE4B_COMPLETE_REVIEW_REQUIRED'
    write_json(out/'run04b_summary.json',summary)
    print('Outputs:',out,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',required=True)
    args=ap.parse_args()
    main(args.root)
