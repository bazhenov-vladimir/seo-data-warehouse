# SEO Data Warehouse Starter

A practical, reproducible starter kit for storing and analysing daily organic-search performance in PostgreSQL.

It provides a safe foundation for a production SEO warehouse without including client code, private reports, credentials, or real search data.

## What it demonstrates

- deterministic URL and query normalisation;
- validated CSV ingestion with actionable error messages;
- idempotent PostgreSQL upserts;
- an analytics-friendly dimensional schema;
- SQL views for landing-page trends, query trends, winners and losers, and opportunity pages;
- optional Google Search Console import with read-only credentials and pagination;
- repeatable daily imports through a separate scheduler container;
- synthetic demo data, unit tests, Docker Compose, and CI.

## Architecture

```text
Synthetic CSV export
        |
        v
Validation and normalisation
        |
        v
PostgreSQL: sites -> pages / queries -> search_performance_daily
        |
        v
Analytics views and example SQL queries
```

The default workflow is deliberately API-free. It works with the included synthetic CSV and does not require Google or Yandex credentials. The optional Search Console adapter uses the same validated importer boundary.

Google Search Console support is optional. See [`GSC_SETUP.md`](GSC_SETUP.md) after the synthetic workflow is running.

## Quick start for SEO specialists

The only required application is Docker Desktop. Python is not required on your computer.

```bash
./setup.sh
```

On Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

The setup command checks Docker, creates a local configuration, starts PostgreSQL, validates the synthetic CSV, imports it, and prints a summary. PostgreSQL is exposed on `localhost:55432` by default so the starter does not take over a common local port.

See [`SEO_SPECIALIST_GUIDE.md`](SEO_SPECIALIST_GUIDE.md) for a non-programmer-oriented walkthrough.

## Everyday commands

```bash
make start        # start PostgreSQL
make stop         # stop the project without deleting its data
make status       # show service status
make import-demo  # validate and import the synthetic CSV
make summary      # show imported totals
make test         # run the automated tests in Docker
```

Optional Search Console commands:

```bash
make gsc-check             # verify credentials and property access
make import-gsc-dry-run    # fetch totals without changing PostgreSQL
make import-gsc            # fetch and upsert finalized data
make start-gsc-scheduler   # repeat the import every 24 hours
make gsc-logs              # inspect scheduler output
```

Stop the demo with:

```bash
docker compose down
```

Add `-v` only when you intentionally want to delete the demo database volume.

## Developer setup without Docker

CSV validation and URL normalisation do not need a database:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
seo-warehouse validate data/demo_search_performance.csv
seo-warehouse normalize-url 'https://www.example.com/guides/seo/?utm_source=sample'
pytest
```

## Demo data format

The importer expects these columns:

| Column | Type | Notes |
| --- | --- | --- |
| `date` | `YYYY-MM-DD` | Metric date |
| `site_code` | text | Stable site identifier |
| `site_name` | text | Human-readable name |
| `domain` | hostname | No scheme or path |
| `url` | absolute URL | Normalised during import |
| `query` | text | Normalised for deduplication |
| `device` | text | For example `desktop` or `mobile` |
| `country` | text | ISO-style country code |
| `impressions` | integer | Must be non-negative |
| `clicks` | integer | Must be between zero and impressions |
| `position` | decimal | Positive average position |

The included dataset uses only reserved `example.*` domains and invented metrics.

## Useful queries

After importing the demo file:

```sql
SELECT *
FROM v_page_performance_28d
ORDER BY clicks DESC;

SELECT *
FROM v_winners_losers
ORDER BY ABS(clicks_delta) DESC;

SELECT *
FROM v_opportunity_pages
ORDER BY opportunity_score DESC;
```

More examples are in [`sql/queries.sql`](sql/queries.sql).

## Development

```bash
python -m pip install -e '.[dev]'
pytest
python scripts/check_public_ready.py
```

CI runs the tests and the public-readiness check on every push and pull request.

## Privacy and scope

- No production database dump is included.
- No API key, OAuth token, service-account file, or `.env` file is included.
- No client name, domain, query export, analytics report, or deployment address is included.
- All committed metrics are synthetic and safe to share.

## License

MIT. See [`LICENSE`](LICENSE).
