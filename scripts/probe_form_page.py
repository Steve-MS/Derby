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

    # Warm up with homepage
    page.goto("https://www.attheraces.com/", wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)

    # Navigate to ATR form page (horse search section)
    page.goto("https://www.attheraces.com/form", wait_until="domcontentloaded", timeout=30000)
    time.sleep(5)

    title = page.title()
    url = page.url
    print(f"URL: {url}")
    print(f"Title: {title}")

    # First 3000 chars of body
    body = page.content()[:3000]
    print(f"\nHTML SNIPPET:\n{body}")

    # Check for horse search form
    forms = page.eval_on_selector_all("form", "els => els.map(e => ({action: e.action, method: e.method, html: e.outerHTML.slice(0,300)}))")
    print(f"\n=== Forms ===")
    for f in forms[:5]:
        print(f)

    # Check for input elements
    inputs = page.eval_on_selector_all("input[type=text], input[type=search]", 
                                        "els => els.map(e => ({name: e.name, id: e.id, placeholder: e.placeholder}))")
    print(f"\n=== Text inputs ===")
    for i in inputs[:10]:
        print(i)

    browser.close()
