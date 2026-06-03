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

api_calls = []

def on_response(resp):
    url = resp.url
    if "attheraces.com" in url and not url.endswith((".jpg",".png",".css",".js",".woff",".gif",".svg")):
        api_calls.append((resp.status, url[:200]))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    )
    Stealth().apply_stealth_sync(context)
    context.add_cookies(load_cookies())
    page = context.new_page()
    page.on("response", on_response)

    # Click search trigger, type, press Enter
    page.goto("https://www.attheraces.com/", wait_until="networkidle", timeout=30000)
    time.sleep(2)
    page.locator("a.js-interface__search-trigger").click(timeout=5000)
    time.sleep(0.5)
    search_input = page.locator("#site-header-search-nav-input")
    search_input.type("Belinus", delay=150)
    time.sleep(2)
    api_calls.clear()
    page.keyboard.press("Enter")
    time.sleep(4)

    print(f"URL after Enter: {page.url!r}")
    print(f"Title: {page.title()!r}")
    
    # Find all horse links on result page
    horse_links = page.eval_on_selector_all(
        "a[href*='/form/horse/']",
        "els => els.map(e => ({href: e.href, text: e.textContent.trim()}))"
    )
    print(f"\n=== Horse links on search result page ===")
    for l in horse_links[:20]:
        print(f"  {l}")

    print(f"\n=== All non-asset requests made ===")
    for s, url in api_calls:
        print(f"  [{s}] {url}")

    browser.close()
