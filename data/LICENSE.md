# Data Licensing

The source code of CCMAP is released under the MIT License (see `../LICENSE`).
The datasets in this `data/` directory are subject to the following separate
terms.

## 1. UNESCO-derived content — CC BY-SA 3.0 IGO

`data/raw/guidemeta_tw.csv`, `data/embeddings/unique_keyidea_texts.csv`, and the
key-idea / learning-outcome texts embedded in
`data/embeddings/keyidea_embeddings.npy` are derived from:

> UNESCO (2024). *Greening curriculum guidance: teaching and learning for
> climate action*. Paris: UNESCO. https://doi.org/10.54675/AOOZ1758
> © UNESCO 2024. Licensed under
> [CC BY-SA 3.0 IGO](https://creativecommons.org/licenses/by-sa/3.0/igo/).

Modifications made in this repository: translation into Traditional Chinese,
restructuring into tabular (CSV) form, assignment of internal identifiers, and
computation of embedding vectors. In accordance with the ShareAlike condition,
these derived data files are likewise made available under
**CC BY-SA 3.0 IGO**. This work is not endorsed by UNESCO.

## 2. Taiwan curriculum content

`data/raw/*-cont.csv` files contain learning-content items from Taiwan's
Curriculum Guidelines of 12-Year Basic Education (十二年國民基本教育課程綱要),
published by the Ministry of Education, Taiwan. These are publicly released
official documents; the tabular restructuring in this repository is provided
for interoperability and carries no additional restrictions.

## 3. Third-party resource metadata

`data/maps/map.csv` (and the derived
`data/embeddings/description_embeddings.npy`) is a **90-item sample** of the
resource index used by the production deployment, restricted to resources
published by Taiwanese government agencies and public institutions (e.g.,
Ministry of Education platforms, Ministry of Environment, Ministry of
Agriculture). For each resource it stores only: the title, the public URL,
the source/publisher name, a short descriptive snippet, and classification
metadata (type, language, age band). The indexed resources themselves remain
the property of their respective publishers and are **not** redistributed
here; users should consult each linked site for its own terms of use. The
full production index is not redistributed; use
`scripts/precomputation.py` to build an index of your own (see README).

## 4. Attribution

If you reuse the datasets, please attribute both UNESCO (as above) and the
CCMAP project (see `../CITATION.cff`).
