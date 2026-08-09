from rag.vectorstore import VectorStore


class Retriever:
    """
    Semantic retriever using a shared embedding model
    and local FAISS vector store.
    """

    def __init__(
        self,
        embedding_model,
        chunks,
        embeddings
    ):

        self.embedding_model = embedding_model

        dimension = embeddings.shape[1]

        self.vector_store = VectorStore(
            dimension=dimension
        )

        self.vector_store.add(
            embeddings,
            chunks
        )

    def retrieve(
        self,
        query,
        top_k=5
    ):
        """
        Retrieve the most relevant chunks.
        """

        query_embedding = self.embedding_model.encode(
            [query]
        )[0]

        return self.vector_store.search(
            query_embedding,
            top_k=top_k
        )