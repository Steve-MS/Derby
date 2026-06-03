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

    # Navigate to Chester results - May 7, 2026 (Dee Stakes day)
    page.goto("https://www.attheraces.com/results/07-May-2026", wait_until="domcontentloaded", timeout=30000)
    time.sleep(4)
    print("=== Chester/May 7 results ===")
    print("URL:", page.url)
    print("Title:", page.title())

    # Find ALL horse form links
    links = page.eval_on_selector_all(
        "a[href*='/form/horse/']",
        "els => els.map(e => ({href: e.href, text: e.innerText.trim().slice(0,40)}))"
    )
    print(f"\nHorse profile links ({len(links)}):")
    for l in links:
        print(f"  {l['text']!r:40s} -> {l['href']}")

    # Search for Constitution River specifically
    const_links = [l for l in links if 'constitution' in l['href'].lower() or 'constitution' in l['text'].lower()]
    print(f"\n=== Constitution River links: {len(const_links)} ===")
    for l in const_links:
        print(f"  {l}")

    browser.close()
