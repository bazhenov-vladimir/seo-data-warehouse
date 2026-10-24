# SEO Data Warehouse Demo

A small, reproducible data pipeline for storing and analysing daily organic-search performance in PostgreSQL.

This portfolio project demonstrates the reusable engineering ideas behind a production SEO warehouse without including client code, private reports, credentials, or real search data.

## What it demonstrates

- deterministic URL and query normalisation;
- validated CSV ingestion with actionable error messages;
- idempotent PostgreSQL upserts;
- an analytics-friendly dimensional schema;
- SQL views for landing-page trends, query trends, winners and losers, and opportunity pages;
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

The default workflow is deliberately API-free. It works with the included synthetic CSV and does not require Google or Yandex credentials. A real API adapter can be added behind the same importer boundary.

## Quick start with Docker

Requirements: Docker with the Compose plugin.

```bash
cp .env.example .env
docker compose up -d
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
seo-warehouse-demo validate data/demo_search_performance.csv
seo-warehouse-demo import-csv data/demo_search_performance.csv
seo-warehouse-demo summary
```

PostgreSQL is exposed on `localhost:55432` by default so the demo does not take over a common local port. Change `POSTGRES_PORT` in `.env` if needed.

Stop the demo with:

```bash
docker compose down
```

Add `-v` only when you intentionally want to delete the demo database volume.

## Run without PostgreSQL

CSV validation and URL normalisation do not need a database:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
seo-warehouse-demo validate data/demo_search_performance.csv
seo-warehouse-demo normalize-url 'https://www.example.com/guides/seo/?utm_source=demo'
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
