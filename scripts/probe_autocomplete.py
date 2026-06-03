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

all_reqs = []

def on_response(resp):
    url = resp.url
    if "attheraces.com" in url and "ajax" in url:
        try:
            body = resp.body()
            all_reqs.append((resp.status, url, body.decode("utf-8","replace")))
        except:
            all_reqs.append((resp.status, url, ""))

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
    page.locator("a.js-interface__search-trigger").click(timeout=5000)
    time.sleep(0.5)

    for horse_query in ["Belinus", "Cato", "Constitution"]:
        all_reqs.clear()
        search_input = page.locator("#site-header-search-nav-input")
        search_input.click(click_count=3)  # Select all
        search_input.type(horse_query, delay=150)
        time.sleep(3)
        
        print(f"\n=== Requests while typing '{horse_query}' ===")
        for s, url, body in all_reqs:
            print(f"  [{s}] {url}")
            if body.strip():
                print(f"  BODY: {body[:600]}")
        
        links = page.eval_on_selector_all(
            "a[href*='/form/horse/']",
            "els => els.slice(0,10).map(e => ({href: e.href, text: e.textContent.trim().slice(0,60)}))"
        )
        if links:
            print(f"  HORSE LINKS IN DOM:")
            for l in links:
                print(f"    {l}")

    browser.close()
