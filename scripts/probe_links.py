import json, re, time
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

    # Intercept navigation to detect horse URLs
    navigated_urls = []
    def handle_response(response):
        url = response.url
        if "horse" in url.lower() or "form" in url.lower():
            navigated_urls.append((response.status, url[:120]))
    page.on("response", handle_response)

    page.goto("https://www.attheraces.com/results", wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)
    print(f"Results page: {page.title()!r}")

    # Find any hrefs pointing to horse profiles
    links = page.eval_on_selector_all("a[href*='horse'], a[href*='form'], a[href*='guide']",
        "els => els.slice(0,20).map(e => e.href)")
    print(f"Links found: {len(links)}")
    for l in links[:20]:
        print(f"  {l}")

    browser.close()
