import os

# Disable Chroma/PostHog telemetry BEFORE importing anything that might import chromadb
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.answering import answer_question


def main():
    print("=" * 80)
    print("Hostel Code of Conduct Chatbot")
    print("Type your question. Type 'exit' to quit.")
    print("=" * 80)

    while True:
        user_query = input("\nYou: ").strip()

        if user_query.lower() in {"exit", "quit", "bye"}:
            print("Bot: Goodbye.")
            break

        result = answer_question(user_query)

        print("\nBot:")
        print(result["answer"])

        if result["sources"]:
            print("\nSources:")
            for src in result["sources"]:
                print(f"- {src}")


if __name__ == "__main__":
    main()