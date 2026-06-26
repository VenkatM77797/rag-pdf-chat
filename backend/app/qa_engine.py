from app.embeddings import get_embedding
from app.vector_store import search
from app.llm import ask_llama

def ask_question(question: str):
    q_emb = get_embedding(question)
    docs = search(q_emb)

    context = "\n\n".join(docs)

    prompt = f"""
Use ONLY the context below:

{context}

Question: {question}
"""

    return ask_llama(prompt)


# -----------------------------
# STREAMING FUNCTION (USED BY /ask-stream)
# -----------------------------
import requests
import json


def ask_llama_stream(prompt: str):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": True
        },
        stream=True
    )

    for line in response.iter_lines():
        if not line:
            continue

        try:
            data = json.loads(line.decode("utf-8"))

            if data.get("response"):
                yield data["response"]

            if data.get("done"):
                break

        except json.JSONDecodeError:
            continue