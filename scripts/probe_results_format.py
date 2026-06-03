import json, time, re
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

COOKIE_FILE = Path(r"C:\Users\stevenn\race-analysis\.cookies\attheraces.txt")
_SAMESITE_MAP = {"no_restriction": "None", "lax": "Lax", "strict": "Strict", "unspecified": "Lax"}

def load_cookies():
    raw = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
    out = []
    for c in raw.get("cookies", []):
        entry = {"name": c["name"], "value": c["value"], "domain": c["domain"],
                 "path": c.get("path", "/"), "httpOnly": c.get("httpOnly", False),
                 "secure": c.get("secure", False),
                 "sameSite": _SAMESITE_MAP.get(c.get("sameSite", "unspecified"), "Lax")}
        if not c.get("session", True) and "expirationDate" in c:
            entry["expires"] = int(c["expirationDate"])
        out.append(entry)
    return out

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    )
    Stealth().apply_stealth_sync(context)
    context.add_cookies(load_cookies())
    page = context.new_page()

    page.goto("https://www.attheraces.com/", wait_until="domcontentloaded", timeout=30000)
    time.sleep(2)

    # Check ATR results page without date
    page.goto("https://www.attheraces.com/results", wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)
    print("URL:", page.url)
    print("Title:", page.title())

    # Look at page structure to understand results URL format
    # Find date picker or navigation links
    nav_links = page.eval_on_selector_all(
        "a[href*='/results']",
        "els => els.map(e => ({href: e.href, text: e.innerText.trim().slice(0,30)})).slice(0,20)"
    )
    print("\n=== Results navigation links ===")
    for l in nav_links[:20]:
        print(f"  {l}")

    # Find any date input or date navigation
    dates = page.eval_on_selector_all(
        "input[type=date], .date-picker, [class*=date], [data-date]",
        "els => els.map(e => ({tag: e.tagName, type: e.type, value: e.value, href: e.href, class: e.className, placeholder: e.placeholder})).slice(0,10)"
    )
    print("\n=== Date elements ===")
    for d in dates[:10]:
        print(f"  {d}")

    # Get current URL format from breadcrumbs or heading  
    heading = page.eval_on_selector_all("h1, h2, .page-title, [class*=heading]",
        "els => els.map(e => e.innerText.slice(0,100)).filter(t => t.length > 0).slice(0,5)")
    print("\n=== Headings ===")
    for h in heading:
        print(f"  {h}")

    # Get the current page URL structure
    current_url = page.url
    print(f"\nFinal URL: {current_url}")

    browser.close()
