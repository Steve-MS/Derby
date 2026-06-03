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

    # Click the search trigger button to reveal the search box
    trigger = page.locator("a.js-interface__search-trigger")
    trigger.click(timeout=5000)
    time.sleep(1)

    print("=== JSON API calls captured ===")
    for s, url, body in captured:
        print(f"\n[{s}] {url}")
        print(body[:500])
    captured.clear()

    # Now the search input should be visible, type into it
    search_input = page.locator("#site-header-search-nav-input")
    search_input.type("Belinus", delay=150)
    time.sleep(4)

    print("\n=== JSON API calls after typing ===")
    for s, url, body in captured:
        print(f"\n[{s}] {url}")
        print(body[:800])

    # Also check what links appeared in the autocomplete dropdown
    links = page.eval_on_selector_all(
        "a[href*='horse'], a[href*='form']",
        "els => els.map(e => ({href: e.href, text: e.textContent.trim().slice(0,80)}))"
    )
    print(f"\n=== Links in autocomplete ===")
    for l in links[:20]:
        print(f"  {l}")

    browser.close()
