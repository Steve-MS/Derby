"""
check_env.py — Startup credential validator for race-analysis.

Reads required / optional environment variables, checks they are set,
non-empty, and not still holding the placeholder values from .env.example.

Exit codes:
  0  — all required vars are set and look real
  1  — one or more required vars missing or still placeholder

Usage:
    python scripts/check_env.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Single source of truth: var registry
#
# Each entry:
#   required    (bool)  – True → exit 1 if missing/placeholder
#   description (str)   – human-readable purpose
#   placeholder (str)   – exact placeholder string used in .env.example
#   get_it_at   (str)   – where to obtain a real value
#   default     (str|None) – shown in warning if optional and unset
# ─────────────────────────────────────────────────────────────────────────────

ENV_VARS: dict[str, dict] = {
    "SPORTINGLIFE_USER": {
        "required": True,
        "description": (
            "Sporting Life registered email address — needed for authenticated "
            "form and live-odds scraping.  Without this the scraper receives a "
            "373-byte JavaScript SPA shell and silently returns no data."
        ),
        "placeholder": "<your-sportinglife-email>",
        "get_it_at": "https://www.sportinglife.com/racing  (free registration)",
        "default": None,
    },
    "SPORTINGLIFE_PASS": {
        "required": True,
        "description": "Password for the Sporting Life account set in SPORTINGLIFE_USER.",
        "placeholder": "<your-sportinglife-password>",
        "get_it_at": "https://www.sportinglife.com/racing  (free registration)",
        "default": None,
    },
    "ATR_COOKIE_FILE": {
        "required": False,
        "description": (
            "Path to the At The Races session cookie file (JSON format, exported "
            "via Cookie-Editor browser extension after logging in).  Used by "
            "Playwright scrapers for horse form history."
        ),
        "placeholder": "<path-to-atr-cookies.txt>",
        "get_it_at": (
            "https://www.attheraces.com — log in, then export cookies with the "
            "Cookie-Editor browser extension"
        ),
        "default": ".cookies/attheraces.txt",
    },
    "RACING_API_KEY": {
        "required": False,
        "description": (
            "API key for The Racing API live-price feed.  Not yet integrated; "
            "reserved for v0.5+ live-price ingestion."
        ),
        "placeholder": "<get-from-theracingapi.com>",
        "get_it_at": "https://api.theracingapi.com",
        "default": None,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Validation logic
# ─────────────────────────────────────────────────────────────────────────────

def _is_placeholder(value: str, placeholder: str) -> bool:
    """Return True if the value still looks like an .env.example placeholder."""
    v = value.strip()
    return v == placeholder or (v.startswith("<") and v.endswith(">"))


def check_env(vars_registry: dict[str, dict] | None = None) -> tuple[int, int, list[str]]:
    """
    Validate environment variables against the registry.

    Returns:
        (required_ok, optional_ok, errors)
        errors is a list of human-readable error strings (empty on success).
    """
    registry = vars_registry if vars_registry is not None else ENV_VARS
    errors: list[str] = []
    required_ok = 0
    optional_ok = 0

    for var_name, spec in registry.items():
        value = os.environ.get(var_name, "")
        placeholder = spec["placeholder"]
        required = spec["required"]

        if not value:
            if required:
                errors.append(
                    f"\n  ❌  {var_name} is not set.\n"
                    f"      Why it's needed : {spec['description']}\n"
                    f"      How to get it   : {spec['get_it_at']}\n"
                    f"      Action          : Add  {var_name}=<real-value>  to your .env file."
                )
            else:
                default_note = (
                    f"  (default: {spec['default']})"
                    if spec.get("default")
                    else "  (no default — feature will be unavailable)"
                )
                print(
                    f"  ⚠️   {var_name} not set — optional{default_note}",
                    file=sys.stderr,
                )
            continue

        if _is_placeholder(value, placeholder):
            if required:
                errors.append(
                    f"\n  ❌  {var_name} is still set to the placeholder value.\n"
                    f"      Value found     : {value!r}\n"
                    f"      Why it's needed : {spec['description']}\n"
                    f"      How to get it   : {spec['get_it_at']}\n"
                    f"      Action          : Replace the placeholder with your real value in .env."
                )
            else:
                print(
                    f"  ⚠️   {var_name} looks like a placeholder — update it when you have a real value.",
                    file=sys.stderr,
                )
            continue

        if required:
            required_ok += 1
        else:
            optional_ok += 1

    return required_ok, optional_ok, errors


def main() -> int:
    """Run the credential check and print results.  Returns exit code."""
    print("Checking race-analysis environment …")

    required_count = sum(1 for s in ENV_VARS.values() if s["required"])
    optional_count = sum(1 for s in ENV_VARS.values() if not s["required"])

    required_ok, optional_ok, errors = check_env()

    if errors:
        print(
            f"\n🚨  Environment check FAILED — {len(errors)} required variable(s) missing or placeholder:\n",
            file=sys.stderr,
        )
        for err in errors:
            print(err, file=sys.stderr)
        print(
            "\nFix the issues above, then re-run:  python scripts/check_env.py\n",
            file=sys.stderr,
        )
        return 1

    print(
        f"✅  Environment OK "
        f"({required_ok} required var{'s' if required_ok != 1 else ''} set, "
        f"{optional_ok} optional)"
    )
    return 0


if __name__ == "__main__":
    # Load .env from repo root if python-dotenv is available (graceful fallback)
    _repo_root = Path(__file__).resolve().parent.parent
    _env_file = _repo_root / ".env"
    if _env_file.exists():
        try:
            from dotenv import load_dotenv  # type: ignore[import-untyped]
            load_dotenv(_env_file)
        except ImportError:
            pass  # dotenv not installed — user must export vars manually

    sys.exit(main())
