from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Settings:
    metabase_url: str = os.getenv("METABASE_URL", "http://localhost:3000").rstrip("/")
    admin_email: str = os.getenv("METABASE_ADMIN_EMAIL", "admin@example.local")
    admin_password: str = os.getenv("METABASE_ADMIN_PASSWORD", "local_admin_2026")
    site_name: str = os.getenv("METABASE_SITE_NAME", "SEO Data Warehouse")
    warehouse_host: str = os.getenv("WAREHOUSE_HOST", "postgres")
    warehouse_port: int = int(os.getenv("WAREHOUSE_PORT", "5432"))
    warehouse_db: str = os.getenv("WAREHOUSE_DB", "seo_demo")
    warehouse_user: str = os.getenv("WAREHOUSE_READER_USER", "seo_reader")
    warehouse_password: str = os.getenv(
        "WAREHOUSE_READER_PASSWORD", "seo_reader_local_only"
    )


class MetabaseAPIError(RuntimeError):
    pass


class MetabaseClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.session_id: str | None = None

    def request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> Any:
        data = None if payload is None else json.dumps(payload).encode()
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["X-Metabase-Session"] = self.session_id
        request = Request(
            f"{self.base_url}{path}", data=data, headers=headers, method=method
        )
        try:
            with urlopen(request, timeout=30) as response:
                body = response.read()
        except HTTPError as error:
            message = error.read().decode(errors="replace")
            raise MetabaseAPIError(
                f"Metabase API {method} {path} returned {error.code}: {message}"
            ) from error
        except URLError as error:
            raise MetabaseAPIError(f"Metabase is unavailable: {error.reason}") from error
        return json.loads(body) if body else None

    def get(self, path: str) -> Any:
        return self.request("GET", path)

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        return self.request("POST", path, payload)


def wait_until_ready(client: MetabaseClient, attempts: int = 60) -> None:
    for _ in range(attempts):
        try:
            if client.get("/api/health").get("status") == "ok":
                return
        except MetabaseAPIError:
            pass
        time.sleep(5)
    raise MetabaseAPIError("Metabase did not become healthy")


def authenticate(client: MetabaseClient, settings: Settings) -> None:
    properties = client.get("/api/session/properties")
    if properties.get("has-user-setup"):
        session = client.post(
            "/api/session",
            {"username": settings.admin_email, "password": settings.admin_password},
        )
    else:
        token = properties.get("setup-token")
        if not token:
            raise MetabaseAPIError("Metabase setup token is unavailable")
        session = client.post(
            "/api/setup",
            {
                "token": token,
                "user": {
                    "first_name": "SEO",
                    "last_name": "Admin",
                    "email": settings.admin_email,
                    "password": settings.admin_password,
                },
                "prefs": {"site_name": settings.site_name, "site_locale": "en"},
            },
        )
    client.session_id = session["id"]


def ensure_database(client: MetabaseClient, settings: Settings) -> int:
    databases = client.get("/api/database")
    records = databases.get("data", []) if isinstance(databases, dict) else databases
    for database in records:
        if database.get("name") == "SEO Warehouse":
            return int(database["id"])

    created = client.post(
        "/api/database",
        {
            "name": "SEO Warehouse",
            "engine": "postgres",
            "details": {
                "host": settings.warehouse_host,
                "port": settings.warehouse_port,
                "dbname": settings.warehouse_db,
                "user": settings.warehouse_user,
                "password": settings.warehouse_password,
                "ssl": False,
            },
        },
    )
    return int(created["id"])


def dashboard_cards(database_id: int, dashboard_id: int) -> list[dict[str, Any]]:
    definitions = [
        (
            "Organic clicks",
            "scalar",
            "SELECT COALESCE(SUM(clicks), 0) AS clicks FROM search_performance_daily",
            6,
            3,
        ),
        (
            "Organic impressions",
            "scalar",
            "SELECT COALESCE(SUM(impressions), 0) AS impressions FROM search_performance_daily",
            6,
            3,
        ),
        (
            "Search performance over time",
            "line",
            """
            SELECT metric_date AS date,
                   SUM(clicks) AS clicks,
                   SUM(impressions) AS impressions
            FROM search_performance_daily
            GROUP BY metric_date
            ORDER BY metric_date
            """,
            24,
            8,
        ),
        (
            "SEO opportunity pages",
            "table",
            """
            SELECT site_code, normalized_url, impressions, clicks,
                   ROUND(avg_position, 2) AS avg_position,
                   ROUND(opportunity_score, 2) AS opportunity_score
            FROM v_opportunity_pages
            ORDER BY opportunity_score DESC
            LIMIT 50
            """,
            24,
            8,
        ),
        (
            "Top landing pages",
            "table",
            """
            SELECT site_code, normalized_url, impressions, clicks,
                   ROUND(ctr * 100, 2) AS ctr_percent,
                   ROUND(weighted_position, 2) AS weighted_position
            FROM v_page_performance_28d
            ORDER BY clicks DESC
            LIMIT 50
            """,
            24,
            8,
        ),
    ]
    return [
        {
            "name": name,
            "type": "question",
            "display": display,
            "description": "Provisioned by SEO Data Warehouse Starter",
            "visualization_settings": {},
            "dashboard_id": dashboard_id,
            "size": {"size_x": size_x, "size_y": size_y},
            "dataset_query": {
                "database": database_id,
                "type": "native",
                "native": {"query": "\n".join(line.strip() for line in sql.splitlines())},
            },
        }
        for name, display, sql, size_x, size_y in definitions
    ]


def ensure_dashboard(client: MetabaseClient, database_id: int) -> int:
    dashboards = client.get("/api/dashboard")
    records = dashboards.get("data", []) if isinstance(dashboards, dict) else dashboards
    for dashboard in records:
        if dashboard.get("name") == "SEO Performance Overview":
            return int(dashboard["id"])

    dashboard = client.post(
        "/api/dashboard",
        {
            "name": "SEO Performance Overview",
            "description": "Organic visibility, traffic trends, and landing-page opportunities.",
        },
    )
    dashboard_id = int(dashboard["id"])
    for card in dashboard_cards(database_id, dashboard_id):
        client.post("/api/card", card)
    return dashboard_id


def main() -> None:
    settings = Settings()
    client = MetabaseClient(settings.metabase_url)
    wait_until_ready(client)
    authenticate(client, settings)
    database_id = ensure_database(client, settings)
    dashboard_id = ensure_dashboard(client, database_id)
    print(f"Metabase is ready: dashboard_id={dashboard_id}")
    print("Open http://localhost:3000")
    print(f"Login: {settings.admin_email}")


if __name__ == "__main__":
    main()
