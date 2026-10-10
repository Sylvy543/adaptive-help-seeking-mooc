"""Curate final OR5–7 results; never rerun fits or modify original pipeline outputs."""
from pathlib import Path
import csv, hashlib, json, shutil
import numpy as np
import pandas as pd
from scipy import stats

import argparse
ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);args=ap.parse_args()
ROOT=args.root.resolve();RUN=ROOT/'revision_round2';PKG=ROOT/'online_resources'
HERE=ROOT/'curation';HERE.mkdir(parents=True,exist_ok=True)
OR4='Online_Resource_4_Three_Category_Results'
OR5='Online_Resource_5_user_course_accuracy'
OR6='Online_Resource_6_Model_Diagnostics'
OR7='Online_Resource_7_Robustness_Results'
derived={}; manifest=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel): return pd.read_csv(RUN/rel)
def clean_records(df): return json.loads(df.to_json(orient='records',double_precision=15))
def table(rel, df, sources, operation):
    # Preserve floating-point values via Python's round-trip JSON serialization.
    df=df.astype(object).where(pd.notna(df),None)
    rows=df.to_dict(orient='records')
    for row in rows:
        for k,v in row.items():
            if isinstance(v,np.generic): row[k]=v.item()
    derived[rel]={'columns':list(df.columns),'rows':rows}
    manifest.append({'package_file':rel,'source_files':'; '.join(sources),'operation':operation,'source_sha256':'; '.join(sha(RUN/s) for s in sources)})
def copy(rel,source,meaning):
    dst=PKG/rel;dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists() and dst.read_bytes()!=(RUN/source).read_bytes():
        raise RuntimeError('Refusing to overwrite different existing result: '+rel)
    shutil.copyfile(RUN/source,dst)
    manifest.append({'package_file':rel,'source_files':source,'operation':'Unchanged final result: '+meaning,'source_sha256':sha(RUN/source)})
def text(rel,body):
    dst=PKG/rel; dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():
        backup=HERE/'backups'/rel;backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():shutil.copyfile(dst,backup)
    dst.write_text(body.strip()+'\n',encoding='utf-8')
def bh(p):
    p=np.asarray(p,float);order=np.argsort(p);q=np.minimum.accumulate((p[order]*len(p)/np.arange(1,len(p)+1))[::-1])[::-1];out=np.empty(len(p));out[order]=np.minimum(q,1);return out
def corr(x,y):
    x=np.asarray(x,float);y=np.asarray(y,float);n=len(y);r=float(np.corrcoef(x,y)[0,1]);rho=float(stats.spearmanr(x,y).statistic)
    ci=np.tanh(np.arctanh(r)+np.array([-1,1])*stats.norm.ppf(.975)/np.sqrt(n-3))
    p=float(2*stats.t.sf(abs(r)*np.sqrt((n-2)/(1-r*r)),n-2))
    return dict(n=n,pearson_r=r,pearson_ci_low=float(ci[0]),pearson_ci_high=float(ci[1]),pearson_p_unadjusted=p,spearman_r=rho)

st=read('run02_outputs/strict_student_model_data.csv')
co=read('run02_outputs/strict_course_model_data.csv')
assert len(st)==st.user_id.nunique()==16389
assert len(co)==2496
np.testing.assert_allclose(st.strict_accuracy_pct,100*st.strict_correct_records/st.strict_valid_records,atol=1e-12)
hist=100*st.correct_problems/st.total_problems
np.testing.assert_allclose(hist,st.historical_accuracy_pct,atol=1e-12)
delta=st.strict_accuracy_pct-st.historical_accuracy_pct
changed=st.strict_correct_records*st.total_problems != st.correct_problems*st.strict_valid_records
assert changed.sum()==1064
comp=st[['user_id','total_problems','correct_problems','strict_valid_records','strict_correct_records','historical_accuracy_pct','strict_accuracy_pct']].copy()
comp=comp.rename(columns={'total_problems':'historical_response_records','correct_problems':'historical_correct_records'})
comp['strict_minus_historical_pp']=delta
comp['accuracy_changed']=changed.astype(int)
table(f'{OR5}/student_accuracy_definition_comparison.csv',comp,['run02_outputs/strict_student_model_data.csv'],'One row per student; signed difference is strict minus historical; flag based on exact integer ratios')
summary=pd.DataFrame([{'n_students':len(st),'n_accuracy_changed':int(changed.sum()),'pct_accuracy_changed':float(changed.mean()*100),
 'mean_strict_minus_historical_pp':float(delta.mean()),'median_strict_minus_historical_pp':float(delta.median()),
 'historical_accuracy_mean_pct':float(hist.mean()),'strict_accuracy_mean_pct':float(st.strict_accuracy_pct.mean()),
 'difference_direction':'strict minus historical','unit':'percentage points; equal student weights'}])
