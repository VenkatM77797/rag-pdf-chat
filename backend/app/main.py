from pathlib import Path

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from fastapi.responses import (
    StreamingResponse,
)
from starlette.concurrency import (
    run_in_threadpool,
)

from app.chunker import chunk_text
from app.embeddings import get_embeddings
from app.pdf_loader import load_pdf_text
from app.qa_engine import (
    ask_question,
    stream_question,
)
from app.vector_store import (
    clear_collection,
    has_documents,
    store_chunks,
)


app = FastAPI(
    title="RAG PDF Chat API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIRECTORY = (
    Path(__file__).resolve().parent.parent
)

DATA_DIRECTORY = (
    BASE_DIRECTORY / "data"
)

PDF_PATH = (
    DATA_DIRECTORY / "uploaded.pdf"
)

MAX_PDF_SIZE = 25 * 1024 * 1024


DATA_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


def process_pdf(
    file_bytes: bytes,
    original_filename: str,
) -> int:
    """
    Save, extract, chunk, embed, and store one PDF.
    """
    PDF_PATH.write_bytes(file_bytes)

    extracted_text = load_pdf_text(
        PDF_PATH
    )

    chunks = chunk_text(
        extracted_text
    )

    if not chunks:
        raise ValueError(
            "No usable text chunks were "
            "created from the PDF."
        )

    embeddings = get_embeddings(
        chunks
    )

    if len(embeddings) != len(chunks):
        raise ValueError(
            "The number of embeddings does "
            "not match the number of text chunks."
        )

    # This application stores one PDF at a time.
    clear_collection()

    stored_count = store_chunks(
        chunks=chunks,
        embeddings=embeddings,
        source=original_filename,
    )

    return stored_count


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": (
            "RAG PDF Chat API is running."
        ),
        "docs": (
            "http://127.0.0.1:8000/docs"
        ),
    }


@app.get("/status")
def status() -> dict[str, bool]:
    return {
        "ready": True,
        "pdf_uploaded": has_documents(),
    }


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
) -> dict[str, str | int]:
    original_filename = (
        file.filename or "uploaded.pdf"
    )

    extension = Path(
        original_filename
    ).suffix.lower()

    if extension != ".pdf":
        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF files are supported."
            ),
        )

    file_bytes = await file.read()

    try:
        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The uploaded PDF is empty."
                ),
            )

        if len(file_bytes) > MAX_PDF_SIZE:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The PDF must be smaller "
                    "than 25 MB."
                ),
            )

        stored_count = await run_in_threadpool(
            process_pdf,
            file_bytes,
            original_filename,
        )

        return {
            "message": (
                "PDF processed successfully."
            ),
            "filename": original_filename,
            "chunks": stored_count,
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        print(
            "PDF processing error: "
            f"{type(error).__name__}: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The server could not process "
                f"the PDF: {error}"
            ),
        ) from error

    finally:
        await file.close()


@app.get("/ask")
def ask(
    q: str,
) -> dict[str, str]:
    question = q.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail=(
                "Question cannot be empty."
            ),
        )

    if not has_documents():
        raise HTTPException(
            status_code=400,
            detail=(
                "Upload a PDF before "
                "asking questions."
            ),
        )

    try:
        answer = ask_question(
            question
        )

        return {
            "answer": answer,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    except Exception as error:
        print(
            "Question error: "
            f"{type(error).__name__}: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The answer could not "
                "be generated."
            ),
        ) from error


@app.get("/ask-stream")
def ask_stream(
    q: str,
) -> StreamingResponse:
    question = q.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail=(
                "Question cannot be empty."
            ),
        )

    if not has_documents():
        raise HTTPException(
            status_code=400,
            detail=(
                "Upload a PDF before "
                "asking questions."
            ),
        )

    try:
        # This prepares the prompt and opens the
        # Ollama connection before sending HTTP headers.
        response_stream = stream_question(
            question
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    except Exception as error:
        print(
            "Streaming error: "
            f"{type(error).__name__}: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The answer stream could "
                "not be generated."
            ),
        ) from error

    return StreamingResponse(
        response_stream,
        media_type=(
            "text/plain; charset=utf-8"
        ),
        headers={
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": (
                "nosniff"
            ),
        },
    )