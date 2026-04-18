import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_pages.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "chunks_updated.json"

KNOWN_SECTIONS = [
    "HALL ADMISSION, SEAT ALLOCATION & RENEWAL POLICY",
    "VISITORS AND GUEST ACCOMMODATION REGULATIONS",
    "STUDENTS ENTRY TIME & NIGHT-OUT REGULATIONS",
    "Room Inspection & Access Authority",
    "HALL AUTHORITY SUPERVISION & DISCIPLINARY JURISDICTION",
    "ROOM ALLOCATION & PERSONAL BELONGINGS POLICY",
    "HEALTH, ISSUE AND STAFF CONDUCT GUIDELINES",
    "PROHIBITED BEHAVIORS & DISCIPLINARY ACTIONS",
    "ENERGY CONSERVATION & PROPERTY RESPONSIBILITY",
    "DINING COMPLAINT GUIDELINES",
    "CRISIS MANAGEMENT AND STUDENT COOPERATION",
    "COMPLIANCE WITH HALL RULES & ADMINISTRATIVE RIGHTS",
]

def normalize_text(text: str) -> str:
    # Make everything single-line for easier regex parsing
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()

    # Fix broken decimal like "2. 5" -> "2.5"
    text = re.sub(r"(\d)\.\s+(\d)", r"\1.\2", text)

    return text

def detect_section(text: str):
    for section in KNOWN_SECTIONS:
        if text.startswith(section):
            return section
    return None

def remove_section_prefix(text: str, section: str) -> str:
    if section and text.startswith(section):
        return text[len(section):].strip()
    return text

def extract_rules(text: str):
    """
    Extract real rules only.
    Matches:
      1. Hall Admission ...
      12. Visitors are ...
      43. Students residing ...
    Avoids decimals like 2.5 because after the dot we require
    optional spaces + a CAPITAL LETTER.
    """
    pattern = re.compile(
        r"(?<!\d)"                 # previous char is not a digit
        r"(\d{1,2})"               # rule number
        r"\.\s*"                   # dot + optional spaces
        r"(?=[A-Z])"               # next real content starts with capital letter
        r"(.*?)"                   # rule text
        r"(?="
        r"(?<!\d)\d{1,2}\.\s*(?=[A-Z])"  # next real rule
        r"|$"                      # or end of text
        r")"
    )

    matches = pattern.findall(text)

    rules = []
    for rule_no, rule_text in matches:
        rules.append({
            "rule_number": int(rule_no),
            "text": rule_text.strip()
        })

    return rules

def main():
    print("Starting chunk_rules.py...")

    if not INPUT_PATH.exists():
        print(f"ERROR: File not found -> {INPUT_PATH}")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        pages = json.load(f)

    print(f"Loaded {len(pages)} page entries from JSON")

    # use dict to prevent duplicate rule numbers
    chunks_by_rule = {}

    for item in pages:
        page_num = item.get("page")
        raw_text = item.get("text", "")

        print("\n" + "=" * 80)
        print(f"Processing page {page_num}")
        print("=" * 80)

        if not raw_text.strip():
            print("Empty text, skipped")
            continue

        text = normalize_text(raw_text)
        print("TEXT PREVIEW:")
        print(text[:250])

        section = detect_section(text)
        print(f"Detected section: {section}")

        if not section:
            print("WARNING: No section detected, skipped")
            continue

        body = remove_section_prefix(text, section)
        rules = extract_rules(body)

        print(f"Rules found on page {page_num}: {len(rules)}")

        for rule in rules:
            rule_number = rule["rule_number"]
            chunk = {
                "id": f"rule_{rule_number}",
                "rule_number": rule_number,
                "section": section,
                "page": page_num,
                "text": rule["text"]
            }

            # dedupe safeguard: if duplicate, keep the longer one
            if rule_number in chunks_by_rule:
                old_chunk = chunks_by_rule[rule_number]
                if len(chunk["text"]) > len(old_chunk["text"]):
                    print(f"WARNING: Duplicate rule_{rule_number} found. Keeping longer text from page {page_num}.")
                    chunks_by_rule[rule_number] = chunk
                else:
                    print(f"WARNING: Duplicate rule_{rule_number} found. Keeping existing text from page {old_chunk['page']}.")
            else:
                chunks_by_rule[rule_number] = chunk

    chunks = sorted(chunks_by_rule.values(), key=lambda x: x["rule_number"])

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print(f"Saved chunks -> {OUTPUT_PATH}")
    print(f"Total chunks -> {len(chunks)}")
    print("=" * 80)

if __name__ == "__main__":
    main()