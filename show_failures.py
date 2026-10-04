import json
from pathlib import Path

reports = sorted(Path("evals_output").glob("*.json"), reverse=True)
latest = reports[0]
print("Report:", latest.name)
print()

with open(latest, encoding="utf-8") as f:
    data = json.load(f)

failed = data.get("failed_cases", [])
print(f"Total failed: {len(failed)}")
print()

for fc in failed:
    print("=" * 70)
    for k, v in fc.items():
        s = str(v)
        if len(s) > 500:
            s = s[:500] + "..."
        print(f"  {k}: {s}")
    print()