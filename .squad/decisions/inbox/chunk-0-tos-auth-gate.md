# Chunk 0 ToS/Auth Gate - Sporting Life live fetch for v0.5.0

Date: 2026-06-09
Repo: C:\Users\stevenn\race-analysis
Scope: Short reconnaissance gate for whether v0.5.0 ships live Sporting Life HTTP fetch or import-only.

## Method and request budget

HTTP GETs made: 5 total. No POSTs. No credentials read. No login attempt. User-Agent was a normal desktop browser UA.

1. https://www.sportinglife.com/robots.txt
2. https://www.sportinglife.com/
3. https://www.sportinglife.com/terms-and-conditions
4. https://www.sportinglife.com/racing/racecards/2026-06-16/ascot
5. https://www.sportinglife.com/account/login

Scratch evidence is in session workspace only: C:\Users\stevenn\.copilot\session-state\race-analysis-chunk0\.
HTML responses were not committed to the repo.

## Q1: robots.txt allowance for /racing/racecards/{date}/{course}

Fetched: https://www.sportinglife.com/robots.txt
Status: 200
Size: 159 bytes

Relevant robots.txt content:

```text
# Host
Host: https://www.sportinglife.com

# Sitemaps
Sitemap: https://www.sportinglife.com/sitemap.xml
Sitemap: https://www.sportinglife.com/sitemap-news.xml
```

Findings:

- There is no `User-agent: *` block.
- There are no `Allow:` or `Disallow:` directives.
- `/racing/racecards/` is unaddressed.
- No `Crawl-delay` directive is present.

Robots interpretation: no applicable robots rule disallows the racecards path. This is not an explicit allow-list; it is simply unrestricted by robots.txt.

Verdict for Q1: ALLOW

## Q2: Terms of Service / acceptable use and personal automation

Homepage footer exposed this ToS URL: https://www.sportinglife.com/terms-and-conditions
Fetched status: 200
Size: 129299 bytes

Keyword search hits included `scraping`, `API`, and `personal use`.

Relevant clause, under Fair Use / Copyright:

```text
We operate a 'fair usage' policy and, while normal behaviour will not contravene this, excessive high-frequency calls, by any means, may result in suspension of access to Sporting Life services. Data capture including, but not limited to, screen scraping is expressly prohibited.

Content and data are supplied for personal use. Copyright of all content is strictly reserved by Sporting Life and no material may be reproduced, stored or transmitted in any form or by any means without written permission. Content or data accessed on any Sporting Life product or via any Sporting Life service must not be copied, reproduced or distributed in any way without explicit permission.
```

Interpretation:

- The terms allow content/data to be used personally, but they expressly prohibit data capture including screen scraping.
- Steve's intended use is personal and non-commercial, but live automated capture of racecard data still falls inside the prohibited data-capture language.
- The fair-usage wording also warns that excessive high-frequency calls, by any means, may suspend access.

Verdict for Q2: PROHIBITS

## Q3: Auth flow and v0.5.0 tractability

### Unauthenticated racecard GET

Fetched: https://www.sportinglife.com/racing/racecards/2026-06-16/ascot
Status: 404
Size: 94812 bytes
Content-Type: text/html; charset=utf-8
First 1000 chars saved to: C:\Users\stevenn\.copilot\session-state\race-analysis-chunk0\04-racecard-first1000.txt

Static inspection:

- The response is not the Derby-Day <1 KB tiny shell; it is a full custom Next.js 404 page.
- It contains `__NEXT_DATA__`, but the embedded app state is only an error page: `page` is `/_error`; `pageProps.statusCode` is `404`.
- It contains no Cloudflare challenge, hCaptcha, or reCAPTCHA markers.
- Visible text starts with `Not Found ... Sorry, but the page you were trying to view does not exist.`

### Login page GET

Fetched: https://www.sportinglife.com/account/login
Status: 404
Size: 84357 bytes
Content-Type: text/html; charset=utf-8
First 1000 chars saved to: C:\Users\stevenn\.copilot\session-state\race-analysis-chunk0\05-login-first1000.txt

