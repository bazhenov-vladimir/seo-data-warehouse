from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from seo_data_warehouse.gsc import (
    GSC_ROW_LIMIT,
    GSCConfigurationError,
    fetch_rows,
    property_domain,
    property_permission,
    resolve_date_range,
)


class FakeRequest:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response

    def execute(self) -> dict[str, object]:
        return self.response


class FakeSearchAnalytics:
    def __init__(self, batches: list[list[dict[str, object]]]) -> None:
        self.batches = batches
        self.bodies: list[dict[str, object]] = []

    def query(self, *, siteUrl: str, body: dict[str, object]) -> FakeRequest:
        assert siteUrl == "sc-domain:example.com"
        self.bodies.append(body)
        index = min(len(self.bodies) - 1, len(self.batches) - 1)
        return FakeRequest({"rows": self.batches[index]})


class FakeSites:
    def list(self) -> FakeRequest:
        return FakeRequest(
            {
                "siteEntry": [
                    {
                        "siteUrl": "sc-domain:example.com",
                        "permissionLevel": "siteRestrictedUser",
                    }
                ]
            }
        )


class FakeService:
    def __init__(self, batches: list[list[dict[str, object]]]) -> None:
        self.analytics = FakeSearchAnalytics(batches)

    def searchanalytics(self) -> FakeSearchAnalytics:
        return self.analytics

    def sites(self) -> FakeSites:
        return FakeSites()


def api_row(day: str = "2026-01-10") -> dict[str, object]:
    return {
        "keys": [
            day,
            "https://www.example.com/guides/seo/?utm_source=test",
            "Technical SEO",
            "DESKTOP",
            "USA",
        ],
        "impressions": 125.5,
        "clicks": 11.25,
        "ctr": 0.0896,
        "position": 5.75,
    }


def test_resolve_date_range_uses_lag_and_lookback() -> None:
    assert resolve_date_range(
        lookback_days=7, lag_days=3, today=date(2026, 1, 20)
    ) == (date(2026, 1, 11), date(2026, 1, 17))


def test_resolve_date_range_requires_both_explicit_dates() -> None:
    with pytest.raises(GSCConfigurationError, match="provided together"):
        resolve_date_range(start_date=date(2026, 1, 1))


def test_property_domain_supports_domain_and_url_prefix_properties() -> None:
    assert property_domain("sc-domain:example.com") == "example.com"
    assert property_domain("https://www.example.com/shop/") == "example.com"


def test_property_permission_finds_exact_property() -> None:
    assert (
        property_permission(FakeService([]), "sc-domain:example.com")
        == "siteRestrictedUser"
    )


def test_fetch_rows_maps_dimensions_and_metrics() -> None:
    service = FakeService([[api_row()]])
    rows = fetch_rows(
        service,
        site_code="example",
        site_name="Example Site",
        property_url="sc-domain:example.com",
        start_date=date(2026, 1, 10),
        end_date=date(2026, 1, 10),
    )
    assert len(rows) == 1
    assert rows[0].normalized_url == "https://example.com/guides/seo"
    assert rows[0].normalized_query == "technical seo"
    assert rows[0].impressions == Decimal("125.5")
    assert rows[0].clicks == Decimal("11.25")
    assert service.analytics.bodies[0]["dataState"] == "final"


def test_fetch_rows_paginates_at_api_limit() -> None:
    full_batch = [api_row()] * GSC_ROW_LIMIT
    service = FakeService([full_batch, []])
    rows = fetch_rows(
        service,
        site_code="example",
        site_name="Example Site",
        property_url="sc-domain:example.com",
        start_date=date(2026, 1, 10),
        end_date=date(2026, 1, 10),
    )
    assert len(rows) == GSC_ROW_LIMIT
    assert service.analytics.bodies[1]["startRow"] == GSC_ROW_LIMIT