table(f'{OR5}/accuracy_definition_comparison_summary.csv',summary,['run02_outputs/strict_student_model_data.csv'],'Full-sample student-level summary; no course-row weighting')
rows=[]
for var in ['ai_frequency','effective_feedback_pct','kg_pct','other_process_pct','task_pct_neutral']:
    for outcome in ['historical_accuracy_pct','strict_accuracy_pct']:
        rows.append({'variable':var,'outcome':outcome,**corr(st[var],st[outcome]),'feature_mapping':'held fixed across the two outcomes','pearson_ci_method':'Fisher z; marginal 95%; not multiplicity-adjusted'})
table(f'{OR5}/accuracy_definition_correlation_comparison.csv',pd.DataFrame(rows),['run02_outputs/strict_student_model_data.csv'],'Recomputed zero-order associations holding the feature mapping fixed; no additional BH family')

# Supply the per-student feature breakdown explicitly promised in manuscript §4.7.2.
student4=st[['user_id','strict_accuracy_pct','ai_frequency','kg_count','other_process_count','task_count_neutral','selfreg_count_neutral','self_count_neutral','other_count_neutral','kg_pct','other_process_pct','task_pct_neutral','selfreg_pct_neutral','self_pct_neutral','other_pct_neutral']].copy()
student4['strict_accuracy_group']=np.select([st.strict_accuracy_pct<67.5,st.strict_accuracy_pct<=84],['Low','Medium'],default='High')
table(f'{OR4}/three_category_student_data.csv',student4,['run02_outputs/strict_student_model_data.csv'],'Per-student feature decomposition, including Other and fixed strict-accuracy group')

patch=json.loads((RUN/'run03_outputs/diagnostics_patch_summary.json').read_text())
diag=json.loads((RUN/'run03_outputs/run03_summary.json').read_text())
status=json.loads((RUN/'run02_outputs/model_status.json').read_text())
family=read('run04c_outputs/multiplicity_v3.csv')
family60=read('run08_outputs/run05_family60_itemized.csv')
assert len(family)==48 and len(family60)==60
for f in [family,family60]:np.testing.assert_allclose(bh(f.raw_p),f.bh_q,rtol=1e-11,atol=1e-14)
coef=read('run02_outputs/model_coefficients.csv')
cross=coef[coef.model=='course_mixed_crossed_user_course'].copy()
cross=cross[cross.term.isin(['Intercept','kg_pct10','other_process_pct10','task_pct_neutral10','selfreg_pct_neutral10','log_ai_frequency'])]
assert len(cross)==6
cross['bh_q_family48']=cross.term.map(family[family.source=='course_mixed_crossed_user_course'].set_index('variable').bh_q)
cross['outcome']='course-cell accuracy (0-100)'
table(f'{OR6}/crossed_model_fixed_effects.csv',cross,['run02_outputs/model_coefficients.csv','run04c_outputs/multiplicity_v3.csv'],'Selected primary crossed-model fixed effects; intercept has no q in family48')
v=next(r for r in status if r['model']=='course_mixed_crossed_user_course')
components={**v['variance_components'],'residual':v['residual_variance']};total=sum(components.values())
table(f'{OR6}/crossed_model_variance_components.csv',pd.DataFrame([{'component':k,'estimated_variance':value,'share_of_variance_components_pct':100*value/total,'interpretation':'conditional on included fixed effects; not percentage of total observed outcome variance'} for k,value in components.items()]),['run02_outputs/model_status.json'],'Shares of sum of course, student and residual variance components')
table(f'{OR6}/binomial_full_sample_coefficients.csv',pd.DataFrame(patch['binomial_fit']['ai_terms']),['run03_outputs/diagnostics_patch_summary.json'],'Patched full-sample binomial fit; student-clustered SE; no dispersion rescaling')
loco=read('run03_outputs/loco_sensitivity.csv')
base={r['term']:r for r in patch['binomial_fit']['ai_terms']}
lr=[]
for term,r in base.items():
    signs=np.sign(loco[term+'_est'])!=np.sign(r['estimate'])
    np.testing.assert_array_equal(signs,loco[term+'_sign_change'])
    np.testing.assert_allclose((loco[term+'_est']-r['estimate'])/r['se_cluster'],loco[term+'_change_in_se_units'],rtol=1e-12)
    lr.append({'term':term,'full_estimate':r['estimate'],'full_p_unadjusted':r['p'],'n_exclusions':10,'n_sign_changes':int(signs.sum()),'courses_with_sign_change':'; '.join(loco.loc[signs,'excluded_course']), 'min_exclusion_estimate':float(loco[term+'_est'].min()),'max_exclusion_estimate':float(loco[term+'_est'].max()),'max_abs_change_in_full_sample_se':float(loco[term+'_change_in_se_units'].abs().max())})
