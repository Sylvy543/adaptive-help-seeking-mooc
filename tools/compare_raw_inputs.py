"""Check a fresh full-log rebuild against the distributed derived inputs."""
from pathlib import Path
import argparse,json
import pandas as pd,numpy as np
R=Path(__file__).resolve().parents[1]
def main(work):
    rows=[]
    for name,keys in [('rebuilt_student_audit.csv',['user_id']),('feature_counts_long.csv',['user_id','base_feature']),('unique_course_binary_audit.csv',['user_id','course_id']),('feature_mapping_audit.csv',['raw_tag'])]:
        a=pd.read_csv(R/'data/inputs'/name);b=pd.read_csv(work/'revision_round2/run01_outputs'/name)
        a=a.sort_values(keys).reset_index(drop=True);b=b.sort_values(keys).reset_index(drop=True)
        bad=[]
        if a.shape!=b.shape or list(a)!=list(b):bad.append('shape/columns')
        else:
            for c in a:
                if pd.api.types.is_numeric_dtype(a[c]):
                    if not np.allclose(a[c],b[c],rtol=1e-13,atol=1e-13,equal_nan=True):bad.append(c)
                elif not a[c].equals(b[c]):bad.append(c)
        rows.append({'table':name,'rows':len(a),'different_columns':bad})
    result={'status':'PASS' if all(not r['different_columns'] for r in rows) else 'FAIL','tables':rows}
    (work/'raw_comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    if result['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);main(p.parse_args().work.resolve())
