from __future__ import annotations

import os

from firecrawl import FirecrawlApp


firecrawl = FirecrawlApp(
    api_key=os.getenv("FIRECRAWL_API_KEY")
)


def search_web(query: str):
    return firecrawl.search(query)


def scrape_url(url: str) -> str:
    result = firecrawl.scrape_url(
        url,
        params={
            "formats": ["markdown"]
        }
    )

    return result.get("markdown", "")