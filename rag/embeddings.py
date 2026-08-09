from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingModel:
    """
    Wrapper around our local Hugging Face embedding model.
    """

    def __init__(self):
        print(f"Loading embedding model: {MODEL_NAME}")

        try:
            # First attempt loading with local_files_only=True to prevent network checks
            self.model = SentenceTransformer(MODEL_NAME, local_files_only=True)
        except Exception as local_err:
            # Fall back to standard cached/remote load if local load fails
            try:
                self.model = SentenceTransformer(MODEL_NAME)
            except Exception as net_err:
                raise RuntimeError(
                    f"Failed to load embedding model '{MODEL_NAME}'. "
                    f"Ensure you are online for the initial download or the model is cached. "
                    f"Details: {net_err}"
                ) from net_err

        print("Embedding model loaded.")

    def encode(self, texts):
        """
        Convert a list of texts into embedding vectors.
        """

        return self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
        )