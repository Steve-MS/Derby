"""Plain-text bookmaker slip rendering."""

from __future__ import annotations

from typing import Any


def _fmt_odds(dec: Any) -> str:
    if not isinstance(dec, (int, float)):
        return str(dec or "?")
    table = {
        2.0: "Evs", 2.25: "5/4", 2.5: "6/4", 3.0: "2/1", 3.25: "9/4",
        3.5: "5/2", 4.0: "3/1", 4.5: "7/2", 5.0: "4/1", 6.0: "5/1",
        7.0: "6/1", 8.0: "7/1", 9.0: "8/1", 10.0: "9/1", 11.0: "10/1",
        13.0: "12/1", 13.5: "25/2", 15.0: "14/1", 17.0: "16/1",
        18.5: "35/2", 19.0: "18/1", 21.0: "20/1", 24.0: "23/1",
        26.0: "25/1", 29.0: "28/1", 34.0: "33/1",
    }
    value = float(dec)
    if value in table:
        return table[value]
    frac = value - 1.0
    rounded = round(frac)
    return f"{rounded}/1" if abs(frac - rounded) < 0.1 else f"{frac:.2f}"


def build_bookmaker_slip(date_label: str, bets: dict[str, Any]) -> str:
    scenario = str(bets.get("scenario") or "")
    banner = f"APEX RACING – BADGER PORTFOLIO{' – ' + scenario if scenario else ''}"
    lines: list[str] = [banner, f"Date: {date_label}", "=" * 60, ""]

    singles = bets.get("singles") or []
    active = [s for s in singles if s.get("bet_type") not in ("PASS", None)]
    passed = [s for s in singles if s.get("bet_type") in ("PASS", None)]

    lines.append("── SINGLES ──────────────────────────────────────────────────")
    for s in active:
        race_id = str(s.get("race_id") or "")
        rid = race_id.split("-")[-1]
        odds = s.get("odds_decimal", s.get("odds_raw", "?"))
        lines.append(
            f"  {rid}  {str(s.get('horse', '')):<28}  {str(s.get('bet_type', '')):<3}  "
            f"{_fmt_odds(odds):<8}  £{float(s.get('stake_gbp') or 0):.2f}"
        )

    item = bets.get("item_special_bet")
    if isinstance(item, dict) and item.get("bet_type") == "WIN":
        rid = str(item.get("race_id") or "").split("-")[-1]
        lines.append(
            f"  {rid}  {str(item.get('horse', '')):<28}  WIN* "
            f"{_fmt_odds(item.get('odds_decimal')):<8}  £{float(item.get('stake_gbp') or 0):.2f}  "
            "[SPECULATIVE – going-conditional]"
        )

    lines += ["", f"  ({len(passed)} races PASS)", ""]

    for key, title in (("doubles", "DOUBLES"), ("trebles", "TREBLE"), ("accumulators", "ACCUMULATORS")):
        group = bets.get(key) or []
        if not group:
            continue
        lines.append(f"── {title} " + "─" * max(0, 58 - len(title)))
        for bet in group:
            legs = " × ".join(str(leg.get("horse") or "") for leg in (bet.get("legs") or []))
            stake = float(bet.get("combined_stake_gbp") or bet.get("stake_gbp") or bet.get("total_stake_gbp") or 0)
            ret = float(bet.get("potential_return_gbp") or bet.get("est_return_gbp") or 0)
            if key == "doubles":
                lines.append(f"  {legs:<52}  £{stake:.2f}  (→ £{ret:.2f})")
            else:
                lines.append(f"  {legs}")
                lines.append(f"  Stake £{stake:.2f}  max return £{ret:.2f}")
        lines.append("")

    active_outsiders = [o for o in (bets.get("outsiders") or []) if o.get("outsider_pick")]
    if active_outsiders:
        lines.append("── OUTSIDERS (value EW) ─────────────────────────────────────")
        for o in active_outsiders:
            rid = str(o.get("race_id") or "").split("-")[-1]
            odds = o.get("morning_price", o.get("odds_decimal", "?"))
            lines.append(
                f"  {rid}  {str(o.get('horse', o.get('outsider_pick', ''))):<28}  EW  "
                f"{_fmt_odds(odds):<8}  £{float(o.get('stake_gbp') or 0):.2f} EW  ({o.get('ew_terms', '')})"
            )
        lines.append("")

    ps = bets.get("portfolio_summary") or {}
    outsider_summary = ps.get("outsider_summary") or {}
    item_stake = float(item.get("stake_gbp") or 0) if isinstance(item, dict) and item.get("bet_type") == "WIN" else 0.0
    total = float(ps.get("total_stake_gbp") or 0) + item_stake
    lines += [
        "── SUMMARY ──────────────────────────────────────────────────",
        f"  Active singles:   {ps.get('active_singles', 0)}",
        f"  Doubles:          {ps.get('doubles_count', 0)}",
        f"  Trebles:          {ps.get('trebles_count', 0)}",
        f"  Outsiders (EW):   {outsider_summary.get('count', 0)}",
        f"  Total stake:      £{total:.2f}" + (f" (incl. £{item_stake:.2f} speculative Item bet)" if item_stake else ""),
        f"  Max win scenario: £{float(ps.get('max_potential_return_gbp') or 0):.2f}",
        "",
        "  18+. Gamble responsibly. BeGambleAware.org.",
        "",
    ]
    return "\n".join(lines)
