from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "provision_metabase", ROOT / "scripts" / "provision_metabase.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_dashboard_cards_are_read_only_and_use_requested_ids() -> None:
    cards = MODULE.dashboard_cards(database_id=7, dashboard_id=11)
    assert len(cards) == 5
    assert {card["display"] for card in cards} == {"line", "scalar", "table"}
    for card in cards:
        assert card["dashboard_id"] == 11
        assert card["dataset_query"]["database"] == 7
        sql = card["dataset_query"]["native"]["query"].casefold()
        assert "select" in sql
        assert all(word not in sql for word in ("insert ", "update ", "delete ", "drop "))


def test_settings_use_a_dedicated_read_only_user() -> None:
    settings = MODULE.Settings()
    assert settings.warehouse_user == "seo_reader"
    assert settings.warehouse_user != "seo_demo"
