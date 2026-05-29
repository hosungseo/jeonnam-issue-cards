#!/usr/bin/env python3
"""Render a JS page to HTML via crawl4ai (run with the 3.13 .venv-crawl).

Standalone because crawl4ai needs python 3.10+ and a browser, while the main
pipeline runs on python 3.9. http_client.fallback_fetch shells out to this.

Usage: .venv-crawl/bin/python scripts/crawl_fetch.py <url>
Prints rendered HTML to stdout, or exits non-zero on failure.
"""
import asyncio
import sys


async def render(url: str) -> str:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    from crawl4ai.async_configs import BrowserConfig

    browser = BrowserConfig(headless=True, verbose=False)
    run = CrawlerRunConfig(page_timeout=30000, wait_until="networkidle",
                           delay_before_return_html=2.0)
    async with AsyncWebCrawler(config=browser) as crawler:
        result = await crawler.arun(url=url, config=run)
        if not result.success:
            print(f"crawl failed: {result.error_message}", file=sys.stderr)
            return ""
        return result.html or ""


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: crawl_fetch.py <url>", file=sys.stderr)
        sys.exit(2)
    html = asyncio.run(render(sys.argv[1]))
    if not html:
        sys.exit(1)
    sys.stdout.write(html)


if __name__ == "__main__":
    main()
