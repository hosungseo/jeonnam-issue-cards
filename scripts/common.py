from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    netloc = parts.netloc.removeprefix("www.")
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme, netloc, path, "", ""))


def title_key(title: str) -> str:
    return re.sub(r"\s+", "", title.lower())


def infer_region(text: str, regions: list[str]) -> str | None:
    for region in regions:
        if region in text:
            return region
    return None


def short_source(url: str) -> str:
    host = urlsplit(url).netloc.removeprefix("www.")
    return host or url

