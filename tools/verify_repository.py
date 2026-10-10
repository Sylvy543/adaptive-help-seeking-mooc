"""Validate archive integrity, input definitions and final numerical controls."""
from pathlib import Path
import argparse,hashlib,json,csv,ast
import numpy as np,pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
R=Path(__file__).resolve().parents[1];REF=R/'results/reference/online_resources'
def main(out):
    checks={}
    def ck(name,value):checks[name]=bool(value)
    checksum=R/'CHECKSUMS.sha256'
    ck('checksum manifest exists',checksum.is_file())
    if checksum.exists():
        for line in checksum.read_text().splitlines():
            h,p=line.split('  ',1);file=R/p;ck('sha256 '+p,file.is_file() and hashlib.sha256(file.read_bytes()).hexdigest()==h)
    for p in R.rglob('*.py'):
        if 'outputs' not in p.relative_to(R).parts:ast.parse(p.read_text());ck('syntax '+str(p.relative_to(R)),True)
    s=pd.read_csv(REF/'Online_Resource_7_Robustness_Results/strict_student_model_data.csv')
    c=pd.read_csv(REF/'Online_Resource_5_user_course_accuracy/Online_Resource_5_user_course_accuracy.csv')
    ck('student sample',len(s)==s.user_id.nunique()==16389)
    ck('AI interactions',s.ai_frequency.sum()==85815)
    ck('strict student accuracy',np.allclose(s.strict_accuracy_pct,100*s.strict_correct_records/s.strict_valid_records))
    ck('course sample and keys',len(c)==2496 and not c.duplicated(['user_id','course_id']).any())
    ck('course accuracy',np.allclose(c.accuracy,100*c.n_correct/c.n_records))
    ck('inclusion flag',np.array_equal(c.included_primary_model,(c.n_records>=5).astype(int)))
    d=c[c.included_primary_model==1];ck('model N',len(d)==1983 and d.user_id.nunique()==1708 and d.course_id.nunique()==396)
    ck('exact outcome changes',(s.strict_correct_records*s.total_problems!=s.correct_problems*s.strict_valid_records).sum()==1064)
    for n in [48,60]:
        f=pd.read_csv(REF/f'Online_Resource_7_Robustness_Results/multiplicity_family{n}.csv')
        ck(f'family {n} size',len(f)==n);ck(f'family {n} BH',np.allclose(multipletests(f.raw_p,method='fdr_bh')[1],f.bh_q,rtol=1e-10,atol=1e-250))
    for name in ['attempts_strata_correlations.csv','attempts_subsample_correlations.csv']:
        f=pd.read_csv(REF/'Online_Resource_7_Robustness_Results'/name)
        ck(name+' intervals',f.loc[f.method=='spearman','ci_method'].str.contains('bootstrap').all())
    l=pd.read_csv(REF/'Online_Resource_6_Model_Diagnostics/loco_sign_change_summary.csv').set_index('term')
    ck('LOCO signs',l.loc['selfreg_pct_neutral10','n_sign_changes']==3 and l.n_sign_changes.sum()==3)
    t=pd.read_csv(REF/'Online_Resource_4_Three_Category_Results/three_category_correlations.csv')
    for r in t.to_dict('records'):
        ck('Pearson '+r['variable'],np.isclose(stats.pearsonr(s[r['variable']],s.strict_accuracy_pct).statistic,r['r (Pearson)']))
    result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':len(checks),'failures':[k for k,v in checks.items() if not v],'checked_files_and_controls':checks}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='checked_files_and_controls'},indent=2))
    if result['failures']:raise SystemExit(1)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);main(p.parse_args().out)
