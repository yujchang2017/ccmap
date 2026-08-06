# -*- coding: utf-8 -*-
"""
Supplementary Table S1 產生器:代表性查詢 × embedding top-3 vs 字面(BM25)對照。
全程使用預計算向量與公開資料檔,無任何 API 呼叫(可離線重現)。

口徑:
- 查詢 = 各領域代表性課綱條目(content_catalog.csv 的 label,與 app 相同的預計算向量)
- 階段過濾 = 依 app/models/data_loader.get_concept_data_by_stage 的對應
  (I→[I]; II→[I,II,III]; III→[III]; IV→[IV]; V→[V])
- embedding 排名 = cosine similarity(與 app 相同)
- keyword 對照 = BM25(中文字元 bigram),同一候選集
"""

import math
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "supplementary_table_s1.md"

catalog = pd.read_csv(ROOT / "data" / "embeddings" / "content_catalog.csv")
content_emb = np.load(ROOT / "data" / "embeddings" / "content_embeddings.npy")
key_texts = pd.read_csv(ROOT / "data" / "embeddings" / "unique_keyidea_texts.csv")["keyidea"].tolist()
key_emb = np.load(ROOT / "data" / "embeddings" / "keyidea_embeddings.npy")
tw = pd.read_csv(ROOT / "data" / "raw" / "guidemeta_tw.csv")
en = pd.read_csv(ROOT / "data" / "raw" / "guidemeta.csv")

# keyidea → (key_id, band, English original)
meta = {}
for i, row in tw.iterrows():
    k = row["keyidea"]
    if k not in meta:
        meta[k] = (row["key_id"], row["age"], en.iloc[i]["keyidea"])

STAGE_MAP = {"I": ["I"], "II": ["I", "II", "III"], "III": ["III"], "IV": ["IV"], "V": ["V"]}

def stage_candidates(stage):
    bands = STAGE_MAP[stage]
    idx = [i for i, k in enumerate(key_texts) if meta.get(k, (None, None, None))[1] in bands]
    return idx

def cosine(v, M):
    v = v / (np.linalg.norm(v) + 1e-12)
    Mn = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-12)
    return Mn @ v

def bigrams(text):
    t = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", str(text))
    return [t[i:i+2] for i in range(len(t) - 1)]

class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs = [Counter(bigrams(d)) for d in docs]
        self.dl = [sum(c.values()) for c in self.docs]
        self.avgdl = sum(self.dl) / max(len(self.dl), 1)
        self.k1, self.b = k1, b
        self.df = Counter()
        for c in self.docs:
            for term in c:
                self.df[term] += 1
        self.N = len(docs)

    def score(self, query, i):
        c, dl = self.docs[i], self.dl[i]
        s = 0.0
        for term in set(bigrams(query)):
            if term not in c:
                continue
            idf = math.log((self.N - self.df[term] + 0.5) / (self.df[term] + 0.5) + 1)
            tf = c[term]
            s += idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return s

# 代表性查詢:每領域一條(以關鍵詞挑選,涵蓋階段 I–V 與 SDG)
PICKS = [  # (domain_label, stage, keyword)
    ("自然", "II", "季節"),      # 與 Fig.2 相同案例,交叉對照
    ("自然", "IV", "天氣與氣候"),
    ("社會", "III", "環境"),
    ("社會", "IV", "資源"),
    ("健康與體育", "IV", "環境"),
    ("綜合活動", "III", "環境"),
    ("國文", "III", None),
    ("英文", "IV", None),
    ("生活", "I", "自然"),
    ("數學", "III", "統計"),
    ("科技", "IV", "能源"),
    ("藝術", "III", None),
    ("SDG", "V", "氣候"),
]

def pick_row(domain_key, stage, keyword):
    sub = catalog[catalog["domain"].astype(str).str.contains(domain_key, na=False)]
    sub = sub[sub["age"].astype(str).str.strip() == stage] if stage else sub
    if sub.empty:
        sub = catalog[catalog["domain"].astype(str).str.contains(domain_key, na=False)]
    if keyword:
        hit = sub[sub["content"].astype(str).str.contains(keyword, na=False)]
        if not hit.empty:
            return hit.iloc[0]
    return sub.iloc[0] if not sub.empty else None

bm25 = BM25(key_texts)

lines = [
    "# Supplementary Table S1 — Face-validity table(產生於 2026-07-30,全離線、零 API 呼叫)",
    "",
    "每列:課綱條目查詢(含階段過濾)→ CCMAP embedding top-3(cosine)對照 BM25 字元-bigram top-3。",
    "Key idea 以 key_id 標示;英文為 GCG 原文。**粗體** = 兩法皆選出;`0.00` = 無字面重疊。",
    "",
]

zero_overlap_queries = 0
for domain_key, stage, keyword in PICKS:
    row = pick_row(domain_key, stage, keyword)
    if row is None:
        print(f"!! no row for {domain_key}")
        continue
    label = row["label"]
    ci = catalog.index[catalog["label"] == label][0]
    qv = content_emb[ci]
    cand = stage_candidates(stage)
    if not cand:
        print(f"!! no candidates for stage {stage}")
        continue
    sims = cosine(qv, key_emb[cand])
    order = np.argsort(-sims)[:3]
    emb_top = [(key_texts[cand[j]], float(sims[j])) for j in order]

    bscores = [(k_i, bm25.score(str(row["content"]), k_i)) for k_i in cand]
    bscores.sort(key=lambda x: -x[1])
    bm_top = [(key_texts[i], s) for i, s in bscores[:3]]
    if bscores[0][1] == 0:
        zero_overlap_queries += 1

    emb_ids = {meta[k][0] for k, _ in emb_top}
    lines.append(f"## {row['domain']} · stage {stage} · {row['conID']}")
    lines.append(f"查詢condition:{row['content']}")
    lines.append("")
    lines.append("| 排名 | CCMAP (embedding) | cos | BM25 keyword | BM25 |")
    lines.append("|---|---|---|---|---|")
    for r in range(3):
        ek, es = emb_top[r]
        bk, bs = bm_top[r] if r < len(bm_top) else ("—", 0)
        eid, _, een = meta[ek]
        bid = meta[bk][0] if bk in meta else "—"
        bmark = f"**{bid}**" if bid in emb_ids else bid
        lines.append(f"| {r+1} | {eid} {een} | {es:.2f} | {bmark} | {bs:.2f} |")
    lines.append("")

lines.append(f"> 附註:{zero_overlap_queries}/{len(PICKS)} 條查詢與所有候選 key idea 完全無字面重疊(BM25 最高分 0),"
             "keyword 法在這些查詢上無法回傳有意義的結果;embedding 法仍可回傳語意相近之候選。")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("written", OUT, "| zero-overlap:", zero_overlap_queries, "/", len(PICKS))
