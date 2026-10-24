from __future__ import annotations

import ipaddress
import posixpath
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "ref",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
    "yclid",
}


def normalize_query(query: str) -> str:
    """Create a stable, case-insensitive key for a search query."""
    return " ".join(query.casefold().split())


def _valid_public_host(host: str) -> bool:
    if not host or host == "localhost" or host.endswith(".local"):
        return False
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return "." in host
    return False


def normalize_url(url: str, *, keep_non_tracking_query: bool = False) -> str | None:
    """Return a stable absolute URL or ``None`` for unsupported local URLs."""
    raw = url.strip()
    if not raw:
        return None

    if "://" not in raw:
        raw = f"https://{raw}"

    parsed = urlsplit(raw)
    scheme = parsed.scheme.casefold()
    if scheme not in {"http", "https"}:
        return None

    host = (parsed.hostname or "").casefold()
    host = host.removeprefix("www.")
    if not _valid_public_host(host):
        return None

    port = parsed.port
    netloc = host
    if port and not (scheme == "http" and port == 80) and not (
        scheme == "https" and port == 443
    ):
        netloc = f"{host}:{port}"

    decoded_path = unquote(parsed.path or "/")
    normal_path = posixpath.normpath(decoded_path)
    if not normal_path.startswith("/"):
        normal_path = f"/{normal_path}"
    if decoded_path.endswith("/") and normal_path != "/":
        normal_path = normal_path.rstrip("/")

    query = ""
    if keep_non_tracking_query:
        kept = [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key.casefold() not in TRACKING_PARAMETERS
        ]
        query = urlencode(sorted(kept))

    return urlunsplit((scheme, netloc, normal_path, query, ""))
