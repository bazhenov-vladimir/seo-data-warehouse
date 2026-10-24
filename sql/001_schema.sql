CREATE TABLE IF NOT EXISTS sites (
    id BIGSERIAL PRIMARY KEY,
    site_code TEXT NOT NULL UNIQUE,
    site_name TEXT NOT NULL,
    domain TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pages (
    id BIGSERIAL PRIMARY KEY,
    site_id BIGINT NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    normalized_url TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (site_id, normalized_url)
);

CREATE TABLE IF NOT EXISTS queries (
    id BIGSERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    normalized_query TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS search_performance_daily (
    id BIGSERIAL PRIMARY KEY,
    site_id BIGINT NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    page_id BIGINT NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    query_id BIGINT NOT NULL REFERENCES queries(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    url TEXT NOT NULL,
    normalized_url TEXT NOT NULL,
    query TEXT NOT NULL,
    device TEXT NOT NULL DEFAULT 'unknown',
    country TEXT NOT NULL DEFAULT 'unknown',
    impressions INTEGER NOT NULL CHECK (impressions >= 0),
    clicks INTEGER NOT NULL CHECK (clicks >= 0 AND clicks <= impressions),
    ctr NUMERIC(10, 8) NOT NULL CHECK (ctr >= 0 AND ctr <= 1),
    avg_position NUMERIC(10, 4) NOT NULL CHECK (avg_position > 0),
    imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (
        site_id, metric_date, normalized_url,
        query_id, device, country
    )
);

CREATE INDEX IF NOT EXISTS idx_performance_site_date
    ON search_performance_daily (site_id, metric_date);
CREATE INDEX IF NOT EXISTS idx_performance_url_date
    ON search_performance_daily (normalized_url, metric_date);
CREATE INDEX IF NOT EXISTS idx_performance_query_date
    ON search_performance_daily (query_id, metric_date);
