# Changelog

All notable changes to CCMAP are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

Versions before 1.0.0 were developed in private repositories and were not
tagged at the time. Their version numbers were assigned retrospectively from
the commit history (87 commits across five repositories, 2025-03-21 to
2026-09-27) so that the history of the production deployment at
<https://cce.tw/search> can be followed. "Private ref" lists the abbreviated
commit IDs in the private repositories; they cannot be opened publicly.
"Resource index" is the number of rows in `data/maps/map.csv` (or `map.csv`
in early versions) after the release.

The study period reported in the paper is 2025-03-30 to 2026-07-27 (16 months).
Releases 0.1.0 to 0.10.0 fall inside it. Training and outreach events are
listed under "Context" when a release falls within 30 days of one. This shows
only that the dates are close; it does not mean the event caused the change,
unless the change is described as such.

## [Unreleased]

Development after the study period, not yet published as a public release.

### Added
- English framework source (`data/raw/guidemeta.csv`) and an offline script
  that reproduces Supplementary Table S1 (public commit `487cef3`, 2026-08-06,
  after the `V1.0.0` tag).
- Lesson-plan and worksheet resource types in labels, filters and material pages.
- 306 additional lesson-plan, slide and worksheet resources; description
  embeddings rebuilt (resource index 6,350 -> 6,656).
- Free-text search as a separate mode on `/search`, with its own optional
  learning-stage filter; free-text-only queries return the top 10 key ideas.

### Changed
- Learning stages shown with Taiwan stage names and the matching UNESCO level;
  stage filter matches resources whose age field contains the stage.
- The "any" option was removed from the domain select in condition mode;
  Chinese labels added for article, book, picture-book and podcast types.

### Fixed
- Age-band metadata of 102 resources for ages 5-8 assigned to Taiwan learning stage I.

Private ref: `32d057d`..`630aac4` (2026-09-26 to 2026-09-27).

## [1.0.0] - 2026-08-06

