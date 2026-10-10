from pathlib import Path
import os
REPO=Path(__file__).resolve().parents[2]
WORK=Path(os.environ.get('REPRO_WORK',str(REPO/'outputs')))
FIGOUT=WORK/'figures';FIGOUT.mkdir(parents=True,exist_ok=True)
import matplotlib
matplotlib.use('Agg')
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from pathlib import Path

# ===== 数据：16 功能 × Coder1 × Coder2 × 裁决后最终类别 =====
ROWS = [
    ('Knowledge Graph Click',            'Process (FP)', 'Process (FP)', None),
    ('Preset Q&A',                       'Task (FT)',    'Task (FT)',    None),
    ('From MOOCCube (Knowledge Base)',   'Task (FT)',    'Task (FT)',    None),
    ('From Turing Bot (General Chatbot)','Self-Regulation (FR)', 'Self (FS)', 'Self (FS)'),
    ('From Baidu (Search Engine)',       'Task (FT)',    'Task (FT)',    None),
    ('From Baike (Encyclopedia)',        'Task (FT)',    'Task (FT)',    None),
    ('Poetry Composition',               'Other / Not Applicable', 'Other / Not Applicable', None),
    ('From FAQ (Platform Help)',         'Other / Not Applicable', 'Other / Not Applicable', None),
    ('From Aminer (Academic Search)',    'Task (FT)',    'Process (FP)', 'Process (FP)'),
    ('TA Answer Browser',                'Other / Not Applicable', 'Task (FT)', 'Other / Not Applicable'),
    ('Pop-up Reflection Question',       'Process (FP)', 'Process (FP)', None),
    ('System Cannot Answer',             'Other / Not Applicable', 'Other / Not Applicable', None),
    ('Ask TA (Human)',                   'Other / Not Applicable', 'Other / Not Applicable', None),
    ('Arithmetic Calculator',            'Other / Not Applicable', 'Other / Not Applicable', None),
    ('Inappropriate Input (Filtered)',   'Other / Not Applicable', 'Other / Not Applicable', None),
    ('From Course Information',          'Other / Not Applicable', 'Other / Not Applicable', None),
]
df = pd.DataFrame(ROWS, columns=['en', 'c1', 'c2', 'adj'])
raw = pd.read_csv(REPO/'materials/irr_side_by_side.csv').set_index('Feature (EN)')
assert df.en.is_unique and set(df.en)==set(raw.index)
assert list(df.c1)==list(raw.loc[df.en,'Coder 1'])
assert list(df.c2)==list(raw.loc[df.en,'Coder 2'])
df['agree'] = df.c1 == df.c2
df['final'] = np.where(df.agree, df.c1, df.adj)
assert len(df) == 16 and df.agree.sum() == 13 and df.final.notna().all()

# κ 现场复算
def kappa(c1, c2):
    n = len(c1)
    po = (np.asarray(c1) == np.asarray(c2)).mean()
    pe = sum((np.asarray(c1) == c).mean() * (np.asarray(c2) == c).mean() for c in set(c1) | set(c2))
    return (po - pe) / (1 - pe)
K = kappa(df.c1, df.c2)

# ===== 样式参数 =====
CAT_ORDER = ['Task (FT)', 'Process (FP)', 'Self-Regulation (FR)', 'Self (FS)', 'Other / Not Applicable']
CAT_SHORT = {'Task (FT)': 'Task', 'Process (FP)': 'Process',
             'Self-Regulation (FR)': 'Self-Reg', 'Self (FS)': 'Self',
             'Other / Not Applicable': 'Other'}
CAT_COLOR = {'Task (FT)': '#1f77b4', 'Process (FP)': '#d62728',
             'Self-Regulation (FR)': '#ff7f0e', 'Self (FS)': '#9467bd',
             'Other / Not Applicable': '#999999'}   
FIGSIZE   = (12.0, 11.5)
FONT_BASE = 13
FONT_ROW  = 13      
FONT_CELL = 11.5    

plt.rcParams.update({'font.size': FONT_BASE, 'font.family': 'DejaVu Sans'})
cat_rank = {c: i for i, c in enumerate(CAT_ORDER)}
d = df.assign(rank=df.final.map(cat_rank)).sort_values(['rank', 'en'], ascending=[True, False]).reset_index(drop=True)

fig = plt.figure(figsize=FIGSIZE)

# 【修改点 1】：拆分为两个独立的 GridSpec。上图左边留白，下图铺满全宽。
gs_top = fig.add_gridspec(1, 1, left=0.35, right=0.97, top=0.90, bottom=0.32)
gs_bot = fig.add_gridspec(1, 1, left=0.05, right=0.97, top=0.18, bottom=0.08)

# ---------- Panel (a): 分类矩阵热图 ----------
ax = fig.add_subplot(gs_top[0])

y_positions = np.zeros(len(d))
current_y = 0.0
gap = 0.35
for i in range(len(d)-1, -1, -1):
    y_positions[i] = current_y
    if i > 0 and d.loc[i, 'rank'] != d.loc[i-1, 'rank']:
        current_y += 1.0 + gap
    else:
        current_y += 1.0

