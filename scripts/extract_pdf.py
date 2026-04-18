import fitz  # PyMuPDF
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PDF_PATH = PROJECT_ROOT / "data" / "raw" / "hostel_code.pdf"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "extracted_pages.json"

def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    pages = []

    for i, page in enumerate(doc):
        text = page.get_text("text")
        pages.append({
            "page": i + 1,
            "text": text
        })

    return pages

def main():
    (PROJECT_ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)

    extracted_pages = extract_pdf_text(PDF_PATH)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(extracted_pages, f, ensure_ascii=False, indent=2)

    print(f"Saved extracted text to: {OUTPUT_PATH}")
    print(f"Total pages extracted: {len(extracted_pages)}")

if __name__ == "__main__":
    main()