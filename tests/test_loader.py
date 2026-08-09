import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from rag.loader import (
    load_markdown_documents,
    load_resolved_cases,
    load_all_documents,
)

def test_loader():
    docs = load_markdown_documents()
    cases = load_resolved_cases()
    all_docs = load_all_documents()

    print("=" * 60)
    print("Markdown Documents")
    print("=" * 60)

    print(f"Loaded: {len(docs)} markdown files\n")

    for doc in docs:
        print(doc["document"])

    print("\n")

    print("=" * 60)
    print("Resolved Cases")
    print("=" * 60)

    print(f"Loaded: {len(cases)} cases\n")

    print(cases[0])

    print("\n")

    print("=" * 60)
    print("Combined Documents")
    print("=" * 60)

    print(f"Total documents available for RAG: {len(all_docs)}")
    
    assert len(docs) > 0
    assert len(cases) > 0
    assert len(all_docs) > 0

