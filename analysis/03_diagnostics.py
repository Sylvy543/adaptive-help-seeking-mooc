# Portable revision pipeline. Run via python run.py reproduce.
"""Stage 3: targeted diagnostics for the three flagged run02 models.

Reads only run02_outputs (strict_course_model_data.csv, model_coefficients.csv,
run02_summary.json). Writes run03_outputs. Never modifies source files, the
manuscript, or earlier-stage outputs.

Diagnose first; do not fit candidate replacement models here.

A. course_mixed_course_random / course_mixed_kg_course_random
   (singular covariance warnings, but reported course variances are positive):
   - refit with several optimizers and record convergence, warnings, and the
     stability of the course variance and fixed effects;
   - profile the likelihood over the course random-intercept sd to check
     whether the maximum is interior or at the boundary;
   - compare fixed effects with the crossed user/course model from run02.
B. course_binomial_fixed_course (Pearson dispersion ~10):
   - decompose Pearson chi-square by course and by cell size;
   - identify extreme courses (near-complete separation);
   - refit excluding extreme courses to test fit stability;
   - retain the original student-clustered covariance; no dispersion rescaling.
C. Print decision guidance mapped to the observed diagnostics. No candidate
   model (beta-binomial, quasi-binomial, observation-level random effects,
   crossed GLMM) is fitted in this stage.
"""
import argparse, json, math, platform, traceback, warnings
from pathlib import Path
import numpy as np
import pandas as pd

VERSION='2026-09-18-v1'

COMPOSITION_FML='accuracy ~ kg_pct10 + other_process_pct10 + task_pct_neutral10 + selfreg_pct_neutral10 + log_ai_frequency'
KG_FML='accuracy ~ kg_pct10 + log_ai_frequency'
BINOMIAL_FML=('n_correct + n_failure ~ kg_pct10 + other_process_pct10 + task_pct_neutral10 '
              '+ selfreg_pct_neutral10 + log_ai_frequency + C(course_id)')
AI_TERMS=['kg_pct10','other_process_pct10','task_pct_neutral10','selfreg_pct_neutral10','log_ai_frequency']
OPTIMIZERS=['lbfgs','bfgs','cg','nm','powell']

def write_json(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str),encoding='utf-8')

def fit_mixed_multi(sm,d,formula,name,out):
    """Refit one course-random-intercept model across optimizers."""
    rows=[]
    for method in OPTIMIZERS:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            rec={'model':name,'optimizer':method}
            try:
                r=sm.MixedLM.from_formula(formula,groups='course_id',re_formula='1',data=d).fit(
                    reml=True,method=method,maxiter=1000,disp=False)
                rec.update(converged=bool(r.converged),llf=float(r.llf),
                           course_var=float(np.asarray(r.cov_re)[0,0]),residual_var=float(r.scale),
                           kg_pct10=float(r.params.get('kg_pct10',np.nan)),
                           intercept=float(r.params.get('Intercept',np.nan)))
                if 'other_process_pct10' in r.params.index:
                    rec['other_process_pct10']=float(r.params['other_process_pct10'])
            except Exception as e:
                rec.update(error=repr(e))
            rec['warnings']=' | '.join(dict.fromkeys(str(w.message) for w in caught))
        rows.append(rec)
        print('  ',name,method,'converged=',rec.get('converged'),'course_var=',rec.get('course_var'),
              'warn=',bool(rec['warnings']),flush=True)
    df=pd.DataFrame(rows)
    ok=df[df.converged==True]
    stab={}
    for col in ['course_var','residual_var','kg_pct10']:
        if col in ok.columns and len(ok)>1:
            vals=ok[col].astype(float)
            stab[col]={'min':float(vals.min()),'max':float(vals.max()),
                       'spread':float(vals.max()-vals.min()),
                       'rel_spread':float((vals.max()-vals.min())/max(abs(vals.mean()),1e-12))}
    return df,stab