Static inspection:

- No HTML `<form>` was present.
- No username/password fields were present.
- No CSRF token field was present.
- No Cloudflare challenge, hCaptcha, or reCAPTCHA markers were present.
- The page was also a Next.js error page: `page` is `/_error`; `pageProps.statusCode` is `404`.

Auth-related links/references found in the fetched pages include:

```text
https://www.sportinglife.com/oauth/skybet
https://www.sportinglife.com/oauth/skybet/loading
https://www.sportinglife.com/api/oauth/codes
https://www.sportinglife.com/api/user/v2/sso
https://auth.skybetservices.com
https://identitysso.skybetservices.com
https://myaccount.skybetservices.com
```

Interpretation:

- I did not find a simple local login form POST.
- The static page references point toward a Sky Bet / Sporting Life SSO OAuth flow rather than a first-party username/password form.
- No credential submission was attempted, so this is a static characterization only.
- Env-var-driven Python could theoretically manage OAuth cookies only after a legitimate browser/session-cookie handoff, but implementing SSO/OAuth login itself is not a T-7 v0.5.0 job.

Verdict for Q3: OAUTH (NOT tractable in v0.5.0)

## Q4: Does the public page have enough unauthenticated racecard data?

Same racecard response as Q3:

- Status: 404
- Size: 94812 bytes
- `__NEXT_DATA__`: present, but only for `/_error` with status 404
- Race times (`HH:MM`): 0 matches
- `jockey`: 0 matches
- `trainer`: 0 matches
- `draw`: 0 matches
- `official rating`: 0 matches
- `OR`: 0 matches

Useful visible text quote:

```text
Not Found ... Sorry, but the page you were trying to view does not exist. Here are some helpful links: Horse Racing Football Greyhound Racing Cricket Darts Golf Join for free Log in Download the app ... Featured Events Cheltenham Royal Ascot Grand National
```

API / endpoint references observed in the page source:

- Auth / account endpoints were present, listed in Q3.
- No usable racecard data API endpoint was identified from this page without fetching bundles or making extra requests.
- The only racecard-like references were navigation/self links such as `/racing/racecards` and the requested URL.

Interpretation:

- The specific public page requested for 2026-06-16 Ascot did not contain a racecard.
- It did not contain embedded race data, runner data, jockey/trainer data, draw, OR, or form.
- This could be because the future card was not published yet, because the route is wrong, or because data loads later through app code; either way, v0.5.0 cannot rely on this anonymous GET for canonical raw card output.

Verdict for Q4: PUBLIC PAGE IS SPA SHELL

## Bonus: dependency decision

Recommendation: stdlib `urllib` only if any small policy/status probe remains; otherwise add no HTTP dependency for v0.5.0. The observed path points to import-only now, and future live auth appears OAuth/session based, where `requests` or `httpx` would not solve the core problem without a larger browser/session design.

## FINAL GATE VERDICT

Recommendation: GO-IMPORT-ONLY

Where:
- GO-LIVE-HTTP: robots ALLOW + ToS allows personal automation + auth is tractable (or unauthenticated card has full data). Ship v0.5.0 with live fetch as Danny scoped.
- GO-IMPORT-ONLY: robots/ToS issues OR auth is intractable in T-7 days. Ship v0.5.0 as "parse HTML/JSON file the operator drops, output canonical raw card." Defer live HTTP to v0.5.1.
- NO-GO-DEFER-FETCH: robots clearly disallow + ToS clearly prohibits + we should not scrape at all. Ship v0.5.0 as something else (e.g., schema validator only) or skip the release.

Confidence: HIGH
Rationale: Robots does not block the path, but the ToS expressly prohibits data capture including screen scraping. The tested anonymous racecard URL returned a Next.js 404/error page with no card data. The available static auth references point to SSO/OAuth, not a simple env-var form POST. v0.5.0 should therefore ship import-only and defer any live HTTP design until there is an allowed source or explicit permission/API.
