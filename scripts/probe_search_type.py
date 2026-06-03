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

captured = []

def on_response(resp):
    url = resp.url
    if "attheraces.com" in url:
        try:
            ct = resp.headers.get("content-type", "")
            if "json" in ct:
                body = resp.body()
                captured.append((resp.status, url, body.decode("utf-8","replace")))
        except:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    )
    Stealth().apply_stealth_sync(context)
    context.add_cookies(load_cookies())
    page = context.new_page()
    page.on("response", on_response)

    page.goto("https://www.attheraces.com/", wait_until="networkidle", timeout=30000)
    time.sleep(2)
    
    # Click the search box and type
    search = page.locator("#site-header-search-nav-input")
    search.click()
    time.sleep(0.5)
    search.type("Belinus", delay=150)
    time.sleep(3)  # Wait for autocomplete

    print("=== JSON responses after search ===")
    for s, url, body in captured:
        print(f"\n[{s}] {url}")
        print(body[:1000])

    # Clear and try next horse
    captured.clear()
    search.triple_click()
    search.type("Constitution River", delay=150)
    time.sleep(3)

    print("\n=== JSON responses for Constitution River ===")
    for s, url, body in captured:
        print(f"\n[{s}] {url}")
        print(body[:1000])

    browser.close()
