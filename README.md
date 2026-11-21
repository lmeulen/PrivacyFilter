# PrivacyFilter 2.0.0

Dutch free-text privacy filter. It replaces URLs, emails, dates, times, Dutch postal codes, numbers, and configured names, places, streets, medicines, diseases, nationalities, and countries. Optional spaCy NER improves detection.

See related articles:

- [Remove personal information from text with Python](https://towardsdatascience.com/remove-personal-information-from-text-with-python-232cb69cf074)
- [Part II: NER](https://leo-vander-meulen.medium.com/remove-personal-information-from-a-text-with-python-part-ii-ner-2e6529d409a6)

## Privacy warning

This tool reduces PII-like content; it does **not** guarantee anonymization, legal compliance, or safe publication. False negatives and false positives occur. Validate results for your data, language, risk model, and applicable law before disclosure. See [SECURITY.md](SECURITY.md).

## Requirements and installation

Python 3.12+ required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install .
```

Editable development install:

```bash
python -m pip install -e '.[dev]'
```

Optional dataset-updater dependencies:

```bash
python -m pip install -e '.[updater]'
```

Legacy requirement files remain available: `requirements.txt`, `requirements-updater.txt`, and `requirements-dev.txt`. `uv.lock` pins exact release-tested dependencies. Install it with `uv sync --extra dev`.

## Library usage

```pycon
>>> from PrivacyFilter import PrivacyFilter
>>> pfilter = PrivacyFilter()
>>> pfilter.initialize(
...     clean_accents=True,
...     nlp_filter=False,
...     wordlist_filter=False,
...     regular_expressions=True,
... )
>>> pfilter.filter("Het is 12-12-2021.")
'Het is <FILTERED>.'
```

`filter()` normalizes all replacement labels to `<FILTERED>`. Lower-level rule methods, such as `remove_dates()`, retain semantic labels such as `<DATUM>`.

Default datasets ship with installed package. To use custom files, call `initialize_from_file("filter.yaml")`.

## API

Run development server:

```bash
uvicorn PrivacyFilterAPI:privacyFilterApp --host 127.0.0.1 --port 8000
```

Endpoints:

- `GET /health` — readiness and release version
- `POST /filter` — filter text
- `GET /docs` — OpenAPI UI

Example:

```bash
curl http://127.0.0.1:8000/filter \
  -H 'content-type: application/json' \
  -d '{"text":"Jan woont in Arnhem op 12-12-2021.","use_nlp":true}'
```

NLP model loads during application startup. Startup can take time and needs substantial memory. Filtering runs in FastAPI's threadpool, so NLP work does not block server event loop. Threadpool capacity remains finite: benchmark realistic request sizes, cap request concurrency at reverse proxy, and use multiple worker processes only after sizing memory for one spaCy model per worker. Run behind a TLS-terminating reverse proxy in production; do not expose plaintext traffic publicly. Generate certificates with `GenerateCertificate.py` only when configuring Uvicorn TLS explicitly.

## CSV column filtering

`FilterCSVColumn.py` filters one or more zero-based CSV column indexes. File mode reads and writes semicolon-delimited (`;`) ISO-8859-1 CSV files:

```bash
python FilterCSVColumn.py --input input.csv --output filtered.csv --column 0 2
```

Directory mode recursively processes comma-delimited (`,`) ISO-8859-1 CSV files and writes each result next to its input with `_filtered` before `.csv`:

```bash
python FilterCSVColumn.py --directory incoming-csv --column 1
# incoming-csv/nested/records.csv -> incoming-csv/nested/records_filtered.csv
```

Directory mode skips existing `*_filtered.csv` files, so rerunning command does not filter generated output again. Use file mode for another delimiter or encoding only after converting source CSV to semicolon-delimited ISO-8859-1; script currently has no delimiter or encoding command-line options. Filtering loads spaCy NLP and can be slow for large files. Test representative samples first, retain unfiltered source, and review output before sharing it.

## Dataset updater

`DataUpdater.py` obtains data from these sources:

- Names: https://www.naamkunde.net
- Places: CBS dataset 84992
- Streets: OpenStreetMap through OSMnx
- Diseases: https://nl.wikibooks.org/wiki/Geneeskunde/Lijst_van_aandoeningen
- Medicines: https://www.apotheek.nl/
- Nationalities: CBS dataset 03743
- Countries: Dutch Wikipedia country list

Install updater dependencies, then run updater from repository root:

```bash
python -m pip install -e '.[updater]'
python DataUpdater.py
```

Updater downloads public sources and may take significant time, network bandwidth, memory, and disk space; street data is especially expensive. It uses HTTPS, timeouts, and retries for direct HTTP sources, but upstream APIs, pages, schemas, and network connections can still fail. On failure, read reported source URL/error, retry later for transient service/network failures, and inspect/update parser logic for a source-layout failure. Cached raw downloads are in ignored `data-cache/`; remove stale relevant cache files before retrying a changed source. Do not commit raw cache data.

Curated CSV output is written directly to `privacyfilter_data/`, single canonical dataset directory included in source distributions and wheels. Review generated changes, source terms, attribution, and data-protection requirements before committing a dataset refresh and creating release. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Migrating from 1.x

- Upgrade runtime to Python 3.12+.
- Install with `pip install .` or `pip install -r requirements.txt`.
- Use `PrivacyFilter.filter(text, nlp_filter=False)` to disable NLP per request.
- API initializes NLP at lifespan startup and exposes `/health`.
- TLS is deployment configuration, no longer implicit in `PrivacyFilterAPI.py`.

## Development and releases

```bash
python -m pytest -q
python -m ruff check . --select E9,F63,F7,F82
python -m pip_audit --progress-spinner off
```

See [CHANGELOG.md](CHANGELOG.md), [CONTRIBUTING.md](CONTRIBUTING.md), and [SECURITY.md](SECURITY.md). Tag `v2.0.0` after release checks; GitHub Actions builds distribution and creates GitHub Release.

## License

PrivacyFilter code is MIT licensed; see [LICENSE](LICENSE). Dutch spaCy model and data sources carry separate terms. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
