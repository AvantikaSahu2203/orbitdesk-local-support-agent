import faiss
import numpy as np


class VectorStore:
    """
    Local FAISS vector store.

    Stores document embeddings and allows
    semantic similarity search.
    """

    def __init__(self, dimension):
        self.dimension = dimension

        # IndexFlatIP performs inner-product similarity.
        # Because our embeddings are normalized,
        # inner product is equivalent to cosine similarity.
        self.index = faiss.IndexFlatIP(dimension)

        # Keep the original chunks so we can return
        # the actual evidence after searching.
        self.chunks = []

    def add(self, embeddings, chunks):
        """
        Add embeddings and their corresponding chunks.
        """

        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )

        self.index.add(embeddings)

        self.chunks.extend(chunks)

    def search(self, query_embedding, top_k=5):
        """
        Search for the most semantically similar chunks.
        """

        query_embedding = np.asarray(
            query_embedding,
            dtype="float32"
        )

        # FAISS expects shape:
        # (number_of_queries, embedding_dimension)
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        scores, indices = self.index.search(
            query_embedding,
            top_k
        )

        results = []

        for score, index in zip(scores[0], indices[0]):

            # FAISS uses -1 when no result exists.
            if index == -1:
                continue

            chunk = self.chunks[index].copy()

            chunk["score"] = float(score)

            results.append(chunk)

        return results