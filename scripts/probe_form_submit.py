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
            all_reqs.append((resp.status, resp.url, resp.body().decode("utf-8","replace")[:600]))
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

    # Try form submit via URL
    for query in ["Belinus", "Cato", "Constitution+River"]:
        all_reqs.clear()
        url = f"https://www.attheraces.com/?search={query}"
        print(f"\n=== GET {url} ===")
        r = page.goto(url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)
        print(f"  Status: {r.status if r else '?'}, Title: {page.title()!r}, Final URL: {page.url!r}")
        
        horse_links = page.eval_on_selector_all(
            "a[href*='/form/horse/']",
            "els => els.map(e => ({href: e.href, text: e.textContent.trim().slice(0,60)}))"
        )
        # Filter for matching horse names
        query_words = query.lower().replace("+", " ").split()
        matching = [l for l in horse_links if any(w in l["text"].lower() or w in l["href"].lower() for w in query_words)]
        print(f"  Matching horse links: {len(matching)}")
        for l in matching[:5]:
            print(f"    {l}")
        if not matching and horse_links:
            print(f"  All horse links (first 5): {horse_links[:5]}")
        
        for s, u, b in all_reqs:
            print(f"  AJAX [{s}] {u}")
            if b.strip():
                print(f"  -> {b[:400]}")

    browser.close()