assert [x['n_sign_changes'] for x in lr]==[0,0,0,3,0]
table(f'{OR6}/loco_sign_change_summary.csv',pd.DataFrame(lr),['run03_outputs/loco_sensitivity.csv','run03_outputs/diagnostics_patch_summary.json'],'Verified coefficient signs against full-sample reference')
overview=[('full_sample_cells',1983),('full_sample_students',1708),('full_sample_courses',396),('binomial_pearson_dispersion',patch['binomial_fit']['pearson_dispersion']),('extreme_courses_excluded',diag['B_binomial']['n_extreme_courses']),('dispersion_after_extreme_course_exclusion',diag['B_binomial']['pearson_dispersion_excl_extreme']),('top10_share_of_pearson_sum',patch['high_contribution']['top10_share']),('loco_min_dispersion',float(loco.pearson_dispersion.min())),('loco_max_dispersion',float(loco.pearson_dispersion.max()))]
table(f'{OR6}/diagnostic_summary.csv',pd.DataFrame(overview,columns=['statistic','value']),['run03_outputs/diagnostics_patch_summary.json','run03_outputs/run03_summary.json','run03_outputs/loco_sensitivity.csv'],'Only retained diagnostic values; withdrawn scaled terms and interpretations omitted')
for name in ['optimizer_stability.csv','extended_variance_profile_course_mixed_course_random.csv','extended_variance_profile_course_mixed_kg_course_random.csv','course_random_vs_crossed.csv','dispersion_by_cell_size.csv','binomial_refit_comparison.csv','extreme_courses.csv','high_contribution_courses.csv','loco_sensitivity.csv']:
    copy(f'{OR6}/{name}',f'run03_outputs/{name}','diagnostics, using extended profiles and patched LOCO')
copy(f'{OR6}/single_course_recheck.csv','run04b_outputs/single_course_recheck.csv','two-optimizer single-course sensitivity recheck')

# Consolidate final full-sample correlations: patched intervals plus corrected p/q.
cis=read('run04b_outputs/spearman_bootstrap_cis.csv').set_index('variable')
rest=read('run04c_outputs/restored_mapping_sensitivity.csv')
final=[]
for _,f in family[family.source=='correlation'].iterrows():
    v=f.variable;m=f.method
    ci_var={'historical_other_share':'other_share','historical_ef_excluding_other_denominator':'ef_mapped_only'}.get(v,v)
    if ci_var in cis.index:
        ref=cis.loc[ci_var];prefix='pearson' if m=='pearson' else 'spearman'
        assert pd.notna(ref[prefix+'_r'])
        rr=ref[prefix+'_r'];n=int(ref['n']);low=ref[prefix+'_ci_low'];high=ref[prefix+'_ci_high'];method=ref[prefix+'_ci_method']
    else:
        ref=rest[(rest.variable==v)&(rest.method==m)].iloc[0]
        rr=ref.r;n=int(ref['n']);low=ref.ci_low;high=ref.ci_high;method=ref.ci_method
    np.testing.assert_allclose(rr,f.stat,rtol=1e-11,atol=1e-14)
    final.append({'variable':v,'method':m,'n':n,'r':f.stat,'ci_low':low,'ci_high':high,'raw_p':f.raw_p,'bh_q':f.bh_q,'family_id':f.family_id,'ci_method':method,'p_method':f.p_method})
