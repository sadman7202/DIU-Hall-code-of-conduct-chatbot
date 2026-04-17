import json

with open("data/processed/extracted_pages.json", "r", encoding="utf-8") as f:
    pages = json.load(f)

for p in [3, 12, 13, 22, 26]:
    page_data = next((x for x in pages if x["page"] == p), None)
    if page_data:
        print("\n" + "="*80)
        print(f"PAGE {p}")
        print("="*80)
        print(page_data["text"][:1500])