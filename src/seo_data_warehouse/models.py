from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class SearchPerformanceRow:
    date: date
    site_code: str
    site_name: str
    domain: str
    url: str
    normalized_url: str
    query: str
    normalized_query: str
    device: str
    country: str
    impressions: int
    clicks: int
    position: Decimal

    @property
    def ctr(self) -> Decimal:
        if self.impressions == 0:
            return Decimal(0)
        return Decimal(self.clicks) / Decimal(self.impressions)

    @property
    def natural_key(self) -> tuple[object, ...]:
        return (
            self.site_code,
            self.date,
            self.normalized_url,
            self.normalized_query,
            self.device,
            self.country,
        )
