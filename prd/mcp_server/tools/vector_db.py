"""ChromaDB vector database operations — query both collections.

This module wraps ChromaDB's PersistentClient and provides functions to:
  - Create / get collections (one per chatbot type)
  - Add document embeddings during ingestion
  - Query for top-k similar chunks during RAG retrieval
  - Health-check the database

ChromaDB stores vectors on disk at the path configured in config.yaml
(default: ./data/chroma_db) using cosine similarity for nearest-neighbor search.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb

from mcp_server.tools.config_manager import get_rag_config

# Singleton ChromaDB client — lazy-initialised on first call
_chroma_client: Optional[Any] = None


def _get_client():
    """Lazy-init the ChromaDB persistent client.

    Creates the persist directory if it doesn't exist and returns a
    singleton client instance.
    """
    global _chroma_client
    if _chroma_client is None:
        rag_cfg = get_rag_config()
        persist_dir = Path(rag_cfg.get("persist_dir", "./data/chroma_db"))
        persist_dir.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(persist_dir))
    return _chroma_client


def get_or_create_collection(name: str) -> chromadb.Collection:
    """Get or create a ChromaDB collection by name.

    Collections use cosine similarity ('hnsw:space': 'cosine') so that
    retrieval scores range from 0 (identical) to 2 (opposite).
    """
    client = _get_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def get_collection_name(chatbot_type: str) -> str:
    """Map chatbot_type ('microsite' or 'support') to its ChromaDB collection name.

    Collection names are defined in config.yaml under rag.collections.
    Raises ValueError for unknown chatbot types.
    """
    rag_cfg = get_rag_config()
    collections = rag_cfg.get("collections", {})
    if chatbot_type == "microsite":
        return collections.get("microsite", "insurance_docs")
    elif chatbot_type == "support":
        return collections.get("support", "support_docs")
    raise ValueError(f"Unknown chatbot_type: {chatbot_type}")


def add_documents(
    collection_name: str,
    ids: List[str],
    embeddings: List[List[float]],
    documents: List[str],
    metadatas: List[Dict],
) -> None:
    """Add document chunks with embeddings to a collection."""
    collection = get_or_create_collection(collection_name)
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )


def retrieve_chunks(
    embedding: List[float],
    collection_name: str,
    top_k: int = 5,
) -> Dict:
    """Query ChromaDB for top-k similar chunks.

    Returns:
        chunks: list of document texts
        sources: list of source filenames
        scores: list of similarity scores (cosine distance converted)
    """
    collection = get_or_create_collection(collection_name)
    if collection.count() == 0:
        return {"chunks": [], "sources": [], "scores": []}

    results = collection.query(
        query_embeddings=[embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []
    distances = results["distances"][0] if results["distances"] else []

    sources = [m.get("source", "unknown") for m in metadatas]
    # ChromaDB cosine distance: 0 = identical, 2 = opposite
    # Convert to a similarity score between 0.0 (opposite) and 1.0 (identical)
    scores = [1.0 - (d / 2.0) for d in distances]

    return {"chunks": chunks, "sources": sources, "scores": scores}


def get_collection_count(collection_name: str) -> int:
    """Return number of documents in a collection."""
    collection = get_or_create_collection(collection_name)
    return collection.count()


def health_check() -> Dict:
    """Check ChromaDB health."""
    try:
        client = _get_client()
        collections = client.list_collections()
        return {
            "status": "healthy",
            "collections": len(collections),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
