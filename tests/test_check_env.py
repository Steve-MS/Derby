"""
tests/test_check_env.py — Unit tests for scripts/check_env.py

Covers:
  1. All required vars set with real values → exit 0, success message
  2. One required var missing               → exit 1, error names the var
  3. Required var is the placeholder value  → exit 1, hint to set real value
  4. Optional var missing                   → warning printed but exit 0
"""

from __future__ import annotations

import importlib.util
import sys
from io import StringIO
from pathlib import Path

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Import check_env from scripts/ without running __main__ block
# ─────────────────────────────────────────────────────────────────────────────

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def _import_check_env():
    """Import scripts/check_env.py as a module (without triggering __main__)."""
    spec = importlib.util.spec_from_file_location(
        "check_env", _SCRIPTS_DIR / "check_env.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


check_env_mod = _import_check_env()
check_env = check_env_mod.check_env
main = check_env_mod.main

# ─────────────────────────────────────────────────────────────────────────────
# Minimal registry fixture — isolates tests from production var list changes
# ─────────────────────────────────────────────────────────────────────────────

MINIMAL_REGISTRY: dict[str, dict] = {
    "TEST_REQUIRED_A": {
        "required": True,
        "description": "First required test variable.",
        "placeholder": "<placeholder-a>",
        "get_it_at": "https://example.com/a",
        "default": None,
    },
    "TEST_REQUIRED_B": {
        "required": True,
        "description": "Second required test variable.",
        "placeholder": "<placeholder-b>",
        "get_it_at": "https://example.com/b",
        "default": None,
    },
    "TEST_OPTIONAL_C": {
        "required": False,
        "description": "Optional test variable.",
        "placeholder": "<placeholder-c>",
        "get_it_at": "https://example.com/c",
        "default": "some-default",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — all required vars set with real values → exit 0
# ─────────────────────────────────────────────────────────────────────────────

def test_all_required_set_returns_exit_0(monkeypatch):
    """When all required vars are set to real (non-placeholder) values → exit 0."""
    monkeypatch.setenv("TEST_REQUIRED_A", "real-value-a")
    monkeypatch.setenv("TEST_REQUIRED_B", "real-value-b")
    monkeypatch.delenv("TEST_OPTIONAL_C", raising=False)

    required_ok, optional_ok, errors = check_env(MINIMAL_REGISTRY)

    assert errors == [], f"Expected no errors, got: {errors}"
    assert required_ok == 2


def test_all_required_set_main_exits_0(monkeypatch, capsys):
    """main() exits 0 when all required vars from production registry are satisfied."""
    # Patch the module-level ENV_VARS to our minimal registry for isolation
    monkeypatch.setattr(check_env_mod, "ENV_VARS", MINIMAL_REGISTRY)
    monkeypatch.setenv("TEST_REQUIRED_A", "real-value-a")
    monkeypatch.setenv("TEST_REQUIRED_B", "real-value-b")
    monkeypatch.delenv("TEST_OPTIONAL_C", raising=False)

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "✅" in captured.out
    assert "Environment OK" in captured.out


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — one required var missing → exit 1, error names the var
# ─────────────────────────────────────────────────────────────────────────────

def test_missing_required_returns_exit_1(monkeypatch):
    """When a required var is absent → errors list non-empty, names the var."""
    monkeypatch.setenv("TEST_REQUIRED_A", "real-value-a")
    monkeypatch.delenv("TEST_REQUIRED_B", raising=False)

    required_ok, optional_ok, errors = check_env(MINIMAL_REGISTRY)

    assert len(errors) == 1
    assert "TEST_REQUIRED_B" in errors[0]


def test_missing_required_main_exits_1(monkeypatch, capsys):
    """main() exits 1 and names the missing var on stderr."""
    monkeypatch.setattr(check_env_mod, "ENV_VARS", MINIMAL_REGISTRY)
    monkeypatch.setenv("TEST_REQUIRED_A", "real-value-a")
    monkeypatch.delenv("TEST_REQUIRED_B", raising=False)

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "TEST_REQUIRED_B" in captured.err
    assert "❌" in captured.err


def test_missing_required_error_includes_description(monkeypatch):
    """Error message mentions why the var is needed."""
    monkeypatch.delenv("TEST_REQUIRED_A", raising=False)
    monkeypatch.setenv("TEST_REQUIRED_B", "real-value-b")

    _, _, errors = check_env(MINIMAL_REGISTRY)

    assert any("TEST_REQUIRED_A" in e for e in errors)
    assert any("https://example.com/a" in e for e in errors)


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 — required var present but matches placeholder → exit 1
# ─────────────────────────────────────────────────────────────────────────────

def test_placeholder_value_required_returns_exit_1(monkeypatch):
    """Required var set to exact placeholder string → error, not treated as real."""
    monkeypatch.setenv("TEST_REQUIRED_A", "<placeholder-a>")
    monkeypatch.setenv("TEST_REQUIRED_B", "real-value-b")

    required_ok, optional_ok, errors = check_env(MINIMAL_REGISTRY)

    assert len(errors) == 1
    assert "TEST_REQUIRED_A" in errors[0]
    # Error should hint the user to replace with a real value
    assert "placeholder" in errors[0].lower() or "real" in errors[0].lower()


def test_placeholder_angle_bracket_pattern(monkeypatch):
    """Any <…> value is treated as placeholder regardless of content."""
    monkeypatch.setenv("TEST_REQUIRED_A", "<some-other-placeholder>")
    monkeypatch.setenv("TEST_REQUIRED_B", "real-value-b")

    _, _, errors = check_env(MINIMAL_REGISTRY)

    assert any("TEST_REQUIRED_A" in e for e in errors)


def test_placeholder_main_exits_1(monkeypatch, capsys):
    """main() exits 1 when required var is still the placeholder value."""
    monkeypatch.setattr(check_env_mod, "ENV_VARS", MINIMAL_REGISTRY)
    monkeypatch.setenv("TEST_REQUIRED_A", "<placeholder-a>")
    monkeypatch.setenv("TEST_REQUIRED_B", "real-value-b")

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "TEST_REQUIRED_A" in captured.err


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 — optional var missing → warning printed but exit 0
# ─────────────────────────────────────────────────────────────────────────────

def test_optional_missing_exits_0(monkeypatch):
    """Optional var absent → no errors returned (exit 0 path)."""
    monkeypatch.setenv("TEST_REQUIRED_A", "real-value-a")
    monkeypatch.setenv("TEST_REQUIRED_B", "real-value-b")
    monkeypatch.delenv("TEST_OPTIONAL_C", raising=False)

    required_ok, optional_ok, errors = check_env(MINIMAL_REGISTRY)

    assert errors == []


def test_optional_missing_prints_warning(monkeypatch, capsys):
    """Optional var absent → warning line on stderr, main() exits 0."""
    monkeypatch.setattr(check_env_mod, "ENV_VARS", MINIMAL_REGISTRY)
    monkeypatch.setenv("TEST_REQUIRED_A", "real-value-a")
    monkeypatch.setenv("TEST_REQUIRED_B", "real-value-b")
    monkeypatch.delenv("TEST_OPTIONAL_C", raising=False)

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "TEST_OPTIONAL_C" in captured.err
    assert "⚠️" in captured.err


def test_optional_set_counts_in_summary(monkeypatch, capsys):
    """Optional var set → counted in the success summary."""
    monkeypatch.setattr(check_env_mod, "ENV_VARS", MINIMAL_REGISTRY)
    monkeypatch.setenv("TEST_REQUIRED_A", "real-value-a")
    monkeypatch.setenv("TEST_REQUIRED_B", "real-value-b")
    monkeypatch.setenv("TEST_OPTIONAL_C", "real-value-c")

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "1 optional" in captured.out


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 — production registry shape sanity check
# ─────────────────────────────────────────────────────────────────────────────

def test_production_registry_has_required_fields():
    """Each entry in the production ENV_VARS dict has the expected keys."""
    required_keys = {"required", "description", "placeholder", "get_it_at", "default"}
    for var_name, spec in check_env_mod.ENV_VARS.items():
        missing = required_keys - set(spec.keys())
        assert not missing, f"{var_name} is missing keys: {missing}"


def test_production_registry_has_sportinglife_vars():
    """Production registry includes the two Sporting Life vars that caused the Derby Day failure."""
    registry = check_env_mod.ENV_VARS
    assert "SPORTINGLIFE_USER" in registry
    assert "SPORTINGLIFE_PASS" in registry
    assert registry["SPORTINGLIFE_USER"]["required"] is True
    assert registry["SPORTINGLIFE_PASS"]["required"] is True


def test_production_registry_placeholders_look_like_placeholders():
    """Placeholder values must start with '<' and end with '>' (never a real credential)."""
    for var_name, spec in check_env_mod.ENV_VARS.items():
        ph = spec["placeholder"]
        assert ph.startswith("<") and ph.endswith(">"), (
            f"{var_name} placeholder {ph!r} does not look like a safe placeholder"
        )
