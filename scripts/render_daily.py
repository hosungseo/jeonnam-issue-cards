#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import subprocess
from pathlib import Path

from common import ROOT, load_json


def accent_summary_line(line: str) -> str:
    escaped = html.escape(line)
    clean = escaped.rstrip(".")
    suffix = "." if escaped.endswith(".") else ""
    if " " not in clean:
        return escaped
    prefix, emphasis = clean.rsplit(" ", 1)
    if len(emphasis) < 3:
        return escaped
    return f'{prefix} <span class="accent">{emphasis}</span>{suffix}'


def fill_template(template: str, spec: dict) -> str:
    summary_html = "<br><br>".join(accent_summary_line(line) for line in spec["summary_lines"])
    headline = html.escape(spec["headline"])
    region = html.escape(spec["region"])
    if "," in headline:
        prefix, emphasis = headline.split(",", 1)
        accented_headline = f"{prefix},<br><span class=\"accent\">{emphasis.strip()}</span>"
    elif " " in headline:
        prefix, emphasis = headline.rsplit(" ", 1)
        accented_headline = f"{prefix} <span class=\"accent\">{emphasis}</span>"
    else:
        accented_headline = headline.replace(region, f'<span class="accent">{region}</span>', 1)
    values = {
        "date_label": spec["date"],
        "region": region,
        "category": html.escape(spec["category"]),
        "category_label": spec["category_label"],
        "headline": headline,
        "accented_headline": accented_headline,
        "summary_html": summary_html,
        "source_label": html.escape(spec["source_label"]),
        "confidence_label": "HIGH" if spec["confidence"] == "high" else "MEDIUM",
    }
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--skip-png", action="store_true")
    args = parser.parse_args()

    specs = load_json(ROOT / "data" / "daily" / args.date / "cards.json")
    template = (ROOT / "templates" / "card.html").read_text(encoding="utf-8")
    html_dir = ROOT / "reports" / args.date / "html"
    card_dir = ROOT / "cards" / args.date
    html_dir.mkdir(parents=True, exist_ok=True)
    card_dir.mkdir(parents=True, exist_ok=True)

    for spec in specs:
        slug = spec["region"]
        html_path = html_dir / f"{slug}.html"
        png_path = card_dir / f"{slug}.png"
        html_path.write_text(fill_template(template, spec), encoding="utf-8")
        if not args.skip_png:
            subprocess.run(
                [
                    "playwright",
                    "screenshot",
                    "--viewport-size=1080,1350",
                    f"file://{html_path}",
                    str(png_path),
                ],
                check=True,
            )
    print(f"rendered {len(specs)} cards -> {card_dir}")


if __name__ == "__main__":
    main()
