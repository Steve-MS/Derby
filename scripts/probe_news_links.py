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

    # Navigate to ATR news article about Constitution River
    url = "https://www.attheraces.com/news/2026/May/31/constitution-river-flows-to-french-derby-success"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)

    print("=== PAGE URL ===", page.url)
    print("=== PAGE TITLE ===", page.title())

    # Find all /form/horse/ links
    links = page.eval_on_selector_all(
        "a[href*='/form/horse/']",
        "els => els.map(e => e.href)"
    )
    print(f"\n=== /form/horse/ links ({len(links)}) ===")
    for l in links[:20]:
        print(f"  {l}")

    # Also look for all horse-related links
    all_horse_links = page.eval_on_selector_all(
        "a[href*='horse']",
        "els => els.map(e => ({href: e.href, text: e.innerText.trim().slice(0,50)}))"
    )
    print(f"\n=== All horse links ({len(all_horse_links)}) ===")
    for l in all_horse_links[:30]:
        print(f"  {l}")

    browser.close()
