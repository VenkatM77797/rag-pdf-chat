import os
from functools import lru_cache

from sentence_transformers import (
    SentenceTransformer,
)


MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """
    Load the embedding model once on first use.
    """
    return SentenceTransformer(
        MODEL_NAME
    )


def get_embedding(
    text: str,
) -> list[float]:
    """
    Generate one normalized embedding.
    """
    clean_text = text.strip()

    if not clean_text:
        raise ValueError(
            "Text cannot be empty."
        )

    embedding = get_model().encode(
        clean_text,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )

    return embedding.tolist()


def get_embeddings(
    texts: list[str],
) -> list[list[float]]:
    """
    Generate embeddings for multiple text chunks.
    """
    if not texts:
        return []

    clean_texts = [
        text.strip()
        for text in texts
    ]

    if any(
        not text
        for text in clean_texts
    ):
        raise ValueError(
            "Embedding input contains "
            "an empty text chunk."
        )

    embeddings = get_model().encode(
        clean_texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )

    return embeddings.tolist()