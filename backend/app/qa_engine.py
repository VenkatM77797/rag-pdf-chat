from app.embeddings import get_embedding
from app.vector_store import search
from app.llm import ask_llama

def ask_question(question):
    q_emb = get_embedding(question)
    docs = search(q_emb)
    context = "\n\n".join(docs)

    prompt = f"""Use ONLY this context:

{context}

Question: {question}
"""

    return ask_llama(prompt)
