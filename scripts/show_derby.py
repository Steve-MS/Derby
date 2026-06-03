import json

s = json.load(open("outputs/scores-2026-06-06.json"))
derby = next(r for r in s["races"] if "1600" in r["race_id"])
runners = derby["ranked_runners"]
total = sum(max(r.get("score", 0), 0) for r in runners)
for r in runners:
    r["model_prob"] = max(r.get("score", 0), 0) / total if total else 0
runners = sorted(runners, key=lambda r: r["model_prob"], reverse=True)

print(f'Derby — {derby["race_name"]} | going: {derby["going"]} | confidence: {derby["confidence"]}')
print()
print(f'{"#":>2}  {"Horse":24} {"Trainer":18} {"Odds":>6}  {"mProb":>6}  {"iProb":>6}  {"edge%":>7}')
print("-" * 86)
for i, r in enumerate(runners, 1):
    mp = r["model_prob"]
    price = r.get("morning_price") or 0
    ip = (1 / price) if price else 0
    edge = ((mp / ip) - 1) * 100 if ip else 0
    flag = ""
    if price >= 16.0 and edge > 0:
        flag = "  <-- OUTSIDER VALUE"
    print(f'{i:>2}  {r["horse"]:24} {r.get("trainer","")[:18]:18} {price:>6.1f}  {mp:>6.3f}  {ip:>6.3f}  {edge:>+6.1f}%{flag}')
