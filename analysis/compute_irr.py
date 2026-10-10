"""Recompute raw five-category agreement from the unchanged coder workbooks."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
from openpyxl import load_workbook
from compute_irr_author_final import kappa
REPO=Path(__file__).resolve().parents[1]
def main(root):
    tables=[]
    for i in (1,2):
        w=load_workbook(REPO/'materials'/f'Coding_Sheet_Coder{i}.xlsx',read_only=True,data_only=True)
        rows=list(w['Coding Sheet'].values)[2:18];tables.append(rows);w.close()
    a,b=tables
    assert len(a)==len(b)==16 and all(x[:7]==y[:7] for x,y in zip(a,b))
    c1=np.array([r[7] for r in a]);c2=np.array([r[7] for r in b]);observed=kappa(c1,c2)
    rng=np.random.default_rng(20260921);boot=[]
    for _ in range(10000):
        idx=rng.integers(0,16,16)
        with np.errstate(invalid='ignore',divide='ignore'):v=kappa(c1[idx],c2[idx])
        if np.isfinite(v):boot.append(v)
    out=Path(root)/'revision_round2/run06_outputs';out.mkdir(parents=True,exist_ok=True)
    result={'n_items':16,'agreements':int((c1==c2).sum()),'kappa_recomputed':observed,'kappa_boot_ci':np.percentile(boot,[2.5,97.5]).tolist(),'kappa_boot_B':10000,'kappa_boot_seed':20260921,'valid_bootstrap_resamples':len(boot),'note':'Item resampling; unchanged raw five-category ratings. Deterministic author remapping is a separate analysis.'}
    (out/'run06_summary.json').write_text(json.dumps(result,indent=2))
    pd.DataFrame([{'Feature (CN)':x[1],'Feature (EN)':x[2],'Coder 1':x[7],'Coder 2':y[7],'Agreement':x[7]==y[7]} for x,y in zip(a,b)]).to_csv(out/'irr_side_by_side.csv',index=False)
    print(json.dumps(result,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);main(ap.parse_args().root)
