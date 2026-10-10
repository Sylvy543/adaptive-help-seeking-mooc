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
labels = ['1', '2–5', '6–10', '11–20', '21–50', '51–100', '>100']
st['g7'] = pd.cut(st.ai_frequency, [0, 1, 5, 10, 20, 50, 100, 10**9], labels=labels)
groups = [st[st.g7 == g] for g in labels]
ns = [len(g) for g in groups]

def group_stats(col):
    m = [g[col].mean() for g in groups]
    se = [g[col].std(ddof=1) / np.sqrt(len(g)) for g in groups]   # ±1 SE（仅 panel a 用）
    return m, se

acc_m, acc_se = group_stats('strict_accuracy_pct')
ef_m, _ = group_stats('effective_feedback_pct')
overall = st.strict_accuracy_pct.mean()
F, p = sst.f_oneway(*[g.strict_accuracy_pct for g in groups])
eta2 = sum(len(g) * (g.strict_accuracy_pct.mean() - overall)**2 for g in groups) / ((st.strict_accuracy_pct - overall)**2).sum()

print(f'panel(a) 核对: F={F:.2f} p={p:.3f} eta2={eta2:.5f} overall={overall:.2f}')
print('acc means:', [f'{m:.1f}' for m in acc_m])
print('EF  means:', [f'{m:.1f}' for m in ef_m], '（应与原图 75.8/70.1/68.2/66.7/64.8/60.4/58.3 一致）')

# 有限值断言。运行警告定位：scipy 1.16 的 xp.vecdot 在 pearsonr/f_oneway 中对 0–100 量纲数组
# 会报 overflow RuntimeWarning，属数值显示性质；此处显式断言统计量有限且范围合法，不屏蔽警告。
# F/p/η² 已与 run08 独立归档输出一致（F=1.26, p=.273, η²=.00046）。
assert np.isfinite([F, p, eta2, overall] + list(acc_m) + list(acc_se) + list(ef_m)).all()
assert F >= 0 and 0 <= p <= 1 and 0 <= eta2 <= 1
print('有限值断言通过')

# ===== 画图（样式参数在这里改） =====
HATCHES = ['', '///', 'xxx', '...', '\\\\\\\\', 'ooo', '+++']
GRAYS   = ['#d0d0d0', '#b8b8b8', '#a8a8a8', '#989898', '#888888', '#606060', '#484848']
BLUES   = [plt.cm.Blues(v) for v in np.linspace(0.35, 0.95, 7)]   # panel b 蓝色渐变（同原图）
COLOR_MEAN = '#C07000'

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# 辅助函数：APA 7 格式去前导零 (适用于 p 值和 η²，因为它们的绝对值不超过1)
def format_no_leading_zero(val, decimals=3):
    s = f"{val:.{decimals}f}"
    if s.startswith("0."):
        return s[1:]
    elif s.startswith("-0."):
        return "-" + s[2:]
    return s

p_str = format_no_leading_zero(p, 3)
eta2_str = format_no_leading_zero(eta2, 4)

# ---------- Panel (a)：准确率，灰度柱 + 误差线 ----------
ax = axes[0]
for i, (m, se, n) in enumerate(zip(acc_m, acc_se, ns)):
    ax.bar(i, m, yerr=se, capsize=4, color=GRAYS[i], hatch=HATCHES[i],
           edgecolor='black', error_kw=dict(ecolor='black', lw=1.5))
    ax.text(i, m + se + 1.5, f'{m:.1f}%', ha='center', fontsize=10, fontweight='bold')
    ax.text(i, 2.0, f'$n$ = {n:,}', ha='center', va='bottom', fontsize=8, rotation=90, color='#444444')

ax.axhline(overall, color=COLOR_MEAN, ls='--', lw=2, label=f'Overall mean ({overall:.1f}%)')

anova_text = f'ANOVA: $F$(6, {len(st)-7}) = {F:.2f}\n$p$ = {p_str} (ns)\nη² = {eta2_str}'
ax.text(0.02, 0.98, anova_text,
        transform=ax.transAxes, va='top', fontsize=10,
        bbox=dict(boxstyle='round', fc='white', ec='gray', alpha=0.9))

ax.set_xticks(range(7)); ax.set_xticklabels(labels)
ax.set_xlabel('AI Usage Frequency Group', fontsize=11)
ax.set_ylabel('Mean Problem Accuracy (%)', fontsize=11)
ax.set_ylim(0, 95)

# 【修改点】：去掉 title，改为左上角悬空的 (a) 标号，完美对齐 Figure 2 风格
ax.text(-0.06, 1.03, '(a)', transform=ax.transAxes, fontsize=14, fontweight='bold', va='bottom')
ax.legend(loc='upper right', fontsize=10)

# ---------- Panel (b)：EF%，蓝色渐变柱，无误差线，y 从 0 开始 ----------
ax = axes[1]
for i, (m, n) in enumerate(zip(ef_m, ns)):
    ax.bar(i, m, color=BLUES[i], hatch=HATCHES[i], edgecolor='black')
    ax.text(i, m + 1.5, f'{m:.1f}%', ha='center', fontsize=10, fontweight='bold')
    ax.text(i, 2.0, f'$n$ = {n:,}', ha='center', va='bottom', fontsize=8, rotation=90, color='#444444')

ax.set_xticks(range(7)); ax.set_xticklabels(labels)
ax.set_xlabel('AI Usage Frequency Group', fontsize=11)
ax.set_ylabel('Mean Effective Feedback (%)', fontsize=11)
ax.set_ylim(0, 95)

# 【修改点】：去掉 title，改为左上角悬空的 (b) 标号，完美对齐 Figure 2 风格
ax.text(-0.06, 1.03, '(b)', transform=ax.transAxes, fontsize=14, fontweight='bold', va='bottom')

fig.tight_layout()


# ===== 保存 =====
fig.savefig(FIGOUT/'Figure3_redraw.png', dpi=600, bbox_inches='tight')
fig.savefig(FIGOUT/'Figure3_redraw.pdf', bbox_inches='tight')
print('saved')


