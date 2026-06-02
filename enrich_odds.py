"""
enrich_odds.py — River's one-shot odds enrichment script.

Adds morning_price, odds_source, odds_fetched_at to every runner in both
Epsom racecard files.  Source priority:
  1. ante_post  — real published prices from notes in racecard / Racing Post
  2. estimated  — morning-line estimates from form context
  3. synthetic  — derived from field size / ratings where no price exists
"""

import json
import math
from pathlib import Path

FETCHED_AT = "2026-06-02T13:55:00+01:00"
DATA_DIR = Path(__file__).parent / "data" / "raw"

# ---------------------------------------------------------------------------
# Odds tables
# ---------------------------------------------------------------------------

# Format: horse_name -> (decimal_price, source)
ODDS_05: dict[str, tuple[float, str]] = {
    # 13:30  Win With Zyn 3yo Dash Handicap  ─ single runner in data
    "Cato (IRE)": (6.0, "synthetic"),          # OR 92; 5/1 synthetic from rating

    # 14:05  EBF Woodcote Stakes  ─ placeholder runner
    "Unnamed 2yo colts": (4.0, "synthetic"),   # uniform prior for unraced 2yos

    # 14:40  Betfred Diomed Stakes (Group 3)
    "Belinus":   (3.5,  "estimated"),          # RPR 122, best in field → 5/2
    "Runner-up": (4.5,  "estimated"),          # RPR 113, second best   → 7/2

    # 16:00  Betfred Oaks (Group 1) – ante-post from Racing Post / Paddypower
    "Amelia Earhart":  (3.5,  "ante_post"),    # 5/2  – won Cheshire Oaks G2, market leader
    "Precise":         (5.0,  "ante_post"),    # 4/1  – Irish 1000 Guineas winner
    "Legacy Link":     (6.0,  "ante_post"),    # 5/1  – Musidora Stakes G2 winner
    "Venetian Lace":   (11.0, "ante_post"),    # 10/1 – 3rd 1000 Guineas
    "Cameo":           (15.0, "ante_post"),    # 14/1 – won Lingfield Oaks Trial; Ballydoyle
    "A La Prochaine":  (17.0, "estimated"),    # 16/1 – 3rd Cheshire Oaks trial
    "Thundering On":   (21.0, "estimated"),    # 20/1 – progressive profile
    "K Sarra":         (26.0, "estimated"),    # 25/1 – lightly raced, winner at 2
    "Prizeland":       (34.0, "estimated"),    # 33/1 – flashes of quality
    "Sugar Island":    (34.0, "estimated"),    # 33/1 – Ballydoyle depth runner
    "Beautify":        (101.0,"estimated"),    # 100/1– last in Curragh, outsider
}

ODDS_06: dict[str, tuple[float, str]] = {
    # 14:40  Coolmore Coronation Cup (Group 1) – ante-post
    "Calandagan":     (2.5,  "ante_post"),     # 6/4  – won KGV, Champion, Japan Cup, Sheema Classic
    "Lambourn":       (3.0,  "ante_post"),     # 2/1  – 2025 Derby winner; Huxley G2 winner
    "Jan Brueghel":   (3.5,  "ante_post"),     # 5/2  – 2025 Coronation Cup winner; Ormonde G2
    "Bay City Roller":(9.0,  "estimated"),     # 8/1  – 2nd Huxley & Curragh May 2026
    "Convergent":     (11.0, "estimated"),     # 10/1 – John Porter G3 winner
    "See The Fire":   (13.0, "estimated"),     # 12/1 – won Middleton Fillies' G2
    "Sunway":         (17.0, "estimated"),     # 16/1 – 4th Jockey Club Stakes G2
    "Illinois":       (21.0, "estimated"),     # 20/1 – 3rd Ormonde G3

    # 16:00  Betfred Derby (Group 1) – ante-post where quoted in racecard notes
    "Benvenuto Cellini": (3.25,  "ante_post"),  # 9/4  – notes "9/4-5/2 favourite"
    "Item":              (5.0,   "ante_post"),  # 4/1  – notes "4/1-5/1 second favourite"
    "Maltese Cross":     (9.0,   "ante_post"),  # 8/1  – notes "8/1-10/1"
    "Constitution River":(9.0,   "ante_post"),  # 8/1  – notes "8/1 odds"
    "James J Braddock":  (11.0,  "ante_post"),  # 10/1 – notes "10/1-14/1"
    "Ancient Egypt":     (17.0,  "ante_post"),  # 16/1 – notes "16/1 odds"
    "Action":            (13.0,  "estimated"),  # 12/1 – OR 113, 2nd Dante
    "Christmas Day":     (15.0,  "estimated"),  # 14/1 – 3rd Dante, OR 109
    "Pierre Bonnard":    (17.0,  "estimated"),  # 16/1 – Derby Trial 2nd, OR 109
    "Bay Of Brilliance": (21.0,  "estimated"),  # 20/1 – Derby Trial 2nd, OR 107
    "Causeway":          (29.0,  "estimated"),  # 28/1 – Gallinule winner; "long odds"
    "Endorsement":       (34.0,  "estimated"),  # 33/1 – Derby Trial 3rd; "long odds"
    "Balzac":            (41.0,  "estimated"),  # 40/1 – OR 97, uneven form
    "A Taste of Glory":  (51.0,  "estimated"),  # 50/1 – OR 84, lesser form
    "Proposition":       (67.0,  "estimated"),  # 66/1 – OR 100, modest form
    "Rebel Rocker":      (67.0,  "estimated"),  # 66/1 – OR 99, outsider
    "Alderman":          (101.0, "estimated"),  # 100/1– OR 83, weaker form
    "Poker":             (101.0, "estimated"),  # 100/1– OR 80, lesser form
}


