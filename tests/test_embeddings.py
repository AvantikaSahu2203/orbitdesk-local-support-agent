import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from rag.loader import load_all_documents
from rag.chunker import chunk_documents
from rag.embeddings import EmbeddingModel


def test_embeddings():
    documents = load_all_documents()
    chunks = chunk_documents(documents)

    print("=" * 60)
    print(f"Number of chunks: {len(chunks)}")
    print("=" * 60)

    model = EmbeddingModel()
    texts = [chunk["content"] for chunk in chunks]
    embeddings = model.encode(texts)

    print("\nEmbedding test completed!")
    print(f"Number of embeddings: {len(embeddings)}")
    print(f"Embedding dimensions: {embeddings.shape[1]}")

    print("\nFirst embedding:")
    print(embeddings[0][:10])
    
    assert len(embeddings) > 0
    assert embeddings.shape[1] == 384  # MiniLM dimension