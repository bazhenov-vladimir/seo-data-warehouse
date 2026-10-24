from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

from .models import SearchPerformanceRow
from .normalize import normalize_query, normalize_url


REQUIRED_COLUMNS = {
    "clicks",
    "country",
    "date",
    "device",
    "domain",
    "impressions",
    "position",
    "query",
    "site_code",
    "site_name",
    "url",
}


class RowValidationError(ValueError):
    """A CSV row cannot be safely imported."""


def _non_negative_int(value: str, field: str, line: int) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise RowValidationError(f"line {line}: {field} must be an integer") from error
    if parsed < 0:
        raise RowValidationError(f"line {line}: {field} must be non-negative")
    return parsed


def parse_row(raw: dict[str, str], line: int) -> SearchPerformanceRow:
    try:
        metric_date = date.fromisoformat(raw["date"].strip())
    except ValueError as error:
        raise RowValidationError(f"line {line}: date must use YYYY-MM-DD") from error

    normalized_url = normalize_url(raw["url"])
    if normalized_url is None:
        raise RowValidationError(f"line {line}: url must be a public HTTP(S) URL")

    domain = raw["domain"].strip().casefold().removeprefix("www.")
    if not domain or "/" in domain or "://" in domain:
        raise RowValidationError(f"line {line}: domain must be a hostname")
    if urlsplit_host(normalized_url) != domain:
        raise RowValidationError(f"line {line}: url host must match domain")

    impressions = _non_negative_int(raw["impressions"], "impressions", line)
    clicks = _non_negative_int(raw["clicks"], "clicks", line)
    if clicks > impressions:
        raise RowValidationError(f"line {line}: clicks cannot exceed impressions")

    try:
        position = Decimal(raw["position"])
    except InvalidOperation as error:
        raise RowValidationError(f"line {line}: position must be numeric") from error
    if position <= 0:
        raise RowValidationError(f"line {line}: position must be positive")

    query = raw["query"].strip()
    site_code = raw["site_code"].strip()
    site_name = raw["site_name"].strip()
    if not site_code or not site_name or not query:
        raise RowValidationError(
            f"line {line}: site_code, site_name, and query are required"
        )

    return SearchPerformanceRow(
        date=metric_date,
        site_code=site_code,
        site_name=site_name,
        domain=domain,
        url=raw["url"].strip(),
        normalized_url=normalized_url,
        query=query,
        normalized_query=normalize_query(query),
        device=raw["device"].strip().casefold() or "unknown",
        country=raw["country"].strip().casefold() or "unknown",
        impressions=impressions,
        clicks=clicks,
        position=position,
    )


def urlsplit_host(url: str) -> str:
    from urllib.parse import urlsplit

    return (urlsplit(url).hostname or "").casefold()


def load_csv(path: str | Path) -> list[SearchPerformanceRow]:
    csv_path = Path(path)
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise RowValidationError(f"missing columns: {', '.join(missing)}")
        rows = [parse_row(raw, line) for line, raw in enumerate(reader, start=2)]

    duplicates = _duplicates(rows)
    if duplicates:
        raise RowValidationError(
            "duplicate natural key in CSV: " + ", ".join(map(str, duplicates[0]))
        )
    return rows


def _duplicates(rows: Iterable[SearchPerformanceRow]) -> list[tuple[object, ...]]:
    seen: set[tuple[object, ...]] = set()
    duplicates: list[tuple[object, ...]] = []
    for row in rows:
        if row.natural_key in seen:
            duplicates.append(row.natural_key)
        seen.add(row.natural_key)
    return duplicates
