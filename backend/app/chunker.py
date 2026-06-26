def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 80,
) -> list[str]:
    """
    Split text into overlapping word-based chunks.
    """
    clean_text = text.strip()

    if not clean_text:
        return []

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than zero."
        )

    if overlap < 0:
        raise ValueError(
            "overlap cannot be negative."
        )

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller "
            "than chunk_size."
        )

    words = clean_text.split()
    step = chunk_size - overlap
    chunks: list[str] = []

    for start in range(
        0,
        len(words),
        step,
    ):
        chunk_words = words[
            start : start + chunk_size
        ]

        if not chunk_words:
            break

        chunks.append(
            " ".join(chunk_words)
        )

        if (
            start + chunk_size
            >= len(words)
        ):
            break

    return chunks