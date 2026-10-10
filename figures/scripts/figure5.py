from pathlib import Path
import os
REPO=Path(__file__).resolve().parents[2]
WORK=Path(os.environ.get('REPRO_WORK',str(REPO/'outputs')))
FIGOUT=WORK/'figures';FIGOUT.mkdir(parents=True,exist_ok=True)
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats as sst

st = pd.read_csv(WORK/'revision_round2/run02_outputs/strict_student_model_data.csv')

def fisher_ci(r, n):
    z = np.arctanh(r); se = 1 / np.sqrt(n - 3); Z = 1.959963984540054
    return float(np.tanh(z - Z * se)), float(np.tanh(z + Z * se))

def fmt_apa(v, d=3):
    s = f'{abs(v):.{d}f}'
    if s.startswith('0'):
        s = s[1:]
    return ('\u2212' if v < 0 else '+') + s

st['selfreg_pct_hist'] = 100 * st.self_reg_count / st.ai_frequency
st['self_pct'] = 100 * st.self_count_neutral / st.ai_frequency
st['tertile'] = np.select([st.strict_accuracy_pct < 67.5, st.strict_accuracy_pct <= 84],
                          ['Low', 'Medium'], default='High')
ORDER = ['Low', 'Medium', 'High']

# ---- panel (a)/(d) 的相关 ----
CATS = [('kg_pct', 'KG Navigation'), ('other_process_pct', 'Other Process'),
        ('task_pct_neutral', 'Task-level'), ('selfreg_pct_hist', 'Self-Regulation'),
        ('self_pct', 'Self-level')]
corr = {}
for col, name in CATS:
    r, p = sst.pearsonr(st[col], st.strict_accuracy_pct)
    lo, hi = fisher_ci(r, len(st))
    corr[name] = dict(r=r, lo=lo, hi=hi, p=p)
    print(f'{name}: r={r:+.4f} CI [{lo:+.4f}, {hi:+.4f}] p={p:.2e}')
r_ef, p_ef = sst.pearsonr(st.effective_feedback_pct, st.strict_accuracy_pct)
print(f'Aggregate EF: r={r_ef:+.4f}')

# ---- panel (b) 的分层均值 ----
tmeans = {name: [st[st.tertile == t][col].mean() for t in ORDER] for col, name in CATS}
for name, v in tmeans.items():
    print(name, [f'{x:.1f}' for x in v])

# ---- panel (c) 的 KG 占 process 比分布 ----
proc_tot = st.kg_count + st.other_process_count
dproc = st[proc_tot > 0]
kg_share = 100 * dproc.kg_count / proc_tot[proc_tot > 0]
print(f'panel(c): n={len(dproc)}, mean={kg_share.mean():.1f}%, median={kg_share.median():.1f}%')

# ===== 画图（样式参数在这里改） =====
CAT_COLOR = {'KG Navigation': '#d62728', 'Other Process': '#2ca02c', 'Task-level': '#1f77b4',
             'Self-Regulation': '#ff7f0e', 'Self-level': '#9467bd'}
T_COLOR = {'Low': '#d62728', 'Medium': '#ff7f0e', 'High': '#2ca02c'}

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# ---------- (a) 各类别与准确率的相关 ----------
ax = axes[0, 0]
names = [n for _, n in CATS]
rs = [corr[n]['r'] for n in names]
err = [[corr[n]['r'] - corr[n]['lo'] for n in names], [corr[n]['hi'] - corr[n]['r'] for n in names]]
xp = np.arange(len(names))
ax.bar(xp, rs, yerr=err, capsize=5, color=[CAT_COLOR[n] for n in names], edgecolor='black',
       error_kw=dict(ecolor='black', lw=1.5))
for i, n in enumerate(names):
    r = corr[n]['r']
    if r >= 0:
        ax.text(i, corr[n]['hi'] + 0.006, fmt_apa(r), ha='center', va='bottom', fontsize=11, fontweight='bold')
    else:
        ax.text(i, corr[n]['lo'] - 0.006, fmt_apa(r), ha='center', va='top', fontsize=11, fontweight='bold')
ax.axhline(0, color='black', lw=0.8)
ax.set_xticks(xp)
ax.set_xticklabels([n.replace(' ', '\n') for n in names], fontsize=10)