assert len(final)==28
table(f'{OR7}/full_sample_correlations_final.csv',pd.DataFrame(final),['run04b_outputs/spearman_bootstrap_cis.csv','run04c_outputs/restored_mapping_sensitivity.csv','run04c_outputs/multiplicity_v3.csv'],'Merged final intervals and corrected p/q; no Fisher-z Spearman intervals')
boot=read('run08_outputs/spearman_bootstrap_cis.csv').set_index(['group','variable'])
for file,groupcol,prefix in [('attempts_strata_correlations.csv','stratum','strata:'),('attempts_subsample_correlations.csv','subsample','subsample:')]:
    d=read('run05_outputs/'+file)
    for i,r in d[d.method=='spearman'].iterrows():
        key=(prefix+r[groupcol],r.variable)
        if key in boot.index:
            q=boot.loc[key];np.testing.assert_allclose(r.r,q.spearman_r,atol=1e-14);np.testing.assert_allclose(r.p,q.p,rtol=1e-10,atol=1e-14)
            assert r['n']==q['n']
            d.loc[i,['ci_low','ci_high','ci_method']]=[q.ci_low,q.ci_high,q.ci_method]
        else:assert 'bootstrap' in r.ci_method
    assert d.loc[d.method=='spearman','ci_method'].str.contains('bootstrap').all()
    table(f'{OR7}/{file}',d,['run05_outputs/'+file,'run08_outputs/spearman_bootstrap_cis.csv'],'Original coefficients/p retained; superseded Spearman intervals replaced by run08 paired-row bootstrap intervals')
within=[]
for name,g in st.assign(group=student4.strict_accuracy_group).groupby('group',sort=False):
    r=corr(g.effective_feedback_pct,g.strict_accuracy_pct)
    within.append({'strict_accuracy_group':name,**r,'predictor':'historical effective-feedback share','interpretation':'outcome-defined fixed groups; descriptive, range restriction possible'})
table(f'{OR7}/within_accuracy_groups_correlations.csv',pd.DataFrame(within),['run02_outputs/strict_student_model_data.csv'],'Descriptive within-group Pearson/Fisher intervals and Spearman point estimates, fixed 67.5/84 cutpoints')
for dest,source in [
 ('multiplicity_family48.csv','run04c_outputs/multiplicity_v3.csv'),('multiplicity_family60.csv','run08_outputs/run05_family60_itemized.csv'),
 ('coder_anchored_feature_mapping.csv','run04c_outputs/restored_feature_mapping.csv'),('coder_anchored_student_counts.csv','run04c_outputs/restored_student_counts.csv'),('coder_anchored_correlations.csv','run04c_outputs/restored_mapping_sensitivity.csv'),
 ('tertile_comparisons_high_minus_low.csv','run04b_outputs/tertile_comparisons_v2.csv'),
 ('alternative_operationalizations_ols.csv','run04_outputs/alternative_operationalizations_ols.csv'),
 ('attempts_strata_descriptives.csv','run05_outputs/attempts_strata_descriptives.csv'),('attempts_weighted_correlations.csv','run05_outputs/attempts_weighted_correlations.csv'),('attempts_models.csv','run05_outputs/attempts_models.csv'),
 ('spearman_bootstrap_cis_attempts.csv','run08_outputs/spearman_bootstrap_cis.csv'),('strict_student_model_data.csv','run02_outputs/strict_student_model_data.csv'),
 ('section42_operationalisations.csv','run08_outputs/section42_operationalisations.csv'),('section44_trends_hc3.csv','run08_outputs/section44_trends_hc3.csv'),('section44_tukey.csv','run08_outputs/section44_tukey.csv')]:
    copy(f'{OR7}/{dest}',source,'final retained result/input; see README for interpretation and test-family scope')

table('SOURCE_MANIFEST.csv',pd.DataFrame(manifest),[], 'Inventory of new/curated CSV sources and operations')
(HERE/'derived_tables.json').write_text(json.dumps(derived,ensure_ascii=False,allow_nan=False),encoding='utf-8')
(HERE/'verification.json').write_text(json.dumps({'derived_tables':len(derived),'manifest_rows':len(manifest)-1,'n_students':len(st),'n_changed':int(changed.sum()),'mean_difference_pp':float(delta.mean()),'loco_sign_changes':lr,'family48_BH_verified':True,'family60_BH_verified':True,'modified_existing_manuscript_or_OR1':False},ensure_ascii=False,indent=2))
print('Prepared',len(derived),'derived tables; final result copies verified; BH48/BH60 verified; LOCO signs verified.')

for rel,t in derived.items():
    p=PKG/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=t['columns']);w.writeheader();w.writerows(t['rows'])
co['included_primary_model']=(co.n_records>=5).astype(int)
co.to_csv(PKG/OR5/'Online_Resource_5_user_course_accuracy.csv',index=False)
