import json
import sys

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))
for i, r in enumerate(d["races"]):
    name = (r.get("race_name") or "(no name)")[:55]
    print(f"R{i+1}: {name} | {r.get('distance_f')}f | {len(r.get('runners') or [])} runners | id={r.get('race_id')}")
