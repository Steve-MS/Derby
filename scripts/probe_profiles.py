import json, time
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

    # Constitution River profile - verify it loads
    page.goto("https://www.attheraces.com/form/horse/Constitution-River/3787036", wait_until="domcontentloaded", timeout=30000)
    time.sleep(4)
    print("=== Constitution River profile ===")
    print("URL:", page.url)
    print("Title:", page.title())
    h1 = page.query_selector("h1")
    print("H1:", h1.inner_text()[:100] if h1 else "none")

    # Sample the going history table
    rows = page.eval_on_selector_all(
        "table tr, .race-history tr, [class*=form] tr, [class*=table] tr",
        "els => els.slice(0,5).map(e => e.innerText.replace(/\\s+/g,' ').trim().slice(0,150))"
    )
    print("Table rows (first 5):")
    for r in rows[:5]:
        print(f"  {r!r}")

    # Try ATR search autocomplete for Belinus
    print("\n=== Belinus ATR search ===")
    r = page.request.get("https://www.attheraces.com/ajax/site-search/H/Belinus/1")
    print(f"Status: {r.status}")
    body = r.text()[:500]
    print(f"Body: {body}")

    # Try Cato search
    print("\n=== Cato ATR search ===")
    r2 = page.request.get("https://www.attheraces.com/ajax/site-search/H/Cato/1")
    print(f"Status: {r2.status}")
    body2 = r2.text()[:800]
    print(f"Body: {body2}")

    browser.close()
