import json
import re
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer
from transformers import logging as hf_logging

hf_logging.set_verbosity_error()

DB_DIR = Path(r"D:\Projects\hostel chatbot\data\vectordb")
COLLECTION_NAME = "hostel_rules"
MODEL_NAME = "all-MiniLM-L6-v2"
CHUNKS_PATH = Path(r"D:\Projects\hostel chatbot\data\processed\chunks_updated.json")

# Load once
model = SentenceTransformer(MODEL_NAME)
client = chromadb.PersistentClient(path=str(DB_DIR))
collection = client.get_collection(COLLECTION_NAME)

with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    CHUNKS = json.load(f)

RULE_MAP = {int(chunk["rule_number"]): chunk for chunk in CHUNKS}


def extract_rule_number(query: str):
    """
    Match:
    - what is rule 12
    - tell me rule 32
    - explain rule 40
    """
    match = re.search(r"\brule\s+(\d{1,2})\b", query.lower())
    if match:
        return int(match.group(1))
    return None


def get_rule_by_number(rule_number: int):
    return RULE_MAP.get(rule_number)


def semantic_search(query: str, top_k: int = 3):
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    formatted = []
    for doc_id, doc, meta, dist in zip(ids, docs, metas, distances):
        rule_number = int(meta.get("rule_number"))
        chunk = RULE_MAP.get(rule_number, {})

        formatted.append({
            "id": doc_id,
            "rule_number": rule_number,
            "section": meta.get("section"),
            "page": int(meta.get("page")),
            "document": doc,
            "distance": float(dist),
            "text": chunk.get("text", "")
        })

    return formatted


def search_rules(query: str, top_k: int = 3):
    """
    Search strategy:
    1. Exact rule lookup if user explicitly asks for a rule number
    2. Otherwise semantic search
    """
    rule_number = extract_rule_number(query)
    if rule_number is not None:
        exact = get_rule_by_number(rule_number)
        if exact:
            return {
                "mode": "exact_rule",
                "results": [{
                    "id": exact["id"],
                    "rule_number": exact["rule_number"],
                    "section": exact["section"],
                    "page": exact["page"],
                    "document": (
                        f"Section: {exact['section']}\n"
                        f"Rule Number: {exact['rule_number']}\n"
                        f"Page: {exact['page']}\n"
                        f"Rule Text: {exact['text']}"
                    ),
                    "distance": 0.0,
                    "text": exact["text"]
                }]
            }

    return {
        "mode": "semantic",
        "results": semantic_search(query, top_k=top_k)
    }