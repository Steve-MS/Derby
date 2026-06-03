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
    # Capture all API/XHR calls from attheraces domain
    if "attheraces.com" in url and ("/api/" in url or "json" in url.lower()):
        try:
            ct = resp.headers.get("content-type", "")
            if "json" in ct:
                body = resp.body()
                captured.append((resp.status, url, body[:500].decode("utf-8","replace")))
        except:
            captured.append((resp.status, url, ""))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    )
    Stealth().apply_stealth_sync(context)
    context.add_cookies(load_cookies())
    page = context.new_page()
    page.on("response", on_response)

    # Load homepage
    page.goto("https://www.attheraces.com/", wait_until="networkidle", timeout=30000)
    time.sleep(3)

    print("=== API calls on homepage ===")
    for s, url, body in captured:
        print(f"  [{s}] {url}")
        if body:
            print(f"       -> {body[:200]}")
    captured.clear()

    # Try to find visible search inputs via JS
    visible_inputs = page.eval_on_selector_all(
        "input", 
        """els => els
            .filter(e => {
                const r = e.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            })
            .map(e => ({type: e.type, id: e.id, name: e.name, class: e.className, placeholder: e.placeholder}))"""
    )
    print(f"\n=== Visible inputs ===")
    for inp in visible_inputs:
        print(f"  {inp}")

    browser.close()
