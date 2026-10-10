# Portable revision pipeline. Run via python run.py reproduce.
"""Stage 3 patch: supplementary diagnostics, correcting run03.

Reads run02_outputs/strict_course_model_data.csv and run03_outputs. Writes
patch files into run03_outputs. Never modifies or deletes earlier outputs.

Corrections relative to 03_diagnostics.py:
1. Dispersion-scaled standard errors are withdrawn. The run02 binomial GLM was
   fitted with student-clustered robust covariance; multiplying those standard
   errors by sqrt(Pearson dispersion) double-inflates uncertainty and is not a
   standard quasi-binomial procedure. dispersion_scaled_terms.csv and the
   scaled_terms field in run03_summary.json MUST NOT be used in the paper.
2. The "systemic extra-binomial variation" conclusion is narrowed. Courses
   with near-complete separation and courses with high Pearson contributions
   are different sets; contribution size also scales with course size. The
   source of the overdispersion is NOT yet determined.
3. The variance profile grids in run03 covered only a neighborhood of the MLE
   (about 144-190 and 148-194), not values near zero. They cannot exclude a
   boundary solution. This patch extends the profile toward small variances.

Supplementary checks (binomial model only; the two course-random-intercept
linear models are NOT re-run across optimizers):
- convergence status and all warnings of the full-sample binomial fit;
- characterization of high-Pearson-contribution courses by size, residuals,
  and separation status, kept distinct from the extreme-course set;
- pre-specified leave-one-course-out (LOCO) sensitivity: exclude each of the
  top-10 Pearson-share courses one at a time, compare the five AI-term
  estimates against the full-sample fit, which is always retained as the
  reference. No course is deleted from any reported primary result.
"""
import argparse, json, platform, traceback, warnings
from pathlib import Path
import numpy as np
import pandas as pd

VERSION='2026-09-18-v1-patch'

COMPOSITION_FML='accuracy ~ kg_pct10 + other_process_pct10 + task_pct_neutral10 + selfreg_pct_neutral10 + log_ai_frequency'
KG_FML='accuracy ~ kg_pct10 + log_ai_frequency'
BINOMIAL_FML=('n_correct + n_failure ~ kg_pct10 + other_process_pct10 + task_pct_neutral10 '
              '+ selfreg_pct_neutral10 + log_ai_frequency + C(course_id)')
AI_TERMS=['kg_pct10','other_process_pct10','task_pct_neutral10','selfreg_pct_neutral10','log_ai_frequency']
LOCO_K=10  # pre-specified: top-10 Pearson-share courses, one at a time

def write_json(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str),encoding='utf-8')

def fit_binomial(sm,smf,d):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        r=smf.glm(BINOMIAL_FML,data=d,family=sm.families.Binomial()).fit(
            maxiter=200,cov_type='cluster',cov_kwds={'groups':d.user_id})
    return r,list(dict.fromkeys(str(w.message) for w in caught))

def extended_profile(sm,d,formula,name,out):
    """Extend the run03 profile grid down toward small course variances."""
    try:
        r=sm.MixedLM.from_formula(formula,groups='course_id',re_formula='1',data=d).fit(
            reml=True,method='lbfgs',maxiter=1000,disp=False)
        var=float(np.asarray(r.cov_re)[0,0])
        dist_low=max(var-2.0,1.0)  # keep grid values positive
        grid=r.profile_re(0,vtype='re',num_low=15,dist_low=dist_low,num_high=5,dist_high=10.0)
        prof=pd.DataFrame({'course_variance':grid[:,0],'profile_llf':grid[:,1]})
        prof['delta_llf']=prof.profile_llf-prof.profile_llf.max()
        prof.to_csv(out/f'extended_variance_profile_{name}.csv',index=False)
        imax=int(prof.profile_llf.idxmax())
        return {'profile_ok':True,'variance_at_mle':var,
                'variance_grid_min':float(prof.course_variance.min()),
                'variance_grid_max':float(prof.course_variance.max()),
                'max_at_grid_edge':bool(prof.course_variance.iloc[imax]<=prof.course_variance.min()+1e-9),
                'llf_at_mle':float(prof.profile_llf.max()),
                'llf_at_smallest_grid_variance':float(prof.profile_llf.iloc[int(prof.course_variance.idxmin())])}
    except Exception as e:
        return {'profile_ok':False,'error':repr(e)}

