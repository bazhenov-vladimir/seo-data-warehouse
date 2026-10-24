-- Landing pages with the most clicks.
SELECT site_code, normalized_url, clicks, impressions, ctr
FROM v_page_performance_28d
ORDER BY clicks DESC;

-- Pages with the largest day-over-day movement.
SELECT site_code, normalized_url, metric_date, clicks_delta, impressions_delta
FROM v_winners_losers
ORDER BY ABS(clicks_delta) DESC;

-- Pages near the first results page with meaningful demand.
SELECT site_code, normalized_url, impressions, clicks, avg_position
FROM v_opportunity_pages
ORDER BY opportunity_score DESC;
