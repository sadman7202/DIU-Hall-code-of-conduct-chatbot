import json
import os
import re

INPUT_PATH = "data/processed/extracted_pages.json"
OUTPUT_JSON = "data/processed/cleaned_pages.json"
OUTPUT_TXT = "data/processed/cleaned_text.txt"

# Skip intro, summary, and thank-you pages
SKIP_PAGES = {1, 2, 3, 4, 29}

NOISE_PATTERNS = [
    r"With the improvement of people's living\s*standards\s*and the enhancement of health\s*awareness,\s*the demand for smart wearable\s*devices is increasing day by day\.",
    r"Project Background",
    r"Project Scope",
    r"Team Members",
    r"Project Objectives",
    r"The project covers the entire process.*?hardware design\.",
    r"The project team consists.*?development\.",
    r"The main goals of the project are to achieve.*?launched\.",
]

def clean_text(text: str) -> str:
    # Remove repeated noisy paragraphs/headings
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Join hyphenated line-break words: e-\ncigarettes -> e-cigarettes
    text = re.sub(r"(\w)-\n(\w)", r"\1-\2", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Fix missing space after rule number: 3.Selected -> 3. Selected
    text = re.sub(r"(?m)^(\d{1,2})\.(\S)", r"\1. \2", text)

    # Fix missing space after sentence period: booking.Incomplete -> booking. Incomplete
    text = re.sub(r"([a-zA-Z])\.([A-Z])", r"\1. \2", text)

    # Remove trailing spaces on each line
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)

    # Turn single newlines inside paragraphs into spaces
    # but keep true paragraph breaks
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Normalize multiple spaces
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Normalize too many blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def main():
    if not os.path.exists(INPUT_PATH):
        print(f"ERROR: File not found -> {INPUT_PATH}")
        return

    os.makedirs("data/processed", exist_ok=True)

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        pages = json.load(f)

    cleaned_pages = []
    combined_parts = []

    for page in pages:
        page_num = page.get("page")
        raw_text = page.get("text", "")

        if page_num in SKIP_PAGES:
            continue

        cleaned = clean_text(raw_text)

        if cleaned:
            cleaned_pages.append({
                "page": page_num,
                "text": cleaned
            })
            combined_parts.append(f"--- PAGE {page_num} ---\n{cleaned}\n")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(cleaned_pages, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(combined_parts))

    print("Cleaning complete.")
    print(f"Saved cleaned pages JSON -> {OUTPUT_JSON}")
    print(f"Saved cleaned text file -> {OUTPUT_TXT}")
    print(f"Total kept pages -> {len(cleaned_pages)}")

if __name__ == "__main__":
    main()