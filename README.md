# RAG Document Assistant

A production-ready **Retrieval-Augmented Generation (RAG)** application that enables intelligent Q&A over your PDF documents using AI.

---

## What is RAG?

RAG (Retrieval-Augmented Generation) combines the power of semantic search with large language models. Instead of relying solely on the AI's training data, RAG retrieves relevant information from your documents and uses it to generate accurate, contextual answers.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                               │
│                         React + TypeScript Frontend                       │
│                           http://localhost:5173                           │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                    │
│                         FastAPI Backend Server                            │
│                           http://localhost:8000                           │
│                                                                           │
│  Endpoints:                                                               │
│  • POST /api/upload    - Upload and process PDF documents                 │
│  • POST /api/query     - Ask questions about documents                    │
│  • GET  /api/documents - List all indexed documents                       │
│  • GET  /health        - Health check                                     │
└───────────────┬───────────────────────────────────────┬──────────────────┘
                │                                       │
                ▼                                       ▼
┌───────────────────────────────┐       ┌───────────────────────────────────┐
│       VECTOR DATABASE         │       │           OPENAI API              │
│     Qdrant (Local Storage)    │       │                                   │
│     ./qdrant_storage/         │       │  • text-embedding-3-large         │
│                               │       │    (3072 dimensions)              │
│  Stores:                      │       │                                   │
│  • Document embeddings        │       │  • gpt-4o-mini                    │
│  • Metadata (filename, page)  │       │    (Answer generation)            │
│  • Text chunks                │       │                                   │
└───────────────────────────────┘       └───────────────────────────────────┘
```

---

## Features

| Feature | Description |
|---------|-------------|
| **PDF Upload** | Drag-and-drop PDF files for automatic processing |
| **Smart Chunking** | Documents split into 1000-character chunks with 200-character overlap |
| **Semantic Search** | Find relevant content using vector similarity (top 5 matches) |
| **AI Answers** | GPT-4o-mini generates answers based on retrieved context |
| **Source Citations** | See exactly which documents and pages were used |
| **Local Storage** | Qdrant runs locally - no Docker required |
| **Modern UI** | Clean, dark-themed React interface |

---

## Requirements

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.12+ | Backend runtime |
| Node.js | 18+ | Frontend build tools |
| OpenAI API Key | - | Embeddings and LLM |

---

## Quick Start

### Step 1: Install Dependencies

```bash
# Navigate to the project
cd Prod-RAGPyApp

# Install Python dependencies
pip install fastapi uvicorn openai qdrant-client llama-index-core llama-index-readers-file python-dotenv python-multipart

# Install frontend dependencies
cd frontend
npm install
```

### Step 2: Configure Environment

Create a `.env` file in the `Prod-RAGPyApp` directory:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Step 3: Start the Backend

```bash
cd Prod-RAGPyApp
python -m uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
```

### Step 4: Start the Frontend

Open a new terminal:

```bash
cd Prod-RAGPyApp/frontend
npm run dev
```

You should see:
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

### Step 5: Use the Application

1. Open http://localhost:5173 in your browser
2. Upload a PDF using the sidebar
3. Wait for processing to complete
4. Ask questions about your document!

---

## Project Structure

```
Prod-RAGPyApp/
│
├── main.py                 # FastAPI server with REST endpoints
├── data_loader.py          # PDF parsing, chunking, and embedding generation
├── vector_db.py            # Qdrant vector database wrapper
├── custom_types.py         # Pydantic models for type safety
├── pyproject.toml          # Python project configuration
├── .env                    # Environment variables (create this)
│
├── qdrant_storage/         # Local vector database storage (auto-created)
│
└── frontend/               # React + TypeScript application
    ├── package.json        # Node.js dependencies
    ├── vite.config.ts      # Vite bundler configuration
    ├── tsconfig.json       # TypeScript configuration
    │
    └── src/
        ├── main.tsx        # Application entry point
        ├── App.tsx         # Main React component
        ├── App.css         # Application styles
        │
        ├── api/
        │   └── client.ts   # API client for backend communication
        │
        ├── components/
        │   ├── FileUpload.tsx   # PDF upload component
        │   ├── DocumentList.tsx # Indexed documents list
        │   ├── ChatInput.tsx    # Message input field
        │   └── ChatMessage.tsx  # Chat message display
        │
        ├── hooks/
        │   ├── useChat.ts       # Chat state management
        │   └── useDocuments.ts  # Document list state
        │
        └── types/
            └── index.ts    # TypeScript type definitions
