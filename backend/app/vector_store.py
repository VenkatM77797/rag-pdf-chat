from pathlib import Path
from uuid import uuid4

import chromadb


BASE_DIRECTORY = Path(__file__).resolve().parent.parent
CHROMA_DB_PATH = BASE_DIRECTORY / "chroma_db"
COLLECTION_NAME = "pdf_documents"


client = chromadb.PersistentClient(
    path=str(CHROMA_DB_PATH),
)


def get_collection():
    """
    Get the existing ChromaDB collection or create it.
    """
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "hnsw:space": "cosine",
        },
    )


def store_chunks(
    chunks: list[str],
    embeddings: list[list[float]],
    source: str | None = None,
) -> int:
    """
    Store PDF chunks and their embeddings in ChromaDB.
    """
    if not chunks:
        raise ValueError("No text chunks were provided.")

    if not embeddings:
        raise ValueError("No embeddings were provided.")

    if len(chunks) != len(embeddings):
        raise ValueError(
            "The number of chunks must match "
            "the number of embeddings."
        )

    collection = get_collection()

    ids = [
        str(uuid4())
        for _ in chunks
    ]

    source_name = source or "unknown.pdf"

    metadatas = [
        {
            "source": source_name,
            "chunk_index": index,
        }
        for index in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(chunks)


def search(
    query_embedding: list[float],
    n_results: int = 5,
) -> list[str]:
    """
    Search ChromaDB and return relevant PDF chunks.
    """
    if not query_embedding:
        return []

    if n_results <= 0:
        raise ValueError(
            "n_results must be greater than zero."
        )

    collection = get_collection()
    document_count = collection.count()

    if document_count == 0:
        return []

    result_count = min(
        n_results,
        document_count,
    )

    results = collection.query(
        query_embeddings=[
            query_embedding
        ],
        n_results=result_count,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    documents = results.get("documents")

    if not documents:
        return []

    if not documents[0]:
        return []

    return [
        document
        for document in documents[0]
        if document
    ]


def has_documents() -> bool:
    """
    Check whether ChromaDB contains PDF chunks.
    """
    collection = get_collection()

    return collection.count() > 0


def clear_collection() -> None:
    """
    Delete all existing PDF chunks.
    """
    collection = get_collection()

    records = collection.get()
    ids = records.get("ids", [])

    if ids:
        collection.delete(
            ids=ids
        )