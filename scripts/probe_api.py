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
    time.sleep(3)

    for query in ["Cato", "Belinus", "Constitution River"]:
        api_url = f"https://www.attheraces.com/api/search/autocomplete?q={query.replace(' ', '%20')}"
        print(f"\n=== Query: {query} ===")
        try:
            r = page.goto(api_url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            body = page.content()
            # Try to parse JSON from body
            import re
            m = re.search(r'<pre[^>]*>(.*?)</pre>', body, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1))
                    print(json.dumps(data, indent=2)[:2000])
                except:
                    print(body[:1000])
            else:
                print(f"Status: {r.status if r else '?'}")
                print(body[:1000])
        except Exception as e:
            print(f"Error: {e}")

    browser.close()
