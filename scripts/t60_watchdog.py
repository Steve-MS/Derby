"""
t60_watchdog.py — T-60 race-day artifact watchdog.

Checks the race-day artifact manifest for a meeting date and exits loud before
operators run the scoring/rendering pipeline on stale or inconsistent data.

Usage:
    python scripts/t60_watchdog.py --date YYYY-MM-DD
"""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date as date_cls
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path.cwd()
SCRIPT_DIR = Path(__file__).resolve().parent
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

OK = "✅ OK"
STALE = "⚠️ STALE"
MISSING = "❌ MISSING"
INCONSISTENT = "🔴 INCONSISTENT"

TAG_RE = re.compile(r"<[^>]+>")
MONEY_RE = re.compile(r"(?:£|\$|GBP\s*)?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)


@dataclass
class ArtifactRow:
    artifact: str
    path: str
    status: str
    age: str = "—"
    size: str = "—"
    detail: str = ""
    severity: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact,
            "path": self.path,
            "status": self.status,
            "age": self.age,
            "size": self.size,
            "detail": self.detail,
            "severity": self.severity,
        }


@dataclass
class WatchdogContext:
    root: Path
    race_date: str
    now: datetime
    rows: list[ArtifactRow] = field(default_factory=list)
    courses: list[str] = field(default_factory=list)
    files: dict[str, Path] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)

    def add(self, row: ArtifactRow) -> None:
        self.rows.append(row)


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _normalise_name(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(str(value)).lower()
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _human_age(path: Path, now: datetime) -> str:
    seconds = max(0, (now - datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)).total_seconds())
    if seconds < 90:
        return f"{int(seconds)}s"
    minutes = seconds / 60
    if minutes < 90:
        return f"{minutes:.0f}m"
    hours = minutes / 60
    if hours < 48:
        return f"{hours:.1f}h"
    return f"{hours / 24:.1f}d"


def _human_size(path: Path) -> str:
    size = path.stat().st_size
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)


def _read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _status_row(
    ctx: WatchdogContext,
    artifact: str,
    path: Path,
    max_age: timedelta | None = None,
    min_size: int = 1,
    stale_is_fail: bool = False,
) -> ArtifactRow:
    rel = _rel(ctx.root, path)
    if not path.exists():
        return ArtifactRow(artifact, rel, MISSING, detail="file not found", severity=2)
    size = path.stat().st_size
    age = _human_age(path, ctx.now)
    size_text = _human_size(path)
    if size < min_size:
        return ArtifactRow(
            artifact,
            rel,
            INCONSISTENT if min_size > 1 else MISSING,
            age,
            size_text,
            f"size {size} B below required {min_size} B",
            2,
        )
    if max_age is not None:
        cutoff = ctx.now - max_age
        if _mtime(path) < cutoff:
            return ArtifactRow(
                artifact,
                rel,
                INCONSISTENT if stale_is_fail else STALE,
                age,
                size_text,
                f"older than {max_age}",
                2 if stale_is_fail else 1,
            )
    return ArtifactRow(artifact, rel, OK, age, size_text, severity=0)


def _extract_stake(value: Any) -> float:
    if value is None:
        return 0.0
    match = MONEY_RE.search(str(value))
    return float(match.group(1)) if match else 0.0


def _computed_bets_total(bets: dict[str, Any]) -> float:
    total = 0.0
    for entry in bets.get("bets") or bets.get("entries") or []:
        status = str(entry.get("status") or "").upper()
        if status in {"NR", "VOID", "NO_BET", "REFUNDED", "NON_RUNNER", "NON-RUNNER", "WITHDRAWN", "SCRATCHED", "CANCELLED"}:
            continue
        if status == "WIN":
            total += _extract_stake(entry.get("stake_guidance"))
        elif status == "EW":
            total += _extract_stake(entry.get("stake_guidance")) * 2
        elif status == "TRIFECTA" or str(entry.get("bet_type") or "").lower() == "trifecta_box":
            total += _extract_stake(entry.get("total_stake") or entry.get("stake_guidance"))
    return round(total, 2)


def _render_header_total(bets: dict[str, Any]) -> float | None:
    try:
        repo_root = SCRIPT_DIR.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from src.report import render_header  # type: ignore

        return float(render_header(bets)["total_outlay"])
    except Exception:
        return None


