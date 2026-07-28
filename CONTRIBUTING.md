# Contributing to CCMAP

Thanks for your interest in improving CCMAP!

## Reporting issues

Please use the GitHub issue tracker. For bug reports, include your OS, Python
version, the command you ran, and the full error output. For broken or
outdated teaching-resource links in `data/maps/map.csv`, include the `map_id`
and the URL.

## Development setup

1. Fork and clone the repository.
2. Create a virtual environment with Python 3.10 and run
   `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and fill in the required values
   (see README for details).
4. Run the app with `python main.py` and the tests with `pytest tests/`
   (note: most tests require a running local instance; see `tests/README.md`).

## Pull requests

- Keep changes focused; one topic per PR.
- Follow the existing MVC structure (`app/controllers`, `app/models`,
  `app/services`, `app/utils`) and validation patterns
  (marshmallow schemas in `app/utils/validators.py`).
- Do not commit `.env`, logs, database dumps, or any credentials.

## Data contributions

Curriculum and resource data live under `data/` and are subject to the
licensing terms in `data/LICENSE.md`. Proposed additions to the resource map
should include: name, public URL, source, type, language, and age band.
