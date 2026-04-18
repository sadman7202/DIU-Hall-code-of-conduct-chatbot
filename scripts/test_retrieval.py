from pathlib import Path
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
import chromadb
from sentence_transformers import SentenceTransformer

# --------------------------------------------------------------------------------------
# Project-relative paths (portable)
# --------------------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_DIR = PROJECT_ROOT / "data" / "vectordb"
COLLECTION_NAME = "hostel_rules"
MODEL_NAME = "all-MiniLM-L6-v2"


def search_rules(query, top_k=5):
    client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    model = SentenceTransformer(MODEL_NAME)
    query_embedding = model.encode([query], normalize_embeddings=True).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
    )

    return results


def print_results(query, results):
    print("\n" + "=" * 100)
    print(f"QUERY: {query}")
    print("=" * 100)

    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for i, (doc_id, doc, meta, dist) in enumerate(
        zip(ids, docs, metas, distances), start=1
    ):
        print(f"\nResult #{i}")
        print(f"ID: {doc_id}")
        print(f"Rule Number: {meta.get('rule_number')}")
        print(f"Section: {meta.get('section')}")
        print(f"Page: {meta.get('page')}")
        print(f"Distance: {dist}")
        print("Document Preview:")
        print(doc[:500])
        print("-" * 100)


def main():
    test_queries = [
        "Can visitors enter my room?",
        "What is the night out rule?",
        "Can I use a heater in the hostel?",
        "How do I make a dining complaint?",
        "Can I change my room?",
        "What happens if someone smokes in the hall?",
        "Who should I report illness to?",
    ]

    for query in test_queries:
        results = search_rules(query, top_k=3)
        print_results(query, results)


if __name__ == "__main__":
    main()