# Contributing

Thanks for improving PrivacyFilter. Report bugs and proposals in a GitHub issue before substantial work. Keep each change focused on one issue and include regression coverage for behavior changes.

## Branches and pull requests

`master` is default and release branch. It must remain releasable. Create a short-lived branch from current `master` for a contribution, then open a pull request targeting `master`. Do not commit generated caches, local environments, credentials, or unreviewed dataset downloads.

The repository also has a `development` branch for integration work; CI runs for both `master` and `development`. It is not required as an intermediate branch for ordinary contributions. A maintainer decides merge timing and release eligibility.

Before requesting review:

- Describe problem, approach, and validation in pull request.
- Link issue with `Fixes #<number>` when applicable.
- Update documentation and changelog when user-visible behavior, operations, or security posture changes.
- Add or update tests for changed behavior.
- Keep commits focused; rebase or merge latest `master` when needed.

## Development setup

Python 3.12+ required. [uv](https://docs.astral.sh/uv/) creates and manages project environment from committed lock file:

```bash
uv sync --extra dev --extra updater --locked
```

Use `uv run` for project commands. Runtime dependencies are default; `dev` provides test/lint/audit tools, and `updater` provides dataset refresh dependencies. Do not manually edit `uv.lock`; update dependencies through `pyproject.toml` and regenerate lock deliberately.

## Required checks

Run same checks as CI before pull request:

```bash
uv run python -m pip check
uv run pip-audit --progress-spinner off
uv run ruff check .
uv run ruff format --check src/privacyfilter/configuration.py \
  src/privacyfilter/rules.py src/privacyfilter/nlp.py src/privacyfilter/core.py \
  test/test_Components.py
uv run pytest -q
uv lock --check
```

Pytest treats warnings as errors. Fix new warnings instead of suppressing them. Ruff checks maintained lint rules project-wide; formatter checks currently cover refactored modules while older files are incrementally formatted.

Dataset changes also require review of data sources, licenses, and privacy implications. Run updater only after installing `updater` extra; see README and `THIRD_PARTY_NOTICES.md`.

## Release process

1. Update only `src/privacyfilter/_version.py` for package version.
2. Run required checks above, then build locally:

   ```bash
   uv build
   uv run python scripts/verify_release_version.py vX.Y.Z dist/* \
     --version-file src/privacyfilter/_version.py
   ```

3. Commit version/changelog changes, merge to `master`, then create matching tag.

Release tags must exactly match source version: final `vX.Y.Z`, or prerelease `vX.Y.ZaN`, `vX.Y.ZbN`, or `vX.Y.ZrcN`. Local versions, post releases, and arbitrary `v*` tags are rejected. Release workflow validates tag against source before dependency installation/building, revalidates built artifacts, then creates GitHub Release.
