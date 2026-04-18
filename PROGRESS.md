# DIU Hall Code of Conduct Chatbot — Progress Summary

## Overview

This document tracks the development milestones, current status, known issues (and applied fixes), and the planned next steps for the DIU Hall Code of Conduct Chatbot project.

---

## Project Structure

```
DIU-Hall-code-of-conduct-chatbot/
├── data/
│   ├── raw/                  # Source PDF (hostel_code.pdf)
│   ├── processed/            # Intermediate JSON files
│   │   ├── extracted_pages.json
│   │   ├── cleaned_pages.json
│   │   ├── cleaned_text.txt
│   │   └── chunks_updated.json
│   └── vectordb/             # ChromaDB persistent store
├── scripts/
│   ├── extract_pdf.py        # Step 1: PDF → extracted_pages.json
│   ├── clean_text.py         # Step 2: raw text → cleaned_pages.json
│   ├── chunk_rules.py        # Step 3: cleaned pages → chunks_updated.json
│   ├── build_index.py        # Step 4: chunks → ChromaDB vector index
│   ├── test_retrieval.py     # Manual retrieval smoke test
│   ├── check_extraction.py   # Inspect raw extracted pages
│   ├── test_output.py        # Inspect chunked rules
│   └── console_chatbot.py    # Interactive CLI chatbot
├── utils/
│   ├── __init__.py
│   ├── retrieval.py          # ChromaDB + semantic / exact-rule search
│   └── answering.py          # Answer formatting + confidence gating
├── app.py                    # Streamlit UI (LangChain + FAISS pipeline)
├── requirements.txt          # Pinned production deps
└── requirements2.txt         # Full frozen env (for reference)
```

---

## Milestones

### ✅ Milestone 1 — PDF Extraction
**Script:** `scripts/extract_pdf.py`

- Opens `data/raw/hostel_code.pdf` using PyMuPDF (`fitz`).
- Extracts text page-by-page into `data/processed/extracted_pages.json`.
- 29 pages total in the source document.

---

### ✅ Milestone 2 — Text Cleaning
**Script:** `scripts/clean_text.py`

- Reads `extracted_pages.json`.
- Skips noise/intro pages (pages 1–4 and 29).
- Removes known noise patterns (project background boilerplate, team-member headings, etc.).
- Fixes hyphenated line breaks, normalises whitespace, repairs missing spaces after rule numbers.
- Outputs `cleaned_pages.json` (JSON) and `cleaned_text.txt` (plain text).

---

### ✅ Milestone 3 — Rule Chunking
**Script:** `scripts/chunk_rules.py`

- Reads `cleaned_pages.json`.
- Detects 12 known section headings via string prefix match.
- Extracts numbered rules (1–43) using a regex that distinguishes rule numbers from decimal values.
- Deduplicates: if a rule appears on multiple pages, the longer version is kept.
- Outputs `data/processed/chunks_updated.json` — 43 rule chunks with fields `id`, `rule_number`, `section`, `page`, `text`.

---

### ✅ Milestone 4 — Embedding & Index Build
**Script:** `scripts/build_index.py`

- Loads chunks from `chunks_updated.json`.
- Builds rich document strings: `Section / Rule Number / Page / Rule Text`.
- Encodes documents with `sentence-transformers/all-MiniLM-L6-v2` (L2-normalised).
- Creates (or recreates) a ChromaDB `PersistentClient` at `data/vectordb/`.
- Stores the collection `hostel_rules` with embeddings + metadata.

---

### ✅ Milestone 5 — Vector DB & Retrieval
**Module:** `utils/retrieval.py`

- Loads the persistent ChromaDB collection and the sentence-transformer model once at import time.
- **Exact-rule mode:** regex detects phrases like *"rule 12"* → direct `RULE_MAP` lookup, distance = 0.
- **Semantic mode:** encodes the query and calls `collection.query()` for top-K nearest neighbours.
- Returns structured result dicts (id, rule\_number, section, page, document, distance, text).

---

### ✅ Milestone 6 — Answer Generation
**Module:** `utils/answering.py`

- Wraps `search_rules()` with confidence gating: results with cosine distance > 1.50 trigger a "low confidence" response.
- `build_answer_from_result()` formats natural-language answers citing rule number and section.
- Returns `{ answer: str, sources: [str] }` for the UI layer.

---

### ✅ Milestone 7 — Console Chatbot Interface
**Script:** `scripts/console_chatbot.py`

- Read-eval-print loop calling `answer_question()`.
- Prints the answer and source citations.
- Exits cleanly on `exit` / `quit` / `bye`.

---

### ✅ Milestone 8 — Streamlit Web App
**File:** `app.py`

- Alternative pipeline using LangChain + FAISS (does **not** use the custom ChromaDB pipeline).
- Loads PDF → splits → embeds with `HuggingFaceEmbeddings` → FAISS vector store.
- Uses `google/flan-t5-base` via `HuggingFacePipeline` for generation.
- Grounding check: token-overlap filter ensures the answer is backed by retrieved context.
- Streamlit UI: single text input, displays answer.

> **Note:** `app.py` is an independent prototype. The primary pipeline is the custom ChromaDB one (`scripts/` + `utils/`).

---

## Known Issues & Applied Fixes

