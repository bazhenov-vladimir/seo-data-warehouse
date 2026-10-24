from seo_warehouse_demo.normalize import normalize_query, normalize_url


def test_normalize_url_removes_www_tracking_and_trailing_slash() -> None:
    assert (
        normalize_url(" HTTPS://www.Example.com/guides/seo/?utm_source=test ")
        == "https://example.com/guides/seo"
    )


def test_normalize_url_rejects_local_and_non_http_urls() -> None:
    assert normalize_url("http://localhost/page") is None
    assert normalize_url("ftp://example.com/file") is None


def test_normalize_url_can_keep_sorted_business_parameters() -> None:
    assert (
        normalize_url(
            "https://example.com/catalog/?size=m&utm_source=test&color=blue",
            keep_non_tracking_query=True,
        )
        == "https://example.com/catalog?color=blue&size=m"
    )


def test_normalize_query_collapses_whitespace_and_case() -> None:
    assert normalize_query("  Technical   SEO Guide ") == "technical seo guide"
