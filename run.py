"""Portable entry point for the final revision archive."""
from pathlib import Path
import argparse,os,subprocess,sys,shutil,json,time
REPO=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command',choices=['verify','reproduce','figures','raw'])
    ap.add_argument('--work',type=Path,default=REPO/'outputs')
    ap.add_argument('--raw-dir',type=Path,help='MOOCCubeX root containing relations/ and entities/')
    ap.add_argument('--responses',type=Path,help='Optional separate user-problem.json path')
    ap.add_argument('--from-raw',action='store_true',help='Use stage01 inputs rebuilt in this work directory')
    args=ap.parse_args();work=args.work.resolve()
    if work==REPO or any(work==REPO/p or REPO/p in work.parents for p in ['analysis','materials','data','results','figures','docs','tools']):
        ap.error('--work must be a separate output directory; reference files are read-only')
    work.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',MPLBACKEND='Agg',MPLCONFIGDIR=str(work/'mpl_cache'),REPRO_WORK=str(work))
    logs=work/'logs';logs.mkdir(exist_ok=True);status=[]
    def call(script,*extra):
        start=time.monotonic();print('Running',script,flush=True)
        log=logs/(Path(script).stem+'.log')
        with log.open('w') as f:r=subprocess.run([sys.executable,str(REPO/script),*map(str,extra)],cwd=REPO,env=env,stdout=f,stderr=subprocess.STDOUT)
        status.append({'script':script,'returncode':r.returncode,'seconds':round(time.monotonic()-start,3),'log':str(log.relative_to(work))})
        (work/'execution_status.json').write_text(json.dumps(status,indent=2))
        if r.returncode:
            print(log.read_text()[-6000:]);raise SystemExit(f'Failed: {script}; see {log}')
        print('Completed',script,flush=True)
    if args.command=='raw':
        if not args.raw_dir:ap.error('raw requires --raw-dir')
        extra=['--raw-dir',args.raw_dir.resolve(),'--out',work/'revision_round2/run01_outputs']
        if args.responses:extra+=['--responses',args.responses.resolve()]
        call('analysis/rebuild_inputs.py',*extra);return
    if args.command=='verify':call('tools/verify_repository.py','--out',work/'verification.json');return
    if args.command=='reproduce':
        inp=work/'revision_round2/run01_outputs';inp.mkdir(parents=True,exist_ok=True)
        if not args.from_raw:
            for p in (REPO/'data/inputs').iterdir():
                if p.is_file():shutil.copyfile(p,inp/p.name)
        elif not (inp/'run_summary.json').exists():ap.error('Run raw first in the same --work directory')
        for name in ['compute_irr.py','02_strict_models.py','03_diagnostics.py','03b_diagnostics_patch.py','04_remaining_analyses.py','04b_corrections.py','04c_mapping_and_pvalues.py','05_attempts_stratified.py','07_table6_trend_cis.py','compute_irr_author_final.py','08_final_checks.py','curate_online_resources.py','three_category_analysis.py']:
            call('analysis/'+name,'--root',work)
        call('tools/compare_results.py','--work',work)
    else:
        # A figures-only run reads archived numerical results when no refit exists.
        for stage in ['run02_outputs','run06_outputs','run04c_outputs']:
            dest=work/'revision_round2'/stage
            if not dest.exists():shutil.copytree(REPO/'results/reference/pipeline'/stage,dest)
    for i in range(1,7):call(f'figures/scripts/figure{i}.py')
    call('analysis/OR3_recompute_and_plot.py','--root',work,'--out',work/'figures')
    print('Finished. Outputs:',work)
if __name__=='__main__':main()
