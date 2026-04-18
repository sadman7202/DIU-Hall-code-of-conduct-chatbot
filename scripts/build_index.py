import json
import os
from pathlib import Path

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

import chromadb
from sentence_transformers import SentenceTransformer

# --------------------------------------------------------------------------------------
# Project-relative paths (portable)
# --------------------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "chunks_updated.json"
DB_DIR = PROJECT_ROOT / "data" / "vectordb"
COLLECTION_NAME = "hostel_rules"

# Lightweight embedding model
MODEL_NAME = "all-MiniLM-L6-v2"


def load_chunks(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"Chunk file not found: {path}\n"
            "Make sure you generated it first (scripts/chunk_rules.py)."
        )

    with open(path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    return chunks


def make_documents(chunks):
    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        rule_id = chunk["id"]
        rule_number = chunk["rule_number"]
        section = chunk["section"]
        page = chunk["page"]
        text = chunk["text"]

        doc_text = (
            f"Section: {section}\n"
            f"Rule Number: {rule_number}\n"
            f"Page: {page}\n"
            f"Rule Text: {text}"
        )

        ids.append(rule_id)
        documents.append(doc_text)
        metadatas.append(
            {
                "rule_number": int(rule_number),
                "section": str(section),
                "page": int(page),
            }
        )

    return ids, documents, metadatas


def main():
    print("Loading chunks...")
    chunks = load_chunks(CHUNKS_PATH)
    print(f"Total chunks loaded: {len(chunks)}")

    print("Preparing documents...")
    ids, documents, metadatas = make_documents(chunks)

    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print("Generating embeddings...")
    embeddings = model.encode(
        documents,
        show_progress_bar=True,
        normalize_embeddings=True,
    ).tolist()

    print(f"Creating vector DB folder: {DB_DIR}")
    os.makedirs(DB_DIR, exist_ok=True)

    client = chromadb.PersistentClient(path=str(DB_DIR))

    # delete old collection if exists
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        print(f"Deleting old collection: {COLLECTION_NAME}")
        client.delete_collection(COLLECTION_NAME)

    print(f"Creating collection: {COLLECTION_NAME}")
    collection = client.create_collection(name=COLLECTION_NAME)

    print("Adding documents to Chroma...")
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    print("\nIndex build complete.")
    print(f"Vector DB saved in: {DB_DIR}")
    print(f"Collection name: {COLLECTION_NAME}")
    print(f"Total indexed documents: {len(ids)}")


if __name__ == "__main__":
    main()