from __future__ import annotations

import os
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit

from .models import SearchPerformanceRow
from .normalize import normalize_query, normalize_url

GSC_READONLY_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
GSC_ROW_LIMIT = 25_000
SUPPORTED_SEARCH_TYPES = {"discover", "googleNews", "image", "news", "video", "web"}


class SearchAnalyticsService(Protocol):
    def searchanalytics(self) -> Any: ...

    def sites(self) -> Any: ...


class GSCConfigurationError(ValueError):
    """Google Search Console configuration is missing or invalid."""


def resolve_date_range(
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    lookback_days: int = 7,
    lag_days: int = 3,
    today: date | None = None,
) -> tuple[date, date]:
    if (start_date is None) != (end_date is None):
        raise GSCConfigurationError("start-date and end-date must be provided together")
    if start_date is not None and end_date is not None:
        if start_date > end_date:
            raise GSCConfigurationError("start-date cannot be after end-date")
        return start_date, end_date
    if lookback_days < 1:
        raise GSCConfigurationError("lookback-days must be at least 1")
    if lag_days < 0:
        raise GSCConfigurationError("lag-days cannot be negative")

    current = today or date.today()
    resolved_end = current - timedelta(days=lag_days)
    resolved_start = resolved_end - timedelta(days=lookback_days - 1)
    return resolved_start, resolved_end


def property_domain(property_url: str) -> str:
    value = property_url.strip()
    if value.startswith("sc-domain:"):
        domain = value.removeprefix("sc-domain:").strip().casefold()
    else:
        parsed = urlsplit(value)
        domain = (parsed.hostname or "").casefold()
    domain = domain.removeprefix("www.")
    if not domain or "." not in domain or "/" in domain:
        raise GSCConfigurationError(
            "property must look like sc-domain:example.com or https://example.com/"
        )
    return domain


def credentials_path(explicit_path: str | None = None) -> Path:
    raw = explicit_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not raw:
        raise GSCConfigurationError(
            "set GOOGLE_APPLICATION_CREDENTIALS or GSC_CREDENTIALS_FILE"
        )
    path = Path(raw).expanduser()
    if not path.is_file():
        raise GSCConfigurationError(f"credentials file was not found: {path}")
    return path


def build_service(explicit_credentials_path: str | None = None) -> Any:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as error:
        raise GSCConfigurationError(
            "install the optional GSC dependencies with: pip install -e '.[gsc]'"
        ) from error

    credentials = service_account.Credentials.from_service_account_file(
        str(credentials_path(explicit_credentials_path)),
        scopes=[GSC_READONLY_SCOPE],
    )
    return build("searchconsole", "v1", credentials=credentials, cache_discovery=False)


def property_permission(service: SearchAnalyticsService, property_url: str) -> str | None:
    response = service.sites().list().execute()
    for entry in response.get("siteEntry", []):
        if entry.get("siteUrl") == property_url:
            return entry.get("permissionLevel", "unknown")
    return None


def fetch_rows(
    service: SearchAnalyticsService,
    *,
    site_code: str,
    site_name: str,
    property_url: str,
    start_date: date,
    end_date: date,
    search_type: str = "web",
) -> list[SearchPerformanceRow]:
    if search_type not in SUPPORTED_SEARCH_TYPES:
        raise GSCConfigurationError(
            "search-type must be one of: " + ", ".join(sorted(SUPPORTED_SEARCH_TYPES))
        )
    if not site_code.strip() or not site_name.strip():
        raise GSCConfigurationError("site-code and site-name are required")

    domain = property_domain(property_url)
    rows: list[SearchPerformanceRow] = []
    start_row = 0

    while True:
        response = (
            service.searchanalytics()
            .query(
                siteUrl=property_url,
                body={
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "dimensions": ["date", "page", "query", "device", "country"],
                    "type": search_type,
                    "dataState": "final",
                    "rowLimit": GSC_ROW_LIMIT,
                    "startRow": start_row,
                },
            )
            .execute()
        )
        batch = response.get("rows", [])
        if not batch:
            break

        for item in batch:
            keys = item.get("keys", [])
            if len(keys) != 5:
                raise ValueError("Search Console returned an unexpected dimension set")
            raw_url = keys[1]
            normal_url = normalize_url(raw_url)
            if normal_url is None:
                continue
            query = keys[2].strip()
            impressions = Decimal(str(item.get("impressions", 0)))
            clicks = Decimal(str(item.get("clicks", 0)))
            rows.append(
                SearchPerformanceRow(
                    date=date.fromisoformat(keys[0]),
                    site_code=site_code.strip(),
                    site_name=site_name.strip(),
                    domain=domain,
                    url=raw_url,
                    normalized_url=normal_url,
                    query=query,
                    normalized_query=normalize_query(query),
                    device=keys[3].casefold() or "unknown",
                    country=keys[4].casefold() or "unknown",
                    impressions=impressions,
                    clicks=clicks,
                    position=Decimal(str(item.get("position", 0))),
                )
            )

        start_row += len(batch)
        if len(batch) < GSC_ROW_LIMIT:
            break

    return rows
