# Technical Documentation

## RAG Document Assistant - Complete Technical Reference

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Backend Architecture](#backend-architecture)
3. [Frontend Architecture](#frontend-architecture)
4. [Data Flow](#data-flow)
5. [Vector Database](#vector-database)
6. [OpenAI Integration](#openai-integration)
7. [API Specification](#api-specification)
8. [Configuration](#configuration)
9. [Performance Considerations](#performance-considerations)

---

## System Overview

### Purpose

This application implements a Retrieval-Augmented Generation (RAG) system that allows users to:

1. Upload PDF documents for processing
2. Ask natural language questions about the uploaded content
3. Receive AI-generated answers with source citations

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Backend Framework | FastAPI | 0.116+ |
| Frontend Framework | React | 18.x |
| Language (Backend) | Python | 3.12+ |
| Language (Frontend) | TypeScript | 5.x |
| Vector Database | Qdrant | 1.15+ |
| Embedding Model | OpenAI text-embedding-3-large | - |
| LLM | OpenAI GPT-4o-mini | - |
| PDF Parser | LlamaIndex | 0.14+ |
| Build Tool | Vite | 5.x |

---

## Backend Architecture

### File Structure

```
├── main.py           # API endpoints and server configuration
├── data_loader.py    # Document processing pipeline
├── vector_db.py      # Vector database operations
└── custom_types.py   # Type definitions
```

### main.py - API Server

The FastAPI server handles all HTTP requests and orchestrates the RAG pipeline.

**Key Components:**

```python
# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend origin
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoints
POST /api/upload      # PDF upload and processing
POST /api/query       # Question answering
GET  /api/documents   # List indexed documents
GET  /health          # Health check
```

**Upload Flow:**

1. Receive PDF file via multipart form
2. Save to temporary file
3. Extract text using LlamaIndex PDFReader
4. Split into chunks (1000 chars, 200 overlap)
5. Generate embeddings using OpenAI
6. Store in Qdrant vector database
7. Return success response with chunk count

**Query Flow:**

1. Receive question as JSON
2. Generate question embedding
3. Search Qdrant for similar chunks (top 5)
4. Build context from retrieved chunks
5. Send context + question to GPT-4o-mini
6. Return answer with source citations

### data_loader.py - Document Processing

Handles PDF parsing, text chunking, and embedding generation.

**Key Functions:**

```python
def load_and_chunk_pdf(file_path: str) -> list[dict]
    """
    Parse PDF and split into chunks.
    
    Parameters:
        file_path: Path to PDF file
        
    Returns:
        List of chunk dictionaries with keys:
        - text: The chunk text content
        - metadata: {filename, page_number}
    
    Chunking Strategy:
        - chunk_size: 1000 characters
        - chunk_overlap: 200 characters
        - Preserves sentence boundaries where possible
    """

def generate_embeddings(chunks: list[dict]) -> list[dict]
    """
    Generate OpenAI embeddings for text chunks.
    
    Parameters:
        chunks: List of chunk dictionaries
        
    Returns:
        Chunks with added 'embedding' key (3072-dim vector)
    
    Model: text-embedding-3-large
    Dimensions: 3072
    """
```

### vector_db.py - Qdrant Operations

Manages vector storage and similarity search.

**Class: QdrantStorage**

```python
class QdrantStorage:
    def __init__(self):
        """
        Initialize Qdrant client with local file storage.
        
        Storage Path: ./qdrant_storage
        Collection: "docs"
        Vector Size: 3072 dimensions
        Distance Metric: Cosine similarity
        """
    
    def add_chunks(self, chunks: list[dict]) -> None:
        """
        Insert document chunks into vector database.
        
        Creates collection if not exists.
        Generates UUIDs for each point.
        Stores embedding, text, and metadata.
        """
    
    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]
        """
        Find similar chunks using cosine similarity.
        
        Parameters:
            query_embedding: 3072-dim query vector
            top_k: Number of results to return
            
        Returns:
            List of matching chunks with scores
        """
    
    def get_all_documents(self) -> list[str]
        """
        Retrieve unique document filenames from database.
        
        Scrolls through all points and extracts
        unique filenames from metadata.
        """
```

### custom_types.py - Type Definitions

Pydantic models for request/response validation.

```python
class QueryRequest(BaseModel):
    question: str

class SourceDocument(BaseModel):
    text: str
    metadata: dict
    score: float

class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]

class UploadResponse(BaseModel):
    success: bool
    filename: str
    chunks_ingested: int
    message: str
```

---

## Frontend Architecture

### File Structure

```
frontend/
├── src/
│   ├── main.tsx              # App entry point
│   ├── App.tsx               # Main component
│   ├── App.css               # Styles
│   ├── api/client.ts         # API client
│   ├── components/           # UI components
│   ├── hooks/                # State management
│   └── types/index.ts        # TypeScript types
```

### Component Hierarchy

```
App
├── Sidebar
│   ├── FileUpload
│   └── DocumentList
└── ChatContainer
    ├── ChatMessage (multiple)
    ├── LoadingIndicator
    └── ChatInput
```

### State Management

**useChat Hook:**

```typescript
interface ChatState {
  messages: Message[];
  loadingState: 'idle' | 'loading' | 'success' | 'error';
  error: string | null;
}

// Actions
sendMessage(question: string): Promise<void>
clearMessages(): void
```

**useDocuments Hook:**

```typescript
interface DocumentsState {
  documents: string[];
  loading: boolean;
  error: string | null;
}

// Actions
refresh(): Promise<void>
```

### API Client

```typescript
// Base URL: http://localhost:8000

async function uploadDocument(file: File): Promise<UploadResponse>
async function queryDocuments(question: string): Promise<QueryResponse>
async function getDocuments(): Promise<string[]>
```

---

## Data Flow

### Document Upload Flow

```
┌─────────────┐
│ User drops  │
│ PDF file    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ FileUpload.tsx      │
│ - Validates file    │
│ - Shows progress    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ api/client.ts       │
│ POST /api/upload    │
│ multipart/form-data │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ main.py             │
│ upload_pdf()        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ data_loader.py      │
│ - Parse PDF         │
│ - Split chunks      │
│ - Generate embeds   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ vector_db.py        │
│ - Create collection │
│ - Insert points     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Qdrant Storage      │
│ ./qdrant_storage/   │
└─────────────────────┘
```

### Question Answering Flow

```
┌─────────────┐
│ User types  │
│ question    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ ChatInput.tsx       │
│ - Captures input    │
│ - Triggers send     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ useChat.ts          │
│ - Adds user msg     │
│ - Sets loading      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ api/client.ts       │
│ POST /api/query     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ main.py             │
│ query_documents()   │
└──────────┬──────────┘
           │
    ┌──────┴───────┐
    │              │
    ▼              ▼
┌────────┐   ┌──────────────┐
│ OpenAI │   │ Qdrant       │
│ Embed  │   │ Search       │
│ Query  │   │ Top 5 chunks │
└───┬────┘   └──────┬───────┘
    │              │
    └──────┬───────┘
           │
           ▼
┌─────────────────────┐
│ OpenAI GPT-4o-mini  │
│ Generate answer     │
│ with context        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ ChatMessage.tsx     │
│ - Display answer    │
│ - Show sources      │
└─────────────────────┘
```

---

## Vector Database

### Qdrant Configuration

```python
# Storage Mode: Local file-based (no server needed)
client = QdrantClient(path="./qdrant_storage")

# Collection Configuration
collection_name = "docs"
vector_config = VectorParams(
    size=3072,           # OpenAI embedding dimensions
    distance=Distance.COSINE
)
```

### Data Schema

```json
{
  "id": "uuid",
  "vector": [0.1, 0.2, ...],  // 3072 floats
  "payload": {
    "text": "Chunk content...",
    "filename": "document.pdf",
    "page_number": 1
  }
}
```

### Storage Structure

```
qdrant_storage/
├── collections/
│   └── docs/
│       ├── config.json
│       └── 0/
│           ├── segments/
│           │   └── [segment-uuid]/
│           │       ├── payload_index/
│           │       ├── payload_storage/
│           │       └── vector_storage/
│           └── wal/
└── aliases/
    └── data.json
```

---

## OpenAI Integration

### Embedding Generation

```python
from openai import OpenAI

client = OpenAI()  # Uses OPENAI_API_KEY env var

response = client.embeddings.create(
    model="text-embedding-3-large",
    input=text,
    dimensions=3072
)

embedding = response.data[0].embedding  # List[float]
```

### Answer Generation

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": """You are a helpful assistant that answers 
            questions based on the provided context. If the context 
            doesn't contain enough information, say so."""
        },
        {
            "role": "user",
            "content": f"""Context:\n{context}\n\nQuestion: {question}"""
        }
    ],
    temperature=0.7,
    max_tokens=1000
)

answer = response.choices[0].message.content
```

---

## API Specification

### POST /api/upload

**Request:**
```
Content-Type: multipart/form-data
Body: file=@document.pdf
```

**Response (200):**
```json
{
  "success": true,
  "filename": "document.pdf",
  "chunks_ingested": 42,
  "message": "Successfully ingested 42 chunks from PDF"
}
```

**Response (400):**
```json
{
  "detail": "Only PDF files are allowed"
}
```

### POST /api/query

**Request:**
```json
{
  "question": "What is machine learning?"
}
```

**Response (200):**
```json
{
  "answer": "Machine learning is a subset of artificial intelligence...",
  "sources": [
    {
      "text": "Machine learning (ML) is the study of...",
      "metadata": {
        "filename": "ai_textbook.pdf",
        "page_number": 15
      },
      "score": 0.92
    }
  ]
}
```

### GET /api/documents

**Response (200):**
```json
{
  "documents": ["document1.pdf", "document2.pdf"]
}
```

### GET /health

**Response (200):**
```json
{
  "status": "healthy"
}
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `PORT` | No | 8000 | Backend server port |

### Chunking Parameters

Located in `data_loader.py`:

```python
CHUNK_SIZE = 1000      # Characters per chunk
CHUNK_OVERLAP = 200    # Overlap between chunks
```

### Search Parameters

Located in `main.py`:

```python
TOP_K = 5              # Number of chunks to retrieve
```

### OpenAI Model Settings

Located in `main.py`:

```python
EMBEDDING_MODEL = "text-embedding-3-large"
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 1000
```

---

## Performance Considerations

### Optimization Tips

| Area | Recommendation |
|------|----------------|
| **Chunk Size** | Increase to 2000 for longer documents |
| **Top K** | Reduce to 3 for faster responses |
| **Embedding Model** | Use `text-embedding-3-small` for cost savings |
| **LLM Model** | Use `gpt-3.5-turbo` for faster, cheaper responses |

### Scaling Considerations

- **Multiple Users**: Add Redis for session management
- **Large Documents**: Implement async processing with Celery
- **High Traffic**: Deploy Qdrant as standalone server (Docker)
- **Cost Control**: Implement rate limiting and caching

### Monitoring

Add logging for production:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

---

## Security Best Practices

1. **API Key Protection**: Never commit `.env` files
2. **Input Validation**: Validate file types and sizes
3. **Rate Limiting**: Implement API rate limits
4. **CORS**: Restrict to known origins in production
5. **HTTPS**: Always use SSL in production

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Embedding fails | Invalid API key | Check OPENAI_API_KEY |
| Search returns nothing | No documents indexed | Upload documents first |
| Slow responses | Large context | Reduce TOP_K or chunk size |
| Out of memory | Too many documents | Use external Qdrant server |

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01 | Initial release |

---

## Contact

For technical support, open a GitHub issue.
