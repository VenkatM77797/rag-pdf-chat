from collections.abc import Iterator

from app.embeddings import get_embedding
from app.llm import ask_llama, stream_llama
from app.vector_store import search


RETRIEVAL_COUNT = 4


def build_prompt(
    question: str,
) -> str:
    """
    Retrieve relevant PDF chunks and build the RAG prompt.
    """
    clean_question = question.strip()

    if not clean_question:
        raise ValueError(
            "Question cannot be empty."
        )

    query_embedding = get_embedding(
        clean_question
    )

    documents = search(
        query_embedding=query_embedding,
        n_results=RETRIEVAL_COUNT,
    )

    if not documents:
        raise ValueError(
            "No PDF content is available. "
            "Upload a PDF first."
        )

    context = "\n\n---\n\n".join(
        documents
    )

    return f"""
You are a document question-answering assistant.

Follow these rules:
1. Answer only from the supplied PDF context.
2. Do not use outside knowledge.
3. If the answer is not present, say exactly:
   "I could not find that information in the uploaded PDF."
4. Keep the answer clear and direct.

PDF context:
{context}

Question:
{clean_question}

Answer:
""".strip()


def ask_question(
    question: str,
) -> str:
    """
    Generate one complete answer.
    """
    prompt = build_prompt(
        question
    )

    return ask_llama(
        prompt
    )


def stream_question(
    question: str,
) -> Iterator[str]:
    """
    Generate a streamed answer.
    """
    prompt = build_prompt(
        question
    )

    return stream_llama(
        prompt
    )