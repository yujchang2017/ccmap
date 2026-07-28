# Changelog

All notable changes to CCMAP are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-07-28

First public release.

Consolidated from the private development history (2025-10 to 2026-07):

### Added
- Flask web application mapping UNESCO *Greening Curriculum Guidance* (2024)
  key ideas and learning outcomes (localized to Traditional Chinese) onto
  Taiwan's 12-Year Basic Education curriculum.
- Semantic search over curated teaching resources using precomputed OpenAI
  `text-embedding-3-large` vectors (offline `.npy` files included). The
  repository ships a 90-item sample resource index from government and
  public-agency sources; the production deployment indexes 6,700+ items.
- MVC architecture (`app/controllers`, `app/models`, `app/services`,
  `app/utils`) with input validation (marshmallow), output sanitization
  (bleach), CORS policies per environment, and rate limiting
  (flask-limiter, optional Upstash Redis burst protection).
- SDG (Sustainable Development Goals) content source for search.
- Anonymous usage-event logging (UUID-based, no personal data) to MongoDB.
- Precomputation scripts (`scripts/precomputation.py`, CI/CD variant) and
  GitHub Actions workflows for data updates and Heroku deployment.
- Test suite for security, rate limiting, API endpoints, and database
  connectivity (`tests/`).
