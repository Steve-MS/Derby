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

    # Check all 5 pages of Cato search for "(IRE)"
    all_cato = []
    for pg in range(1, 6):
        r = page.evaluate(f"""
            async () => {{
                const r = await fetch('/ajax/site-search/H/Cato/{pg}', {{
                    headers: {{'X-Requested-With': 'XMLHttpRequest', 'Accept': 'text/html, */*', 'Referer': 'https://www.attheraces.com/'}}
                }});
                return await r.text();
            }}
        """)
        # Extract all href="/form/horse/..." entries
        matches = re.findall(r'href="(/form/horse/[^"]+)"[^>]*>[^<]*<span>\s*([^<]+?)\s*</span>', r)
        all_cato.extend(matches)
        time.sleep(0.5)
    
    print("=== All Cato search results ===")
    for url, name in all_cato:
        print(f"  {name.strip()!r:30s} -> {url}")
    
    # Check IRE ones
    ire_catos = [(u, n) for u, n in all_cato if 'IRE' in n or '/IRE/' in u]
    print(f"\n=== Cato (IRE) entries: {len(ire_catos)} ===")
    for u, n in ire_catos:
        print(f"  {n!r} -> {u}")
    
    # Check Cato profile ID 3182235
    print("\n=== Cato profile /form/horse/Cato/3182235 ===")
    page.goto("https://www.attheraces.com/form/horse/Cato/3182235", wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)
    print("URL:", page.url)
    print("Title:", page.title())
    # Get header info (horse details)
    header = page.eval_on_selector_all(
        ".horse-profile-header, .horse-details, h1, h2, [class*=horse] p, [class*=profile] p",
        "els => els.map(e => e.innerText.trim().slice(0,150)).filter(t => t.length > 0).slice(0,8)"
    )
    print("Header info:")
    for h in header[:8]:
        print(f"  {h!r}")

    browser.close()
