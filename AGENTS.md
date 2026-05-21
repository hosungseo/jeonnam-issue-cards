# AGENTS.md

## Product

This repository builds a daily Telegram card-news briefing for Jeonnam local issues.

## Operating Rules

- Keep every pipeline step executable as a CLI.
- Every CLI should support `--date`; external delivery commands should support `--dry-run`.
- Do not send Telegram messages from scripts unless `--send` is explicitly used.
- Do not generate new AI images during daily cron runs.
- Archive all generated JSON, HTML, PNG, and markdown outputs under date-based folders.
- Prefer deterministic fixtures and tests before adding live site adapters.

## QC Rules

- Block cards without region, headline, summary lines, and at least one source URL.
- Exclude personnel notices, simple procurement/bid notices, and photo-op-only items.
- Block text overflow before sending.
- Deduplicate by normalized URL and similar title.
- Keep source method and confidence in data, even when not shown prominently on cards.

