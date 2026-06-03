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

captured = []

def on_response(resp):
    url = resp.url
    if "attheraces.com" in url:
        try:
            ct = resp.headers.get("content-type", "")
            if "json" in ct:
                body = resp.body()
                captured.append((resp.status, url, body.decode("utf-8","replace")))
        except:
            pass

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

    # Find the search form action
    form_info = page.eval_on_selector_all(
        "form",
        "els => els.map(e => ({action: e.action, method: e.method, id: e.id, class: e.className}))"
    )
    print("=== Forms ===")
    for f in form_info:
        print(f"  {f}")

    # Find the search toggle button
    btns = page.eval_on_selector_all(
        "button, a",
        """els => els
            .filter(e => {
                const t = (e.textContent||'').toLowerCase() + (e.className||'').toLowerCase() + (e.getAttribute('aria-label')||'').toLowerCase();
                return t.includes('search');
            })
            .slice(0, 10)
            .map(e => ({tag: e.tagName, text: e.textContent.trim().slice(0,50), class: e.className.slice(0,80), href: e.href||''}))"""
    )
    print("\n=== Search-related buttons/links ===")
    for b in btns:
        print(f"  {b}")

    # Try to use fetch from within the page context
    print("\n=== Try fetch from page context ===")
    for horse in ["Belinus", "Cato", "Constitution River"]:
        try:
            result = page.evaluate(f"""async () => {{
                const r = await fetch('/api/search?q={horse}&type=horse', {{credentials: 'include'}});
                return {{status: r.status, url: r.url, ct: r.headers.get('content-type')}};
            }}""")
            print(f"  {horse}: {result}")
        except Exception as e:
            print(f"  {horse}: error {e}")

    browser.close()
