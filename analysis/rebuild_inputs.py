"""Stream all raw records to rebuild the three portable analysis inputs.

No coverage-based early stopping and no deduplication of response records.
The strict denominator counts valid binary is_correct records, not the raw
attempts field. Course linkage must be unambiguous across all resources.
"""
from pathlib import Path
import argparse,collections,csv,hashlib,json,math,time
REPO=Path(__file__).resolve().parents[1]
def writecsv(p,fields,rows):
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def pid(v):
    if isinstance(v,bool):return None
    s=str(v);s=s[3:] if s.startswith('Pm_') else s
    return int(s) if s.isdigit() else None
def main(raw,responses,out):
    paths={'ai':raw/'relations/user-xiaomu.json','responses':responses or raw/'relations/user-problem.json','problems':raw/'entities/problem.json','courses':raw/'entities/course.json'}
    for p in paths.values():
        if not p.is_file():raise FileNotFoundError(p)
    out.mkdir(parents=True,exist_ok=True);counts=collections.Counter();hashes={}
    def records(name):
        p=paths[name];h=hashlib.sha256();last=time.monotonic()
        with p.open('rb') as f:
            for n,line in enumerate(f,1):
                h.update(line);counts[name+'_physical_lines']+=1
                if not line.strip():counts[name+'_blank']+=1;continue
                try:
                    r=json.loads(line)
                    if not isinstance(r,dict):raise ValueError()
                except (ValueError,UnicodeDecodeError):counts[name+'_invalid_json']+=1;continue
                yield r
                if time.monotonic()-last>15:print(name,n,'records scanned',flush=True);last=time.monotonic()
        hashes[name]={'file':p.name,'bytes':p.stat().st_size,'sha256':h.hexdigest()}
    rules=list(csv.DictReader((REPO/'data/inputs/feature_mapping_audit.csv').open(encoding='utf-8-sig')))
    lookup={r['raw_tag']:r['historical_category'] for r in rules};validbase={r['base_feature'] for r in rules}
    ai=collections.defaultdict(collections.Counter);feat=collections.defaultdict(collections.Counter);tags=collections.Counter()
    for r in records('ai'):
        u,t=r.get('user_id'),r.get('question_type')
        if not isinstance(u,str) or not isinstance(t,str):counts['ai_invalid_fields']+=1;continue
        if t not in lookup or t.split('|')[0] not in validbase:raise ValueError('Unrecognised feature label: '+t)
        ai[u][lookup[t]]+=1;feat[u][t.split('|')[0]]+=1;tags[t]+=1
    ex=collections.defaultdict(set)
    for r in records('courses'):
        cid=r.get('id');resources=r.get('resource',[])
        if not isinstance(cid,str) or not isinstance(resources,list):continue
        for res in resources:
            if isinstance(res,dict) and isinstance(res.get('resource_id'),str) and res['resource_id'].startswith('Ex_'):ex[res['resource_id']].add(cid)
    candidates=collections.defaultdict(set)
    for r in records('problems'):
        p=pid(r.get('problem_id'));e=r.get('exercise_id')
        if p is not None and isinstance(e,str) and e in ex:candidates[p].update(ex[e])
    unique={p:next(iter(c)) for p,c in candidates.items() if len(c)==1};ambiguous=sum(len(c)>1 for c in candidates.values());del ex,candidates
    outcomes=collections.defaultdict(lambda:[0,0,0,0]);cells=collections.defaultdict(lambda:[0,0])
    for r in records('responses'):
        u=r.get('user_id')
        if not isinstance(u,str) or u not in ai:continue
        v=r.get('is_correct');numeric=isinstance(v,(bool,int,float)) and math.isfinite(float(v))
        strict=int(v) if numeric and v in (0,1) else None
        historical=int(bool(v or r.get('correct',False) or r.get('score',0)==1))
        a=outcomes[u];a[0]+=1;a[1]+=historical
        if strict is not None:
            a[2]+=1;a[3]+=strict;c=unique.get(pid(r.get('problem_id')))
            if c is not None:cells[(u,c)][0]+=1;cells[(u,c)][1]+=strict
        else:counts['invalid_binary_ai_responses']+=1
    cats={'Task':'task_count','Process':'process_count','Self-Regulation':'self_reg_count','Self':'self_count','Other':'other_count'}
    rows=[]
    for u,(n,h,v,k) in sorted(outcomes.items()):
        rows.append(dict(user_id=u,ai_frequency=sum(ai[u].values()),total_problems=n,correct_problems=h,problem_accuracy=100*h/n,strict_valid_records=v,strict_correct_records=k,strict_accuracy_pct=100*k/v if v else None,**{c:ai[u][label] for label,c in cats.items()}))
    if not rows:raise RuntimeError('No matched students')
    writecsv(out/'rebuilt_student_audit.csv',list(rows[0]),rows)
    writecsv(out/'feature_counts_long.csv',['user_id','base_feature','n_interactions'],(dict(user_id=u,base_feature=t,n_interactions=n) for u in sorted(feat) for t,n in sorted(feat[u].items())))
    writecsv(out/'unique_course_binary_audit.csv',['user_id','course_id','n_records','n_correct','accuracy_pct'],(dict(user_id=u,course_id=c,n_records=n,n_correct=k,accuracy_pct=100*k/n) for (u,c),(n,k) in sorted(cells.items())))
    writecsv(out/'feature_mapping_audit.csv',['raw_tag','base_feature','historical_category','n'],(dict(raw_tag=t,base_feature=t.split('|')[0],historical_category=lookup[t],n=n) for t,n in sorted(tags.items())))
    summary={'full_scan_complete':True,'ai_rows':sum(tags.values()),'ai_users':len(ai),'main_users':len(rows),'course_cells':len(cells),'ambiguous_problem_ids':ambiguous,'scan_counts':dict(counts),'input_manifest':hashes,'notes':['Full scans; historical mapping preserved, including four Baike variants.','Binary correctness; unique-course links; records are not distinct questions.','Raw inputs not modified; no outcome filtering beyond stated valid-binary definition.']}
    (out/'run_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw-dir',type=Path,required=True);p.add_argument('--responses',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.raw_dir.resolve(),a.responses.resolve() if a.responses else None,a.out.resolve())