First public release (tag `V1.0.0`, archived on Zenodo,
https://doi.org/10.5281/zenodo.21824594). It ships a 13-item sample resource
index (reduced from 90 items during release preparation) instead of the full
production index.

### Added
- Offline unit tests, a CI test workflow and a Dockerfile.

### Changed
- Second-stage resource recommendation uses precomputed key-idea embeddings,
  so the whole flow runs without an API key.
- Rate limiting moved into the application factory, so the production WSGI
  entry point is also protected.
- `precomputation.py` gains `--force` and writes a provenance manifest
  (input checksums, model, dimension, output shapes).
- CI validates that embedding rows line up with source CSVs and checks the
  3,072-dimension size.
- Production resource index cleaned before publication: 170 same-title
  near-duplicates removed (6,729 -> 6,559), 201 resources from foreign sites
  removed out of caution over licensing (6,559 -> 6,358), and 8 borderline
  non-domestic entries removed (6,358 -> 6,350).
- License text is standard MIT; data terms moved to `NOTICE.md`.

Public commits: `bcb320e`..`4ea7200`. Private ref (development repository):
`e87e2b4`..`527c124` (2026-07-28 to 2026-07-30).

## [0.10.0] - 2026-07-22

### Added
- Topic level in the curriculum filter (domain -> topic -> sub-content).
- Curriculum domains expanded from 2 (science, social studies) to 10.
- Precomputed embeddings for curriculum content (2,601 items); live API calls
  are used only for additional free text.
- SDG curriculum table as a further content source for search.

Resource index: 6,729. Private ref: `2137d94`..`cce1038` (2026-07-02 to 2026-07-22).

## [0.9.1] - 2026-05-18

### Fixed
- Tailwind CSS is now built locally instead of loaded from a CDN, fixing an
  SSL error on the deployed site.

Private ref: `fab33d6`.

## [0.9.0] - 2026-04-28

### Added
- UNESCO license notice on the site.

### Changed
- Resource index cleanup: 653 duplicate or invalid-URL rows removed and 444
  rows re-added with new IDs (6,938 -> 6,729); embeddings recomputed.

Private ref: `1125703`..`aa96586` (2026-04-17 to 2026-04-28).

## [0.8.2] - 2026-02-25

### Changed
- Resource type "news" reclassified as "video".

### Fixed
- Long resource names and source-site names now wrap in result tables.

Resource index: 6,938. Private ref: `b3af488`..`d2736a5`.

## [0.8.1] - 2026-01-08

### Fixed
- Resource reporting: UUID format, optional comment, new "outdated
  information" option, database fallback (2026-01-06).
- Validation error when the "any" option was selected for learning stage
  or domain (2026-01-08).

Context: seed-teacher training on 2026-01-07 (one day before and one day after).

Private ref: `ed0440d`..`85ed255`.

## [0.8.0] - 2025-12-29

### Added
- Login reminder on topic pages for resources hosted on the national ADL
  platform (adl.edu.tw), which requires a login.
- About 5,120 Public Television Service "Our Island" (《我們的島》) videos
  added to the resource index (1,818 -> 6,938).

### Changed
- Embedding model switched from `text-embedding-ada-002` to
  `text-embedding-3-large`; resource index
  cleaned (1,925 -> 1,818) and embeddings rebuilt.
- Teaching-package lists use server-side pagination and search.

### Fixed
- Filter options now refresh after resources are fetched again.
- Teaching-package quick search no longer freezes the browser. A debounce was
  tried first; the client-side quick search was then removed.

Context: seed-teacher workshop on 2025-12-25 (1-4 days before these changes);
seed-teacher training on 2026-01-07.

Private ref: `43e4d39`..`dc137b9` (2025-12-26 to 2025-12-29).

## [0.7.0] - 2025-12-23

### Added
- User onboarding: quick-start guide on the home page, a first-visit tour of
  the learning map and a help button.
- In-app feedback form: 1-5 satisfaction rating, feedback type, willingness
  to take part (recommend resources, try new features, develop materials) and
  an optional contact e-mail.

### Changed
- Localized framework text and topic-detail template updated.

### Fixed
- Wider candidate set when filtering resources.
- Navigation link and resource-list display.
- Values for the report issue type made consistent; old values are still
  accepted and normalized on `/report`.

Context: seed-teacher workshop on 2025-12-25 (2-6 days after these changes).

Private ref: `9c23697`..`4823ad5` (2025-12-19 to 2025-12-23).

## [0.6.2] - 2025-12-09

### Fixed
- "Self-learning" link on the home page points to the external learning-game
  site (changed in both the legacy and the refactored codebase).

Private ref: `7ac4163` (legacy), `c9bf909`.

## [0.6.1] - 2025-11-19

### Changed
- Embedding workflow documented for local precomputation.
- Automatic deployment to Heroku disabled; deployment is now triggered by hand.

### Fixed
- Curriculum filter: concept names, source-filter logic, table headers.

Private ref: `3897151`..`050202f` (2025-11-18 to 2025-11-19).

## [0.6.0] - 2025-10-08

Rewrite of the application.

### Added
- Model-view-controller layout (`app/controllers`, `app/models`,
  `app/services`, `app/utils`), input validation, output sanitization, CORS
  policy and rate limiting with burst protection.
- Resource reporting: users can flag a broken link, a wrong category,
  inappropriate content or another problem.
- Per-key-idea resource filters (language, type, source, learning stage),
  similarity shown as a percentage, and a short-description column in all
  resource tables.
- Test suite (security, rate limiting, API, database) and GitHub Actions
  workflows that rebuild embeddings when data changes and deploy the app.

### Fixed
- Search and pagination conflict on the teaching-package list.
- Duplicate resources in results (de-duplicated by URL, then by name).

Resource index: 1,925. Context: Ministry of Education digital teaching-material
workshop on 2025-10-17 (9 days later).

Private ref: `3b09cb3`..`a22ecc5`. Fix notes dated 2025-10-07 are in
`BUGFIX_20251007.md`, `FEATURE_UPDATE.md`, `MAP_DISPLAY_FIX.md`,
`MAP_UI_OPTIMIZATION.md` and `RESOURCE_TABLE_UNIFICATION.md`.

## [0.5.3] - 2025-09-02

### Changed
- Resource index 1,651 -> 1,925.

Context: cross-domain workshop on 2025-08-06 (27 days earlier).

Private ref: `e11b64a`.

## [0.5.2] - 2025-08-06

### Changed
- Resource names shown for video resources; resource index 1,363 -> 1,651.

Context: committed on the day of the cross-domain workshop (2025-08-06), 8 days
after the one on 2025-07-29.

Private ref: `276aa24`.

## [0.5.1] - 2025-07-27

### Changed
- Resource index 1,143 -> 1,244 (2025-07-19) -> 1,363 (2025-07-27).
- Localized framework text revised.

Context: cross-domain workshop on 2025-07-29 (2-10 days later).

Private ref: `1ed676f`..`192e9c3`.

## [0.5.0] - 2025-07-02

### Added
- Multi-page site ("4 in 1"): home page, search map, materials, lists by
  resource type and concept pages.

### Fixed
- Item 4.6 of the localized framework text.

Context: Pingtung lesson-plan writing workshop on 2025-06-06 (25-26 days earlier).

Private ref: `2a1b324`..`6ae8fb4`.

## [0.4.0] - 2025-06-12

### Added
- New resource filter items.

### Changed
- Resource index 995 -> 1,143; localized framework text updated.

Context: Pingtung lesson-plan writing workshop on 2025-06-06 (6 days earlier).

Private ref: `9300d02`.

## [0.3.0] - 2025-05-24

### Added
- Concept map: concept overview and topic-detail pages.

### Changed
- Localized framework text revised.

Context: 13-15 days before the 2025-06-06 workshop.

Private ref: `7b3eeeb`..`98acc68` (2025-05-22 to 2025-05-24).

## [0.2.1] - 2025-05-13

### Changed
- Front-end search and result script rewritten.

### Fixed
- Python runtime version pinned for deployment.

Private ref: `72f87ff`..`b54ecf7`.

## [0.2.0] - 2025-05-04

Second codebase.

### Added
- Precomputed embeddings for key ideas and resource descriptions.

### Changed
- Science and social-studies curriculum tables updated.
- Resource index rebuilt and curated (995 rows, replacing a 4,247-row draft
  committed on 2025-04-29); layout updated.

Private ref: `27200da`..`afa6b24` (2025-04-29 to 2025-05-04).

## [0.1.0] - 2025-03-30

First deployed prototype (Flask).

### Added
- Mapping of UNESCO key ideas onto the Taiwan curriculum, with semantic search
  (`text-embedding-ada-002`).
- Resource index of 41 -> 306 -> 706 rows (2025-03-21 to 2025-03-25).
- Anonymous usage-event logging to MongoDB (2025-03-30). The study period
  starts on this date.

Private ref: `8a1a11d`..`d0d2b25` (2025-03-21 to 2025-03-30).

[Unreleased]: https://github.com/yujchang2017/ccmap/compare/V1.0.0...HEAD
[1.0.0]: https://github.com/yujchang2017/ccmap/releases/tag/V1.0.0
