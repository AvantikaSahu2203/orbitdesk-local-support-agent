import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from rag.loader import load_all_documents
from rag.chunker import chunk_documents
from rag.embeddings import EmbeddingModel
from rag.vectorstore import VectorStore


# --------------------------------------------------
# 1. Load documents
# --------------------------------------------------

def test_vectorstore():
    documents = load_all_documents()
    print(f"Loaded documents: {len(documents)}")

    chunks = chunk_documents(documents)
    print(f"Created chunks: {len(chunks)}")

    embedding_model = EmbeddingModel()
    texts = [chunk["content"] for chunk in chunks]
    embeddings = embedding_model.encode(texts)

    print(f"Embedding shape: {embeddings.shape}")

    dimension = embeddings.shape[1]
    vector_store = VectorStore(dimension=dimension)

    vector_store.add(embeddings, chunks)
    print(f"Vectors stored: {vector_store.index.ntotal}")

    query = (
        "My scheduled export stopped "
        "after I changed the workspace timezone."
    )

    query_embedding = embedding_model.encode([query])[0]
    results = vector_store.search(query_embedding, top_k=5)

    print("\n")
    print("=" * 70)
    print("SEARCH RESULTS")
    print("=" * 70)

    for i, result in enumerate(results, start=1):
        print(f"\nResult {i}")
        print(f"Document: {result['document']}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Score: {result['score']:.4f}")
        print(f"Content:\n{result['content'][:500]}")

    assert len(results) > 0
    assert any(res["document"] == "03_workspace_settings_and_timezones.md" for res in results)