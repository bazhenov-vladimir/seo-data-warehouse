from __future__ import annotations

import os
from collections.abc import Iterable

import psycopg
from psycopg import Connection

from .models import SearchPerformanceRow


def database_url() -> str:
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit
    user = os.getenv("POSTGRES_USER", "seo_demo")
    password = os.getenv("POSTGRES_PASSWORD", "seo_demo_local_only")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "55432")
    name = os.getenv("POSTGRES_DB", "seo_demo")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def connect() -> Connection:
    return psycopg.connect(database_url())


def upsert_rows(conn: Connection, rows: Iterable[SearchPerformanceRow]) -> int:
    processed = 0
    with conn.cursor() as cursor:
        for row in rows:
            cursor.execute(
                """
                INSERT INTO sites (site_code, site_name, domain)
                VALUES (%s, %s, %s)
                ON CONFLICT (site_code) DO UPDATE SET
                    site_name = EXCLUDED.site_name,
                    domain = EXCLUDED.domain
                RETURNING id
                """,
                (row.site_code, row.site_name, row.domain),
            )
            site_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO pages (site_id, url, normalized_url)
                VALUES (%s, %s, %s)
                ON CONFLICT (site_id, normalized_url) DO UPDATE SET
                    url = EXCLUDED.url
                RETURNING id
                """,
                (site_id, row.url, row.normalized_url),
            )
            page_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO queries (query, normalized_query)
                VALUES (%s, %s)
                ON CONFLICT (normalized_query) DO UPDATE SET
                    query = EXCLUDED.query
                RETURNING id
                """,
                (row.query, row.normalized_query),
            )
            query_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO search_performance_daily (
                    site_id, page_id, query_id, metric_date, url,
                    normalized_url, query, device, country,
                    impressions, clicks, ctr, avg_position
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (
                    site_id, metric_date, normalized_url,
                    query_id, device, country
                ) DO UPDATE SET
                    page_id = EXCLUDED.page_id,
                    url = EXCLUDED.url,
                    query = EXCLUDED.query,
                    impressions = EXCLUDED.impressions,
                    clicks = EXCLUDED.clicks,
                    ctr = EXCLUDED.ctr,
                    avg_position = EXCLUDED.avg_position,
                    imported_at = NOW()
                """,
                (
                    site_id,
                    page_id,
                    query_id,
                    row.date,
                    row.url,
                    row.normalized_url,
                    row.query,
                    row.device,
                    row.country,
                    row.impressions,
                    row.clicks,
                    row.ctr,
                    row.position,
                ),
            )
            processed += 1
    conn.commit()
    return processed
