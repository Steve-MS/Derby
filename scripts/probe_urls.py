import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    )
    page = context.new_page()

    # Try navigating to ATR and look for horse URLs
    page.goto("https://www.attheraces.com/", wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)
    
    # Try the form/guide section
    for url in [
        "https://www.attheraces.com/form",
        "https://www.attheraces.com/results", 
        "https://www.attheraces.com/racecard",
    ]:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)
        print(f"URL: {url} -> title: {page.title()!r}, final_url: {page.url!r}")

    browser.close()
