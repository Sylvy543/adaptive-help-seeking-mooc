"""Recompute OR3 descriptive tables and redraw Figure 1 from strict run02 data.

Existing bootstrap intervals are checked against run04b/run04c outputs, not
re-estimated here. Writes only to this script's output directory.
Usage: python OR3_recompute_and_plot.py --root /path/to/project
"""
from pathlib import Path
import argparse,json,hashlib,os,platform

def main(root, out):
    out.mkdir(parents=True,exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR',str(out/'mpl_cache'))
    import numpy as np
    import pandas as pd
    import scipy
    from scipy import stats
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rev=root/'revision_round2'
    src=rev/'run02_outputs/strict_student_model_data.csv'
    s=pd.read_csv(src)
    assert len(s)==16389 and s.user_id.is_unique
    assert int(s.ai_frequency.sum())==85815
    assert np.allclose(s.strict_accuracy_pct,100*s.strict_correct_records/s.strict_valid_records)
    s['historical_ef']=100*(s.process_count+s.self_reg_count)/s.ai_frequency
    s['kg_moved_to_task']=100*(s.process_count-s.kg_count+s.self_reg_count)/s.ai_frequency
    assert np.allclose(s.historical_ef,s.effective_feedback_pct)
    assert np.allclose(s.historical_ef-s.kg_moved_to_task,s.kg_pct)
    s['group']=np.select([s.strict_accuracy_pct<67.5,s.strict_accuracy_pct<=84.0],['Low','Medium'],default='High')
    groups=['Low','Medium','High']; desc=[];tests=[]
    for group,n in zip(groups,[5540,5467,5382]):
        z=s[s.group==group]; assert len(z)==n
        row={'group':group,'n':n}
        for col in ['historical_ef','kg_moved_to_task','kg_pct']:
            row[col+'_mean']=float(z[col].mean());row[col+'_sd']=float(z[col].std(ddof=1))
            row[col+'_mean_ci_halfwidth']=float(stats.t.ppf(.975,n-1)*z[col].std(ddof=1)/np.sqrt(n))
        row['delta_pp']=row['historical_ef_mean']-row['kg_moved_to_task_mean']
        desc.append(row)
    for col in ['historical_ef','kg_moved_to_task']:
        a=s.loc[s.group=='Low',col];b=s.loc[s.group=='High',col]
        n1,n2=len(a),len(b);v1,v2=a.var(ddof=1),b.var(ddof=1)
        diff=float(a.mean()-b.mean());se=float(np.sqrt(v1/n1+v2/n2))
        df=float((v1/n1+v2/n2)**2/((v1/n1)**2/(n1-1)+(v2/n2)**2/(n2-1)))
        t=diff/se;p=float(2*stats.t.sf(abs(t),df))
        independent=stats.ttest_ind(a,b,equal_var=False)
        assert np.isclose(t,independent.statistic) and np.isclose(p,independent.pvalue,rtol=1e-8,atol=0)
        pooled=np.sqrt(((n1-1)*v1+(n2-1)*v2)/(n1+n2-2))
        g=float((1-3/(4*(n1+n2)-9))*diff/pooled)
        gse=np.sqrt((n1+n2)/(n1*n2)+g*g/(2*(n1+n2-2)))
        tests.append({'variable':col,'n_low':n1,'n_high':n2,'mean_low':float(a.mean()),'sd_low':float(a.std()),'mean_high':float(b.mean()),'sd_high':float(b.std()),'difference_low_minus_high':diff,'difference_ci_low':diff-stats.t.ppf(.975,df)*se,'difference_ci_high':diff+stats.t.ppf(.975,df)*se,'t':t,'df':df,'p':p,'hedges_g':g,'g_ci_low':g-stats.norm.ppf(.975)*gse,'g_ci_high':g+stats.norm.ppf(.975)*gse})
    f=pd.read_csv(rev/'run04c_outputs/multiplicity_v3.csv')
    for col in ['historical_ef','kg_moved_to_task','kg_pct']:
        x=s[col];y=s.strict_accuracy_pct
        for method,func in [('pearson',stats.pearsonr),('spearman',stats.spearmanr)]:
            old=f[(f.variable==col)&(f.method==method)].iloc[0]
            assert np.isclose(func(x,y).statistic,old.stat,atol=1e-12)
    process_ratio=100*s.kg_count/s.process_count.replace(0,np.nan)
    prevalence={'mean_kg_share':float(s.kg_pct.mean()),'sd_kg_share':float(s.kg_pct.std()),'median_kg_share':float(s.kg_pct.median()),'kg_interactions':int(s.kg_count.sum()),'total_interactions':int(s.ai_frequency.sum()),'pooled_kg_share':float(100*s.kg_count.sum()/s.ai_frequency.sum()),'positive_process_users':int(process_ratio.notna().sum()),'mean_kg_within_process':float(process_ratio.mean()),'sd_kg_within_process':float(process_ratio.std()),'historical_process_count':int(s.process_count.sum()),'other_count_main':int(s.other_count.sum())}
    summary={'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__,'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'n':len(s),'cuts':[67.5,84.0],'quantiles_one_third_two_thirds':s.strict_accuracy_pct.quantile([1/3,2/3]).tolist(),'prevalence':prevalence,'tertiles':desc,'welch_low_minus_high':tests,'notes':['Fixed cuts, same groups for both mappings.','Student shares, not pooled proportions; process ratio uses positive-process users only.','Low-minus-high contrasts; unadjusted Welch tests; Hedges g uses pooled SD with small-sample correction.','Mean error bars in Figure 1 are 95% t intervals; scatter contains every student.','No bootstrap CIs regenerated; Table 2 uses existing run04b/run04c outputs.']}
    (out/'OR3_verified_statistics.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
    pd.DataFrame(desc).to_csv(out/'OR3_tertile_descriptives.csv',index=False)
    pd.DataFrame(tests).to_csv(out/'OR3_welch_comparisons.csv',index=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,'axes.labelsize':11,'pdf.fonttype':42})
    fig,axes=plt.subplots(2,2,figsize=(13.6,10),layout='constrained')
    for ax,col,color,title in [(axes[0,0],'historical_ef','#4477AA','(a) Historical mapping: KG in Process'),(axes[0,1],'kg_moved_to_task','#228833','(b) Alternative mapping: KG moved to Task')]:
        x=s[col].to_numpy();y=s.strict_accuracy_pct.to_numpy();lr=stats.linregress(x,y)
        ax.scatter(x,y,s=7,alpha=.10,c=color,edgecolors='none',rasterized=True)
        xx=np.array([0,100]);rr=stats.pearsonr(x,y).statistic
        ax.plot(xx,lr.intercept+lr.slope*xx,c='#CC3311',lw=1.8,label=f'Pearson r = {rr:+.3f}')
        ax.set(xlim=(-2,102),ylim=(-2,102),xlabel='Effective-feedback composite share (%)',ylabel='Strict problem-solving accuracy (%)',title=title)
        ax.legend(loc='lower left',framealpha=.95)
    x=np.arange(3);width=.34;ax=axes[1,0]
    for col,color,label,shift in [('historical_ef','#4477AA','Historical mapping',-width/2),('kg_moved_to_task','#228833','KG moved to Task',width/2)]:
        values=[d[col+'_mean'] for d in desc];errs=[d[col+'_mean_ci_halfwidth'] for d in desc]
        ax.bar(x+shift,values,width,yerr=errs,capsize=3,color=color,label=label,error_kw={'lw':1})
        for xx,v,e in zip(x+shift,values,errs):ax.text(xx,v+e+1.2,f'{v:.2f}',ha='center',fontsize=9)
    labels=['Low\n<67.5%\nn = 5,540','Medium\n67.5–84.0%\nn = 5,467','High\n>84.0%\nn = 5,382']
    ax.set(xticks=x,xticklabels=labels,ylim=(0,96),ylabel='Mean effective-feedback share (%)',title='(c) Composite shares by strict-accuracy group')
    ax.legend(loc='upper right',fontsize=9)
    ax=axes[1,1];values=[d['kg_pct_mean'] for d in desc];errs=[d['kg_pct_mean_ci_halfwidth'] for d in desc]
    ax.bar(x,values,.56,color='#EE7733',yerr=errs,capsize=3,error_kw={'lw':1})
    for xx,v,e in zip(x,values,errs):ax.text(xx,v+e+1.3,f'{v:.2f}',ha='center',fontsize=10)
    ax.set(xticks=x,xticklabels=labels,ylim=(0,75),ylabel='Mean KG Navigation share (%)',title='(d) Feature-level KG Navigation share\nPearson r = −0.107 with strict accuracy')
    for ax in axes.flat:
        ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
    fig.savefig(out/'OR3_Figure1_strict.png',dpi=300)
    fig.savefig(out/'OR3_Figure1_strict.pdf')
    plt.close(fig)
    print(json.dumps(summary,indent=2,ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]/'outputs');ap.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'outputs/figures')
    args=ap.parse_args();main(args.root.resolve(),args.out.resolve())
