from __future__ import annotations

import argparse
import os
from datetime import date
from decimal import Decimal

from .db import connect, upsert_rows
from .gsc import (
    GSCConfigurationError,
    build_service,
    fetch_rows,
    property_permission,
    resolve_date_range,
)
from .importer import RowValidationError, load_csv
from .normalize import normalize_url


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SEO data warehouse starter kit")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate a CSV without a database")
    validate.add_argument("path")

    import_csv = commands.add_parser("import-csv", help="validate and import a CSV")
    import_csv.add_argument("path")

    normalise = commands.add_parser("normalize-url", help="normalise one URL")
    normalise.add_argument("url")

    commands.add_parser("summary", help="show imported demo metrics")

    gsc_check = commands.add_parser(
        "gsc-check", help="verify credentials and property access"
    )
    add_gsc_connection_arguments(gsc_check, include_site_identity=False)

    import_gsc = commands.add_parser(
        "import-gsc", help="import finalized Google Search Console data"
    )
    add_gsc_connection_arguments(import_gsc, include_site_identity=True)
    import_gsc.add_argument("--start-date", type=date.fromisoformat)
    import_gsc.add_argument("--end-date", type=date.fromisoformat)
    import_gsc.add_argument(
        "--lookback-days", type=int, default=int(os.getenv("GSC_LOOKBACK_DAYS", "7"))
    )
    import_gsc.add_argument(
        "--lag-days", type=int, default=int(os.getenv("GSC_LAG_DAYS", "3"))
    )
    import_gsc.add_argument(
        "--search-type", default=os.getenv("GSC_SEARCH_TYPE", "web")
    )
    import_gsc.add_argument("--dry-run", action="store_true")
    return parser


def add_gsc_connection_arguments(
    parser: argparse.ArgumentParser, *, include_site_identity: bool
) -> None:
    parser.add_argument("--property", default=os.getenv("GSC_PROPERTY", ""))
    parser.add_argument(
        "--credentials", default=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    )
    if include_site_identity:
        parser.add_argument("--site-code", default=os.getenv("GSC_SITE_CODE", ""))
        parser.add_argument("--site-name", default=os.getenv("GSC_SITE_NAME", ""))


def require_value(value: str, option: str) -> str:
    if not value.strip():
        raise GSCConfigurationError(f"{option} is required")
    return value.strip()


def metric_total(rows: list[object], field: str) -> Decimal:
    return sum((getattr(row, field) for row in rows), start=Decimal(0))


def main() -> None:
    args = build_parser().parse_args()
    try:
        if args.command == "validate":
            rows = load_csv(args.path)
            print(f"Valid: {len(rows)} rows")
        elif args.command == "normalize-url":
            value = normalize_url(args.url)
            if value is None:
                raise SystemExit("Unsupported URL")
            print(value)
        elif args.command == "import-csv":
            rows = load_csv(args.path)
            with connect() as connection:
                processed = upsert_rows(connection, rows)
            print(f"Imported: {processed} rows")
        elif args.command == "summary":
            with connect() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT site_code, rows_count, impressions, clicks,
                           ROUND((clicks::numeric / NULLIF(impressions, 0)) * 100, 2)
                    FROM v_site_summary
                    ORDER BY site_code
                    """
                )
                print("site_code | rows | impressions | clicks | ctr_percent")
                for row in cursor.fetchall():
                    print(" | ".join(map(str, row)))
        elif args.command == "gsc-check":
            property_url = require_value(args.property, "--property / GSC_PROPERTY")
            service = build_service(args.credentials)
            permission = property_permission(service, property_url)
            if permission is None:
                raise GSCConfigurationError(
                    "the configured service account cannot see this property"
                )
            print(f"Connected: {property_url} ({permission})")
        elif args.command == "import-gsc":
            property_url = require_value(args.property, "--property / GSC_PROPERTY")
            start_date, end_date = resolve_date_range(
                start_date=args.start_date,
                end_date=args.end_date,
                lookback_days=args.lookback_days,
                lag_days=args.lag_days,
            )
            service = build_service(args.credentials)
            rows = fetch_rows(
                service,
                site_code=require_value(args.site_code, "--site-code / GSC_SITE_CODE"),
                site_name=require_value(args.site_name, "--site-name / GSC_SITE_NAME"),
                property_url=property_url,
                start_date=start_date,
                end_date=end_date,
                search_type=args.search_type,
            )
            print(
                f"Fetched {len(rows)} rows for {start_date}..{end_date}; "
                f"impressions={metric_total(rows, 'impressions')}; "
                f"clicks={metric_total(rows, 'clicks')}"
            )
            if args.dry_run:
                print("Dry run: database was not changed")
            else:
                with connect() as connection:
                    processed = upsert_rows(connection, rows)
                print(f"Imported: {processed} rows")
    except (GSCConfigurationError, RowValidationError) as error:
        raise SystemExit(f"Configuration error: {error}") from error


if __name__ == "__main__":
    main()
