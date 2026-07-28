# CCMAP — Climate Change Curriculum Map

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/)

CCMAP is a web platform that helps teachers integrate climate change education
into everyday subject teaching. It localizes the key ideas and learning
outcomes of UNESCO's *Greening Curriculum Guidance* (2024) into Traditional
Chinese, maps them onto **Taiwan's 12-Year Basic Education curriculum**
(11 learning domains plus the UN Sustainable Development Goals), and uses
semantic search over precomputed text embeddings to recommend relevant
teaching resources. The production deployment indexes a curated map of
**6,700+ publicly available materials**; this repository ships a
**90-item sample index** drawn from government and public-agency sources,
together with the scripts to build a full index of your own
(see [Bringing your own resource index](#adapting-ccmap-to-other-curricula-and-resources)).

The interface is in Traditional Chinese and targets K-12 teachers,
pre-service teachers, curriculum designers, and education researchers in
Taiwan.

## Features

- **Curriculum mapping** — browse UNESCO key ideas / learning outcomes by
  concept, topic, and age band, aligned with Taiwan curriculum learning
  content items.
- **Semantic resource search** — select a curriculum item (or enter free
  text) and retrieve the most relevant teaching resources, ranked by cosine
  similarity of `text-embedding-3-large` vectors (3072-d). All corpus
  embeddings are **precomputed offline** and shipped as `.npy` files, so no
  API calls are needed at browse time; an OpenAI API key is only required to
  embed free-text queries.
- **Resource map** — indexed resources (videos, lesson plans, articles,
  interactive media) with type / language / age-band metadata; 6,700+ items
  in the production deployment, 90 sample items in this repository.
- **Anonymous usage analytics** — UUID-based event logging (searches,
  resource clicks) to MongoDB; no personal data is collected.
- **Hardened by default** — input validation (marshmallow), output
  sanitization (bleach), per-environment CORS policy, rate limiting
  (flask-limiter) with optional Redis-backed burst protection.

## Architecture

```
Flask (MVC)
├── app/controllers/   HTTP routes: pages, JSON API, secured endpoints
├── app/models/        CSV/embedding loaders (pandas, numpy)
├── app/services/      embedding search, MongoDB logging
├── app/utils/         validation schemas, sanitizers, helpers
├── config/            environment-based settings (dev / production)
├── data/
│   ├── raw/           UNESCO guidance (zh-TW) + Taiwan curriculum CSVs
│   ├── maps/map.csv   resource index (90-row public sample)
│   └── embeddings/    precomputed .npy vectors + catalogs
├── scripts/           embedding precomputation, data cleaning
├── templates/ static/ Jinja2 + Bootstrap 5 + Tailwind CSS frontend
└── tests/             security / rate-limit / API / DB test suite
```

## Quick start

Requirements: **Python 3.10**, pip. (MongoDB and Redis are optional — see
notes below.)

```bash
git clone https://github.com/yujchang2017/ccmap.git
cd ccmap
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # then edit .env (see below)
python main.py                       # http://localhost:5000
```

Set `FLASK_ENV=development` in `.env` for local development. For production,
use the provided `Procfile` / Gunicorn:

```bash
gunicorn -w 1 -b 0.0.0.0:$PORT wsgi:app
```

Or with Docker:

```bash
docker build -t ccmap .
docker run -p 5000:5000 -e SECRET_KEY=change-me ccmap
```

### Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | For free-text search only | Embeds user queries at runtime. Browsing and item-based search work without it (corpus embeddings are precomputed). |
| `MONGO_URI` | For usage logging / feedback | MongoDB connection string (e.g., Atlas). Without it the app runs but analytics endpoints are degraded. |
| `SECRET_KEY` | Yes (production) | Flask session signing key. |
| `UPSTASH_REDIS_REST_URL` / `_TOKEN` | Optional | Enables burst protection and persistent rate limiting. |
| `CORS_ORIGINS` | Optional | Comma-separated allowed origins. |

See `.env.example` for the full list including MongoDB pool tuning.

### Regenerating embeddings (optional)

Precomputed embeddings for the shipped datasets are included. If you modify
`data/maps/map.csv` or the curriculum CSVs, regenerate them (requires
`OPENAI_API_KEY`):

```bash
python scripts/precomputation.py
```

## Adapting CCMAP to other curricula and resources

CCMAP's pipeline is language- and country-agnostic: all domain knowledge
lives in swappable CSV files, and the code makes no assumption about which
curriculum or which resources are indexed. To adapt it:

1. **Curriculum**: replace the domain CSVs in `data/raw/` (`*-cont.csv`,
   columns: stage/domain/topic/content) with your own curriculum's learning
   content items, and adjust `DOMAIN_CSV_FILES` in `config/settings.py`.
2. **UNESCO guidance localization**: `data/raw/guidemeta_tw.csv` holds the
   translated key ideas / learning outcomes; translate into your target
   language keeping the same columns.
3. **Resource index**: extend `data/maps/map.csv` (columns: `map_id, old_id,
   type, name, snippet, URL, description, lang, source, age`) with your own
   resources. The shipped file is a 90-item sample from Taiwanese government
   and public-agency sources; the production instance runs the same code on
   a 6,700+ item index.
4. **Embeddings**: run `python scripts/precomputation.py` once to embed the
   new texts (any OpenAI embedding model can be configured via
   `EMBEDDING_MODEL` / `EMBEDDING_DIM`).

## Tests

Offline unit tests (no API key, database, or network required — these also run
in CI on every push):

```bash
pytest tests/unit
```

They cover input validation and sanitization, similarity computation, and the
integrity/alignment of the shipped datasets and embeddings.

The remaining suites under `tests/` are integration tests that expect a
running local instance (default `http://127.0.0.1:5001`, configurable via
`CCMAP_TEST_URL`) and, for some, a reachable MongoDB. See `tests/README.md`
for prerequisites and the scope of each suite.

## Data and licensing

- **Code**: [MIT](LICENSE).
- **Data**: see [`data/LICENSE.md`](data/LICENSE.md). In short: UNESCO-derived
  content is CC BY-SA 3.0 IGO (© UNESCO 2024, *Greening Curriculum Guidance*,
  https://doi.org/10.54675/AOOZ1758 — this project is not endorsed by UNESCO);
  Taiwan curriculum items come from official Ministry of Education documents;
  the resource map stores only titles, URLs, and short descriptive metadata of
  third-party materials, not the materials themselves.

## Citation

If you use CCMAP in your research or teaching, please cite it via the
metadata in [`CITATION.cff`](CITATION.cff) (GitHub's "Cite this repository"
button).

## Contributing

Bug reports, broken-link reports for the resource map, and pull requests are
welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md).