def main(root):
    root=Path(root).expanduser().resolve()
    inp=root/'revision_round2/run02_outputs'; out=root/'revision_round2/run03_outputs'
    if not (inp/'strict_course_model_data.csv').is_file():
        raise FileNotFoundError('Run stage 2 first.')
    out.mkdir(exist_ok=True)
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    print('Script',VERSION,'Python',platform.python_version(),'statsmodels',sm.__version__,flush=True)

    d=pd.read_csv(inp/'strict_course_model_data.csv')
    d=d[d.n_records>=5].copy()
    summary={'version':VERSION,'status':'STARTED',
        'corrections':['dispersion_scaled_terms.csv and the scaled_terms field in run03_summary.json are WITHDRAWN: '
            'the binomial fit already used student-clustered robust covariance; multiplying by sqrt(dispersion) '
            'double-inflates uncertainty and is not a standard quasi-binomial procedure. Cluster-robust standard '
            'errors from the full-sample fit remain the inference basis.',
            'The run03 conclusion of "systemic extra-binomial variation" is narrowed: the source of overdispersion '
            'is not yet determined; high Pearson contribution does not by itself identify an abnormal course.',
            'run03 variance profiles covered only the MLE neighborhood and cannot exclude a boundary solution; '
            'this patch extends the grids toward small variances.'],
        'binomial_fit':{},'loco':{},'extended_profiles':{}}

    # ---------- Full-sample binomial fit: convergence, warnings, inference basis ----------
    print('Refitting full-sample binomial with warning capture',flush=True)
    glm,glm_warnings=fit_binomial(sm,smf,d)
    disp=float(glm.pearson_chi2/glm.df_resid)
    summary['binomial_fit']={'converged':bool(glm.converged),'llf':float(glm.llf),
        'pearson_dispersion':disp,'nobs':int(glm.nobs),'df_resid':float(glm.df_resid),
        'warnings':glm_warnings,
        'covariance':'cluster-robust by student (HC cluster); NO dispersion rescaling applied',
        'ai_terms':[{'term':t,'estimate':float(glm.params[t]),'se_cluster':float(glm.bse[t]),
            'ci_low':float(glm.params[t]-1.959963984540054*glm.bse[t]),
            'ci_high':float(glm.params[t]+1.959963984540054*glm.bse[t]),
            'p':float(glm.pvalues[t])} for t in AI_TERMS]}

    # ---------- High-contribution courses: size, residuals, separation kept distinct ----------
    d['pearson_sq']=np.asarray(glm.resid_pearson)**2
    by_course=d.groupby('course_id').agg(pearson_sq_sum=('pearson_sq','sum'),cells=('user_id','size'),
        n_records=('n_records','sum'),mean_success=('success_prop','mean')).reset_index()
    by_course['pearson_share']=by_course.pearson_sq_sum/by_course.pearson_sq_sum.sum()
    by_course['separated']=((by_course.mean_success>0.995)|(by_course.mean_success<0.005))
    by_course=by_course.sort_values('pearson_sq_sum',ascending=False).reset_index(drop=True)
    by_course.to_csv(out/'high_contribution_courses.csv',index=False)
    top=by_course.head(LOCO_K)
    summary['high_contribution']={'top10_share':float(top.pearson_share.sum()),
        'top10_ids':top.course_id.tolist(),
        'top10_n_records_range':[int(top.n_records.min()),int(top.n_records.max())],
        'top10_separated_count':int(top.separated.sum()),
        'note':'Pearson share scales with course size; membership in this list is not evidence of abnormality.'}
    print('Top-10 Pearson share:',round(float(top.pearson_share.sum()),4),flush=True)

    # ---------- Pre-specified LOCO sensitivity (full sample always reference) ----------
    print('LOCO sensitivity over top-10 Pearson-share courses',flush=True)
    ref={t:float(glm.params[t]) for t in AI_TERMS}
    ref_se={t:float(glm.bse[t]) for t in AI_TERMS}
    loco=[]
    for cid in top.course_id:
        d2=d[d.course_id!=cid]
        try:
            g2,w2=fit_binomial(sm,smf,d2)
            row={'excluded_course':cid,'converged':bool(g2.converged),
                 'pearson_dispersion':float(g2.pearson_chi2/g2.df_resid),'warnings':' | '.join(w2)}
            for t in AI_TERMS:
                est=float(g2.params[t])
                row[t+'_est']=est
                row[t+'_change_in_se_units']=(est-ref[t])/ref_se[t]
                row[t+'_sign_change']=bool(np.sign(est)!=np.sign(ref[t]))
        except Exception as e:
            row={'excluded_course':cid,'error':repr(e)}
        loco.append(row)
        print('  excluded',cid,'dispersion=',row.get('pearson_dispersion'),flush=True)
    loco_df=pd.DataFrame(loco)
    loco_df.to_csv(out/'loco_sensitivity.csv',index=False)
    max_shift={t:float(np.nanmax(np.abs(loco_df[t+'_change_in_se_units']))) for t in AI_TERMS if t+'_change_in_se_units' in loco_df}
    summary['loco']={'reference':'full-sample fit retained','n_exclusions':int(len(top)),
        'max_abs_change_in_se_units':max_shift,
        'any_sign_change':bool(loco_df[[c for c in loco_df.columns if c.endswith('_sign_change')]].any().any())
            if any(c.endswith('_sign_change') for c in loco_df.columns) else None,
        'dispersion_range':[float(loco_df.pearson_dispersion.min()),float(loco_df.pearson_dispersion.max())]
            if 'pearson_dispersion' in loco_df else None}

    # ---------- Extended variance profiles toward small variances ----------
    print('Extended variance profiles',flush=True)
    for fml,name in [(COMPOSITION_FML,'course_mixed_course_random'),(KG_FML,'course_mixed_kg_course_random')]:
        ep=extended_profile(sm,d,fml,name,out)
        summary['extended_profiles'][name]=ep
        print('  ',name,ep,flush=True)

    notes=[]
    if summary['binomial_fit']['converged'] and not glm_warnings:
        notes.append('Binomial full-sample fit converged with no warnings; cluster-robust SEs retained as inference basis.')
    else:
        notes.append(f"Binomial full-sample fit: converged={summary['binomial_fit']['converged']}, warnings={glm_warnings}; inspect before use.")
    if summary['loco']['any_sign_change'] is False:
        notes.append('LOCO: no AI-term sign changes across the 10 pre-specified exclusions; '
                     f"max shift in cluster-SE units: {max_shift}.")
    else:
        notes.append('LOCO: at least one exclusion changed an AI-term sign; inspect loco_sensitivity.csv before interpreting.')
    for name,ep in summary['extended_profiles'].items():
        if ep.get('profile_ok'):
            notes.append(f"{name}: extended profile grid [{ep['variance_grid_min']:.1f}, {ep['variance_grid_max']:.1f}], "
                         f"max at grid edge={ep['max_at_grid_edge']}, "
                         f"llf drop from MLE to smallest grid variance={ep['llf_at_mle']-ep['llf_at_smallest_grid_variance']:.3f}.")
        else:
            notes.append(f"{name}: extended profile failed: {ep.get('error')}; boundary question remains open.")
    notes.append('Overdispersion source remains undetermined; candidate count models are decided separately '
                 'from these diagnostics, not by dispersion size alone.')
    summary['decision_notes']=notes
    summary['status']='PATCH_COMPLETE_REVIEW_REQUIRED'
    write_json(out/'diagnostics_patch_summary.json',summary)
    print('\n'.join(notes),flush=True)
    print('Outputs:',out,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',required=True)
    args=ap.parse_args()
    main(args.root)
