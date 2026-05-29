# Jeonnam Issue Cards

Daily Jeonnam local-issue briefing pipeline.

The MVP collects regional issue candidates, scores and deduplicates them, builds one card spec per city/county when a meaningful issue exists, renders 1080x1350 PNG cards, and prepares a Telegram bundle.

## Scope

- Region coverage: 22 Jeonnam cities/counties
- Primary delivery: Telegram image bundle
- Archive: date-based JSON, HTML, PNG, and markdown reports
- Sources: real RSS + city/county press boards via adapters under `scripts/adapters/`

## Setup

```bash
# 1) core pipeline deps (collect / score / render)
python3 -m pip install -r requirements.txt
# 2) PNG rendering uses Playwright's chromium
python3 -m playwright install chromium
```

For JS-rendered boards (e.g. Gwangyang's board.es), an optional crawl4ai
renderer is used as a fallback. It needs python 3.10+ in a separate venv:

```bash
python3.13 -m venv .venv-crawl
.venv-crawl/bin/pip install -r requirements-crawl.txt
.venv-crawl/bin/python -m playwright install chromium
```

The main pipeline runs without it; only boards marked `"render": true` in
`config/sources.json` require the crawl4ai venv.

## Pipeline

```bash
python3 scripts/collect.py --date 2026-05-22
python3 scripts/score.py --date 2026-05-22
python3 scripts/build_specs.py --date 2026-05-22
python3 scripts/audit_pipeline.py --date 2026-05-22
python3 scripts/render_daily.py --date 2026-05-22
python3 scripts/qc.py --date 2026-05-22
python3 scripts/send_telegram.py --date 2026-05-22 --dry-run
```

Or:

```bash
./scripts/run_daily.sh 2026-05-22
```

## Design Policy

- Daily cards do not call an image generation API.
- Generated images, if used, are limited to reusable abstract category backgrounds.
- Text, sources, region names, and confidence are rendered deterministically in HTML/CSS.
- Personnel notices, simple bid/procurement notices, and institution-head photo-op items are excluded.

## Pipeline Quality

`scripts/score.py` records score components, item age, and a cluster key for each surviving candidate. `scripts/audit_pipeline.py` writes `reports/YYYY-MM-DD/pipeline_quality.json` with raw/scored/card counts, source mix, region/category coverage, multi-source clusters, and warnings before rendering begins.

## Sources

- RSS feeds: `config/news_rss_sources.json` (province + media)
- City/county boards: `config/sources.json` (`html_boards`); 10 cities live
- Adding a board: find the press-list URL, then
  `python3 scripts/smart_discover.py <list_url> <region>` to derive selectors,
  add the entry to `config/sources.json` (set `"render": true` for JS boards),
  and verify with `scripts/collect.py`.
