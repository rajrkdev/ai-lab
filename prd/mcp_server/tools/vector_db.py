"""ChromaDB vector database operations — query both collections."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb

from mcp_server.tools.config_manager import get_rag_config

_chroma_client: Optional[Any] = None


def _get_client():
    global _chroma_client
    if _chroma_client is None:
        rag_cfg = get_rag_config()
        persist_dir = Path(rag_cfg.get("persist_dir", "./data/chroma_db"))
        persist_dir.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(persist_dir))
    return _chroma_client


def get_or_create_collection(name: str) -> chromadb.Collection:
    """Get or create a ChromaDB collection by name."""
    client = _get_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def get_collection_name(chatbot_type: str) -> str:
    """Map chatbot_type to collection name from config."""
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
    # Convert to similarity score: 1 - (distance / 2)
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
