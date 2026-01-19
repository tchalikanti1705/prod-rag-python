"""
Vector Database Module

This module provides a clean abstraction layer for vector storage and retrieval
using Qdrant as the underlying vector database.

Design Principles:
    - Encapsulation: Database implementation details are hidden from consumers
    - Single Responsibility: Only handles vector storage operations
    - Dependency Injection: Connection settings are configurable
    - Fail-Safe Initialization: Collection is created if it doesn't exist
"""

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_PATH = "./qdrant_storage"  # Local file-based storage
DEFAULT_COLLECTION = "docs"
DEFAULT_DIMENSION = 3072  # Matches OpenAI text-embedding-3-large


# =============================================================================
# Vector Storage Class
# =============================================================================


class QdrantStorage:
    """
    A wrapper class for Qdrant vector database operations.
    
    This class provides a simplified interface for:
        - Storing document embeddings with metadata
        - Performing similarity searches
        - Managing the vector collection
    
    Uses local file-based storage (no Qdrant server required).
    
    Attributes:
        client: The Qdrant client instance
        collection: Name of the vector collection
        
    Example:
        >>> storage = QdrantStorage()
        >>> storage.upsert(
        ...     ids=["doc1", "doc2"],
        ...     vectors=[[0.1, 0.2, ...], [0.3, 0.4, ...]],
        ...     payloads=[{"text": "Hello"}, {"text": "World"}]
        ... )
        >>> results = storage.search(query_vector=[0.1, 0.2, ...], top_k=5)
    """

    def __init__(
        self,
        path: str = DEFAULT_PATH,
        collection: str = DEFAULT_COLLECTION,
        dim: int = DEFAULT_DIMENSION,
    ):
        """
        Initialize the Qdrant storage with local file-based persistence.
        
        Args:
            path: Path for local storage (default: ./qdrant_storage)
            collection: Name of the collection to use (default: "docs")
            dim: Dimension of the embedding vectors (default: 3072)
        """
        # Use local file-based storage instead of server
        self.client = QdrantClient(path=path)
        self.collection = collection
        self._dimension = dim
        
        # Ensure collection exists
        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> None:
        """
        Create the collection if it doesn't already exist.
        
        Uses cosine similarity as the distance metric, which is
        optimal for normalized text embeddings.
        """
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self._dimension,
                    distance=Distance.COSINE,
                ),
            )

    def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:
        """
        Insert or update vectors in the collection.
        
        Args:
            ids: Unique identifiers for each vector
            vectors: The embedding vectors to store
            payloads: Metadata dictionaries associated with each vector
                     (typically contains 'source' and 'text' fields)
                     
        Raises:
            ValueError: If the lengths of ids, vectors, and payloads don't match
        """
        if not (len(ids) == len(vectors) == len(payloads)):
            raise ValueError(
                f"Mismatched lengths: ids={len(ids)}, "
                f"vectors={len(vectors)}, payloads={len(payloads)}"
            )
        
        # Convert to Qdrant point format
        points = [
            PointStruct(
                id=ids[i],
                vector=vectors[i],
                payload=payloads[i],
            )
            for i in range(len(ids))
        ]
        
        self.client.upsert(
            collection_name=self.collection,
            points=points,
        )

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> dict[str, Any]:
        """
        Search for the most similar vectors to the query.
        
        Args:
            query_vector: The embedding vector to search with
            top_k: Maximum number of results to return (default: 5)
            
        Returns:
            Dictionary containing:
                - contexts: List of text content from matching documents
                - sources: List of unique source identifiers
        """
        results = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            with_payload=True,
            limit=top_k,
        ).points
        
        contexts = []
        sources = set()
        
        for result in results:
            payload = getattr(result, "payload", None) or {}
            text = payload.get("text", "")
            source = payload.get("source", "")
            
            if text:
                contexts.append(text)
            if source:
                sources.add(source)
        
        return {
            "contexts": contexts,
            "sources": list(sources),
        }

    def get_collection_info(self) -> dict[str, Any]:
        """
        Get information about the current collection.
        
        Returns:
            Dictionary with collection statistics
        """
        info = self.client.get_collection(self.collection)
        return {
            "name": self.collection,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
        }

    def delete_collection(self) -> bool:
        """
        Delete the entire collection.
        
        Returns:
            True if deletion was successful
            
        Warning:
            This operation is irreversible and will delete all stored vectors.
        """
        return self.client.delete_collection(self.collection)
