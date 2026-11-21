# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## Unreleased

### Changed

- Moved pyOpenSSL from core runtime dependencies to optional `certificates` extra used only by self-signed development certificate helper.
- Refreshed contribution guide with current branch/PR policy, locked `uv` setup, validation commands, warnings policy, and release/tag workflow.
- Split configuration/data loading, regular-expression formatting rules, and spaCy NLP interpretation into focused typed components behind the stable `PrivacyFilter` API.
- Corrected `PrivacyFilter.to_string()` class-name typo and added public-path type annotations.
- Enabled maintained Ruff lint rules and formatting checks for refactored modules.

### Security

- Escaped dynamic example-report content to prevent HTML/script injection in generated HTML.

### Changed

- Release workflow validates tag against source version before dependency installation or distribution build.
- Removed deprecated flat module compatibility shims and legacy requirements files. Use `privacyfilter.*` imports/module commands and package extras instead.
- Removed deprecated `seperator` keyword alias; use `separator`.

## [2.0.0] - 2026-11-21

### Added
- Python package metadata and installable distribution.
- Python 3.12 support.
- Reproducible `uv.lock` dependency lock.
- API health endpoint and OpenAPI version metadata.
- API regression tests and release workflow.
- Separate core, updater, and development dependency groups.
- Security, privacy, and third-party attribution documentation.

### Changed
- Upgraded FastAPI, spaCy, Dutch NLP model, pandas, GeoPandas, OSMnx, and related dependencies.
- API NLP model now loads during application lifespan startup rather than module import.
- Bundled default datasets in distributable package.
- Updated dataset updater for modern pandas and OSMnx APIs.

### Fixed
- API `use_nlp` request option now reaches filter implementation.
- NLP fallback behavior handles model tag changes while preserving regression fixtures.

### Breaking changes
- Python 3.12 or newer is required.
- `PrivacyFilterAPI` no longer creates TLS certificates or serves HTTPS itself. Terminate TLS at a reverse proxy or run Uvicorn with explicit certificate options.
