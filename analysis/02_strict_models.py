# Portable revision pipeline. Run via python run.py reproduce.
"""Stage 2: strict outcome and robustness models.

Run from the supplied notebook after 01_rebuild_audit.py has completed.
This script reads only run01_outputs and writes a separate run02_outputs
directory. It never modifies source files or the manuscript.

The main outcome uses is_correct from the raw response log. The historical
score==1 OR rule is retained only as a comparison column. Student-course
n_attempts is the number of response records, matching Online Resource 5;
the raw per-record `attempts` field is not summed into this denominator.
"""
import argparse, json, math, platform, sys, traceback, warnings
from pathlib import Path
import numpy as np
import pandas as pd

VERSION='2026-09-18-v2'

FEATURE_GROUPS={
    'kg_count':['知识图谱点击'],
    'other_process_count':['来自mooccube','来自Aminer'],
    'task_count_neutral':['预设问答','来自课程信息','加减乘除','来自baidu','来自baike'],
    'selfreg_count_neutral':['助教回答','问助教','飘窗回答','来自Faq'],
    'self_count_neutral':['作诗','来自图灵机器人'],
    'other_count_neutral':['cannot_answer','脏问题'],
}

def write_json(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str),encoding='utf-8')

def fisher_ci(r,n):
    if n<=3 or abs(r)>=1: return [None,None]
    z=np.arctanh(r); se=1/np.sqrt(n-3)
    return [float(np.tanh(z-1.959963984540054*se)),float(np.tanh(z+1.959963984540054*se))]

def corr_row(df,x,y,label,method='pearson'):
    z=df[[x,y]].dropna(); n=len(z)
    if n<4: return {'variable':label,'n':n,'r':None,'ci_low':None,'ci_high':None}
    if method=='spearman':
        r=float(z[x].rank().corr(z[y].rank()))
        ci=[None,None]
    else:
        r=float(z[x].corr(z[y])); ci=fisher_ci(r,n)
    return {'variable':label,'method':method,'n':n,'r':r,'ci_low':ci[0],'ci_high':ci[1]}

def save_model(result,model_name,rows):
    try:
        params=result.params; ci=result.conf_int(); bse=result.bse; pvals=result.pvalues
        out=[]
        for k in params.index:
            out.append({'model':model_name,'term':k,'estimate':float(params[k]),'se':float(bse[k]),
                        'ci_low':float(ci.loc[k,0]),'ci_high':float(ci.loc[k,1]),'p':float(pvals[k])})
        rows.extend(out)
        converged=getattr(result,'converged',None)
        return {'model':model_name,'nobs':float(result.nobs),'converged':bool(converged) if converged is not None else None,
                'aic':float(getattr(result,'aic',np.nan)),'bic':float(getattr(result,'bic',np.nan)),
                'error':None}
    except Exception as e:
        return {'model':model_name,'error':repr(e)}

