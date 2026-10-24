CREATE OR REPLACE VIEW v_site_summary AS
SELECT
    s.site_code,
    COUNT(*) AS rows_count,
    SUM(p.impressions) AS impressions,
    SUM(p.clicks) AS clicks
FROM search_performance_daily AS p
JOIN sites AS s ON s.id = p.site_id
GROUP BY s.site_code;

CREATE OR REPLACE VIEW v_page_performance_28d AS
SELECT
    s.site_code,
    p.normalized_url,
    SUM(p.impressions) AS impressions,
    SUM(p.clicks) AS clicks,
    CASE
        WHEN SUM(p.impressions) = 0 THEN 0
        ELSE SUM(p.clicks)::NUMERIC / SUM(p.impressions)
    END AS ctr,
    SUM(p.avg_position * p.impressions)
        / NULLIF(SUM(p.impressions), 0) AS weighted_position
FROM search_performance_daily AS p
JOIN sites AS s ON s.id = p.site_id
WHERE p.metric_date >= (
    SELECT MAX(metric_date) - INTERVAL '27 days'
    FROM search_performance_daily
)
GROUP BY s.site_code, p.normalized_url;

CREATE OR REPLACE VIEW v_winners_losers AS
WITH daily AS (
    SELECT
        site_id,
        normalized_url,
        metric_date,
        SUM(clicks) AS clicks,
        SUM(impressions) AS impressions
    FROM search_performance_daily
    GROUP BY site_id, normalized_url, metric_date
), compared AS (
    SELECT
        *,
        LAG(clicks) OVER (
            PARTITION BY site_id, normalized_url ORDER BY metric_date
        ) AS previous_clicks,
        LAG(impressions) OVER (
            PARTITION BY site_id, normalized_url ORDER BY metric_date
        ) AS previous_impressions
    FROM daily
)
SELECT
    s.site_code,
    c.normalized_url,
    c.metric_date,
    c.clicks,
    c.previous_clicks,
    c.clicks - c.previous_clicks AS clicks_delta,
    c.impressions,
    c.previous_impressions,
    c.impressions - c.previous_impressions AS impressions_delta
FROM compared AS c
JOIN sites AS s ON s.id = c.site_id
WHERE c.previous_clicks IS NOT NULL;

CREATE OR REPLACE VIEW v_opportunity_pages AS
SELECT
    s.site_code,
    p.normalized_url,
    SUM(p.impressions) AS impressions,
    SUM(p.clicks) AS clicks,
    AVG(p.avg_position) AS avg_position,
    SUM(p.impressions) * GREATEST(AVG(p.avg_position) - 1, 0) AS opportunity_score
FROM search_performance_daily AS p
JOIN sites AS s ON s.id = p.site_id
GROUP BY s.site_code, p.normalized_url
HAVING SUM(p.impressions) >= 100
   AND AVG(p.avg_position) BETWEEN 4 AND 20;
