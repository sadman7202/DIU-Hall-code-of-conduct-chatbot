import json
import os

CHUNKS_PATH = "data/processed/chunks_updated.json"

if not os.path.exists(CHUNKS_PATH):
    print(f"ERROR: File not found -> {CHUNKS_PATH}")
    raise SystemExit

with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print("=" * 80)
print("TOTAL CHUNKS:", len(chunks))
print("=" * 80)

print("\nFIRST 5 CHUNKS:\n")
for chunk in chunks[:5]:
    print(chunk)
    print("-" * 80)

print("\nCHECK SPECIFIC RULES:\n")
for rule_id in [1, 2, 12, 13, 14, 15, 25, 32, 40, 43]:
    found = next((c for c in chunks if c["rule_number"] == rule_id), None)
    print("=" * 80)
    print(f"RULE {rule_id}")
    print("=" * 80)
    if found:
        print(found)
    else:
        print("Not found")