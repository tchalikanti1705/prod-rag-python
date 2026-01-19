"""
Data Loader Module

This module handles PDF document processing and text embedding generation.
It provides utilities for:
    - Loading PDF files and extracting text content
    - Chunking text into smaller segments for embedding
    - Generating vector embeddings using OpenAI's embedding model

Design Principles:
    - Single Responsibility: Each function has one clear purpose
    - Dependency Injection: OpenAI client is initialized at module level
    - Configuration: Model settings are defined as constants
"""

from openai import OpenAI
from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv

# =============================================================================
# Configuration
# =============================================================================

load_dotenv()

# OpenAI embedding configuration
EMBED_MODEL = "text-embedding-3-large"
EMBED_DIM = 3072  # Dimension of the embedding vectors

# Text chunking configuration
CHUNK_SIZE = 1000  # Maximum characters per chunk
CHUNK_OVERLAP = 200  # Overlap between consecutive chunks for context continuity

# =============================================================================
# Module-level Instances
# =============================================================================

# Initialize OpenAI client (uses OPENAI_API_KEY from environment)
_openai_client = OpenAI()

# Initialize text splitter with semantic sentence boundaries
_text_splitter = SentenceSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)

# =============================================================================
# Public Functions
# =============================================================================


def load_and_chunk_pdf(path: str) -> list[str]:
    """
    Load a PDF file and split its content into chunks.
    
    This function:
    1. Reads the PDF file and extracts text from all pages
    2. Splits the text into smaller chunks using sentence boundaries
    3. Maintains overlap between chunks to preserve context
    
    Args:
        path: Absolute or relative path to the PDF file
        
    Returns:
        List of text chunks suitable for embedding
        
    Example:
        >>> chunks = load_and_chunk_pdf("document.pdf")
        >>> len(chunks)
        42
    """
    # Load PDF and extract text from each page
    documents = PDFReader().load_data(file=path)
    
    # Filter out empty pages and extract text content
    texts = [
        doc.text 
        for doc in documents 
        if getattr(doc, "text", None)
    ]
    
    # Split each page's text into smaller chunks
    chunks = []
    for text in texts:
        page_chunks = _text_splitter.split_text(text)
        chunks.extend(page_chunks)
    
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate vector embeddings for a list of text strings.
    
    Uses OpenAI's text-embedding-3-large model to create
    high-dimensional (3072) vector representations of text.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors (each is a list of 3072 floats)
        
    Example:
        >>> embeddings = embed_texts(["Hello world", "How are you?"])
        >>> len(embeddings)
        2
        >>> len(embeddings[0])
        3072
    """
    response = _openai_client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
    )
    
    # Extract embedding vectors from response
    return [item.embedding for item in response.data]


def get_embedding_dimension() -> int:
    """
    Get the dimension of the embedding vectors.
    
    Returns:
        The embedding dimension (3072 for text-embedding-3-large)
    """
    return EMBED_DIM
