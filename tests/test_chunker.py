import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from rag.loader import load_all_documents
from rag.chunker import chunk_documents

def test_chunker():
    documents = load_all_documents()
    chunks = chunk_documents(documents)

    print("=" * 60)
    print(f"Documents : {len(documents)}")
    print(f"Chunks     : {len(chunks)}")
    print("=" * 60)

    print("\nFirst Chunk:\n")
    print(chunks[0])
    
    assert len(documents) > 0
    assert len(chunks) > 0