ax.set_ylabel('Pearson $r$ (% usage × Accuracy)', fontsize=11)
ax.text(-0.08, 1.04, '(a)', transform=ax.transAxes, fontsize=14, fontweight='bold', va='bottom')
ax.text(0.03, 0.96, f'$N$ = 16,389\n(error bars = 95% CI)', transform=ax.transAxes, 
        va='top', fontsize=10, bbox=dict(boxstyle='round', fc='white', ec='gray', alpha=0.9))

ax.set_ylim(-0.15, 0.15); ax.grid(axis='y', alpha=0.3)

# ---------- (b) 三层 × 类别均值 ----------
ax = axes[0, 1]
width = 0.16
for j, n in enumerate(names):
    ax.bar(np.arange(3) + (j - 2) * width, tmeans[n], width, label=n,
           color=CAT_COLOR[n], edgecolor='black')
ax.set_xticks(range(3))

ns = [len(st[st.tertile == t]) for t in ORDER]
ax.set_xticklabels([f'{t} (T{i+1})\n($n$ = {n:,})' for i, (t, n) in zip(range(3), zip(ORDER, ns))], fontsize=10)

ax.set_ylabel('Mean % of AI Interactions', fontsize=11)
ax.text(-0.08, 1.04, '(b)', transform=ax.transAxes, fontsize=14, fontweight='bold', va='bottom')
ax.legend(fontsize=9)
ax.grid(axis='y', alpha=0.3)

# ---------- (c) KG 占个人 process 使用的分布 ----------
ax = axes[1, 0]
ax.hist(kg_share, bins=50, color='#d62728', edgecolor='black', alpha=0.85)
ax.axvline(kg_share.mean(), color='black', ls='--', lw=2, label=f'Mean: {kg_share.mean():.1f}%')
ax.axvline(kg_share.median(), color='black', ls=':', lw=2, label=f'Median: {kg_share.median():.1f}%')

ax.set_xlabel("KG Navigation as % of User's Process-level Usage", fontsize=11)
ax.set_ylabel('Number of Students', fontsize=11)

ax.text(-0.08, 1.04, '(c)', transform=ax.transAxes, fontsize=14, fontweight='bold', va='bottom')

# 【左框变大】：加入 pad=0.5 增加白边，linespacing=1.3 拉开两行文字的间距
ax.text(0.03, 0.963, f'$n$ = {len(dproc):,} students with\n$\geq$ 1 process interaction', transform=ax.transAxes, 
        va='top', fontsize=10, linespacing=1.3,
        bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='gray', alpha=0.9))

# 【右框变小且对齐】：加入 borderpad=0.4 减小白边，labelspacing=0.4 缩小图例行距，并让纵坐标 0.97 与左框严格对齐
ax.legend(loc='upper left', bbox_to_anchor=(0.35, 0.995), fontsize=10, edgecolor='gray',
          borderpad=0.4, labelspacing=0.4)

# ---------- (d) 聚合相关分解 ----------
ax = axes[1, 1]
d_names = ['Aggregate\n"Effective\nFeedback"', 'KG\nonly', 'Other Process\nonly', 'Self-Reg\nonly']
d_vals = [r_ef, corr['KG Navigation']['r'], corr['Other Process']['r'], corr['Self-Regulation']['r']]
d_cols = ['#4d4d4d', CAT_COLOR['KG Navigation'], CAT_COLOR['Other Process'], CAT_COLOR['Self-Regulation']]
xp = np.arange(4)
ax.bar(xp, d_vals, color=d_cols, edgecolor='black')
for i, v in enumerate(d_vals):
    ax.text(i, v + (0.003 if v >= 0 else -0.003), fmt_apa(v),
            ha='center', va='bottom' if v >= 0 else 'top', fontsize=11, fontweight='bold')
ax.axhline(0, color='black', lw=0.8)
ax.set_xticks(xp); ax.set_xticklabels(d_names, fontsize=10)

ax.set_ylabel('Pearson $r$ (% usage × Accuracy)', fontsize=11)
ax.text(-0.08, 1.04, '(d)', transform=ax.transAxes, fontsize=14, fontweight='bold', va='bottom')

ax.set_ylim(-0.12, 0.07); ax.grid(axis='y', alpha=0.3)

fig.tight_layout()


# ===== 保存 =====
fig.savefig(FIGOUT/'Figure5_redraw.png', dpi=600, bbox_inches='tight')
fig.savefig(FIGOUT/'Figure5_redraw.pdf', bbox_inches='tight')
print('saved')


