import time
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright

mcp = FastMCP("Israel-Weather-Automation")

browser = None
page = None
pw = None

@mcp.tool()
async def init_browser():
    global browser, page, pw
    if page is None:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
# 3. הגדרת הכלים (Tools) עבור ה-AI - ללא העברת אובייקט ה-page מבחוץ
@mcp.tool()
async def open_forecast_page():
    await init_browser()
    await page.goto("https://www.weather2day.co.il/forecast")
    return "page opened"


@mcp.tool()
async def search_city(city_name: str):
    await init_browser()
    await page.locator("#city_search_forecast").fill(city_name)
    await page.keyboard.press("Enter")
    await page.wait_for_load_state("networkidle")
    return f"searched {city_name}"

@mcp.tool()
async def get_forecast_text() -> str:
    await init_browser()
    text = await page.locator("body").inner_text()
    return text[:1000]

# הוסיפי את הפונקציות האלו לקובץ func.py הקיים שלך

@mcp.tool()
async def login_to_gmail():
    """חיבור ל-Gmail לצורך שליפת הודעות"""
    await init_browser()
    # ניווט לתיבת הדואר
    await page.goto("https://mail.google.com/")
    # המתנה כדי שתוכלי לבצע Login ידני אם זה לא שמור
    # בשימוש ב-launch_persistent_context זה יישמר לפעם הבאה
    await page.wait_for_load_state("networkidle")
    return "Gmail page loaded"

@mcp.tool()
async def get_unread_emails_list() -> str:
    """שליפת 5 ההודעות האחרונות שלא נקראו"""
    await init_browser()
    # ניווט ישיר לחיפוש הודעות שלא נקראו
    await page.goto("https://mail.google.com/mail/u/0/#search/is%3Aunread")
    await page.wait_for_load_state("networkidle")
    
    # המתנה להופעת שורות ההודעות (הקלאס zA מסמן הודעה ב-Gmail)
    try:
        await page.wait_for_selector('tr.zA', timeout=10000)
        email_elements = await page.query_selector_all('tr.zA')
        
        results = []
        # שליפת 5 ההודעות הראשונות
        for i, el in enumerate(email_elements[:5]):
            text = await el.inner_text()
            results.append(f"הודעה {i+1}: {text.strip()}")
            
        if not results:
            return "לא נמצאו הודעות שלא נקראו."
        return "\n".join(results)
        
    except Exception as e:
        return f"שגיאה בשליפת הודעות: {str(e)}"

import re

@mcp.tool()
async def get_page_content() -> str:
    """שליפת וניקוי תוכן הדף הנוכחי כדי שה-AI יוכל לנתח אותו"""
    if page is None:
        return "הדפדפן אינו פתוח. אנא הפעילי אותו תחילה."

    # 1. שליפת ה-HTML של ה-body
    content = await page.evaluate("document.body.innerText")
    
    # 2. ניקוי בסיסי של רווחים מיותרים ושורות ריקות
    # הפיכת טקסט לטקסט נקי יותר לקריאת ה-AI
    cleaned_content = re.sub(r'\n\s*\n', '\n', content)
    cleaned_content = re.sub(r'\s{2,}', ' ', cleaned_content)
    
    # 3. הגבלת כמות הטקסט (כדי לא לחרוג ממכסת הטוקנים של Groq)
    # אנחנו שומרים את ה-10,000 תווים הראשונים שהם בדרך כלל מספיקים לתוכן המרכזי
    return cleaned_content[:10000]
# 4. הרצת שרת ה-MCP (השרת ימשיך לרוץ ויאזין לפקודות)
if __name__ == "__main__":
    mcp.run()