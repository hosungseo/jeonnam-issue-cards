# Jeonnam Issue Cards

Daily Jeonnam local-issue briefing pipeline.

The MVP collects regional issue candidates, scores and deduplicates them, builds one card spec per city/county when a meaningful issue exists, renders 1080x1350 PNG cards, and prepares a Telegram bundle.

## Scope

- Region coverage: 22 Jeonnam cities/counties
- Primary delivery: Telegram image bundle
- Archive: date-based JSON, HTML, PNG, and markdown reports
- MVP sources: official/candidate fixtures first; real adapters can be added under `scripts/collect.py`

## Pipeline

```bash
python3 scripts/collect.py --date 2026-05-22
python3 scripts/score.py --date 2026-05-22
python3 scripts/build_specs.py --date 2026-05-22
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

