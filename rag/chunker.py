from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_documents(documents):
    """
    Split documents into smaller chunks for embedding.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
    )

    chunks = []

    for doc in documents:

        pieces = splitter.split_text(doc["content"])

        for i, piece in enumerate(pieces):

            chunks.append(
                {
                    "document": doc["document"],
                    "chunk_id": i,
                    "content": piece,
                }
            )

    return chunks