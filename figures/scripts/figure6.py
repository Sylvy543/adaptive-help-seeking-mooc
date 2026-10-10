from pathlib import Path
import os
REPO=Path(__file__).resolve().parents[2]
WORK=Path(os.environ.get('REPRO_WORK',str(REPO/'outputs')))
FIGOUT=WORK/'figures';FIGOUT.mkdir(parents=True,exist_ok=True)
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt

BASE = str(WORK/'revision_round2/run02_outputs')

def fmt_apa(v, d=2):
    s = f'{abs(v):.{d}f}'
    if s.startswith('0'):
        s = s[1:]
    return ('\u2212' if v < 0 else '+') + s

# ---- panel (a)：两个模型的五 AI 项系数与 CI ----
mc = pd.read_csv(f'{BASE}/model_coefficients.csv')
TERMS = [('kg_pct10', 'KG Navigation share'),
         ('other_process_pct10', 'Other Process share'),
         ('task_pct_neutral10', 'Task-feature share'),
         ('selfreg_pct_neutral10', 'Self-Regulation share'),
         ('log_ai_frequency', 'log AI frequency')]
MODELS = [('course_ols_composition', 'OLS (no random intercepts; student-clustered SEs)'),
          ('course_mixed_crossed_user_course', 'Crossed model (1|user) + (1|course), REML')]
coef = {}
for mdl, label in MODELS:
    for term, tname in TERMS:
        r = mc[(mc.model == mdl) & (mc.term == term)].iloc[0]
        coef[(label, tname)] = dict(b=r.estimate, lo=r.ci_low, hi=r.ci_high, p=r.p)
        print(f'{label[:12]:12} {tname:22} b={r.estimate:+.3f} [{r.ci_low:+.3f}, {r.ci_high:+.3f}] p={r.p:.4f}')

# ---- panel (b)：方差分解（读 summary，现场算占比） ----
summ = json.load(open(f'{BASE}/run02_summary.json'))
crossed = [m for m in summ['models'] if m['model'] == 'course_mixed_crossed_user_course'][0]
vc = crossed['variance_components']; resid = crossed['residual_variance']
tot = vc['course'] + vc['user'] + resid
shares = {'Course': 100 * vc['course'] / tot, 'Student': 100 * vc['user'] / tot, 'Residual': 100 * resid / tot}
print('variance shares:', {k: round(v, 1) for k, v in shares.items()})

# ===== 画图（样式参数在这里改） =====
MODEL_COLOR = {MODELS[0][1]: '#888888', MODELS[1][1]: '#1f77b4'}
MODEL_MARKER = {MODELS[0][1]: 's', MODELS[1][1]: 'o'}
DODGE = 0.16

fig, (ax, axb) = plt.subplots(1, 2, figsize=(14, 5.8), gridspec_kw={'width_ratios': [1.5, 1]})

# 【新增】：专门用于回归系数的格式化函数（保留前导 0，使用数学真减号）
def fmt_coef(v, d=2):
    s = f'{abs(v):.{d}f}'
    return ('\u2212' if v < 0 else '+') + s

# ---------- (a) 系数森林图 ----------
tnames = [t for _, t in TERMS]
ypos = np.arange(len(tnames))[::-1]   # 第一个术语在最上
for k, (mdl, label) in enumerate(MODELS):
    bs  = [coef[(label, t)]['b'] for t in tnames]
    los = [coef[(label, t)]['lo'] for t in tnames]
    his = [coef[(label, t)]['hi'] for t in tnames]
    yy = ypos + (k - 0.5) * 2 * DODGE + DODGE
    ax.errorbar(bs, yy, xerr=[np.array(bs) - np.array(los), np.array(his) - np.array(bs)],
                fmt=MODEL_MARKER[label], color=MODEL_COLOR[label], ecolor=MODEL_COLOR[label],
                capsize=4, ms=7, lw=1.8, label=label)
    for b, y, t in zip(bs, yy, tnames):
        # 【修改点 1】：使用新函数，保留前导零
        ax.text(b, y + 0.12, fmt_coef(b), ha='center', va='bottom', fontsize=9.5,
                fontweight='bold', color=MODEL_COLOR[label])
        
ax.axvline(0, color='black', lw=0.8)
ax.set_yticks(ypos)
ax.set_yticklabels(tnames, fontsize=10)

# 【修改点 2】：确保标签中的 b 呈现数学斜体
ax.set_xlabel('Coefficient $b$ per 10-point share increase\n(log AI frequency per 1 log unit)', fontsize=11)
ax.set_ylim(-0.6, len(tnames) - 0.1)

# 【修改点 3】：将图例移到绝对空旷的左上角，彻底解决遮挡问题
ax.legend(loc='upper left', fontsize=9.5, edgecolor='gray', borderpad=0.4, labelspacing=0.4)
ax.grid(axis='x', alpha=0.3)
ax.text(-0.06, 1.04, '(a)', transform=ax.transAxes, fontsize=14, fontweight='bold', va='bottom')

# ---------- (b) 方差分解 ----------
parts = ['Course', 'Student', 'Residual']
pcolor = {'Course': '#1f77b4', 'Student': '#9467bd', 'Residual': '#bbbbbb'}
left = 0
for p in parts:
    v = shares[p]
    axb.barh([0], [v], left=left, color=pcolor[p], edgecolor='black', height=0.45)
    axb.text(left + v / 2, 0, f'{p}\n{v:.1f}%', ha='center', va='center', fontsize=11,
             fontweight='bold', color='white' if p != 'Residual' else 'black')
    left += v
axb.set_xlim(0, 100)
axb.set_xlabel('Share of estimated variance components (%)', fontsize=11)
axb.set_yticks([])
axb.set_ylim(-0.5, 0.5)
axb.text(-0.06, 1.04, '(b)', transform=axb.transAxes, fontsize=14, fontweight='bold', va='bottom')

fig.tight_layout()


# ===== 保存 =====
fig.savefig(FIGOUT/'Figure6_redraw.png', dpi=600, bbox_inches='tight')
fig.savefig(FIGOUT/'Figure6_redraw.pdf', bbox_inches='tight')
print('saved')

