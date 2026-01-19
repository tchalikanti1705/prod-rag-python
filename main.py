"""
RAG Application - Main FastAPI Server

This module serves as the entry point for the RAG (Retrieval-Augmented Generation)
application. It exposes REST API endpoints for PDF upload, document querying,
and document management.

Architecture:
    - FastAPI handles HTTP requests from the React frontend
    - Qdrant stores and retrieves document embeddings
    - OpenAI provides embeddings and LLM capabilities
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel

from custom_types import RAGChunkAndSrc, RAGSearchResult, RAGUpsertResult
from data_loader import embed_texts, load_and_chunk_pdf
from vector_db import QdrantStorage

# =============================================================================
# Configuration
# =============================================================================

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory for storing uploaded PDF files
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


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
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*",  # Allow all origins for production deployment
    ],
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
    chunks_ingested: int


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
    
    logger.info(f"Processing PDF: {file.filename}")
    
    # Process PDF synchronously
    try:
        # Step 1: Load and chunk the PDF
        chunks = load_and_chunk_pdf(str(file_path.resolve()))
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF",
            )
        
        logger.info(f"Extracted {len(chunks)} chunks from PDF")
        
        # Step 2: Generate embeddings
        vectors = embed_texts(chunks)
        
        logger.info(f"Generated {len(vectors)} embeddings")
        
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
        
        logger.info(f"Stored {len(chunks)} chunks in vector database")
        
        return IngestResponse(
            message=f"Successfully ingested {len(chunks)} chunks from PDF",
            filename=file.filename,
            chunks_ingested=len(chunks),
        )
    except Exception as e:
        logger.error(f"Failed to process PDF: {str(e)}")
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
    
    logger.info(f"Query received: {request.question[:100]}...")
    
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
    
    logger.info(f"Found {len(results['contexts'])} relevant chunks")
    
    # Step 3: Generate answer using LLM
    client = OpenAI()
    context_block = "\n\n".join(f"- {ctx}" for ctx in results["contexts"])
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": "You answer questions using only the provided context. Be concise and accurate.",
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
    
    logger.info("Generated answer successfully")
    
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
