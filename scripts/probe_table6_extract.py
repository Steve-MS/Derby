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

    page.goto("https://www.attheraces.com/form/horse/Constitution-River/3787036", wait_until="domcontentloaded", timeout=30000)
    time.sleep(5)

    # Extract Table 6 full data using JS
    table6_data = page.evaluate("""
        () => {
            const tables = Array.from(document.querySelectorAll('table'));
            const t = tables[6];  // Table index 6
            const rows = Array.from(t.querySelectorAll('tr'));
            return rows.map(row => {
                const cells = Array.from(row.querySelectorAll('td, th'));
                return {
                    tag: cells.length > 0 ? cells[0].tagName : 'empty',
                    cells: cells.map(c => c.innerText.replace(/\\s+/g,' ').trim())
                };
            });
        }
    """)
    
    print("=== Table 6 all rows ===")
    for row in table6_data:
        print(f"  [{row['tag']}] {row['cells']}")

    # Also check the HTML structure of Race Details cell to understand inner structure
    detail_html = page.evaluate("""
        () => {
            const tables = Array.from(document.querySelectorAll('table'));
            const t = tables[6];
            const rows = Array.from(t.querySelectorAll('tbody tr'));
            if (rows.length === 0) return 'no rows in tbody';
            const firstDataRow = rows[0];
            const cells = Array.from(firstDataRow.querySelectorAll('td'));
            return cells[1] ? cells[1].innerHTML : 'no second cell';
        }
    """)
    print("\n=== Race Details cell HTML (1st data row) ===")
    print(detail_html[:1000])

    # Also check structure of Result cell
    result_html = page.evaluate("""
        () => {
            const tables = Array.from(document.querySelectorAll('table'));
            const t = tables[6];
            const rows = Array.from(t.querySelectorAll('tbody tr'));
            if (rows.length === 0) return 'no rows in tbody';
            return rows.map((r, i) => {
                const cells = Array.from(r.querySelectorAll('td'));
                const date_cell = cells[0] ? cells[0].innerText.trim() : '';
                const detail = cells[1] ? cells[1].innerText.replace(/\\s+/g, ' ').trim() : '';
                const result = cells[3] ? cells[3].innerText.replace(/\\s+/g, ' ').trim() : '';
                return {row: i, date: date_cell, detail, result};
            });
        }
    """)
    print("\n=== Table 6 key columns ===")
    for r in result_html:
        print(f"  row {r['row']}: date={r['date']!r:20s} detail={r['detail']!r:40s} result={r['result']!r}")

    browser.close()
