from __future__ import annotations

import os

from firecrawl import FirecrawlApp


def get_client() -> FirecrawlApp:
    """
    Retrieves or initializes the FirecrawlApp client using the environment API key.
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY environment variable is missing.")
    return FirecrawlApp(api_key=api_key)


def search_web(query: str):
    """
    Search the web using Firecrawl.
    Returns a list of search result items.
    """
    try:
        client = get_client()
        result = client.search(query)

        if hasattr(result, "web"):
            return result.web
        elif isinstance(result, dict):
            return result.get("data", []) or result.get("web", [])
        return result
    except Exception as e:
        print(f"Error in search_web: {e}")
        return []


def scrape_web(url: str) -> str:
    """
    Extract markdown content from a URL using Firecrawl.
    """
    try:
        client = get_client()
        result = client.scrape_url(
            url,
            params={"formats": ["markdown"]}
        )

        if hasattr(result, "markdown"):
            return result.markdown
        elif isinstance(result, dict):
            return result.get("markdown", "")
        return str(result)
    except Exception as e:
        print(f"Error in scrape_web for {url}: {e}")
        return ""


def crawl_web(url: str) -> list[dict]:
    """
    Crawl a website and return a list of page objects.
    """
    try:
        client = get_client()
        result = client.crawl_url(
            url,
            params={
                "limit": 5,
                "scrapeOptions": {
                    "formats": ["markdown"]
                },
            },
        )

        if hasattr(result, "data"):
            return result.data
        elif isinstance(result, dict):
            return result.get("data", [])
        return []
    except Exception as e:
        print(f"Error in crawl_web for {url}: {e}")
        return []