def profile_course_sd(sm,d,formula,name,out):
    """Profile likelihood over the course random-intercept sd."""
    try:
        r=sm.MixedLM.from_formula(formula,groups='course_id',re_formula='1',data=d).fit(
            reml=True,method='lbfgs',maxiter=1000,disp=False)
        sd=float(np.sqrt(np.asarray(r.cov_re)[0,0]))
        dist=max(2*sd,1.0)
        grid=r.profile_re(0,vtype='re',num_low=10,dist_low=dist,num_high=10,dist_high=dist)
        # profile_re returns column 0 = constrained variance value (variance
        # units, not sd, for a random-intercept model), column 1 = profile
        # likelihood. The grid covers a neighborhood of the MLE, not zero.
        prof=pd.DataFrame({'course_variance':grid[:,0],'profile_llf':grid[:,1]})
        prof['delta_llf']=prof.profile_llf-prof.profile_llf.max()
        prof.to_csv(out/f'variance_profile_{name}.csv',index=False)
        imax=int(prof.profile_llf.idxmax())
        at_boundary=bool(prof.course_variance.iloc[imax]<=prof.course_variance.min()+1e-9)
        return {'profile_ok':True,'variance_at_mle':sd**2,'max_at_grid_edge':at_boundary,
                'variance_grid_min':float(prof.course_variance.min()),
                'variance_grid_max':float(prof.course_variance.max()),
                'llf_at_mle':float(prof.profile_llf.max()),
                'llf_at_grid_edge':float(prof.profile_llf.iloc[int(prof.course_variance.idxmin())])}
    except Exception as e:
        return {'profile_ok':False,'error':repr(e)}

