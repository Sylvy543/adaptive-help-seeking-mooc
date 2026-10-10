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

# ===== 数据与统计量 =====
st = pd.read_csv(WORK/'revision_round2/run02_outputs/strict_student_model_data.csv')

def fisher_ci(r, n):
    z = np.arctanh(r); se = 1 / np.sqrt(n - 3); Z = 1.959963984540054
    return float(np.tanh(z - Z * se)), float(np.tanh(z + Z * se))

def fmt_apa(v, d=3):
    # APA 去零 + 真减号：+.008 / −.103
    s = f'{abs(v):.{d}f}'
    if s.startswith('0'):
        s = s[1:]
    return ('\u2212' if v < 0 else '+') + s

st['tertile'] = np.select([st.strict_accuracy_pct < 67.5, st.strict_accuracy_pct <= 84],
                          ['Low', 'Medium'], default='High')
ORDER = ['Low', 'Medium', 'High']
x_all = st.effective_feedback_pct.astype(float)
y_all = st.strict_accuracy_pct.astype(float)
r_agg, p_agg = sst.pearsonr(x_all, y_all)
ci_agg = fisher_ci(r_agg, len(st))

rows = []
for tn in ORDER:
    d = st[st.tertile == tn]
    r, p = sst.pearsonr(d.effective_feedback_pct, d.strict_accuracy_pct)
    lo, hi = fisher_ci(r, len(d))
    rows.append(dict(name=tn, n=len(d), r=r, lo=lo, hi=hi))
    print(f'{tn}: n={len(d)} r={r:+.4f} CI [{lo:+.4f}, {hi:+.4f}] p={p:.3f}')
print(f'Aggregate: r={r_agg:+.4f} CI [{ci_agg[0]:+.4f}, {ci_agg[1]:+.4f}]')

# ===== 画图（样式参数在这里改） =====
COLORS = {'Low': '#d62728', 'Medium': '#ff7f0e', 'High': '#2ca02c'}
AGG_COLOR = '#4d4d4d'
POINT_SIZE = 3; POINT_ALPHA = 0.08

fig, (ax, axb) = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={'width_ratios': [1.15, 1]})

# ---------- Panel (a)：散点 + 分层回归线 + 聚合虚线 ----------
for tn in ORDER:
    d = st[st.tertile == tn]
    ax.scatter(d.effective_feedback_pct, d.strict_accuracy_pct,
               s=POINT_SIZE, alpha=POINT_ALPHA, color=COLORS[tn], rasterized=True)
    xs = np.linspace(0, 100, 50)
    b, a = np.polyfit(d.effective_feedback_pct, d.strict_accuracy_pct, 1)
    r_t = rows[ORDER.index(tn)]['r']
    
    # 【修改点】：加入斜体 $r$
    ax.plot(xs, a + b * xs, color=COLORS[tn], lw=2.5,
            label=f"{tn} (T{ORDER.index(tn)+1}): $r$ = {fmt_apa(r_t)}")

b_agg, a_agg = np.polyfit(x_all, y_all, 1)
xs = np.linspace(0, 100, 50)

# 【修改点】：加入斜体 $r$
ax.plot(xs, a_agg + b_agg * xs, color='black', ls='--', lw=2, label=f'Aggregate: $r$ = {fmt_apa(r_agg)}')

ax.set_xlabel('Effective Feedback Usage (%)', fontsize=11)
ax.set_ylabel('Problem-Solving Accuracy (%)', fontsize=11)

# 【修改点】：去掉长标题，改为左上角悬空的 (a)
ax.text(-0.08, 1.04, '(a)', transform=ax.transAxes, fontsize=14, fontweight='bold', va='bottom')
ax.legend(loc='lower left', fontsize=10)
ax.set_xlim(-2, 102); ax.set_ylim(-2, 103)

# ---------- Panel (b)：聚合 vs 组内柱状对比 ----------
names = ['Aggregate', 'Low (T1)', 'Medium (T2)', 'High (T3)']
rs   = [r_agg] + [r['r'] for r in rows]
los  = [ci_agg[0]] + [r['lo'] for r in rows]
his  = [ci_agg[1]] + [r['hi'] for r in rows]

# 【修改点】：将 N 和 n 斜体化
nlabs = [r'$N$ = 16,389'] + [f"$n$ = {r['n']:,}" for r in rows]
cols = [AGG_COLOR] + [COLORS[t] for t in ORDER]
xpos = np.arange(4)

# 误差线（总样本的 CI 也在这里正确应用了）
err = [[r - l for r, l in zip(rs, los)], [h - r for r, h in zip(rs, his)]]
axb.bar(xpos, rs, yerr=err, capsize=5, color=cols, edgecolor='black',
        error_kw=dict(ecolor='black', lw=1.5))

for i, r in enumerate(rs):
    # fmt_apa 已经自带 3 位小数、去零化和真减号功能
    if r >= 0:
        axb.text(i, his[i] + 0.005, fmt_apa(r), ha='center', va='bottom', fontsize=11, fontweight='bold')
    else:
        axb.text(i, los[i] - 0.005, fmt_apa(r), ha='center', va='top', fontsize=11, fontweight='bold')

axb.axhline(0, color='black', lw=0.8)
axb.set_xticks(xpos)
axb.set_xticklabels([f'{a}\n({b})' for a, b in zip(names, nlabs)], fontsize=10)

# 【修改点】：斜体 $r$，并把小写英文字母 x 换成数学乘号 ×
axb.set_ylabel('Pearson $r$ (EF% × Accuracy)', fontsize=11)

# 【修改点】：去掉长标题，改为左上角悬空的 (b)
axb.text(-0.08, 1.04, '(b)', transform=axb.transAxes, fontsize=14, fontweight='bold', va='bottom')

axb.set_ylim(-0.16, 0.06)
axb.grid(axis='y', alpha=0.3)

fig.tight_layout()


# ===== 保存 =====
fig.savefig(FIGOUT/'Figure4_redraw.png', dpi=600, bbox_inches='tight')
fig.savefig(FIGOUT/'Figure4_redraw.pdf', bbox_inches='tight')
print('saved')