def _declared_bets_total(bets: dict[str, Any]) -> float | None:
    meta = bets.get("meta") if isinstance(bets.get("meta"), dict) else {}
    candidates = [
        meta.get("total_stake"),
        meta.get("total_stake_gbp"),
        meta.get("total_outlay_gbp"),
        bets.get("total_outlay_gbp"),
        (bets.get("portfolio_summary") or {}).get("total_stake_gbp"),
    ]
    for value in candidates:
        if isinstance(value, (int, float)):
            return round(float(value), 2)
        if isinstance(value, str):
            parsed = _extract_stake(value)
            if parsed:
                return round(parsed, 2)
    return None


def _race_time(value: Any) -> str:
    text = str(value or "")
    match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
    if match:
        return f"{int(match.group(1)):02d}:{match.group(2)}"
    match = re.search(r"(?:^|\D)([01]\d|2[0-3])([0-5]\d)(?:\D|$)", text)
    if match:
        return f"{match.group(1)}:{match.group(2)}"
    return ""


def _race_scope_key(race_time: Any, course: Any = "", race_name: Any = "") -> tuple[str, str, str]:
    return (_race_time(race_time), _normalise_name(str(course or "")), _normalise_name(str(race_name or "")))


def _active_bet_horses(bets: dict[str, Any]) -> list[dict[str, str]]:
    horses: list[dict[str, str]] = []
    meta = bets.get("meta") if isinstance(bets.get("meta"), dict) else {}
    default_course = str(meta.get("course") or meta.get("venue") or "")
    for entry in bets.get("bets") or bets.get("entries") or []:
        status = str(entry.get("status") or "").upper()
        race_time = str(entry.get("race_time") or entry.get("off_time") or entry.get("race_id") or "")
        race_name = str(entry.get("race_name") or entry.get("name") or "")
        course = str(entry.get("course") or entry.get("venue") or default_course)
        if status in {"WIN", "EW"} and entry.get("pick"):
            horses.append({
                "horse": str(entry["pick"]),
                "race_time": race_time,
                "race_name": race_name,
                "course": course,
                "stake": str(entry.get("stake_guidance") or ""),
                "status": status,
            })
        elif status == "TRIFECTA" or str(entry.get("bet_type") or "").lower() == "trifecta_box":
            stake = str(entry.get("total_stake") or entry.get("stake_guidance") or "")
            for horse in entry.get("horses") or []:
                name = horse.get("horse") if isinstance(horse, dict) else horse
                if name:
                    horses.append({
                        "horse": str(name),
                        "race_time": race_time,
                        "race_name": race_name,
                        "course": course,
                        "stake": stake,
                        "status": "TRIFECTA",
                    })
    return horses


