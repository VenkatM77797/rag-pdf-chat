# RAG PDF Chat

A full-stack Retrieval-Augmented Generation (RAG) application that lets users upload a PDF and ask questions about its contents. The application extracts text from the document, creates embeddings, retrieves the most relevant sections, and generates a streamed answer using a locally running Llama 3 model through Ollama.
cdkckw
cndvk
nieni
## Features

- Upload PDFs through file selection or drag and drop
- Validate PDF type and enforce a 25 MB upload limit
- Extract selectable text with PyMuPDF
- Split document text into overlapping chunks
- Generate embeddings with Sentence Transformers
- Store and search embeddings using persistent ChromaDB storage
- Retrieve relevant PDF sections for each question
- Generate answers using Llama 3 through Ollama
- Stream generated answers to the browser
- Responsive Next.js chat interface
- FastAPI Swagger documentation
- Local-first document processing

## Tech Stack

### Frontend

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4

### Backend

- Python
- FastAPI
- Uvicorn
- PyMuPDF
- Sentence Transformers
- ChromaDB
- Ollama
- Llama 3

## How It Works

```text
PDF upload
    ↓
Text extraction with PyMuPDF
    ↓
Word-based chunking with overlap
    ↓
Embedding generation with all-MiniLM-L6-v2
    ↓
Persistent storage in ChromaDB
    ↓
User question embedding
    ↓
Semantic retrieval of the four most relevant chunks
    ↓
Context-aware prompt construction
    ↓
Llama 3 response generation through Ollama
    ↓
Streamed answer displayed in the Next.js interface
```

The model is instructed to answer only from the retrieved PDF context. When the requested information is not present, it returns a document-specific fallback response instead of intentionally using external knowledge.

## Project Structure

```text
rag-pdf-chat/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── chunker.py          # Splits extracted text into chunks
│   │   ├── embeddings.py       # Loads and uses the embedding model
│   │   ├── llm.py              # Communicates with Ollama
│   │   ├── main.py             # FastAPI application and endpoints
│   │   ├── pdf_loader.py       # Extracts text from PDF files
│   │   ├── qa_engine.py        # Retrieval and prompt construction
│   │   └── vector_store.py     # ChromaDB storage and search
│   ├── chroma_db/              # Generated local vector database
│   ├── data/                   # Generated uploaded PDF storage
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── public/
│   ├── package.json
│   └── tsconfig.json
└── README.md
```

## Prerequisites

Install the following before running the project:

- Python 3.10 or newer
- Node.js 20 or newer
- npm
- Ollama
- Git

The first PDF upload may take longer because the Sentence Transformers embedding model is downloaded and loaded on first use.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/rag-pdf-chat.git
cd rag-pdf-chat
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Download the Llama 3 model

```bash
ollama pull llama3
```

Ensure Ollama is running:

```bash
ollama serve
```

On systems where Ollama already runs as a background service, you do not need to run `ollama serve` manually.

### 3. Set up the backend

Open a terminal in the repository root:

```bash
cd backend
python -m venv venv
```

Activate the virtual environment.

#### Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

#### Windows Command Prompt

```cmd
venv\Scripts\activate
```

#### macOS or Linux

```bash
source venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI backend:

```bash
python run.py
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### 4. Set up the frontend

Open another terminal in the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open the application at:

```text
http://localhost:3000
```

## Environment Variables

The project works with its default local configuration. You can override the following variables when needed.

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3` | Ollama model used for answer generation |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Sentence Transformers embedding model |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | Backend URL used by the frontend |

### Windows PowerShell example

```powershell
$env:OLLAMA_MODEL="llama3"
$env:OLLAMA_BASE_URL="http://127.0.0.1:11434"
python run.py
```

```powershell
$env:NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"
npm run dev
```

### macOS or Linux example

```bash
export OLLAMA_MODEL=llama3
export OLLAMA_BASE_URL=http://127.0.0.1:11434
python run.py
```

```bash
export NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Confirms that the API is running |
| `GET` | `/status` | Reports whether a document is currently indexed |
| `POST` | `/upload` | Uploads, extracts, chunks, embeds, and indexes a PDF |
| `GET` | `/ask?q=...` | Returns a complete answer |
| `GET` | `/ask-stream?q=...` | Streams the generated answer |

### Upload a PDF with cURL

```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### Ask a question with cURL

```bash
curl "http://127.0.0.1:8000/ask?q=What%20is%20the%20document%20about%3F"
```

## Current Limitations

- Only one PDF is indexed at a time. Uploading another PDF replaces the previous document index.
- The application extracts selectable text only. Scanned or image-only PDFs require OCR, which is not currently implemented.
- Chat history exists only in the current browser session and is not stored in a database.
- The backend currently allows browser requests only from local frontend addresses on port `3000`.
- There is no authentication or per-user document isolation.
- Response speed depends on the selected Ollama model and the available CPU, GPU, and memory.

## Troubleshooting

### The backend cannot connect to Ollama

Confirm that Ollama is running:

```bash
ollama serve
```

Check that the model is installed:

```bash
ollama list
```

Download it when necessary:

```bash
ollama pull llama3
```

### The first upload is slow

The embedding model is loaded during the first upload. On the first run, its files may also need to be downloaded. Later uploads should avoid most of this initialization cost because the model is cached in memory while the backend remains running.

### The PDF contains no readable text

The document may be scanned or image-based. Convert it to a searchable PDF with OCR before uploading it.

### The frontend cannot reach the backend

Confirm that:

- The FastAPI server is running on `http://127.0.0.1:8000`.
- `NEXT_PUBLIC_API_URL` points to the correct backend address.
- The frontend is running on port `3000`, or the backend CORS configuration has been updated for the frontend origin.

### PowerShell blocks virtual environment activation

For the current PowerShell session, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

## Before Publishing Publicly

Do not commit uploaded documents, generated ChromaDB files, virtual environments, build output, or environment files.

Add a root `.gitignore` containing at least:

```gitignore
# Python
backend/venv/
backend/.venv/
**/__pycache__/
*.py[cod]

# Generated application data
backend/data/*
!backend/data/.gitkeep
backend/chroma_db/

# Node and Next.js
frontend/node_modules/
frontend/.next/
frontend/out/

# Environment variables
.env
.env.*
!.env.example

# Editors and operating systems
.vscode/
.idea/
.DS_Store
Thumbs.db
```

If generated data is already tracked by Git, remove it from the Git index before pushing:

```bash
git rm -r --cached backend/chroma_db
git rm --cached backend/data/uploaded.pdf
git add .gitignore README.md
git commit -m "Add project documentation and ignore generated data"
git push origin main
```

Review the PDF and database history before making the repository public. Removing a file in a new commit does not remove it from older Git commits.

## Roadmap

- Support multiple PDFs and document selection
- Persist chat sessions and conversation history
- Store richer document and page metadata
- Add source citations and page references to answers
- Add retrieval reranking
- Add OCR support for scanned PDFs
- Process large documents with background jobs
- Add automated tests
- Dockerize the frontend, backend, Ollama, and vector database
- Add production deployment configuration

## License

No license is currently included. Add a license before publishing if you want to define how other people may use, modify, and distribute the project.