def main(root, check_only=False):
    root=Path(root).expanduser().resolve()
    inp=root/'revision_round2/run01_outputs'; out=root/'revision_round2/run02_outputs'; out.mkdir(exist_ok=True)
    needed=['rebuilt_student_audit.csv','feature_counts_long.csv','unique_course_binary_audit.csv','run_summary.json']
    miss=[x for x in needed if not (inp/x).is_file()]
    if miss: raise FileNotFoundError('Run stage 1 first. Missing: '+', '.join(miss))
    audit=json.loads((inp/'run_summary.json').read_text(encoding='utf-8'))
    if not audit.get('full_scan_complete'):
        raise RuntimeError('Stage 1 full scan has not completed.')
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
    except Exception as e:
        print('STATSmodels_IMPORT_ERROR:',repr(e)); print('Install statsmodels in the Jupyter environment, then rerun.'); raise
    try:
        from scipy import stats
        scipy_ok=True
    except Exception:
        scipy_ok=False
    print('Script',VERSION,'Python',platform.python_version(),'statsmodels',sm.__version__,'scipy',scipy_ok,flush=True)
    strict=pd.read_csv(inp/'rebuilt_student_audit.csv')
    fc=pd.read_csv(inp/'feature_counts_long.csv')
    course=pd.read_csv(inp/'unique_course_binary_audit.csv')
    if course.empty: raise RuntimeError('unique_course_binary_audit.csv is empty')
    required=['user_id','ai_frequency','process_count','self_reg_count','total_problems',
              'correct_problems','problem_accuracy','strict_valid_records',
              'strict_correct_records','strict_accuracy_pct']
    missing_columns=sorted(set(required)-set(strict.columns))
    if missing_columns:
        raise ValueError('Student input is missing columns: '+', '.join(missing_columns))
    if strict.user_id.duplicated().any() or course.duplicated(['user_id','course_id']).any():
        raise ValueError('Duplicate student or student-course keys found.')
    if not ((strict.ai_frequency>0)&(strict.strict_valid_records>0)).all():
        raise ValueError('Nonpositive denominators found.')
    if not ((strict.strict_correct_records>=0)&(strict.strict_correct_records<=strict.strict_valid_records)).all():
        raise ValueError('Invalid student success counts.')
    if not ((course.n_records>0)&(course.n_correct>=0)&(course.n_correct<=course.n_records)).all():
        raise ValueError('Invalid course success/record counts.')
    # Historical EF must use the original classification, including the four
    # Baike-variant records historically assigned to Process. Do not substitute
    # the neutral feature grouping here.
    strict['effective_feedback_pct']=100*(strict.process_count+strict.self_reg_count)/strict.ai_frequency
    if not strict.effective_feedback_pct.between(0,100).all():
        raise ValueError('Historical EF share outside [0,100].')
    # Pivot neutral feature counts. These labels preserve recorded functions;
    # they are not claimed to be feedback levels.
    piv=fc.pivot_table(index='user_id',columns='base_feature',values='n_interactions',aggfunc='sum',fill_value=0)
    unknown=set(piv.columns)-set(sum(FEATURE_GROUPS.values(),[]))
    if unknown:
        raise ValueError('Unmapped base features: '+', '.join(sorted(unknown)))
    for col in set(sum(FEATURE_GROUPS.values(),[])):
        if col not in piv.columns: piv[col]=0
    feat=pd.DataFrame(index=piv.index)
    for name,cols in FEATURE_GROUPS.items(): feat[name]=piv[cols].sum(axis=1)
    feat['ai_frequency_neutral']=feat.sum(axis=1)
    feat['kg_pct']=100*feat.kg_count/feat.ai_frequency_neutral
    feat['other_process_pct']=100*feat.other_process_count/feat.ai_frequency_neutral
    feat['task_pct_neutral']=100*feat.task_count_neutral/feat.ai_frequency_neutral
    feat['selfreg_pct_neutral']=100*feat.selfreg_count_neutral/feat.ai_frequency_neutral
    feat['self_pct_neutral']=100*feat.self_count_neutral/feat.ai_frequency_neutral
    feat['other_pct_neutral']=100*feat.other_count_neutral/feat.ai_frequency_neutral
    feat=feat.reset_index()
    student=strict.merge(feat,on='user_id',how='left',validate='one_to_one')
    if student.ai_frequency_neutral.isna().any() or not (student.ai_frequency==student.ai_frequency_neutral).all():
        raise ValueError('Neutral feature counts do not sum to the historical interaction total.')
    # Derive both outcomes from counts to avoid floating-point artifacts when
    # counting students whose accuracy actually changed.
    student['strict_accuracy_pct']=100*student.strict_correct_records/student.strict_valid_records
    student['historical_accuracy_pct']=100*student.correct_problems/student.total_problems
    student['accuracy_change']=student.strict_accuracy_pct-student.historical_accuracy_pct
    student['log_ai_frequency']=np.log1p(student.ai_frequency.astype(float))
    student['kg_pct10']=student.kg_pct/10
    if not np.isfinite(student[['strict_accuracy_pct','effective_feedback_pct','kg_pct','log_ai_frequency']].to_numpy()).all():
        raise ValueError('Nonfinite analysis variables found.')
    student.to_csv(out/'strict_student_model_data.csv',index=False)
    course=course.merge(student[['user_id','strict_accuracy_pct','historical_accuracy_pct','ai_frequency','log_ai_frequency',
                                 'kg_pct','other_process_pct','task_pct_neutral','selfreg_pct_neutral','self_pct_neutral',
                                 'other_pct_neutral','kg_count','other_process_count']],on='user_id',how='inner',validate='many_to_one')
    course['accuracy']=course.n_correct/course.n_records*100
    course['success_prop']=course.n_correct/course.n_records
    course['n_failure']=course.n_records-course.n_correct
    course['log_ai_frequency']=course.log_ai_frequency.astype(float)
    for c in ['kg_pct','other_process_pct','task_pct_neutral','selfreg_pct_neutral']:
        course[c+'10']=course[c]/10
    course.to_csv(out/'strict_course_model_data.csv',index=False)
    print('DATA CHECKS PASSED:',len(student),'students,',len(course),'course cells; historical EF reconstructed.',flush=True)
    write_json(out/'data_checks.json',{'version':VERSION,'status':'PASSED','n_student':len(student),
        'n_course_cells':len(course),'course_input':'unique_course_binary_audit.csv',
        'historical_ef_formula':'100 * (historical process_count + historical self_reg_count) / ai_frequency'})
    if check_only:
        print('Data checks only; no models fitted.',flush=True)
        return
    summary={'version':VERSION,'status':'STARTED','n_student':len(student),'n_course_cells':len(course),
             'n_course_ge5':int((course.n_records>=5).sum()),'strict_missing':int(student.strict_accuracy_pct.isna().sum()),
             'strict_vs_historical':{'records':int(strict.strict_valid_records.sum()),'correct_strict':int(strict.strict_correct_records.sum()),
                'correct_historical':int(strict.correct_problems.sum()),'users_changed':int((student.strict_correct_records*student.total_problems != student.correct_problems*student.strict_valid_records).sum()),
                'mean_pp_change':float(student.accuracy_change.mean()),'median_pp_change':float(student.accuracy_change.median())},
             'models':[],'notes':['Percentages are per-student or per-student-course shares of recorded AI interaction rows.',
                'Strict outcome uses raw is_correct; historical outcome retains the old score==1 OR rule.',
                'Neutral feature names do not assert Hattie–Timperley feedback levels.']}
    corr=[]
    for x,label in [('ai_frequency','AI interaction count'),('log_ai_frequency','log AI interaction count'),
                    ('effective_feedback_pct','Historical effective-feedback share'),('kg_pct','KG Navigation share'),
                    ('kg_count','KG Navigation count'),('other_process_pct','Other Process share'),
                    ('other_process_count','Other Process count'),('task_pct_neutral','Task-feature share')]:
        corr.append(corr_row(student,x,'strict_accuracy_pct',label,'pearson'))
        corr.append(corr_row(student,x,'strict_accuracy_pct',label,'spearman'))
    pd.DataFrame(corr).to_csv(out/'strict_student_correlations.csv',index=False)
    # Accuracy denominator comparison by observed total AI interaction thresholds.
    thresh=[]
    for threshold in [1,2,5,10,20]:
        d=student[student.ai_frequency>=threshold]
        row={'minimum_ai_interactions':threshold,'n_students':len(d)}
        row.update(corr_row(d,'kg_pct','strict_accuracy_pct','KG share','pearson'))
        row['kg_count_r']=corr_row(d,'kg_count','strict_accuracy_pct','KG count','pearson')['r']
        row['historical_ef_r']=corr_row(d,'effective_feedback_pct','strict_accuracy_pct','Historical EF','pearson')['r']
        thresh.append(row)
    pd.DataFrame(thresh).to_csv(out/'strict_threshold_sensitivity.csv',index=False)
    model_rows=[]
    def fit_record(name, fit):
        print('Fitting:',name,flush=True)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            try:
                result=fit()
                info=save_model(result,name,model_rows)
                if hasattr(result,'vcomp'):
                    info['variance_components']=dict(zip(result.model.exog_vc.names,map(float,result.vcomp)))
                if hasattr(result,'cov_re'):
                    info['random_intercept_covariance']=np.asarray(result.cov_re).tolist()
                    info['residual_variance']=float(result.scale)
                if hasattr(result,'pearson_chi2'):
                    info['pearson_dispersion']=float(result.pearson_chi2/result.df_resid) if result.df_resid>0 else None
            except Exception as e:
                info={'model':name,'error':repr(e),'traceback':traceback.format_exc()}
            info['warnings']=list(dict.fromkeys(str(w.message) for w in caught))
        summary['models'].append(info)
        summary['status']='RUNNING'
        pd.DataFrame(model_rows).to_csv(out/'model_coefficients.csv',index=False)
        write_json(out/'run02_summary.json',summary)
        print('Finished:',name,'error=',info.get('error'),'converged=',info.get('converged'),flush=True)
    # Student-level OLS with HC3: descriptive association only.
    for formula,name in [('strict_accuracy_pct ~ log_ai_frequency','student_ols_log_frequency'),
                         ('strict_accuracy_pct ~ kg_pct10 + log_ai_frequency','student_ols_kg_share'),
                         ('strict_accuracy_pct ~ kg_count + log_ai_frequency','student_ols_kg_count')]:
        fit_record(name,lambda: smf.ols(formula,data=student).fit(cov_type='HC3'))
    d=course[course.n_records>=5].copy()
    # Course-cell OLS and strict binomial GLM with course fixed effects.
    for formula,name in [('accuracy ~ kg_pct10 + other_process_pct10 + task_pct_neutral10 + selfreg_pct_neutral10 + log_ai_frequency','course_ols_composition'),
                         ('accuracy ~ kg_pct10 + log_ai_frequency','course_ols_kg')]:
        fit_record(name,lambda: smf.ols(formula,data=d).fit(cov_type='cluster',cov_kwds={'groups':d.user_id}))
    # Explicit success/failure columns encode the binomial denominator without
    # frequency weights. Course effects are fixed here; this is not a GLMM.
    fit_record('course_binomial_fixed_course',lambda: smf.glm(
        'n_correct + n_failure ~ kg_pct10 + other_process_pct10 + task_pct_neutral10 + selfreg_pct_neutral10 + log_ai_frequency + C(course_id)',
        data=d,family=sm.families.Binomial()).fit(maxiter=200,cov_type='cluster',cov_kwds={'groups':d.user_id}))
    # Mixed models: course-only first, then crossed user/course variance components.
    d['all_group']=1
    for fml,name in [('accuracy ~ kg_pct10 + other_process_pct10 + task_pct_neutral10 + selfreg_pct_neutral10 + log_ai_frequency','course_mixed_course_random'),
                     ('accuracy ~ kg_pct10 + log_ai_frequency','course_mixed_kg_course_random')]:
        fit_record(name,lambda: sm.MixedLM.from_formula(fml,groups='course_id',re_formula='1',data=d).fit(reml=True,method='lbfgs',maxiter=1000,disp=False))
    # Crossed linear model, using sparse matrices for the variance components.
    fit_record('course_mixed_crossed_user_course',lambda: sm.MixedLM.from_formula(
        'accuracy ~ kg_pct10 + other_process_pct10 + task_pct_neutral10 + selfreg_pct_neutral10 + log_ai_frequency',
        groups='all_group',re_formula='0',vc_formula={'user':'0+C(user_id)','course':'0+C(course_id)'},
        data=d,use_sparse=True).fit(reml=True,method='lbfgs',maxiter=2000,disp=False))
    pd.DataFrame(model_rows).to_csv(out/'model_coefficients.csv',index=False)
    # Tertile descriptions use strict accuracy; no causal/Simpson claim is made.
    student['strict_tertile']=pd.Categorical(np.select(
        [student.strict_accuracy_pct<67.5,student.strict_accuracy_pct<=84],['Low','Medium'],default='High'),
        categories=['Low','Medium','High'],ordered=True)
    tert=student.groupby('strict_tertile',observed=False).agg(n=('user_id','size'),accuracy=('strict_accuracy_pct','mean'),ai_frequency=('ai_frequency','mean'),
        kg_pct=('kg_pct','mean'),kg_count=('kg_count','mean'),other_process_pct=('other_process_pct','mean'),task_pct=('task_pct_neutral','mean'),
        strict_accuracy_sd=('strict_accuracy_pct','std')).reset_index()
    tert.to_csv(out/'strict_tertiles.csv',index=False)
    summary['status']='REVIEW_REQUIRED' if any(x.get('error') or x.get('warnings') or x.get('converged') is False for x in summary['models']) else 'MODELS_COMPLETED_REQUIRES_REVIEW'
    write_json(out/'run02_summary.json',summary)
    pd.DataFrame(summary['models']).to_json(out/'model_status.json',orient='records',force_ascii=False,indent=2)
    print(json.dumps(summary,ensure_ascii=False,indent=2,default=str))
    print('Outputs:',out)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]/'outputs'))
    ap.add_argument('--check-only',action='store_true')
    args=ap.parse_args()
    main(args.root,args.check_only)
