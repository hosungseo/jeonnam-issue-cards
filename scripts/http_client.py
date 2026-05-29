"""Shared HTTP fetcher for source adapters.

Follows redirects, sets a browser-like UA, applies timeout and retries.
On block signals (403/timeout/empty) returns None and logs a warning; a
hook is provided for delegating blocked pages to an external fetcher
(e.g. the insane-search skill). crawl4ai is intentionally not used here
because it requires python 3.10+ and this pipeline runs on python 3.9.
"""
from __future__ import annotations

import sys
import time
from typing import Callable, Optional

import requests

DEFAULT_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
DEFAULT_TIMEOUT = 10
DEFAULT_RETRIES = 2

# Optional delegate for blocked pages: fn(url) -> str | None.
# Wired by callers that have insane-search available; default is a no-op.
fallback_fetch: Optional[Callable[[str], Optional[str]]] = None


def _warn(msg: str) -> None:
    print(f"[http_client] {msg}", file=sys.stderr)


def fetch(url: str, *, timeout: int = DEFAULT_TIMEOUT,
          retries: int = DEFAULT_RETRIES, ua: str = DEFAULT_UA) -> Optional[str]:
    """Return response text, or None if the page is unreachable/blocked."""
    headers = {"User-Agent": ua, "Accept-Language": "ko,en;q=0.8"}
    last_status = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout,
                                allow_redirects=True)
            last_status = resp.status_code
            if resp.status_code == 200 and resp.text.strip():
                return resp.text
            if resp.status_code in (403, 429):
                break  # block signal; stop retrying, try fallback
        except requests.RequestException as exc:
            _warn(f"request error {url}: {exc}")
        if attempt < retries:
            time.sleep(1)

    _warn(f"unreachable url={url} status={last_status}")
    if fallback_fetch is not None:
        try:
            return fallback_fetch(url)
        except Exception as exc:  # noqa: BLE001 - fallback must never crash collect
            _warn(f"fallback failed {url}: {exc}")
    return None
