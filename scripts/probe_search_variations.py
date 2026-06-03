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

    # Try calling the search AJAX endpoint directly from page context
    queries = [
        ("H", "Belinus"),
        ("H", "Cato"),
        ("H", "Constitution"),
        ("H", "Bel"),
        ("H", "Cato+IRE"),
        ("", "Belinus"),  # no type prefix
    ]

    for typ, q in queries:
        if typ:
            url = f"/ajax/site-search/{typ}/{q}/1"
        else:
            url = f"/ajax/site-search/{q}/1"
        try:
            result = page.evaluate(f"""async () => {{
                const r = await fetch('{url}', {{credentials: 'include'}});
                return {{status: r.status, body: (await r.text()).slice(0,300)}};
            }}""")
            print(f"[{result['status']}] {url}")
            print(f"   -> {result['body']!r}")
        except Exception as e:
            print(f"ERR {url}: {e}")
        time.sleep(1)

    browser.close()
