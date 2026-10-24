from pathlib import Path

import pytest

from seo_data_warehouse.importer import RowValidationError, load_csv, parse_row

ROOT = Path(__file__).resolve().parents[1]


def valid_raw_row() -> dict[str, str]:
    return {
        "date": "2026-01-05",
        "site_code": "demo",
        "site_name": "Demo Site",
        "domain": "example.com",
        "url": "https://www.example.com/page/?utm_source=test",
        "query": "Example Query",
        "device": "Desktop",
        "country": "US",
        "impressions": "100",
        "clicks": "10",
        "position": "5.5",
    }


def test_load_demo_csv() -> None:
    rows = load_csv(ROOT / "data" / "demo_search_performance.csv")
    assert len(rows) == 12
    assert {row.site_code for row in rows} == {"demo_docs", "demo_shop"}


def test_parse_row_normalizes_dimensions() -> None:
    row = parse_row(valid_raw_row(), 2)
    assert row.normalized_url == "https://example.com/page"
    assert row.normalized_query == "example query"
    assert row.device == "desktop"
    assert row.country == "us"
    assert str(row.ctr) == "0.1"


def test_clicks_cannot_exceed_impressions() -> None:
    raw = valid_raw_row()
    raw["clicks"] = "101"
    with pytest.raises(RowValidationError, match="cannot exceed"):
        parse_row(raw, 2)


def test_url_host_must_match_domain() -> None:
    raw = valid_raw_row()
    raw["url"] = "https://another.example/page"
    with pytest.raises(RowValidationError, match="host must match"):
        parse_row(raw, 2)
