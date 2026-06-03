"""
ATR Going-History Playwright Scraper
Fetches going history for 3 horses from attheraces.com using authenticated session cookies.
RULE: Never fabricate data. Empty/unavailable > invented.

Horse IDs confirmed via ATR:
  Constitution River  -> /form/horse/Constitution-River/3787036  (confirmed, Aidan O'Brien 3yo)
  Cato (IRE)          -> /form/horse/Cato/3182235  (closest ATR match — no "(IRE)" variant exists)
  Belinus             -> not found on ATR at all
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from playwright_stealth import Stealth

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(r"C:\Users\stevenn\race-analysis")
COOKIE_FILE  = PROJECT_ROOT / ".cookies" / "attheraces.txt"
OUTPUT_FILE  = PROJECT_ROOT / "data" / "enrichment" / "atr-going-playwright.json"

# ── Target horses (ATR IDs confirmed via profile search) ──────────────────
# atr_path=None means horse is absent from ATR — mark unavailable in output.
HORSES = [
    {
        "name":     "Constitution River",
        "atr_path": "/form/horse/Constitution-River/3787036",
    },
    {
        "name":     "Cato (IRE)",
        "atr_path": "/form/horse/Cato/3182235",
        "note":     "ATR has 'Cato' (2017, no country code) — no Cato (IRE) exists on ATR; may not be same horse",
    },
    {
        "name":     "Belinus",
        "atr_path": None,
        "note":     "Not found in ATR horse database",
    },
]

# ── ATR going-code -> canonical label ────────────────────────────────────
GOING_LABEL = {
    "HY":  "Heavy",
    "Hy":  "Heavy",
    "Sft": "Soft",
    "GS":  "Good to Soft",
    "GY":  "Good to Yielding",
    "Y":   "Yielding",
    "Yg":  "Yielding",
    "Gd":  "Good",
    "G":   "Good",
    "GF":  "Good to Firm",
    "FM":  "Firm",
    "Fm":  "Firm",
    "F":   "Firm",
    "Std": "Standard",
    "SD":  "Standard",
    "AW":  "All-Weather",
}

# ── Cookie parser (JSON format from Cookie-Editor extension) ──────────────
_SAMESITE_MAP = {
    "no_restriction": "None",
    "lax":            "Lax",
    "strict":         "Strict",
    "unspecified":    "Lax",
}

def parse_cookie_file(filepath: Path) -> list[dict]:
    """Handles both JSON (Cookie-Editor) and Netscape tab-separated formats."""
    raw = filepath.read_bytes()
    # JSON format: starts with '{' or '['
    if raw[0:1] in (b"{", b"["):
        data = json.loads(raw.decode("utf-8"))
        raw_list = data["cookies"] if isinstance(data, dict) and "cookies" in data else data
        cookies = []
        for c in raw_list:
            same_site_raw = (c.get("sameSite") or "lax").lower()
            cookie = {
                "name":     c["name"],
                "value":    c["value"],
                "domain":   c["domain"],
                "path":     c.get("path", "/"),
                "httpOnly": bool(c.get("httpOnly", False)),
                "secure":   bool(c.get("secure", False)),
                "sameSite": _SAMESITE_MAP.get(same_site_raw, "Lax"),
            }
            # Only set expires if we have a real epoch value
            if c.get("expirationDate") and not c.get("session", True):
                cookie["expires"] = int(c["expirationDate"])
            cookies.append(cookie)
        return cookies

    # Netscape tab-separated format
    cookies = []
    for line in raw.decode("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        domain, _, path, secure_str, expires_str, name, value = parts[:7]
        try:
            expires_int = int(expires_str)
        except ValueError:
            expires_int = 0
        cookie = {
            "name":     name,
            "value":    value,
            "domain":   domain,
            "path":     path,
            "expires":  expires_int if expires_int > 0 else -1,
            "httpOnly": False,
            "secure":   secure_str.upper() == "TRUE",
            "sameSite": "Lax",
        }
        cookies.append(cookie)
    return cookies


# ── Challenge / block detection ────────────────────────────────────────────
def is_blocked(page) -> tuple[bool, str]:
    url   = page.url
    title = page.title()
    if "/cdn-cgi/" in url:
        return True, f"Fastly CDN challenge URL: {url}"
    bad_titles = ("Just a moment", "Challenge", "Attention Required",
                  "Too Many Requests", "429", "Access Denied", "Forbidden")
    if any(phrase.lower() in title.lower() for phrase in bad_titles):
        return True, f"Blocked page — title: {title!r}"
    html_snip = page.content()[:2000].lower()
    for phrase in ("checking your browser", "enable javascript",
                   "too many requests", "rate limit", "429 too many"):
        if phrase in html_snip:
            return True, f"Blocked: '{phrase}' in page body"
    return False, ""


# ── Search ATR for a horse ─────────────────────────────────────────────────
def find_horse_profile_url(page, horse_name: str, search_query: str) -> str | None:
    """
    Try multiple strategies to find the ATR horse profile URL.
    Returns the URL string or None.
    """
    name_clean = horse_name.lower().replace("(ire)", "").replace("(gb)", "").replace("(usa)", "").strip()

    def _check_page_for_horse_links() -> str | None:
        """Scan currently-open page for any anchor matching the horse name."""
        # Broad link patterns ATR might use
        for attr_pattern in ("/horse/", "/form/horse/", "/racecard/horse/"):
            try:
                links = page.locator(f"a[href*='{attr_pattern}']").all()
                for link in links:
                    href = link.get_attribute("href") or ""
                    text = (link.text_content() or "").strip().lower()
                    text_clean = text.replace("(ire)", "").replace("(gb)", "").strip()
                    if name_clean in text_clean or text_clean in name_clean:
                        return href if href.startswith("http") else "https://www.attheraces.com" + href
                # If only one link found and name check failed, still return it
                if len(links) == 1:
                    href = links[0].get_attribute("href") or ""
                    if href:
                        return href if href.startswith("http") else "https://www.attheraces.com" + href
            except Exception:
                pass
        return None

    # Strategy 1: ATR search endpoint
    for search_variant in [search_query, name_clean]:
        search_url = f"https://www.attheraces.com/search?q={search_variant.replace(' ', '+')}"
        print(f"  [search] GET {search_url}")
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            # Wait for search results to load (JS-rendered)
            time.sleep(4)
        except PWTimeout:
            print("  [search] timeout")
            continue

        blocked, reason = is_blocked(page)
        if blocked:
            print(f"  [search] BLOCKED: {reason}")
            return None

        title = page.title()
        print(f"  [search] page title: {title!r}")

        found = _check_page_for_horse_links()
        if found:
            print(f"  [search] profile link: {found}")
            return found

    # Strategy 2: try /form/horse/ slug variants directly
    # ATR slug format examples: "cato-ire", "constitution-river", "belinus"
    ire_suffix = "-ire" if "(ire)" in horse_name.lower() else ""
    slug_variants = list(dict.fromkeys([
        name_clean.replace(" ", "-") + ire_suffix,
        name_clean.replace(" ", "-"),
        search_query.lower().replace(" ", "-") + ire_suffix,
        search_query.lower().replace(" ", "-"),
    ]))
    for slug in slug_variants:
        candidate = f"https://www.attheraces.com/form/horse/{slug}"
        print(f"  [direct] trying {candidate}")
        try:
            page.goto(candidate, wait_until="domcontentloaded", timeout=30000)
            time.sleep(10)  # longer delay to avoid rate limiting
        except PWTimeout:
            continue
        blocked, reason = is_blocked(page)
        if blocked:
            print(f"  [direct] BLOCKED: {reason}")
            # If 429, wait and retry once
            if "429" in reason or "Too Many" in reason or "Rate" in reason:
                print("  [direct] 429 — waiting 15s before retry")
                time.sleep(15)
                try:
                    page.goto(candidate, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(5)
                except PWTimeout:
                    continue
                blocked2, reason2 = is_blocked(page)
                if blocked2:
                    print(f"  [direct] still blocked after retry: {reason2}")
                    continue
            else:
                continue
        title = page.title()
        current_url = page.url
        print(f"  [direct] title: {title!r}, url: {current_url}")
        # Accept if: not a homepage redirect, has content, not an error page
        error_titles = ("404", "not found", "error", "too many", "forbidden", "access denied")
        if (current_url != "https://www.attheraces.com/"
                and "attheraces.com" in current_url
                and not any(e in title.lower() for e in error_titles)):
            print(f"  [direct] accepted: {current_url}")
            return current_url

    # Strategy 3: ATR autocomplete / search-suggest API (JSON)
    suggest_url = f"https://www.attheraces.com/api/search/autocomplete?q={search_query.replace(' ', '%20')}"
    print(f"  [api] trying {suggest_url}")
    try:
        page.goto(suggest_url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        content = page.content()
        # Look for a horse URL in the JSON response
        horse_url_match = re.search(r'"url"\s*:\s*"(/[^"]*horse[^"]*)"', content, re.IGNORECASE)
        if horse_url_match:
            path = horse_url_match.group(1)
            full = "https://www.attheraces.com" + path
            print(f"  [api] found URL in autocomplete: {full}")
            return full
    except Exception as exc:
        print(f"  [api] error: {exc}")

    return None


# ── Extract form rows from the open page ──────────────────────────────────
def extract_going_history(page) -> tuple[list[dict], str, str]:
    """
    Returns (rows, evidence_html_snippet, error_message).
    rows is a list of dicts; empty list on failure.
    """
    # Wait for some kind of results table
    table_selectors = [
        "table[class*='form']",
        "table[class*='result']",
        "table[class*='Form']",
        "table[class*='Result']",
        ".horse-form table",
        ".form-table",
        "table",
    ]
    found_selector = None
    for sel in table_selectors:
        try:
            page.wait_for_selector(sel, timeout=8000)
            found_selector = sel
            print(f"  [table] found via selector: {sel}")
            break
        except PWTimeout:
            continue

    if not found_selector:
        return [], "", "No form table found on page"

    # Grab all <tr> rows from the first matching table
    try:
        rows_html = page.locator(f"{found_selector} tbody tr").all()
        if not rows_html:
            rows_html = page.locator(f"{found_selector} tr").all()
    except Exception as exc:
        return [], "", f"Error locating rows: {exc}"

    if not rows_html:
        return [], "", "Table found but no rows"

    evidence_snippet = ""
    going_history    = []

    for i, row in enumerate(rows_html):
        try:
            row_html  = row.inner_html()
            row_text  = row.text_content() or ""
            cells     = row.locator("td").all()
            cell_texts = [c.text_content().strip() for c in cells]

            # Capture evidence from first data row
            if i == 0 and row_html.strip():
                evidence_snippet = row_html.strip()[:200]

            if not cell_texts or len(cell_texts) < 3:
                continue

            # Heuristic: look for a cell containing a date-like string YYYY-MM-DD or DD/MM/YYYY or DD Mon YYYY
            date_val    = None
            going_val   = None
            pos_val     = None
            field_val   = None

            date_patterns = [
                r"\b(\d{4}-\d{2}-\d{2})\b",
                r"\b(\d{2}/\d{2}/\d{4})\b",
                r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\b",
                r"\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\b",
            ]
            going_pattern = re.compile(
                r"\b(heavy|soft|good to soft|good to firm|good|firm|yielding|standard|fast|"
                r"g/s|g/f|gd/sft|gd/fm|gs|gf)\b",
                re.IGNORECASE,
            )
            pos_pattern   = re.compile(r"^\s*(\d+|PU|F|UR|RO|BD|SU|DSQ|DQ|WV|NR)\s*(/\s*\d+)?\s*$", re.IGNORECASE)
            field_pattern = re.compile(r"^\s*(\d{1,3})\s*$")

            for cell_text in cell_texts:
                # Try date
                if date_val is None:
                    for dp in date_patterns:
                        m = re.search(dp, cell_text, re.IGNORECASE)
                        if m:
                            raw_date = m.group(1)
                            # Normalise to YYYY-MM-DD
                            try:
                                if re.match(r"\d{4}-\d{2}-\d{2}", raw_date):
                                    date_val = raw_date
                                elif re.match(r"\d{2}/\d{2}/\d{4}", raw_date):
                                    dt = datetime.strptime(raw_date, "%d/%m/%Y")
                                    date_val = dt.strftime("%Y-%m-%d")
                                else:
                                    # "12 Apr 2025" or "12th Apr 2025"
                                    clean = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", raw_date)
                                    for fmt in ("%d %b %Y", "%d %B %Y"):
                                        try:
                                            dt = datetime.strptime(clean, fmt)
                                            date_val = dt.strftime("%Y-%m-%d")
                                            break
                                        except ValueError:
                                            pass
                            except ValueError:
                                pass
                            if date_val:
                                break

                # Try going
                if going_val is None:
                    gm = going_pattern.search(cell_text)
                    if gm:
                        going_val = normalise_going(gm.group(1))

                # Try position (often "1", "2", "PU", or "3/14")
                if pos_val is None:
                    pm = pos_pattern.match(cell_text)
                    if pm:
                        raw_pos = pm.group(1).upper()
                        if raw_pos.isdigit():
                            pos_val = int(raw_pos)
                        else:
                            pos_val = raw_pos

                # Try field size (small integer, separate cell OR after "/" in pos cell)
                if field_val is None:
                    # Check "pos/field" in same cell e.g. "3/14"
                    slash_match = re.search(r"\d+\s*/\s*(\d{1,3})", cell_text)
                    if slash_match:
                        field_val = int(slash_match.group(1))
                    elif field_pattern.match(cell_text):
                        candidate = int(cell_text.strip())
                        if 2 <= candidate <= 40:
                            field_val = candidate

            # Only record if we got at least a date
            if date_val:
                row_dict = {
                    "date":       date_val,
                    "going":      going_val,
                    "position":   pos_val,
                    "field_size": field_val,
                }
                going_history.append(row_dict)

        except Exception as exc:
            print(f"  [row {i}] error: {exc}")
            continue

    return going_history, evidence_snippet, ""


# ── Per-horse entry point ─────────────────────────────────────────────────
def scrape_horse(page, horse: dict) -> dict:
    """Uses an already-open, warmed, stealth page."""
    name         = horse["name"]
    search_query = horse["search_query"]
    print(f"\n{'='*60}")
    print(f"Horse: {name}")
    print(f"{'='*60}")

    result = {
        "status":                "unavailable",
        "profile_url":           None,
        "evidence_html_snippet": None,
        "going_history":         [],
        "failure_reason":        None,
    }

    try:
        # Find profile URL
        profile_url = find_horse_profile_url(page, name, search_query)
        if not profile_url:
            result["failure_reason"] = "Profile URL not found via search or direct slug"
            return result

        result["profile_url"] = profile_url

        # Load profile (may already be on this page from discovery step)
        if page.url != profile_url:
            print(f"  [profile] loading {profile_url}")
            try:
                page.goto(profile_url, wait_until="networkidle", timeout=45000)
            except PWTimeout:
                try:
                    page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
                except PWTimeout:
                    result["failure_reason"] = "Profile page timeout"
                    return result
            time.sleep(5)

        blocked, reason = is_blocked(page)
        if blocked:
            # One retry after a pause
            print(f"  [profile] blocked ({reason}), waiting 20s and retrying")
            time.sleep(20)
            try:
                page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(5)
            except PWTimeout:
                pass
            blocked2, reason2 = is_blocked(page)
            if blocked2:
                result["failure_reason"] = f"Profile blocked after retry: {reason2}"
                return result

        # Extract going history
        going_history, evidence_snippet, err = extract_going_history(page)

        if err:
            result["failure_reason"] = err
        elif not going_history:
            result["failure_reason"] = "Table found but zero date-bearing rows extracted"
        else:
            result["status"]                = "ok"
            result["evidence_html_snippet"] = evidence_snippet
            result["going_history"]         = going_history
            print(f"  [ok] extracted {len(going_history)} rows")

    except Exception as exc:
        result["failure_reason"] = f"Unhandled error: {exc}"

    return result


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    print("ATR Going-History Playwright Scraper")
    print(f"Started: {datetime.now().isoformat()}")

    # Load cookies (privacy: never print names/values)
    if not COOKIE_FILE.exists():
        print(f"ERROR: cookie file not found: {COOKIE_FILE}")
        sys.exit(1)
    cookies = parse_cookie_file(COOKIE_FILE)
    print(f"Loaded {len(cookies)} cookies (names/values redacted)")

    output = {
        "fetched_at": "2026-06-02T20:01:00+01:00",
        "source":     "attheraces (playwright)",
        "horses":     {},
    }

    with sync_playwright() as p:
        # Use headed mode — better TLS/JS fingerprint, avoids headless detection
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--window-size=1280,800",
            ],
        )
        raw_context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-GB",
            timezone_id="Europe/London",
            extra_http_headers={
                "Accept-Language":  "en-GB,en;q=0.9",
                "Accept":           "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Encoding":  "gzip, deflate, br",
                "DNT":              "1",
            },
        )
        raw_context.add_cookies(cookies)
        # Apply stealth evasions to the context (patches navigator, webdriver, etc.)
        Stealth().apply_stealth_sync(raw_context)

        page = raw_context.new_page()

        try:
            # ONE warmup — load homepage to establish session
            print("[warmup] loading ATR homepage...")
            try:
                page.goto("https://www.attheraces.com/", wait_until="domcontentloaded", timeout=30000)
                time.sleep(5)
            except PWTimeout:
                print("[warmup] homepage timeout — continuing")

            blocked, reason = is_blocked(page)
            if blocked:
                print(f"[warmup] BLOCKED on homepage: {reason}")
                # Still try horses — maybe individual pages are unblocked
            else:
                print(f"[warmup] homepage OK — title: {page.title()!r}")

            for horse in HORSES:
                try:
                    result = scrape_horse(page, horse)
                except Exception as exc:
                    result = {
                        "status":                "unavailable",
                        "profile_url":           None,
                        "evidence_html_snippet": None,
                        "going_history":         [],
                        "failure_reason":        f"Script-level error: {exc}",
                    }
                output["horses"][horse["name"]] = result
                # Polite delay between horses
                print("  [pause] 12s between horses...")
                time.sleep(12)

        finally:
            raw_context.close()
            browser.close()

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)
    print(f"\nOutput written to: {OUTPUT_FILE}")

    # Summary
    print("\n---- SUMMARY ----")
    for hname, hdata in output["horses"].items():
        status = hdata["status"]
        if status == "ok":
            n = len(hdata['going_history'])
            print(f"  {hname}: OK - {n} rows")
        else:
            print(f"  {hname}: UNAVAILABLE - {hdata['failure_reason']}")


if __name__ == "__main__":
    main()