for i, r in d.iterrows():
    for j, col in enumerate(['c1', 'c2', 'final']):
        cat = r[col]
        disagree = col != 'final' and not r.agree
        ax.add_patch(Rectangle((j, y_positions[i]), 1, 1, facecolor=CAT_COLOR[cat],
                               edgecolor='black' if disagree else 'white',
                               lw=2.4 if disagree else 0.8, zorder=2))
        label = CAT_SHORT[cat] + (' *' if col == 'final' and not r.agree else '')
        ax.text(j+0.5, y_positions[i]+0.5, label, ha='center', va='center',
                fontsize=FONT_CELL,
                color='white' if cat != 'Other / Not Applicable' else 'black',
                fontweight='bold' if disagree else 'normal', zorder=3)
    ax.text(-0.12, y_positions[i]+0.5, r.en, ha='right', va='center', fontsize=FONT_ROW)

ax.set_xlim(0, 3)
ax.set_ylim(0, current_y)
ax.set_xticks([0.5, 1.5, 2.5])
ax.set_xticklabels(['Coder 1', 'Coder 2', 'Consensus\n(Coder Adjudication)'], fontsize=13.5)
ax.set_yticks([])
for s in ('top', 'right', 'left', 'bottom'): 
    ax.spines[s].set_visible(False)
ax.tick_params(length=0)

# 【修改点 2】：去掉长标题，使用全局绝对坐标放置悬空的 (a) 和 图例
fig.text(0.02, 0.95, '(a)', fontsize=16, fontweight='bold', va='top')
fig.legend(handles=[Patch(facecolor=CAT_COLOR[c], edgecolor='none',
                          label=CAT_SHORT[c] if c != 'Other / Not Applicable' else 'Other / N.A.')
                    for c in CAT_ORDER],
           loc='upper left', bbox_to_anchor=(0.35, 0.95), ncol=5, frameon=False,
           fontsize=12, columnspacing=1.2, handlelength=1.4)

# 【优化】：去掉多余换行符，使用全局绝对定位 (fig.text) 让说明文字横贯全图
note_text = (
    "* adjudicated after documented disagreement; bold border marks disagreeing coder cells.\n"
    "Note: This panel reflects the raw coder consensus for IRR purposes. See Appendix A for subsequent author-level mapping of 'Other' items."
)
fig.text(0.05, 0.29, note_text, fontsize=11, color='#555555', ha='left', va='top', linespacing=1.5)

# ---------- Panel (b): κ vs Landis–Koch 标尺 ----------
axb = fig.add_subplot(gs_bot[0])
bands = [(0.0, 0.20, 'Slight'), (0.20, 0.40, 'Fair'), (0.40, 0.60, 'Moderate'),
         (0.60, 0.80, 'Substantial'), (0.80, 1.00, 'Almost perfect')]
for k, (lo, hi, lab) in enumerate(bands):
    axb.axvspan(lo, hi, color='#DDDDDD' if k % 2 else '#EFEFEF', zorder=0)
    axb.text((lo+hi)/2, 0.86, lab, ha='center', va='center', fontsize=11, color='#666666')
axb.axvline(K, ymin=0.0, ymax=0.72, color='#D55E00', lw=3.5, zorder=3)
axb.scatter([K], [0.45], s=130, color='#D55E00', zorder=4)

# 【修改点 3】：斜体 kappa，APA 7 去零化；CI 从 run06 归档输出读取，不手填
import json as _json
_r06 = _json.load(open(WORK/'revision_round2/run06_outputs/run06_summary.json'))
CI_LO, CI_HI = _r06['kappa_boot_ci']   # bootstrap B=10,000, seed=20260921
assert abs(_r06['kappa_recomputed'] - K) < 0.0005, 'run06 κ 与现场复算不一致'
def _apa(v, d=3):
    s = f'{abs(v):.{d}f}'
    if s.startswith('0'):
        s = s[1:]
    return s
K_str = _apa(K)
ci_str = f'[{_apa(CI_LO)}, {CI_HI:.3f}]'
kappa_str = f"Cohen's κ = {K_str}, 95% CI {ci_str}\n(13/16 agreements)"

# 【修改点 4】：因为画布拉宽了，左边空间非常大，这里的排版更加舒展大气
axb.text(K - 0.015, 0.45, kappa_str, 
         fontsize=13.5, fontweight='bold', color='#9E3D00',
         ha='right', va='center', linespacing=1.4)

axb.set_xlim(0, 1); axb.set_ylim(0, 1)
axb.set_yticks([]); axb.set_xticks(np.arange(0, 1.01, 0.2))
axb.set_xlabel('Landis–Koch benchmark scale', fontsize=12.5)

# 【修改点 5】：去掉长标题，使用全局绝对坐标放置悬空的 (b)
fig.text(0.02, 0.22, '(b)', fontsize=16, fontweight='bold', va='top')

for s in ('top', 'right', 'left'): 
    axb.spines[s].set_visible(False)



# ===== 保存 =====
out = FIGOUT
fig.savefig(out / 'Figure1_redraw.png', dpi=600, bbox_inches='tight')
fig.savefig(out / 'Figure1_redraw.pdf', bbox_inches='tight')

# ===== 保存（改输出路径/格式在这里） =====
