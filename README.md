# DIU Hall Code of Conduct Chatbot

A retrieval-augmented chatbot that answers questions about the DIU (Daffodil International University) Hall Code of Conduct. I built this project to make hostel rules easy to look up through a conversational interface.

## Project Progress Summary

### What I Built

- **PDF extraction pipeline** – I wrote `scripts/extract_pdf.py` to pull raw text out of the hostel code-of-conduct PDF and save it as structured JSON (`data/processed/extracted_pages.json`).
- **Text cleaning** – I created `scripts/clean_text.py` to strip noise, repeated junk phrases, and section headings so that only the rule content is kept. The cleaned output is stored in `data/processed/cleaned_text.txt` and `data/processed/cleaned_pages.json`.
- **Rule chunking** – I implemented `scripts/chunk_rules.py` to split the cleaned text into individual rule chunks (one rule per chunk), producing `data/processed/chunks_updated.json` with 43 total rules.
- **Vector index** – I built `scripts/build_index.py` to embed each rule chunk using `all-MiniLM-L6-v2` (SentenceTransformers) and store the embeddings in a persistent ChromaDB collection under `data/vectordb/`.
- **Retrieval utilities** – I wrote `utils/retrieval.py` to handle both exact rule-number lookups and semantic similarity search against the vector store.
- **Answer generation** – I implemented `utils/answering.py` to format retrieved rules into readable answers and apply a confidence threshold so the bot falls back gracefully when no relevant rule is found.
- **Streamlit web app** – I developed `app.py` as a user-facing chat interface (using Streamlit) that combines a FAISS vector store with a HuggingFace `flan-t5-base` LLM through a LangChain `RetrievalQA` chain.
- **Console chatbot** – I also made `scripts/console_chatbot.py` for quick terminal-based testing of the retrieval pipeline without launching the full web app.

### How I Structured the Data Pipeline

```
data/raw/hostel_code.pdf
        ↓  extract_pdf.py
data/processed/extracted_pages.json
        ↓  clean_text.py
data/processed/cleaned_pages.json + cleaned_text.txt
        ↓  chunk_rules.py
data/processed/chunks_updated.json  (43 rules)
        ↓  build_index.py
data/vectordb/  (ChromaDB embeddings)
        ↓  utils/retrieval.py + utils/answering.py
app.py  (Streamlit UI)
```

### Key Design Decisions I Made

- **One rule per chunk** – I chose this strategy so that each retrieved document maps directly to a single, self-contained hostel rule, which makes answers more precise.
- **Exact rule-number lookup** – I added a regex-based extraction step so that when users ask "What is rule 5?", I bypass semantic search entirely and return the exact rule instantly.
- **Confidence threshold** – I set a maximum distance of `1.50` in ChromaDB similarity scores; queries that score above this threshold receive the fallback response `"Not mentioned in hostel rules."` rather than a hallucinated answer.
- **Telemetry disabled** – I set `ANONYMIZED_TELEMETRY=False` to prevent ChromaDB from sending usage data during development and testing.

## Setup

### Prerequisites

- Python 3.10+
- The hostel code-of-conduct PDF placed at `data/raw/hostel_code.pdf`

### Installation

```bash
pip install -r requirements.txt
```

### Build the Vector Index

```bash
python scripts/build_index.py
```

### Run the Web App

```bash
streamlit run app.py
```

### Run the Console Chatbot

```bash
python scripts/console_chatbot.py
```

## Project Structure

```
├── app.py                  # Streamlit web interface
├── data/
│   ├── raw/                # Source PDF
│   ├── processed/          # Extracted, cleaned, and chunked rule data
│   └── vectordb/           # ChromaDB persistent vector store
├── scripts/
│   ├── extract_pdf.py      # PDF → JSON extraction
│   ├── clean_text.py       # Text cleaning and normalisation
│   ├── chunk_rules.py      # Rule chunking
│   ├── build_index.py      # Embedding generation and indexing
│   ├── console_chatbot.py  # Terminal-based chatbot
│   ├── test_retrieval.py   # Retrieval smoke tests
│   └── test_output.py      # Answer output tests
├── utils/
│   ├── retrieval.py        # Vector search helpers
│   └── answering.py        # Answer formatting and confidence filtering
├── requirements.txt        # Core dependencies
└── requirements2.txt       # Extended / alternative dependencies
```
