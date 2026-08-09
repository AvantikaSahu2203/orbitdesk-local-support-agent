import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from rag.loader import load_all_documents
from rag.chunker import chunk_documents
from rag.embeddings import EmbeddingModel
from rag.retriever import Retriever


# ---------------------------------------------
# Load documents
# ---------------------------------------------

def test_retriever():
    documents = load_all_documents()
    chunks = chunk_documents(documents)

    print(f"Documents: {len(documents)}")
    print(f"Chunks: {len(chunks)}")

    embedding_model = EmbeddingModel()
    texts = [chunk["content"] for chunk in chunks]
    embeddings = embedding_model.encode(texts)

    print(f"Embedding shape: {embeddings.shape}")

    retriever = Retriever(
        embedding_model=embedding_model,
        chunks=chunks,
        embeddings=embeddings
    )

    query = (
        "My scheduled exports stopped after "
        "I changed my workspace timezone. "
        "What should I check?"
    )

    results = retriever.retrieve(query, top_k=5)

    print("\n")
    print("=" * 70)
    print("RETRIEVED EVIDENCE")
    print("=" * 70)

    for i, result in enumerate(results, start=1):
        print(f"\n[{i}]")
        print(f"Document: {result['document']}")
        print(f"Chunk: {result['chunk_id']}")
        print(f"Score: {result['score']:.4f}")
        print(f"Content:\n{result['content']}")

    assert len(results) > 0
    assert any(res["document"] == "03_workspace_settings_and_timezones.md" for res in results)


def test_duplicate_retrieval_consolidation():
    # Setup mock retrieved documents with duplicate files
    mock_retrieved = [
        {"document": "03_workspace_settings_and_timezones.md", "content": "Chunk 1 content"},
        {"document": "03_workspace_settings_and_timezones.md", "content": "Chunk 2 content"},
        {"document": "04_scheduled_exports.md", "content": "Chunk 3 content"},
    ]

    consolidated = {}
    for document in mock_retrieved:
        source = document.get("document", "unknown")
        content = document.get("content", "")
        if source not in consolidated:
            consolidated[source] = []
        consolidated[source].append(content)

    assert len(consolidated) == 2
    assert "03_workspace_settings_and_timezones.md" in consolidated
    assert "04_scheduled_exports.md" in consolidated
    assert len(consolidated["03_workspace_settings_and_timezones.md"]) == 2
    assert consolidated["03_workspace_settings_and_timezones.md"][0] == "Chunk 1 content"
    assert consolidated["03_workspace_settings_and_timezones.md"][1] == "Chunk 2 content"