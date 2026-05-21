# PRD: Jeonnam Daily Issue Card Briefing

## Goal

Every morning, collect key issues for Jeonnam's 22 cities/counties, create one concise card per region when a meaningful issue exists, and send the card bundle to Telegram.

## MVP

1. Collect issue candidates from structured source adapters.
2. Normalize candidate records into one schema.
3. Score candidates by relevance, public impact, source quality, and recency.
4. Deduplicate repeated URL/title items.
5. Select at most one primary issue per region.
6. Build one daily card spec with headline, 3 summary paragraphs, category, confidence, and sources.
7. Render 1080x1350 PNG cards via HTML/CSS.
8. Run QC gates.
9. Prepare Telegram dry-run/send payload.
10. Archive daily artifacts.

## Card Design System

- Default region cards use a dark editorial photo-overlay style: one strong headline, blue emphasis, fuller 3-paragraph body copy, and a small source footer.
- Metadata such as category, confidence, and date stays in the card spec for audit, but is not shown prominently on the card.
- Fallback backgrounds should look like public briefings, meetings, documents, markets, roads, weather, or other news-relevant scenes rather than decorative abstract art.
- When source articles provide a representative image, use it as the card background with a dark overlay; otherwise use a deterministic fallback background.
- Inline blue accents should highlight the issue-driving phrase, number, risk, deadline, place, or action, not arbitrary region metadata.
- A `contrast` variant may be inserted when two credible sources, agencies, regions, or datasets interpret the same issue differently. It should use a single thesis headline and two short labeled blocks, with blue emphasis reserved for the disagreement point.
- Use the `contrast` variant only when the distinction materially changes public interpretation or follow-up action; do not use it for routine duplicate coverage.
- An `outlook` variant may be appended after the region cards when the day has a clear cross-region pattern. It answers "what next?" with 2-3 short lines and can use a more atmospheric landscape/crossroads background.
- Use the `outlook` variant only for editorial synthesis across multiple cards, not for a single city/county press release.
- A `cta` variant may be appended as the final card when a daily bundle is sent to a broad audience. It should use a portrait/brand-style visual, one short call to action, and one access line such as Telegram channel, GitHub Pages archive, or search link.
- The `cta` variant should not repeat news content. It exists only to guide readers to the full archive, subscribe/share destination, or source index.

## Reference Architecture

- `openclaw-newsroom`: source collection, SQLite dedup, scoring, editorial profile.
- `card-news-publication-workflow`: JSON spec, validation, HTML-to-PNG rendering.
- `insane-search`: fallback for blocked or SPA-heavy source pages.
- `crawl4ai`: browser/Markdown extraction fallback for inconsistent city/county HTML boards.
- `ScrapeGraphAI`: LLM-guided structured extraction for adapter bootstrapping and one-off difficult pages.
- OpenClaw SNS workflows: cron, channel delivery, operational memory.
- Imagegen skills: optional reusable background asset generation only.
- Korean news RSS gist: national/regional media RSS fallback candidates, not official city/county sources.

## Regions

목포시, 여수시, 순천시, 나주시, 광양시, 담양군, 곡성군, 구례군, 고흥군, 보성군, 화순군, 장흥군, 강진군, 해남군, 영암군, 무안군, 함평군, 영광군, 장성군, 완도군, 진도군, 신안군.

## Exclusions

- 인사발령
- 입찰/계약/구매 공고만 있는 문서
- 채용 공고
- 기관장 동정/사진행사만 있는 보도자료
- 지역명이 우연히 언급된 전국 기사

## Source Strategy

1. Official city/county board adapters are the primary source for each region.
2. Jeonnam province RSS is the primary province-level official source.
3. National and regional media RSS feeds are fallback/corroboration sources.
4. Search adapters fill gaps when official boards or RSS feeds are missing.
5. Media RSS-only candidates require stricter region and public-impact scoring than official sources.
6. Crawl4AI-style browser/Markdown extraction is used when a city/county HTML board is dynamic, inconsistent, or hard to parse with static selectors.
7. Successful Crawl4AI discoveries should be promoted into deterministic adapters for recurring runs.
8. ScrapeGraphAI-style LLM extraction is reserved for prototyping selectors/schema or one-off hard pages, not the default daily production path.

## Crawler Adapter Policy

- Basic RSS and static HTML adapters should run first because they are fast and reproducible.
- Crawl4AI is optional fallback infrastructure for difficult public pages, not a replacement for source-specific adapters.
- Raw Markdown, extracted links, and metadata from Crawl4AI runs must be archived under `data/raw/YYYY-MM-DD/`.
- A source method field must distinguish `rss`, `html_board`, `crawl4ai_markdown`, and `search_fallback`.
- Browser-based crawls should be capped by page count and timeout to avoid delaying the 07:00 delivery.
- LLM-based extraction outputs must store the prompt, model/provider, source URL, and resulting JSON for audit.
- Recurring LLM extraction logic must be replaced with deterministic adapters once the page pattern is understood.

## Success Metrics

- 07:00 KST delivery success rate >= 95%
- region misclassification <= 5 per month
- duplicate cards <= 10 per month
- source URL coverage = 100%
