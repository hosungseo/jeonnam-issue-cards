#!/usr/bin/env python3
"""Collect raw issue candidates from source adapters.

Iterates adapters from the registry, normalizes items, fills region for
RSS/media items via text matching (official board items already carry their
region), removes exact-duplicate URLs, and writes data/raw/<date>.json.

Region matching and exclusion keyword filtering for scoring live in score.py;
collect only ensures region is populated and drops identical URLs.
"""
from __future__ import annotations

import argparse
from collections import Counter

from urllib.parse import urlsplit, urlunsplit

from common import ROOT, infer_region, load_json, write_json
from adapters.registry import build_adapters


def dedup_key(url: str) -> str:
    """Normalize for dedup while KEEPING query string.

    Board pages identify articles via query (e.g. ?idx=545617), so unlike
    common.normalize_url (which drops query for title-paired scoring) we must
    preserve it here or every board item collapses into one.
    """
    parts = urlsplit(url.strip())
    netloc = parts.netloc.removeprefix("www.")
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme, netloc, path, parts.query, ""))


def fill_region(item: dict, regions: list[str]) -> dict:
    if not item.get("region"):
        text = f"{item.get('title','')} {item.get('body','')}"
        item["region"] = infer_region(text, regions)
    return item


def dedupe_by_url(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out = []
    for item in items:
        url = item.get("url") or ""
        key = dedup_key(url) if url else ""
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        out.append(item)
    return out


def collect(date: str, adapters=None, regions=None):
    adapters = adapters if adapters is not None else build_adapters()
    regions = regions if regions is not None else load_json(ROOT / "config" / "regions.json")

    items: list[dict] = []
    counts: Counter = Counter()
    for adapter in adapters:
        name = getattr(adapter, "name", adapter.source_method)
        try:
            fetched = adapter.fetch(date)
        except Exception as exc:  # noqa: BLE001 - isolate one source's failure
            print(f"[collect] adapter failed {name}: {exc}")
            fetched = []
        counts[f"{adapter.source_method}:{name}"] = len(fetched)
        items.extend(fetched)

    items = [fill_region(it, regions) for it in items]
    items = dedupe_by_url(items)
    return items, counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    items, counts = collect(args.date)
    out = ROOT / "data" / "raw" / f"{args.date}.json"
    write_json(out, items)

    for source, n in counts.items():
        print(f"  {source}: {n}")
    print(f"collected {len(items)} items -> {out}")


if __name__ == "__main__":
    main()
