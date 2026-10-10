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

def apa_num(v, d=3):
    """APA 去零 + 真减号，不带 +/- 号：.006 / −.103"""
    s = f'{abs(v):.{d}f}'
    if s.startswith('0'):
        s = s[1:]
    return ('\u2212' if v < 0 else '') + s

def fmt_r(r):
    return f'$r$ = {apa_num(r, 3)}'

def fmt_p(p):
    return '$p$ < .001' if p < .001 else f'$p$ = {apa_num(p, 2)}'

# ---- (a) 频率 × 准确率 ----
xa = st.ai_frequency.astype(float)
ya = st.strict_accuracy_pct.astype(float)
r_a, p_a = sst.pearsonr(xa, ya)                     # 全样本：r=.0063, p=.419
mean_acc = ya.mean()                                 # 73.34
slope_a, intercept_a = np.polyfit(xa, ya, 1)         # 趋势线拟合全样本
n_a = len(st)
resid_se = np.sqrt(np.sum((ya - np.polyval([slope_a, intercept_a], xa))**2) / (n_a - 2))
xs = np.linspace(0, 100, 200)
ys = intercept_a + slope_a * xs
se_line = resid_se * np.sqrt(1/n_a + (xs - xa.mean())**2 / np.sum((xa - xa.mean())**2))
tcrit = sst.t.ppf(0.975, n_a - 2)
print(f'(a) r={r_a:.4f} p={p_a:.4f} mean={mean_acc:.2f}')

# ---- (b) EF 占比 × 准确率 ----
xb = st.effective_feedback_pct.astype(float)
r_b, p_b = sst.pearsonr(xb, ya)                     # r=−.1027
slope_b, intercept_b = np.polyfit(xb, ya, 1)
print(f'(b) r={r_b:.4f} p={p_b:.2e} slope={slope_b:.4f}')

# ===== 画图（样式参数在这里改） =====
GRIDSIZE = 40
COLOR_TREND = '#C07000'
COLOR_BAND = '#E8A33D'
POINT_SIZE = 5
POINT_ALPHA = 0.25

fig, (ax, axb) = plt.subplots(1, 2, figsize=(14, 5.5))

# ---------- (a) hexbin ----------
d = st[st.ai_frequency <= 100]
hb = ax.hexbin(d.ai_frequency, d.strict_accuracy_pct, gridsize=GRIDSIZE, cmap='gray_r',
               mincnt=1, extent=(0, 100, 0, 100))
cb = fig.colorbar(hb, ax=ax)
cb.set_label('Number of Students', fontsize=11)
ax.fill_between(xs, ys - tcrit*se_line, ys + tcrit*se_line, color=COLOR_BAND, alpha=0.35, label='95% CI')
ax.plot(xs, ys, color=COLOR_TREND, lw=2,
        label=f'Linear trend ({fmt_r(r_a)}, {fmt_p(p_a)})')
ax.axhline(mean_acc, color='black', ls=':', lw=1.5, label=f'Mean accuracy ({mean_acc:.1f}%)')
ax.text(0.02, 0.97, f'$N$ = 16,389 students\n(AI frequency ≤100 shown)', transform=ax.transAxes,
        va='top', fontsize=10, linespacing=1.3,
        bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='gray', alpha=0.9))
ax.set_xlabel('AI Usage Frequency (number of interactions)', fontsize=11)
ax.set_ylabel('Problem-Solving Accuracy (%)', fontsize=11)
ax.set_xlim(-2, 102); ax.set_ylim(-2, 102)
ax.legend(loc='lower right', fontsize=9.5, edgecolor='gray', borderpad=0.4, labelspacing=0.4)
ax.text(-0.08, 1.04, '(a)', transform=ax.transAxes, fontsize=14, fontweight='bold', va='bottom')

# ---------- (b) EF 散点 ----------
sc = axb.scatter(xb, ya, c=np.log1p(st.ai_frequency), cmap='plasma',
                 s=POINT_SIZE, alpha=POINT_ALPHA, rasterized=True)
cb2 = fig.colorbar(sc, ax=axb)
cb2.set_label('log (AI Frequency)', fontsize=11)
xs2 = np.linspace(0, 100, 100)
axb.plot(xs2, intercept_b + slope_b * xs2, color='#C07000', ls='--', lw=2,
         label=f'Trend ({fmt_r(r_b)}, {fmt_p(p_b)})')
axb.axvline(70, color='#2a9d8f', ls='-.', lw=2, label='High-EF-share threshold (70%)')
axb.text(0.98, 0.03, '$N$ = 16,389', transform=axb.transAxes, ha='right', va='bottom',
         fontsize=10, bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='gray', alpha=0.9))
axb.set_xlabel('Effective Feedback Percentage (%)', fontsize=11)
axb.set_ylabel('Problem-Solving Accuracy (%)', fontsize=11)
axb.set_xlim(-2, 102); axb.set_ylim(-2, 103)
axb.legend(loc='lower left', fontsize=9.5, edgecolor='gray', borderpad=0.4, labelspacing=0.4)
axb.text(-0.08, 1.04, '(b)', transform=axb.transAxes, fontsize=14, fontweight='bold', va='bottom')

fig.tight_layout()


# ===== 保存 =====
fig.savefig(FIGOUT/'Figure2_redraw.png', dpi=600, bbox_inches='tight')
fig.savefig(FIGOUT/'Figure2_redraw.pdf', bbox_inches='tight')
print('saved')


