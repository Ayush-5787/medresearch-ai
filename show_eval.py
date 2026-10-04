import json
from pathlib import Path

# Find latest JSON report
reports = sorted(Path("evals_output").glob("*.json"), reverse=True)
latest = reports[0]
print("Report:", latest.name)
print()

with open(latest, encoding="utf-8") as f:
    data = json.load(f)

total = data.get("total", 0)
passed = data.get("passed", 0)
accuracy = data.get("accuracy", 0)

print(f"TOTAL: {passed}/{total} passed ({accuracy}%)")
print()
print("By Category:")
for cat, stats in data.get("by_category", {}).items():
    cat_total = stats.get("total", 0)
    cat_passed = stats.get("passed", 0)
    pct = round(100 * cat_passed / cat_total, 1) if cat_total else 0
    print(f"  {cat:25} {cat_passed}/{cat_total} ({pct}%)")
print()

failed = data.get("failed_cases", [])
if failed:
    print(f"Failed Tests ({len(failed)}):")
    for fc in failed:
        q = fc.get("question", "")[:60]
        print(f"  X {fc.get('id')}: {q}")
        print(f"     Expected: {fc.get('expected_decision')} | Got: {fc.get('actual_decision')}")
        checks = fc.get("check_results", {}).get("checks", {})
        print(f"     Checks: {checks}")
else:
    print("All tests passed!")