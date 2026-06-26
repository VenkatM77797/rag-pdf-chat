from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import shutil
import uuid

from app.pdf_loader import load_pdf_text
from app.chunker import chunk_text
from app.embeddings import get_embedding
from app.vector_store import store_chunk, search
from app.qa_engine import ask_question, ask_llama_stream


app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PDF_PATH = "data/uploaded.pdf"


# ---------------- UPLOAD ----------------
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    with open(PDF_PATH, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = load_pdf_text(PDF_PATH)
    chunks = chunk_text(text)

    for chunk in chunks:
        emb = get_embedding(chunk)
        store_chunk(str(uuid.uuid4()), chunk, emb)

    return {"message": "PDF processed", "chunks": len(chunks)}


# ---------------- NORMAL ASK ----------------
@app.get("/ask")
def ask(q: str):
    return {"answer": ask_question(q)}


# ---------------- STREAMING ASK ----------------
@app.get("/ask-stream")
def ask_stream(q: str):

    def generate():
        # RAG retrieval
        q_emb = get_embedding(q)
        docs = search(q_emb)

        context = "\n\n".join(docs)

        prompt = f"""
Use ONLY the context below:

{context}

Question: {q}
"""

        # stream from LLM
        for chunk in ask_llama_stream(prompt):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")