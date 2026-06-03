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

    page.goto("https://www.attheraces.com/form/horse/Constitution-River/3787036", wait_until="domcontentloaded", timeout=30000)
    time.sleep(5)

    # Find all tables and check headers to identify the race history table
    tables_info = page.evaluate("""
        () => {
            const tables = Array.from(document.querySelectorAll('table'));
            return tables.map((t, i) => {
                const headers = Array.from(t.querySelectorAll('th')).map(th => th.innerText.trim()).join(' | ');
                const rowCount = t.querySelectorAll('tr').length;
                const firstRows = Array.from(t.querySelectorAll('tr')).slice(0,3).map(tr => 
                    Array.from(tr.querySelectorAll('td, th')).map(c => c.innerText.trim().slice(0,20)).join(' | '));
                return {index: i, headers: headers.slice(0,200), rowCount, firstRows};
            });
        }
    """)
    
    print(f"Found {len(tables_info)} tables")
    for t in tables_info:
        print(f"\n[Table {t['index']}] rows={t['rowCount']} headers={t['headers'][:150]!r}")
        for row in t['firstRows'][:3]:
            print(f"  {row[:150]!r}")

    browser.close()