def main(root):
    root=Path(root).expanduser().resolve()
    inp=root/'revision_round2/run02_outputs'; out=root/'revision_round2/run03_outputs'; out.mkdir(exist_ok=True)
    needed=['strict_course_model_data.csv','model_coefficients.csv','run02_summary.json']
    miss=[x for x in needed if not (inp/x).is_file()]
    if miss: raise FileNotFoundError('Run stage 2 first. Missing: '+', '.join(miss))
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    from scipy import stats as sstats
    print('Script',VERSION,'Python',platform.python_version(),'statsmodels',sm.__version__,flush=True)

    d=pd.read_csv(inp/'strict_course_model_data.csv')
    d=d[d.n_records>=5].copy()
    d['all_group']=1
    base=pd.read_csv(inp/'model_coefficients.csv')
    run02=json.loads((inp/'run02_summary.json').read_text(encoding='utf-8'))
    print('Loaded',len(d),'student-course cells;',d.user_id.nunique(),'students,',d.course_id.nunique(),'courses',flush=True)
    summary={'version':VERSION,'status':'STARTED','n_cells':int(len(d)),'A_mixed_singular':{},'B_binomial':{},'decision_notes':[]}

    # ---------- Part A: singular-warning course random intercept models ----------
    print('PART A: course random intercept models with singular warnings',flush=True)
    stab_all={}
    frames=[]
    for fml,name in [(COMPOSITION_FML,'course_mixed_course_random'),(KG_FML,'course_mixed_kg_course_random')]:
        df,stab=fit_mixed_multi(sm,d,fml,name,out)
        frames.append(df); stab_all[name]=stab
        summary['A_mixed_singular'][name]={'optimizer_stability':stab,
            'profile':profile_course_sd(sm,d,fml,name,out)}
    pd.concat(frames,ignore_index=True).to_csv(out/'optimizer_stability.csv',index=False)
    # Compare fixed effects with the crossed model baseline from run02.
    crossed=base[base.model=='course_mixed_crossed_user_course'].set_index('term')
    comp=base[base.model=='course_mixed_course_random'].set_index('term')
    cmp_rows=[]
    for t in AI_TERMS:
        if t in crossed.index and t in comp.index:
            cmp_rows.append({'term':t,'course_random_est':float(comp.loc[t,'estimate']),
                'crossed_est':float(crossed.loc[t,'estimate']),
                'abs_diff':float(abs(comp.loc[t,'estimate']-crossed.loc[t,'estimate'])),
                'crossed_ci_width':float(crossed.loc[t,'ci_high']-crossed.loc[t,'ci_low'])})
    cmp_df=pd.DataFrame(cmp_rows)
    cmp_df.to_csv(out/'course_random_vs_crossed.csv',index=False)
    summary['A_mixed_singular']['fixed_effect_comparison']=cmp_rows

    # ---------- Part B: binomial fixed-course model overdispersion ----------
    print('PART B: binomial fixed-course model diagnostics',flush=True)
    with warnings.catch_warnings(record=True):
        warnings.simplefilter('always')
        glm=smf.glm(BINOMIAL_FML,data=d,family=sm.families.Binomial()).fit(
            maxiter=200,cov_type='cluster',cov_kwds={'groups':d.user_id})
    disp=float(glm.pearson_chi2/glm.df_resid)
    d['pearson_resid']=np.asarray(glm.resid_pearson)
    d['pearson_sq']=d.pearson_resid**2
    by_course=d.groupby('course_id').agg(pearson_sq_sum=('pearson_sq','sum'),cells=('user_id','size'),
        n_records=('n_records','sum'),mean_success=('success_prop','mean'),
        min_cell_success=('success_prop','min'),max_cell_success=('success_prop','max')).reset_index()
    by_course['pearson_share']=by_course.pearson_sq_sum/by_course.pearson_sq_sum.sum()
    by_course=by_course.sort_values('pearson_sq_sum',ascending=False)
    by_course.to_csv(out/'pearson_contributions_by_course.csv',index=False)
    top10_share=float(by_course.pearson_share.head(10).sum())
    # Extreme courses: near-complete separation at course level.
    extreme=by_course[(by_course.mean_success>0.995)|(by_course.mean_success<0.005)].copy()
    # Cross-check with run02 dummy coefficients (|estimate|>15).
    dummy=base[(base.model=='course_binomial_fixed_course')&base.term.str.startswith('C(course_id)')]
    big=dummy[dummy.estimate.abs()>15].copy()
    extreme_ids=sorted(set(extreme.course_id)|set(big.term.str.extract(r'\[T\.(.+)\]')[0]))
    ext_rows=[]
    for cid in extreme_ids:
        sub=d[d.course_id==cid]
        ext_rows.append({'course_id':cid,'cells':len(sub),'n_records':int(sub.n_records.sum()),
            'mean_success':float(sub.success_prop.mean()),
            'run02_dummy_est':float(dummy[dummy.term.str.contains(cid)].estimate.iloc[0]) if (dummy.term.str.contains(cid)).any() else None})
    pd.DataFrame(ext_rows).to_csv(out/'extreme_courses.csv',index=False)
    # Dispersion by cell size.
    bins=pd.cut(d.n_records,[4,9,19,49,99,np.inf],labels=['5-9','10-19','20-49','50-99','100+'])
    size_disp=d.groupby(bins,observed=False).agg(cells=('user_id','size'),mean_pearson_sq=('pearson_sq','mean')).reset_index(names='n_records_bin')
    size_disp.to_csv(out/'dispersion_by_cell_size.csv',index=False)
    # Refit without extreme courses: coefficient and dispersion stability.
    d2=d[~d.course_id.isin(extreme_ids)].copy()
    with warnings.catch_warnings(record=True):
        warnings.simplefilter('always')
        glm2=smf.glm(BINOMIAL_FML,data=d2,family=sm.families.Binomial()).fit(
            maxiter=200,cov_type='cluster',cov_kwds={'groups':d2.user_id})
    disp2=float(glm2.pearson_chi2/glm2.df_resid)
    refit=[]
    for t in AI_TERMS:
        refit.append({'term':t,'full_est':float(glm.params[t]),'full_p':float(glm.pvalues[t]),
            'excl_extreme_est':float(glm2.params[t]),'excl_extreme_p':float(glm2.pvalues[t]),
            'sign_change':bool(np.sign(glm.params[t])!=np.sign(glm2.params[t]))})
    refit_df=pd.DataFrame(refit)
    refit_df.to_csv(out/'binomial_refit_comparison.csv',index=False)
    summary['B_binomial']={'pearson_dispersion_full':disp,'top10_course_pearson_share':top10_share,
        'n_extreme_courses':len(extreme_ids),'extreme_course_ids':extreme_ids,
        'pearson_dispersion_excl_extreme':disp2,
        'dispersion_by_cell_size':size_disp.to_dict('records'),'refit_comparison':refit}

    notes=['Optimizer warnings are retained. Extended variance profiles and corrected binomial diagnostics are supplied by stage03b.',
           'Excluding extreme courses does not establish the source of overdispersion. No dispersion rescaling of cluster-robust covariance is performed.']
    summary['decision_notes']=notes
    summary['status']='DIAGNOSTICS_COMPLETE_REVIEW_REQUIRED'
    write_json(out/'run03_summary.json',summary)
    print('\n'.join(notes),flush=True)
    print(json.dumps(summary,ensure_ascii=False,indent=2,default=str),flush=True)
    print('Outputs:',out,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',required=True)
    args=ap.parse_args()
    main(args.root)