def _racecard_index(raw_cards: list[dict[str, Any]]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    all_horses: set[str] = set()
    for card in raw_cards:
        for race in card.get("races", []):
            key = _race_time(race.get("off_time") or race.get("race_time") or race.get("time") or race.get("race_id") or "")
            runners = race.get("runners") or []
            names = {
                _normalise_name(r.get("horse") or r.get("horse_name") or r.get("name"))
                for r in runners
                if isinstance(r, dict)
            }
            names.discard("")
            all_horses |= names
            if key:
                index.setdefault(key, set()).update(names)
    index["*"] = all_horses
    return index


def _live_runner_sets(live: dict[str, Any]) -> dict[tuple[str, str, str], dict[str, set[str]]]:
    scopes: dict[tuple[str, str, str], dict[str, set[str]]] = {}
    default_course = live.get("course") or live.get("venue") or live.get("meeting") or ""
    for race in live.get("races") or []:
        if not isinstance(race, dict):
            continue
        race_time = race.get("time") or race.get("off_time") or race.get("race_time") or race.get("race_id") or ""
        race_name = race.get("name") or race.get("race_name") or ""
        course = race.get("course") or race.get("venue") or default_course
        key = _race_scope_key(race_time, course, race_name)
        if not key[0]:
            continue
        scope = scopes.setdefault(key, {"active": set(), "nr_void": set()})
        for runner in race.get("runners") or race.get("active_runners") or []:
            if isinstance(runner, dict):
                name = runner.get("name") or runner.get("horse") or runner.get("horse_name")
                status = str(runner.get("status") or "").upper()
                norm = _normalise_name(name)
                if not norm:
                    continue
                if status in {"NR", "VOID", "NON_RUNNER", "NON-RUNNER", "WITHDRAWN", "SCRATCHED"}:
                    scope["nr_void"].add(norm)
                else:
                    scope["active"].add(norm)
            else:
                norm = _normalise_name(str(runner))
                if norm:
                    scope["active"].add(norm)
        for nr_key in ("non_runners_excluded", "non_runners", "void_runners", "withdrawn"):
            for value in race.get(nr_key) or []:
                text = value.get("name") if isinstance(value, dict) else str(value)
                first = re.split(r"\s+[–—-]\s+|\s*\(", text, maxsplit=1)[0]
                norm = _normalise_name(first)
                if norm:
                    scope["nr_void"].add(norm)
    return scopes


def _matching_live_scopes(
    scopes: dict[tuple[str, str, str], dict[str, set[str]]],
    bet: dict[str, str],
) -> list[dict[str, set[str]]]:
    bet_time, bet_course, bet_race_name = _race_scope_key(bet.get("race_time"), bet.get("course"), bet.get("race_name"))
    if not bet_time:
        return []
    candidates = [(key, scope) for key, scope in scopes.items() if key[0] == bet_time]
    if bet_course:
        course_matches = [(key, scope) for key, scope in candidates if not key[1] or key[1] == bet_course]
        if course_matches:
            candidates = course_matches
    if bet_race_name:
        name_matches = [(key, scope) for key, scope in candidates if key[2] == bet_race_name]
        if name_matches:
            candidates = name_matches
    return [scope for _, scope in candidates]


def _html_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return _normalise_name(TAG_RE.sub(" ", text))


def _check_env() -> tuple[bool, str]:
    check_env_path = SCRIPT_DIR / "check_env.py"
    if not check_env_path.exists():
        return False, "scripts/check_env.py not found"
    spec = importlib.util.spec_from_file_location("t60_check_env", check_env_path)
    if spec is None or spec.loader is None:
        return False, "unable to load scripts/check_env.py"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _, _, errors = module.check_env()  # type: ignore[attr-defined]
    if errors:
        names = []
        for err in errors:
            match = re.search(r"❌\s+([A-Z0-9_]+)", err)
            names.append(match.group(1) if match else "required env")
        return False, "missing/placeholder env vars: " + ", ".join(names)
    return True, "required environment variables set"


def _discover_courses(ctx: WatchdogContext) -> list[Path]:
    raw_dir = ctx.root / "data" / "raw"
    suffix = f"-{ctx.race_date}-racecards.json"
    paths = sorted(raw_dir.glob(f"*{suffix}"))
    ctx.courses = [p.name[: -len(suffix)] for p in paths]
    return paths


def _load_if_ok(ctx: WatchdogContext, key: str, path: Path) -> None:
    if path.exists() and path.stat().st_size > 0:
        try:
            ctx.data[key] = _read_json(path)
        except Exception as exc:
            ctx.add(ArtifactRow(key, _rel(ctx.root, path), INCONSISTENT, _human_age(path, ctx.now), _human_size(path), f"invalid JSON: {exc}", 2))


def run_watchdog(race_date: str, root: Path | None = None, now: datetime | None = None) -> int:
    root = (root or PROJECT_ROOT).resolve()
    now = now or datetime.now(timezone.utc)
    ctx = WatchdogContext(root=root, race_date=race_date, now=now)

    outputs_dir = root / "outputs"
    enrich_dir = root / "data" / "enrichment"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    raw_paths = _discover_courses(ctx)
    if not raw_paths:
        ctx.add(ArtifactRow("racecards", f"data/raw/*-{race_date}-racecards.json", MISSING, detail="no course racecards discovered", severity=2))
    raw_cards: list[dict[str, Any]] = []
    for path in raw_paths:
        course = path.name[: -len(f"-{race_date}-racecards.json")]
        row = _status_row(ctx, f"racecards:{course}", path, timedelta(hours=24), min_size=1)
        ctx.add(row)
        if row.severity < 2:
            try:
                raw_cards.append(_read_json(path))
            except Exception as exc:
                ctx.add(ArtifactRow(f"racecards:{course}:json", _rel(root, path), INCONSISTENT, _human_age(path, now), _human_size(path), f"invalid JSON: {exc}", 2))

    required = {
        "live-runners": (enrich_dir / f"live-runners-{race_date}.json", timedelta(hours=4), 1),
        "sportinglife": (enrich_dir / f"sportinglife-{race_date}.json", timedelta(hours=4), 1025),
        "racingpost": (enrich_dir / f"racingpost-{race_date}.json", timedelta(hours=4), 1),
        "going": (enrich_dir / f"going-{race_date}.json", timedelta(hours=12), 1),
    }
    for key, (path, max_age, min_size) in required.items():
        row = _status_row(ctx, key, path, max_age, min_size=min_size, stale_is_fail=False)
        if key == "sportinglife" and path.exists() and path.stat().st_size < min_size:
            row.status = INCONSISTENT
            row.severity = 2
            row.detail = "Sporting Life artifact below 1KB SPA-shell threshold"
        ctx.add(row)
        ctx.files[key] = path
        _load_if_ok(ctx, key, path)

    scores_path = outputs_dir / f"scores-{race_date}.json"
    scores_row = _status_row(ctx, "scores", scores_path, None, min_size=1)
    if scores_row.severity == 0:
        enrichment_mtimes = [_mtime(p) for p, _, _ in required.values() if p.exists()]
        if enrichment_mtimes and _mtime(scores_path) <= max(enrichment_mtimes):
            scores_row.status = STALE
            scores_row.severity = 1
            scores_row.detail = "scores not modified after enrichment files"
    ctx.add(scores_row)
    ctx.files["scores"] = scores_path

    bets_path = outputs_dir / f"bets-{race_date}.json"
    bets_row = _status_row(ctx, "bets", bets_path, None, min_size=1)
    header_row: ArtifactRow | None = None
    bets_data: dict[str, Any] = {}
    expected_total: float | None = None
    if bets_row.severity == 0:
        try:
            bets_data = _read_json(bets_path)
            expected_total = _computed_bets_total(bets_data)
            declared = _declared_bets_total(bets_data)
            detail_prefix = "missing meta block; " if not isinstance(bets_data.get("meta"), dict) else ""
            if declared is None:
                bets_row.status = INCONSISTENT
                bets_row.severity = 2
                bets_row.detail = f"{detail_prefix}no declared total stake; computed GBP {expected_total:.2f}"
            elif abs(declared - expected_total) > 0.01:
                bets_row.status = INCONSISTENT
                bets_row.severity = 2
                bets_row.detail = f"{detail_prefix}declared GBP {declared:.2f} != computed GBP {expected_total:.2f}"
            elif detail_prefix:
                bets_row.detail = detail_prefix + "using declared total fallback"

            rendered_total = _render_header_total(bets_data)
            if rendered_total is None:
                header_row = ArtifactRow("header consistency", "src/report.py::render_header", INCONSISTENT, detail="render_header failed", severity=2)
            elif abs(rendered_total - expected_total) > 0.01:
                header_row = ArtifactRow(
                    "header consistency",
                    "src/report.py::render_header",
                    INCONSISTENT,
                    detail=f"render_header total GBP {rendered_total:.2f} != computed GBP {expected_total:.2f}",
                    severity=2,
                )
            else:
                header_row = ArtifactRow(
                    "header consistency",
                    "src/report.py::render_header",
                    OK,
                    detail=f"render_header total matches computed GBP {expected_total:.2f}",
                    severity=0,
                )
        except Exception as exc:
            bets_row.status = INCONSISTENT
            bets_row.severity = 2
            bets_row.detail = f"invalid JSON: {exc}"
    ctx.add(bets_row)
    if header_row is not None:
        ctx.add(header_row)
    ctx.files["bets"] = bets_path
    ctx.data["bets"] = bets_data

    report_path = outputs_dir / f"report-{race_date}.html"
    report_row = _status_row(ctx, "report", report_path, None, min_size=1)
    if report_row.severity == 0 and scores_path.exists() and _mtime(report_path) <= _mtime(scores_path):
        report_row.status = STALE
        report_row.severity = 1
        report_row.detail = "report not modified after scores"
    ctx.add(report_row)

    racecard_path = outputs_dir / f"racecard-{race_date}.html"
    racecard_row = _status_row(ctx, "racecard", racecard_path, None, min_size=1)
    if racecard_row.severity == 0:
        if bets_path.exists() and _mtime(racecard_path) <= _mtime(bets_path):
            racecard_row.status = STALE
            racecard_row.severity = 1
            racecard_row.detail = "racecard not modified after bets"
        if expected_total is not None:
            text = racecard_path.read_text(encoding="utf-8", errors="ignore")
            if not re.search(rf"£\s*{expected_total:.2f}\b", text):
                racecard_row.status = INCONSISTENT
                racecard_row.severity = 2
                racecard_row.detail = f"header does not show bets total GBP {expected_total:.2f}"
    ctx.add(racecard_row)

    slip_path = outputs_dir / f"slip-{race_date}.txt"
    slip_row = _status_row(ctx, "slip", slip_path, None, min_size=1)
    if slip_row.severity == 0 and bets_data:
        slip_text = slip_path.read_text(encoding="utf-8", errors="ignore")
        slip_norm = _normalise_name(slip_text)
        missing_bits: list[str] = []
        for bet in _active_bet_horses(bets_data):
            horse_norm = _normalise_name(bet["horse"])
            if horse_norm and horse_norm not in slip_norm:
                missing_bits.append(bet["horse"])
                continue
            stake = _extract_stake(bet.get("stake"))
            if stake and f"£{stake:.2f}" not in slip_text:
                missing_bits.append(f"{bet['horse']} stake GBP {stake:.2f}")
        if missing_bits:
            slip_row.status = INCONSISTENT
            slip_row.severity = 2
            slip_row.detail = "missing slip entries: " + ", ".join(missing_bits[:5])
    ctx.add(slip_row)

    consistency_details: list[str] = []
    live_data = ctx.data.get("live-runners") or {}
    live_scopes = _live_runner_sets(live_data if isinstance(live_data, dict) else {})
    bet_horses = _active_bet_horses(bets_data) if bets_data else []
    for bet in bet_horses:
        norm = _normalise_name(bet["horse"])
        if not norm:
            continue
        for scope in _matching_live_scopes(live_scopes, bet):
            if norm in scope["nr_void"]:
                race_time = _race_time(bet.get("race_time")) or "?"
                consistency_details.append(f"bet horse marked NR/VOID in live-runners for race {race_time}: {bet['horse']}")
                break

    raw_index = _racecard_index(raw_cards)
    for bet in bet_horses:
        norm = _normalise_name(bet["horse"])
        race_time = _race_time(bet.get("race_time"))
        race_set = raw_index.get(race_time) or raw_index.get("*") or set()
        if norm and norm not in race_set:
            consistency_details.append(f"{bet['horse']} not found in raw racecard for race {race_time or '?'}")

    env_ok, env_detail = _check_env()
    if not env_ok:
        consistency_details.append(f"check_env failed: {env_detail}")

    if consistency_details:
        ctx.add(ArtifactRow("consistency", "cross-checks", INCONSISTENT, detail="; ".join(consistency_details[:8]), severity=2))
    else:
        ctx.add(ArtifactRow("consistency", "cross-checks", OK, detail="live runners, raw racecards, slip, and environment agree", severity=0))

    manifest = {
        "date": race_date,
        "generated_at": ctx.now.isoformat(),
        "courses": ctx.courses,
        "exit_code": 2 if any(r.severity == 2 for r in ctx.rows) else 1 if any(r.severity == 1 for r in ctx.rows) else 0,
        "artifacts": [r.as_dict() for r in ctx.rows],
    }
    manifest_path = outputs_dir / f"t60-status-{race_date}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    _print_console(ctx, manifest_path)
    return int(manifest["exit_code"])


def _print_console(ctx: WatchdogContext, manifest_path: Path) -> None:
    print(f"\nT-60 WATCHDOG — {ctx.race_date}")
    print(f"Courses discovered: {', '.join(ctx.courses) if ctx.courses else 'none'}")
    print("\nArtifact                         Status              Age      Size      Detail")
    print("-" * 96)
    for row in ctx.rows:
        print(f"{row.artifact[:30]:30} {row.status:18} {row.age:8} {row.size:9} {row.detail}")
    print("-" * 96)
    print(f"JSON manifest: {_rel(ctx.root, manifest_path)}")

    if any(r.severity == 2 for r in ctx.rows):
        print("\n" + "!" * 72)
        print("🔴 DO NOT RUN PIPELINE — T-60 watchdog found missing/inconsistent artifacts")
        print("!" * 72)
    elif any(r.severity == 1 for r in ctx.rows):
        print("\n⚠️ REVIEW BEFORE PROCEEDING — one or more artifacts are stale")
    else:
        print("\n✅ T-60 CLEAR — pipeline ready")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T-60 race-day artifact watchdog")
    parser.add_argument("--date", default=date_cls.today().isoformat(), help="Race date YYYY-MM-DD (default: today)")
    args = parser.parse_args(argv)
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print("--date must be YYYY-MM-DD", file=sys.stderr)
        return 2
    return run_watchdog(args.date)


if __name__ == "__main__":
    sys.exit(main())