```

---

## API Reference

### Upload Document

```http
POST /api/upload
Content-Type: multipart/form-data

file: <PDF file>
```

**Response:**
```json
{
  "success": true,
  "filename": "document.pdf",
  "chunks_ingested": 42,
  "message": "Successfully ingested 42 chunks from PDF"
}
```

### Query Documents

```http
POST /api/query
Content-Type: application/json

{
  "question": "What is the main topic of the document?"
}
```

**Response:**
```json
{
  "answer": "The document discusses...",
  "sources": [
    {
      "text": "Relevant chunk text...",
      "metadata": {
        "filename": "document.pdf",
        "page_number": 1
      },
      "score": 0.89
    }
  ]
}
```

### List Documents

```http
GET /api/documents
```

**Response:**
```json
{
  "documents": ["document1.pdf", "document2.pdf"]
}
```

---

## How It Works

### 1. Document Ingestion

```
PDF File → LlamaIndex PDFReader → Extract Text
    ↓
Text → SentenceSplitter → Chunks (1000 chars, 200 overlap)
    ↓
Chunks → OpenAI Embedding API → Vector Embeddings (3072 dim)
    ↓
Embeddings + Metadata → Qdrant → Stored in ./qdrant_storage/
```

### 2. Question Answering

```
User Question → OpenAI Embedding API → Query Vector
    ↓
Query Vector → Qdrant Similarity Search → Top 5 Chunks
    ↓
Chunks + Question → GPT-4o-mini → Generated Answer
    ↓
Answer + Sources → Frontend → Displayed to User
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **"OPENAI_API_KEY not set"** | Create `.env` file with your API key |
| **Port 8000 already in use** | Kill existing process or use different port |
| **Frontend can't connect** | Ensure backend is running on port 8000 |
| **PDF upload fails** | Check file is a valid PDF, not corrupted |
| **No answer returned** | Upload documents first, then ask questions |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 18 + TypeScript | User interface |
| Build Tool | Vite | Fast development server |
| Backend | FastAPI | REST API server |
| Vector DB | Qdrant (local) | Semantic search |
| Embeddings | OpenAI text-embedding-3-large | Document vectorization |
| LLM | OpenAI GPT-4o-mini | Answer generation |
| PDF Parsing | LlamaIndex | Document processing |

---

## Documentation

For detailed technical documentation including deployment guides, see [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md).

---

## Support

For issues and questions, please open a GitHub issue
│   └── package.json
└── uploads/             # Uploaded PDF files
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/upload` | Upload a PDF file |
| POST | `/api/query` | Ask a question |
| GET | `/api/documents` | List uploaded documents |

## 🧪 Example Usage

1. **Upload a PDF**: Drag and drop a PDF file into the upload zone
2. **Wait for Processing**: The document will be chunked and embedded
3. **Ask Questions**: Type your question and get AI-powered answers

## 🔧 Configuration

### Backend (`main.py`)

- **CORS Origins**: Configure allowed origins for the frontend
- **Rate Limits**: Adjust Inngest throttle/rate limit settings

### Frontend (`frontend/.env`)

- **VITE_API_URL**: Backend API URL (default: `http://localhost:8000`)

### Embeddings (`data_loader.py`)

- **EMBED_MODEL**: OpenAI embedding model
- **CHUNK_SIZE**: Text chunk size (default: 1000)
- **CHUNK_OVERLAP**: Overlap between chunks (default: 200)

