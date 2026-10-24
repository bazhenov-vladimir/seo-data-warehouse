from __future__ import annotations

import argparse

from .db import connect, upsert_rows
from .importer import RowValidationError, load_csv
from .normalize import normalize_url


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SEO data warehouse portfolio demo")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate a CSV without a database")
    validate.add_argument("path")

    import_csv = commands.add_parser("import-csv", help="validate and import a CSV")
    import_csv.add_argument("path")

    normalise = commands.add_parser("normalize-url", help="normalise one URL")
    normalise.add_argument("url")

    commands.add_parser("summary", help="show imported demo metrics")
    return parser


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
    except RowValidationError as error:
        raise SystemExit(f"Invalid CSV: {error}") from error


if __name__ == "__main__":
    main()