# ---------------------------------------------------------------------------
# Synthetic fallback: softmax over ratings blended with uniform prior
# ---------------------------------------------------------------------------

def synthetic_price(runner: dict, field_size: int) -> float:
    """Derive a synthetic decimal price from OR / RPR and field size."""
    # Try to find any numeric rating
    rating = None
    for key in ("or", "rpr", "ts"):
        val = runner.get(key)
        try:
            rating = float(val)
            break
        except (TypeError, ValueError):
            continue

    if rating is not None and field_size > 0:
        # Scale rating to a rough win probability
        # Assume average OR ~90; map rating to prob via softmax-like approach
        # win_prob ≈ 0.5 / field_size + 0.5 * rating / (field_size * 90)
        base_prob = 1.0 / field_size
        rating_boost = max(0.0, (rating - 70.0) / 50.0)  # 0 for OR 70, 1 for OR 120
        prob = base_prob * (1 + rating_boost)
        # Clamp to reasonable bounds
        prob = max(0.01, min(0.90, prob))
    else:
        prob = 1.0 / max(1, field_size)

    dec = round(1.0 / prob, 2)
    # Snap to nearest market bookmaker increment
    dec = round(dec * 2) / 2.0  # round to nearest 0.5
    return max(1.5, dec)


# ---------------------------------------------------------------------------
# Core enrichment
# ---------------------------------------------------------------------------

def enrich_file(racecard_path: Path, odds_table: dict[str, tuple[float, str]]) -> dict:
    """Load, enrich, and return updated racecard dict."""
    with racecard_path.open(encoding="utf-8") as fh:
        card = json.load(fh)

    enriched_count = 0
    ant_post_count = 0
    estimated_count = 0
    synthetic_count = 0

    for race in card.get("races", []):
        runners = race.get("runners", [])
        if not runners:
            continue

        field_size = len(runners)
        for runner in runners:
            horse = runner.get("horse", "")
            if horse in odds_table:
                price, source = odds_table[horse]
            else:
                # Synthetic fallback
                price = synthetic_price(runner, field_size)
                source = "synthetic"

            runner["morning_price"] = price
            runner["odds_source"] = source
            runner["odds_fetched_at"] = FETCHED_AT
            enriched_count += 1
            if source == "ante_post":
                ant_post_count += 1
            elif source == "estimated":
                estimated_count += 1
            else:
                synthetic_count += 1

    print(f"  Enriched {enriched_count} runners  "
          f"(ante_post={ant_post_count}, estimated={estimated_count}, synthetic={synthetic_count})")
    return card


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    files = {
        "2026-06-05": (DATA_DIR / "epsom-2026-06-05-racecards.json", ODDS_05),
        "2026-06-06": (DATA_DIR / "epsom-2026-06-06-racecards.json", ODDS_06),
    }

    for date, (path, odds_table) in files.items():
        print(f"\nEnriching {path.name}")
        card = enrich_file(path, odds_table)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(card, fh, indent=2, ensure_ascii=False)
        print(f"  Written back to {path}")


if __name__ == "__main__":
    main()
