"""Compare recomputed final OR tables with the archived submission tables."""
from pathlib import Path
import argparse,json
import pandas as pd,numpy as np
REPO=Path(__file__).resolve().parents[1]
def main(work):
    ref=REPO/'results/reference/online_resources';out=work/'online_resources';rows=[];fail=[]
    for p in sorted(ref.rglob('*.csv')):
        rel=p.relative_to(ref);target=out/rel
        if not target.exists():fail.append(str(rel)+': missing');continue
        a=pd.read_csv(p);b=pd.read_csv(target);bad=[]
        if list(a.columns)!=list(b.columns) or a.shape!=b.shape:bad.append('shape/columns')
        else:
            # Some stage sources order groups differently; compare the same groups.
            if 'strict_accuracy_group' in a and 'user_id' not in a:
                a=a.sort_values('strict_accuracy_group').reset_index(drop=True);b=b.sort_values('strict_accuracy_group').reset_index(drop=True)
            if p.name=='high_contribution_courses.csv':
                # Near-zero residual contributions can tie numerically. Course
                # identity, not floating-point rank among ties, aligns the rows.
                a=a.sort_values('course_id').reset_index(drop=True);b=b.sort_values('course_id').reset_index(drop=True)
            for c in a:
                if c in ['source','warnings','p_method','ci_method','pearson_ci_method','interpretation']:continue
                if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]):
                    is_p=c.lower() in ['p','raw_p','bh_q','bh_q_family48','pearson_p_unadjusted','p (pearson; unadjusted)','p (spearman; unadjusted)','p (two-sided; unadjusted)']
                    if not np.allclose(a[c],b[c],rtol=1e-5 if is_p else 1e-6,atol=1e-250 if is_p else 1e-9,equal_nan=True):bad.append(c)
                elif not a[c].fillna('').astype(str).equals(b[c].fillna('').astype(str)):bad.append(c)
        rows.append({'table':str(rel),'rows':len(a),'different_columns':bad})
        if bad:fail.append(str(rel)+': '+', '.join(bad))
    summary={'status':'PASS' if not fail else 'FAIL','tables_checked':len(rows),'failures':fail,'comparisons':rows,'tolerances':'Numeric rtol=1e-6, atol=1e-9; p/q rtol=1e-5, atol=1e-250. Text exact except provenance/method/warning descriptions.'}
    (work/'comparison.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
    if fail:raise SystemExit(1)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);main(p.parse_args().work.resolve())
