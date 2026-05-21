# PRD: Jeonnam Daily Issue Card Briefing

## Goal

Every morning, collect key issues for Jeonnam's 22 cities/counties, create one concise card per region when a meaningful issue exists, and send the card bundle to Telegram.

## MVP

1. Collect issue candidates from structured source adapters.
2. Normalize candidate records into one schema.
3. Score candidates by relevance, public impact, source quality, and recency.
4. Deduplicate repeated URL/title items.
5. Select at most one primary issue per region.
6. Build card specs with headline, 2-3 summary lines, category, confidence, and sources.
7. Render 1080x1350 PNG cards via HTML/CSS.
8. Run QC gates.
9. Prepare Telegram dry-run/send payload.
10. Archive daily artifacts.

## Reference Architecture

- `openclaw-newsroom`: source collection, SQLite dedup, scoring, editorial profile.
- `card-news-publication-workflow`: JSON spec, validation, HTML-to-PNG rendering.
- `insane-search`: fallback for blocked or SPA-heavy source pages.
- OpenClaw SNS workflows: cron, channel delivery, operational memory.
- Imagegen skills: optional reusable background asset generation only.

## Regions

목포시, 여수시, 순천시, 나주시, 광양시, 담양군, 곡성군, 구례군, 고흥군, 보성군, 화순군, 장흥군, 강진군, 해남군, 영암군, 무안군, 함평군, 영광군, 장성군, 완도군, 진도군, 신안군.

## Exclusions

- 인사발령
- 입찰/계약/구매 공고만 있는 문서
- 채용 공고
- 기관장 동정/사진행사만 있는 보도자료
- 지역명이 우연히 언급된 전국 기사

## Success Metrics

- 07:00 KST delivery success rate >= 95%
- region misclassification <= 5 per month
- duplicate cards <= 10 per month
- source URL coverage = 100%

