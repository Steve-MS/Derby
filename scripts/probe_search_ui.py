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

    # Use browser UI search - find the search input and type "Belinus"
    search_input = page.query_selector("input[type=search], input[placeholder*=earch], input[name*=search], .search-input, #search")
    if not search_input:
        # Try to find any search input
        inputs = page.eval_on_selector_all("input", "els => els.map(e => ({type: e.type, name: e.name, placeholder: e.placeholder, class: e.className, id: e.id})).slice(0,20)")
        print("All inputs:", inputs[:10])
    else:
        print("Found search input:", search_input.get_attribute("class"), search_input.get_attribute("placeholder"))
        search_input.click()
        search_input.type("Belinus", delay=100)
        time.sleep(2)
        # Capture autocomplete
        sugg = page.eval_on_selector_all(
            "[class*=suggest], [class*=autocomplete], [class*=dropdown] a, [role=option], [role=listbox] li",
            "els => els.map(e => ({text: e.innerText.trim().slice(0,100), href: e.href}))"
        )
        print(f"Belinus autocomplete ({len(sugg)}):", sugg[:10])
        time.sleep(1)
        search_input.triple_click()
        search_input.type("Cato", delay=100)
        time.sleep(2)
        sugg2 = page.eval_on_selector_all(
            "[class*=suggest], [class*=autocomplete], [class*=dropdown] a, [role=option], [role=listbox] li",
            "els => els.map(e => ({text: e.innerText.trim().slice(0,100), href: e.href}))"
        )
        print(f"\nCato autocomplete ({len(sugg2)}):", sugg2[:10])

    browser.close()
