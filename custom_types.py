"""
Custom Type Definitions

This module defines Pydantic models used throughout the RAG application
for data validation and serialization.

Design Principles:
    - Type Safety: All data structures are strongly typed
    - Validation: Pydantic provides automatic validation
    - Serialization: Models can be easily converted to/from JSON
    - Documentation: Each field has clear descriptions
"""

from typing import Optional

import pydantic


# =============================================================================
# Ingestion Types
# =============================================================================


class RAGChunkAndSrc(pydantic.BaseModel):
    """
    Container for document chunks and their source identifier.
    
    Used during the ingestion workflow to pass chunked text
    between processing steps.
    
    Attributes:
        chunks: List of text segments extracted from the document
        source_id: Identifier for the source document (usually filename)
    """
    chunks: list[str]
    source_id: Optional[str] = None


class RAGUpsertResult(pydantic.BaseModel):
    """
    Result of a vector upsert operation.
    
    Attributes:
        ingested: Number of chunks successfully ingested into the vector DB
    """
    ingested: int


# =============================================================================
# Query Types
# =============================================================================


class RAGSearchResult(pydantic.BaseModel):
    """
    Result of a vector similarity search.
    
    Attributes:
        contexts: List of text chunks retrieved from the vector DB
        sources: List of source document identifiers
    """
    contexts: list[str]
    sources: list[str]


class RAGQueryResult(pydantic.BaseModel):
    """
    Complete result of a RAG query including the generated answer.
    
    Attributes:
        answer: The AI-generated response to the user's question
        sources: List of source documents used to generate the answer
        num_contexts: Number of context chunks used in generation
    """
    answer: str
    sources: list[str]
    num_contexts: int
