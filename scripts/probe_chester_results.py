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

    # Try ATR results page for Chester May 7, 2026 (Dee Stakes day)
    page.goto("https://www.attheraces.com/results/chester/07-05-2026", wait_until="domcontentloaded", timeout=30000)
    time.sleep(4)
    print("URL:", page.url)
    print("Title:", page.title())

    # Find all horse form links
    links = page.eval_on_selector_all(
        "a[href*='/form/horse/']",
        "els => els.map(e => ({href: e.href, text: e.innerText.trim().slice(0,40)}))"
    )
    print(f"\n=== Horse form links ({len(links)}) ===")
    for l in links:
        if any(n in l.get('href','').lower() or n in l.get('text','').lower() 
               for n in ['constitution', 'belinus', 'cato', 'dee', 'hawk']):
            print(f"  *** {l}")
        else:
            print(f"  {l}")

    # Also try a general results search for these horse names
    print("\n=== All horse links containing 'constitution' ===")
    all_links = page.eval_on_selector_all(
        "a",
        "els => els.filter(e => e.href.toLowerCase().includes('constitution') || e.innerText.toLowerCase().includes('constitution')).map(e => ({href: e.href, text: e.innerText.trim().slice(0,60)}))"
    )
    for l in all_links:
        print(f"  {l}")

    browser.close()
