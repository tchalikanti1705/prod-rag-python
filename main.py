"""
RAG Application - Main FastAPI Server

This module serves as the entry point for the RAG (Retrieval-Augmented Generation)
application. It exposes both REST API endpoints for direct client interaction and
Inngest workflow functions for background processing.

Architecture:
    - FastAPI handles HTTP requests from the React frontend
    - Inngest manages background workflows for PDF ingestion and AI queries
    - Qdrant stores and retrieves document embeddings
    - OpenAI provides embeddings and LLM capabilities
"""

import datetime
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import inngest
import inngest.fast_api
from inngest.experimental import ai

from custom_types import RAGChunkAndSrc, RAGSearchResult, RAGUpsertResult
from data_loader import embed_texts, load_and_chunk_pdf
from vector_db import QdrantStorage

# =============================================================================
# Configuration
# =============================================================================

load_dotenv()

# Directory for storing uploaded PDF files
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# Inngest Client Setup
# =============================================================================

inngest_client = inngest.Inngest(
    app_id="rag_app",
    logger=logging.getLogger("uvicorn"),
    is_production=False,
    serializer=inngest.PydanticSerializer(),
)

# =============================================================================
# Inngest Workflow Functions
# =============================================================================


@inngest_client.create_function(
    fn_id="RAG: Ingest PDF",
    trigger=inngest.TriggerEvent(event="rag/ingest_pdf"),
    throttle=inngest.Throttle(limit=2, period=datetime.timedelta(minutes=1)),
    rate_limit=inngest.RateLimit(
        limit=1,
        period=datetime.timedelta(hours=4),
        key="event.data.source_id",
    ),
)
async def rag_ingest_pdf(ctx: inngest.Context):
    """
    Background workflow for PDF ingestion.
    
    This function is triggered by the 'rag/ingest_pdf' event and performs:
    1. Loading and chunking the PDF into smaller text segments
    2. Generating embeddings for each chunk
    3. Storing embeddings in the vector database
    
    Rate Limits:
        - Max 2 ingestions per minute (throttle)
        - Max 1 ingestion per source every 4 hours (rate limit)
    """

    def _load_and_chunk(ctx: inngest.Context) -> RAGChunkAndSrc:
        """Step 1: Load PDF and split into chunks."""
        pdf_path = ctx.event.data["pdf_path"]
        source_id = ctx.event.data.get("source_id", pdf_path)
        chunks = load_and_chunk_pdf(pdf_path)
        return RAGChunkAndSrc(chunks=chunks, source_id=source_id)

    def _embed_and_upsert(chunks_and_src: RAGChunkAndSrc) -> RAGUpsertResult:
        """Step 2: Generate embeddings and store in vector DB."""
        chunks = chunks_and_src.chunks
        source_id = chunks_and_src.source_id
        
        # Generate embeddings using OpenAI
        vectors = embed_texts(chunks)
        
        # Create deterministic IDs based on source and chunk index
        ids = [
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_id}:{i}"))
            for i in range(len(chunks))
        ]
        
        # Prepare payload with source metadata and text content
        payloads = [
            {"source": source_id, "text": chunks[i]} 
            for i in range(len(chunks))
        ]
        
        # Store in Qdrant
        QdrantStorage().upsert(ids, vectors, payloads)
        return RAGUpsertResult(ingested=len(chunks))

    # Execute workflow steps
    chunks_and_src = await ctx.step.run(
        "load-and-chunk",
        lambda: _load_and_chunk(ctx),
        output_type=RAGChunkAndSrc,
    )
    
    result = await ctx.step.run(
        "embed-and-upsert",
        lambda: _embed_and_upsert(chunks_and_src),
        output_type=RAGUpsertResult,
    )
    
    return result.model_dump()


@inngest_client.create_function(
    fn_id="RAG: Query PDF",
    trigger=inngest.TriggerEvent(event="rag/query_pdf_ai"),
)
async def rag_query_pdf_ai(ctx: inngest.Context):
    """
    Background workflow for answering questions using RAG.
    
    This function is triggered by the 'rag/query_pdf_ai' event and performs:
    1. Embedding the user's question
    2. Searching for relevant document chunks
    3. Generating an AI-powered answer using retrieved context
    """

    def _search_documents(question: str, top_k: int = 5) -> RAGSearchResult:
        """Step 1: Embed question and search for relevant chunks."""
        query_vector = embed_texts([question])[0]
        results = QdrantStorage().search(query_vector, top_k)
        return RAGSearchResult(
            contexts=results["contexts"],
            sources=results["sources"],
        )

    question = ctx.event.data["question"]
    top_k = int(ctx.event.data.get("top_k", 5))

    # Search for relevant context
    search_result = await ctx.step.run(
        "embed-and-search",
        lambda: _search_documents(question, top_k),
        output_type=RAGSearchResult,
    )

    # Construct prompt with retrieved context
    context_block = "\n\n".join(f"- {c}" for c in search_result.contexts)
    user_prompt = (
        "Use the following context to answer the question.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n"
        "Answer concisely using the context above."
    )

    # Configure OpenAI adapter for LLM inference
    adapter = ai.openai.Adapter(
        auth_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
    )

    # Generate answer using LLM
    response = await ctx.step.ai.infer(
        "llm-answer",
        adapter=adapter,
        body={
            "max_tokens": 1024,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": "You answer questions using only the provided context.",
                },
                {"role": "user", "content": user_prompt},
            ],
        },
    )

    answer = response["choices"][0]["message"]["content"].strip()
    
    return {
        "answer": answer,
        "sources": search_result.sources,
        "num_contexts": len(search_result.contexts),
    }


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="RAG API",
    description="Retrieval-Augmented Generation API for PDF documents",
    version="1.0.0",
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Request/Response Models
# =============================================================================


