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

def on_request(req):
    url = req.url
    if "search" in url.lower() or "autocomplete" in url.lower() or "suggest" in url.lower() or "find" in url.lower():
        captured.append(("REQ", req.method, url[:200]))

def on_response(resp):
    url = resp.url
    if "search" in url.lower() or "autocomplete" in url.lower() or "suggest" in url.lower() or "find" in url.lower():
        try:
            body = resp.body()
            captured.append(("RSP", resp.status, url[:200], body[:300].decode("utf-8","replace")))
        except:
            captured.append(("RSP", resp.status, url[:200]))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    )
    Stealth().apply_stealth_sync(context)
    context.add_cookies(load_cookies())
    page = context.new_page()
    page.on("request", on_request)
    page.on("response", on_response)

    page.goto("https://www.attheraces.com/", wait_until="domcontentloaded", timeout=30000)
    time.sleep(2)

    # Try to find and type into search box
    try:
        search_box = page.query_selector("input[type=search], input[placeholder*=earch], input[name*=earch], input[id*=earch]")
        if search_box:
            print("Found search box!")
            search_box.click()
            time.sleep(0.5)
            search_box.type("Belinus", delay=100)
            time.sleep(3)
        else:
            print("No search box found — looking at page inputs...")
            inputs = page.eval_on_selector_all("input", "els => els.map(e => ({type: e.type, id: e.id, name: e.name, placeholder: e.placeholder}))")
            for inp in inputs[:10]:
                print(f"  input: {inp}")
    except Exception as e:
        print(f"Search error: {e}")

    print("\n=== Captured search requests ===")
    for item in captured:
        print(item)

    browser.close()
