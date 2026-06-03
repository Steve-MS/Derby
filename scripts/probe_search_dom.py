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
    if "attheraces.com" in resp.url and "/ajax/" in resp.url:
        try:
            all_reqs.append((resp.status, resp.url, resp.body().decode("utf-8","replace")[:1000]))
        except:
            all_reqs.append((resp.status, resp.url, ""))

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

    # Trigger search and look at DOM changes
    page.locator("a.js-interface__search-trigger").click(timeout=5000)
    time.sleep(0.5)
    search_input = page.locator("#site-header-search-nav-input")
    search_input.click(click_count=3)
    search_input.type("Belinus", delay=150)
    time.sleep(1)
    all_reqs.clear()
    page.keyboard.press("Enter")
    time.sleep(4)

    print("=== AJAX after submit ===")
    for s, url, body in all_reqs:
        print(f"[{s}] {url}")
        print(f"BODY: {body}")

    # Look at page structure after search
    # Find any search result containers
    containers = page.eval_on_selector_all(
        ".site-search-results, .search-results, [class*=search], [id*=search]",
        "els => els.map(e => ({tag: e.tagName, id: e.id, class: e.className, text: e.innerText.slice(0,200)}))"
    )
    print(f"\n=== Search result containers ===")
    for c in containers[:10]:
        print(f"  {c}")

    browser.close()