class QueryRequest(BaseModel):
    """Request model for querying documents."""
    question: str
    top_k: Optional[int] = 5


class QueryResponse(BaseModel):
    """Response model for document queries."""
    answer: str
    sources: list[str]
    num_contexts: int


class IngestResponse(BaseModel):
    """Response model for PDF ingestion."""
    message: str
    filename: str
    event_id: str


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    message: str


# =============================================================================
# API Endpoints
# =============================================================================


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the current status of the API server.
    """
    return HealthResponse(status="healthy", message="RAG API is running")


@app.post("/api/upload", response_model=IngestResponse, tags=["Documents"])
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF document for ingestion.
    
    This endpoint:
    1. Saves the uploaded PDF to the server
    2. Processes the PDF synchronously (chunks, embeds, stores)
    3. Returns the ingestion result
    
    Args:
        file: The PDF file to upload
        
    Returns:
        IngestResponse with the ingestion result
        
    Raises:
        HTTPException: If the file is not a PDF
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )
    
    # Save file to disk
    file_path = UPLOADS_DIR / file.filename
    content = await file.read()
    file_path.write_bytes(content)
    
    # Process PDF synchronously (no Inngest required)
    try:
        # Step 1: Load and chunk the PDF
        chunks = load_and_chunk_pdf(str(file_path.resolve()))
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF",
            )
        
        # Step 2: Generate embeddings
        vectors = embed_texts(chunks)
        
        # Step 3: Create IDs and payloads
        ids = [
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{file.filename}:{i}"))
            for i in range(len(chunks))
        ]
        payloads = [
            {"source": file.filename, "text": chunks[i]}
            for i in range(len(chunks))
        ]
        
        # Step 4: Store in vector database
        storage = QdrantStorage()
        storage.upsert(ids, vectors, payloads)
        
        return IngestResponse(
            message=f"Successfully ingested {len(chunks)} chunks from PDF",
            filename=file.filename,
            event_id="sync-processing",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF: {str(e)}",
        )


@app.post("/api/query", response_model=QueryResponse, tags=["Query"])
async def query_documents(request: QueryRequest):
    """
    Query the document database with a natural language question.
    
    This endpoint performs synchronous RAG:
    1. Embeds the question using OpenAI
    2. Searches Qdrant for relevant document chunks
    3. Generates an answer using GPT-4o-mini
    
    Args:
        request: QueryRequest containing the question and optional top_k
        
    Returns:
        QueryResponse with the generated answer and source documents
        
    Raises:
        HTTPException: If the question is empty
    """
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )
    
    # Step 1: Embed the question
    query_vector = embed_texts([request.question])[0]
    
    # Step 2: Search for relevant chunks
    storage = QdrantStorage()
    results = storage.search(query_vector, request.top_k)
    
    if not results["contexts"]:
        return QueryResponse(
            answer="No relevant documents found. Please upload some PDFs first.",
            sources=[],
            num_contexts=0,
        )
    
    # Step 3: Generate answer using LLM
    from openai import OpenAI
    
    client = OpenAI()
    context_block = "\n\n".join(f"- {ctx}" for ctx in results["contexts"])
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": "You answer questions using only the provided context.",
            },
            {
                "role": "user",
                "content": (
                    "Use the following context to answer the question.\n\n"
                    f"Context:\n{context_block}\n\n"
                    f"Question: {request.question}\n"
                    "Answer concisely using the context above."
                ),
            },
        ],
    )
    
    answer = response.choices[0].message.content.strip()
    
    return QueryResponse(
        answer=answer,
        sources=results["sources"],
        num_contexts=len(results["contexts"]),
    )


@app.get("/api/documents", tags=["Documents"])
async def list_documents():
    """
    List all uploaded documents.
    
    Returns:
        List of uploaded PDF filenames
    """
    files = [f.name for f in UPLOADS_DIR.glob("*.pdf")]
    return {"documents": files, "count": len(files)}


# =============================================================================
# Inngest Integration
# =============================================================================

# Register Inngest functions with FastAPI
inngest.fast_api.serve(
    app,
    inngest_client,
    [rag_ingest_pdf, rag_query_pdf_ai],
)
