"""Retained stage04 analyses: log KG count and any KG use, HC3 OLS.

Classification, intervals, single-course checks and multiple testing are
implemented in stages 04b/04c. Superseded stage04 methods are not executed.
"""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
def main(root):
    root=Path(root);st=pd.read_csv(root/'revision_round2/run02_outputs/strict_student_model_data.csv')
    out=root/'revision_round2/run04_outputs';out.mkdir(parents=True,exist_ok=True)
    st['log_kg_count']=np.log1p(st.kg_count.astype(float));st['kg_any']=(st.kg_count>=1).astype(int)
    rows=[]
    for v in ['log_kg_count','kg_any']:
        r=smf.ols(f'strict_accuracy_pct ~ {v} + log_ai_frequency',data=st).fit(cov_type='HC3')
        for t in [v,'log_ai_frequency']:
            rows.append({'model':f'student_ols_{v}','term':t,'estimate':float(r.params[t]),'se':float(r.bse[t]),'ci_low':float(r.conf_int().loc[t,0]),'ci_high':float(r.conf_int().loc[t,1]),'p':float(r.pvalues[t])})
    pd.DataFrame(rows).to_csv(out/'alternative_operationalizations_ols.csv',index=False)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);main(p.parse_args().root)
