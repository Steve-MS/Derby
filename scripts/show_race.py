import json, re, sys

day = sys.argv[1]  # 05 or 06
race_idx = int(sys.argv[2])  # 0-based
path = rf"C:\Users\stevenn\race-analysis\data\raw\epsom-2026-06-{day}-racecards.json"
d = json.load(open(path, encoding="utf-8"))
race = d["races"][race_idx]
print(f"Race {race_idx+1}: {race.get('race_name') or '(unnamed)'} | {race.get('distance_f')}f | {len(race['runners'])} runners")
print()
for run in race["runners"]:
    notes = run.get("notes") or ""
    m = re.search(r"badges\s+([A-Za-z,\s]+?)(?:;|$|source)", notes)
    badges = m.group(1).strip() if m else "-"
    or_ = run.get("or") if run.get("or") is not None else "?"
    rpr = run.get("rpr") if run.get("rpr") is not None else "?"
    price = run.get("morning_price")
    print(f"  {run['horse']:30s} OR={or_!s:>4} RPR={rpr!s:>4} badges={badges:10s} price={price}")