### Issue 1 — Hardcoded Windows Paths (Fixed ✅)
**Problem:**  
Several scripts used absolute Windows paths such as `D:\Projects\hostel chatbot\data\vectordb`, which broke on any other machine or OS.

**Fix applied:**  
All scripts and modules now derive paths from `PROJECT_ROOT`:
```python
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_DIR      = PROJECT_ROOT / "data" / "vectordb"
CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "chunks_updated.json"
```
Affected files: `utils/retrieval.py`, `scripts/build_index.py`, `scripts/extract_pdf.py`, `scripts/clean_text.py`, `scripts/chunk_rules.py`, `scripts/check_extraction.py`, `scripts/test_output.py`, `scripts/test_retrieval.py`.

---

### Issue 2 — ChromaDB Telemetry Warning (Fixed ✅)
**Problem:**  
Running any ChromaDB code printed:
```
Failed to send telemetry event ClientStartEvent: capture() takes 1 positional argument but 3 were given
```
This is a bug in the PostHog telemetry client bundled with older ChromaDB versions.

**Fix applied:**  
Set the telemetry opt-out environment variables **before** importing `chromadb`:
```python
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"]      = "False"
```
Added to: `scripts/build_index.py`, `scripts/test_retrieval.py`, `scripts/console_chatbot.py`, `utils/retrieval.py`.

---

### Issue 3 — Duplicate `import os` in build_index.py (Fixed ✅)
**Problem:**  
`scripts/build_index.py` had `import os` twice (lines 1 and 4), with `os.environ` set in between, making the intent confusing.

**Fix applied:**  
Consolidated to a single `import os` block at the top, followed immediately by the environment-variable assignments, before any other imports.

---

### Issue 4 — ChromaDB Migration Error (Documented)
**Problem:**  
When upgrading from ChromaDB `0.5.x` to `1.x` the persistent store schema changed. Running `build_index.py` against an existing `data/vectordb/` folder built with the old version raises a migration error:
```
sqlite3.OperationalError: no such column: ...
```
or a similar schema-mismatch traceback.

**Resolution:**  
Delete (or rename) the `data/vectordb/` folder and re-run `build_index.py`. The script already handles this gracefully: it deletes the old collection before creating a new one, but a complete folder wipe is needed after a major ChromaDB version upgrade.

```bash
rm -rf data/vectordb/       # or rename it
python scripts/build_index.py
```

`requirements2.txt` pins `chromadb==1.5.7` (the current working version).

---

## How to Run (Step-by-Step)

> All commands run from the repository root directory.

```bash
# 1. Extract text from the PDF
python scripts/extract_pdf.py

# 2. Clean and normalise the extracted pages
python scripts/clean_text.py

# 3. Chunk the rules
python scripts/chunk_rules.py

# 4. Build (or rebuild) the ChromaDB vector index
python scripts/build_index.py

# 5. (Optional) Smoke-test retrieval
python scripts/test_retrieval.py

# 6. Launch the console chatbot
python scripts/console_chatbot.py

# 7. (Optional) Launch the Streamlit web app
streamlit run app.py
```

---

## Next Steps

### 🔲 Next Step 1 — Gate Pass Automation (SQLite + PDF + Approval)

Design and implement a Gate Pass system that allows students to request overnight / out-of-hall passes digitally.

**Sub-tasks:**

1. **Database schema** (`data/gatepass.db` via SQLite):
   - `students(id, name, room_number, contact)`
   - `gate_passes(id, student_id, reason, destination, departure_date, return_date, status, created_at)`
   - `status` values: `pending` → `approved` / `rejected`

2. **CLI script** (`scripts/gatepass_request.py`):
   - Student submits a gate-pass request (prompted input).
   - Validates dates and required fields.
   - Inserts record into SQLite with status `pending`.

3. **Approval script** (`scripts/gatepass_approve.py`):
   - Lists all `pending` requests.
   - Hall authority approves or rejects individual requests.
   - Updates `status` in the database.

4. **PDF generation** (`utils/gatepass_pdf.py`):
   - On approval, generates a printable PDF gate pass using `reportlab` or `fpdf2`.
   - Saves to `data/passes/<student_id>_<pass_id>.pdf`.
   - PDF includes: student name, room, dates, reason, approval signature line, hall logo placeholder.

5. **Streamlit integration** (extend `app.py`):
   - Add a "Gate Pass" tab / sidebar section.
   - Students fill a form; on submit, record is created.
   - Admin view shows pending requests with approve/reject buttons.
   - Approved passes display a PDF download link.

---

### 🔲 Next Step 2 — Improve Chunking Coverage

- Investigate rules that are currently missed by the chunking regex (edge cases where a rule starts with a lowercase continuation or a rule number is followed by a sub-item).
- Add unit tests for `extract_rules()` with known page samples.

---

### 🔲 Next Step 3 — Better Answer Quality

- Explore returning 2–3 supporting rules when confidence is medium, rather than only the top-1 result.
- Consider a lightweight re-ranker (e.g., cross-encoder) to improve relevance ordering.

---

### 🔲 Next Step 4 — Deployment

- Dockerise the application (`Dockerfile` + `.dockerignore`).
- Add a `README.md` with quick-start instructions and a screenshot of the Streamlit UI.
- Set up a GitHub Actions CI workflow to lint and smoke-test the pipeline scripts.

---

*Last updated: 2026-04-18*
