import os
import re
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

mcp = FastMCP("Israel-Weather-Automation")

pw = None
browser = None
context = None
page = None


@mcp.tool()
async def init_browser() -> str:
    """Initialize Playwright browser context once."""
    global pw, browser, context, page

    if page is None:
        pw = await async_playwright().start()
        headless = os.getenv("PLAYWRIGHT_HEADLESS", "false").strip().lower() == "true"
        browser_channel = (os.getenv("PLAYWRIGHT_BROWSER_CHANNEL") or "chromium").strip().lower()

        # Use regular launch for stability. Persistent profiles can crash/lock on some Windows setups.
        try:
            if browser_channel == "chromium":
                browser = await pw.chromium.launch(headless=headless)
            else:
                browser = await pw.chromium.launch(headless=headless, channel=browser_channel)
        except Exception:
            browser = await pw.chromium.launch(headless=headless)

        context = await browser.new_context()
        page = await context.new_page()

    return "browser initialized"


@mcp.tool()
async def open_weather_forecast_israel() -> str:
    """Open weather2day forecast page for Israel workflow."""
    await init_browser()
    await page.goto("https://www.weather2day.co.il/forecast", wait_until="domcontentloaded")
    await page.wait_for_timeout(1200)
    return "opened weather forecast page"


@mcp.tool()
async def enter_weather_forecast_city_israel(city_name: str) -> str:
    """Type city name in weather2day forecast search field."""
    await init_browser()
    await page.locator("#city_search_forecast").fill(city_name)
    await page.wait_for_timeout(500)
    # Trigger autocomplete consistently across keyboard layouts.
    await page.keyboard.press("Space")
    await page.keyboard.press("Backspace")
    await page.wait_for_timeout(500)
    return f"typed city: {city_name}"


@mcp.tool()
async def select_weather_forecast_city_israel() -> str:
    """Select first city option from weather2day autocomplete list."""
    await init_browser()

    options = page.locator(".ui-menu-item a, .ui-menu-item-wrapper, .pac-item")
    option_count = await options.count()

    if option_count > 0:
        try:
            await options.first.click()
        except Exception:
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")
    else:
        await page.keyboard.press("ArrowDown")
        await page.keyboard.press("Enter")

    # Fallback: if still on forecast root, press Enter once more.
    await page.wait_for_timeout(900)
    if page.url.rstrip("/") == "https://www.weather2day.co.il/forecast":
        await page.keyboard.press("Enter")

    await page.wait_for_timeout(1600)
    return "selected city and submitted search"


@mcp.tool()
async def extract_weather_forecast_content_israel() -> str:
    """Extract and lightly clean current forecast page text for LLM reasoning."""
    await init_browser()
    content = await page.evaluate("document.body.innerText")
    cleaned_content = re.sub(r"\n\s*\n", "\n", content)
    cleaned_content = re.sub(r"\s{2,}", " ", cleaned_content)
    return cleaned_content[:12000]


@mcp.tool()
async def close_browser() -> str:
    """Close browser resources at end of workflow."""
    global pw, browser, context, page

    if page is not None:
        try:
            await page.close()
        except Exception:
            pass
    page = None

    if context is not None:
        try:
            await context.close()
        except Exception:
            pass
    context = None

    if browser is not None:
        try:
            await browser.close()
        except Exception:
            pass
    browser = None

    if pw is not None:
        try:
            await pw.stop()
        except Exception:
            pass
    pw = None

    return "browser closed"


if __name__ == "__main__":
    mcp.run()
