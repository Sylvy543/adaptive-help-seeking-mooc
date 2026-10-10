# Portable revision pipeline. Run via python run.py reproduce.
"""compute_irr_author_final.py — author-final κ under the as-implemented mapping.

Recomputes the author-final inter-rater statistics exactly under the
classification that the analysis pipeline implemented (the historical
mapping), from the archived coder ratings. This supersedes the earlier
documented scheme (Pop-up Reflection Question at Process; TA Answer Browser
excluded) under which κ values .743/.796 were computed.

Definitions fixed at 2026-09-29, before execution:

1. Input: archived coder ratings (16 features, five categories:
   FT/FP/FR/FS/Other). No recomputation of the raw ratings.

2. Author-final (as-implemented) classification:
   - Adjudicated disagreements applied as documented (Turing Bot -> Self;
     Aminer -> Process), EXCEPT TA Answer Browser, which the implemented
     pipeline placed at Self-Regulation (not the adjudicated Other).
   - Author remapping of features unanimously coded "Other":
     Poetry Composition -> Self; From FAQ, Ask TA (Human), TA Answer Browser,
     Pop-up Reflection Question -> Self-Regulation; Arithmetic Calculator,
     From Course Information -> Task; System Cannot Answer and
     Inappropriate Input -> Excluded.
   - Departures from coder consensus: From MOOCCube (coders: Task) ->
     Process; Pop-up Reflection Question (coders: Process) ->
     Self-Regulation.
   - For coder-vs-coder κ under the author-final scheme, each coder's
     "Other" responses are programmatically remapped by the same rules;
     "Excluded" is treated as a category. Per-coder responses for the two
     departure features are left as coded; the author-final column holds the
     implemented classification.

3. Reported statistics: κ(coder1, coder2) under author-final scheme;
   κ(coder1, author-final); κ(coder2, author-final); their mean.
   Reference values (asserted): raw five-category κ = .716;
   author-final κ(c1,c2) = .743; mean κ(coder, final) = .712.
"""
import argparse, json, platform
from pathlib import Path
import numpy as np
import pandas as pd

VERSION = '2026-09-29-v1'

SHORT = {'Process (FP)': 'Process', 'Task (FT)': 'Task', 'Self-Regulation (FR)': 'Self-Regulation',
         'Self (FS)': 'Self', 'Other / Not Applicable': 'Other'}

# Author-final classification AS IMPLEMENTED in the analysis pipeline.
FINAL = {'知识图谱点击': 'Process', '预设问答': 'Task', '来自mooccube': 'Process',
         '来自图灵机器人': 'Self', '来自baidu': 'Task', '来自baike': 'Task',
         '作诗': 'Self', '来自Faq': 'Self-Regulation', '来自Aminer': 'Process',
         '助教回答': 'Self-Regulation', '飘窗回答': 'Self-Regulation',
         'cannot_answer': 'Excluded', '问助教': 'Self-Regulation',
         '加减乘除': 'Task', '脏问题': 'Excluded', '来自课程信息': 'Task'}

# Remapping of coders' "Other" responses under the author-final rules,
# identical to FINAL for these features (unified rule; 2026-09-30 fix:
# 助教回答 previously mapped to Excluded here, contradicting FINAL).
# 飘窗回答: no coder said "Other", so it needs no entry here.
OTHER_REMAP = {'作诗': 'Self', '来自Faq': 'Self-Regulation', '问助教': 'Self-Regulation',
               '加减乘除': 'Task', '来自课程信息': 'Task',
               'cannot_answer': 'Excluded', '脏问题': 'Excluded', '助教回答': 'Self-Regulation'}
def kappa(a, b):
    a, b = np.asarray(a), np.asarray(b)
    n = len(a)
    po = (a == b).mean()
    pe = sum((a == c).mean() * (b == c).mean() for c in set(a) | set(b))
    return float((po - pe) / (1 - pe))

def main(root):
    root = Path(root).expanduser().resolve()
    ratings = Path(__file__).resolve().parents[1]/'materials/irr_side_by_side.csv'
    if not ratings.is_file():
        raise FileNotFoundError(str(ratings))
    out = root / 'revision_round2/run09_outputs'; out.mkdir(exist_ok=True)

    raw = pd.read_csv(ratings)
    if len(raw) != 16:
        raise ValueError('Archived rating table is not 16 rows.')
    raw['cn'] = raw['Feature (CN)'].str.replace(r'\s+', '', regex=True)
    raw['c1'] = raw['Coder 1'].map(SHORT)
    raw['c2'] = raw['Coder 2'].map(SHORT)
    if raw[['c1', 'c2']].isna().any().any():
        raise ValueError('Unrecognised coder label.')
    raw['final'] = raw.cn.map(FINAL)
    if raw.final.isna().any():
        raise ValueError('Feature missing from FINAL mapping: ' +
                         ', '.join(raw.loc[raw.final.isna(), 'cn']))

    def remap(cn, lab):
        return OTHER_REMAP[cn] if lab == 'Other' else lab
    raw['c1r'] = [remap(cn, l) for cn, l in zip(raw.cn, raw.c1)]
    raw['c2r'] = [remap(cn, l) for cn, l in zip(raw.cn, raw.c2)]

    k_raw = kappa(raw.c1, raw.c2)
    k_cc = kappa(raw.c1r, raw.c2r)
    k_1f = kappa(raw.c1r, raw.final)
    k_2f = kappa(raw.c2r, raw.final)
    k_mean = float(np.mean([k_1f, k_2f]))

    # Reference-value assertions (computed 2026-09-27/29 from the same inputs).
    assert abs(k_raw - 0.716) < 0.0005, k_raw
    assert abs(k_cc - 0.7433) < 0.0005, k_cc
    assert abs(k_mean - 0.7117) < 0.0005, k_mean

    tbl = raw[['Feature (EN)', 'cn', 'c1', 'c2', 'c1r', 'c2r', 'final']].rename(columns={
        'Feature (EN)': 'feature_en', 'cn': 'feature_cn', 'c1': 'coder1_raw', 'c2': 'coder2_raw',
        'c1r': 'coder1_remapped', 'c2r': 'coder2_remapped', 'final': 'author_final_as_implemented'})
    tbl.to_csv(out / 'author_final_mapping_table.csv', index=False)

    summary = {
        'python': platform.python_version(),
        'input': str(ratings),
        'scheme': 'author-final as implemented in the analysis pipeline (historical mapping)',
        'kappa_raw_five_category': k_raw,
        'kappa_author_final_coder_vs_coder': k_cc,
        'kappa_coder1_vs_author_final': k_1f,
        'kappa_coder2_vs_author_final': k_2f,
        'kappa_mean_coder_vs_author_final': k_mean,
        'agreements_raw': int((raw.c1 == raw.c2).sum()),
        'notes': [
            'Raw five-category κ = .716 (13/16 agreements), as reported in Section 3.4.4.',
            'Author-final coder-vs-coder κ = .743; mean coder-vs-author-final κ = .712 under the as-implemented mapping.',
            'The previously documented values .796 (mean coder-vs-final) correspond to the documented scheme with Pop-up Reflection Question at Process and TA Answer Browser excluded; they are superseded by the as-implemented values reported here.']}
    (out / 'author_final_irr.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print('Outputs:', out)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=str(Path(__file__).resolve().parents[1]/'outputs'))
    args = ap.parse_args()
    main(args.root)
