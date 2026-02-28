"""Document ingestion — Extract text from PDF/DOCX/TXT/MD/JSON/YAML, chunk, embed, store in ChromaDB."""

import hashlib
import json
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

from mcp_server.tools.config_manager import get_rag_config
from mcp_server.tools.vector_db import add_documents, get_collection_name
from mcp_server.tools.embedder import embed_documents


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF."""
    import fitz  # pymupdf

    doc = fitz.open(file_path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX using python-docx."""
    from docx import Document

    doc = Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())


def extract_text_from_txt(file_path: str) -> str:
    """Read plain text file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text_from_json(file_path: str) -> str:
    """Extract text from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, indent=2)


def extract_text_from_yaml(file_path: str) -> str:
    """Extract text from YAML file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return yaml.dump(data, default_flow_style=False)


def extract_text(file_path: str) -> str:
    """Extract text from any supported file format."""
    ext = Path(file_path).suffix.lower()
    extractors = {
        ".pdf": extract_text_from_pdf,
        ".docx": extract_text_from_docx,
        ".txt": extract_text_from_txt,
        ".md": extract_text_from_txt,
        ".json": extract_text_from_json,
        ".yaml": extract_text_from_yaml,
        ".yml": extract_text_from_yaml,
    }
    extractor = extractors.get(ext)
    if extractor is None:
        raise ValueError(f"Unsupported file format: {ext}")
    return extractor(file_path)


def chunk_text(text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> List[str]:
    """Split text into overlapping chunks by approximate token count.

    Uses word-based splitting as a proxy for tokens (~0.75 words per token).
    """
    words = text.split()
    # Approximate words per chunk (tokens * 1.3 to convert token count to word count)
    words_per_chunk = int(chunk_size * 0.75)
    words_overlap = int(chunk_overlap * 0.75)

    if words_per_chunk <= 0:
        words_per_chunk = 384
    if words_overlap >= words_per_chunk:
        words_overlap = words_per_chunk // 8

    chunks = []
    start = 0
    while start < len(words):
        end = start + words_per_chunk
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        start += words_per_chunk - words_overlap

    return chunks


def ingest_document(
    file_path: str,
    collection: str,
    category: str = "general",
) -> Dict:
    """Full ingestion pipeline: extract → chunk → embed → store.

    Args:
        file_path: Path to the document file
        collection: ChromaDB collection name (e.g. 'insurance_docs' or 'support_docs')
        category: Document category tag

    Returns:
        dict with chunks_ingested count and status
    """
    source_name = Path(file_path).name

    # 1. Extract text
    text = extract_text(file_path)
    if not text.strip():
        return {"chunks_ingested": 0, "status": "empty_document", "source": source_name}

    # 2. Chunk
    rag_cfg = get_rag_config()
    chunks = chunk_text(
        text,
        chunk_size=rag_cfg.get("chunk_size", 512),
        chunk_overlap=rag_cfg.get("chunk_overlap", 64),
    )
    if not chunks:
        return {"chunks_ingested": 0, "status": "no_chunks", "source": source_name}

    # 3. Embed (batch)
    embeddings = embed_documents(chunks)

    # 4. Prepare IDs and metadata
    ids = []
    metadatas = []
    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.sha256(f"{source_name}_{i}_{chunk[:50]}".encode()).hexdigest()[:16]
        ids.append(f"{source_name}_{chunk_id}")
        metadatas.append({
            "source": source_name,
            "category": category,
            "chunk_index": i,
            "total_chunks": len(chunks),
        })

    # 5. Store in ChromaDB
    add_documents(
        collection_name=collection,
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    return {
        "chunks_ingested": len(chunks),
        "status": "success",
        "source": source_name,
    }


def ingest_file_for_chatbot(file_path: str, chatbot_type: str, category: str = "general") -> Dict:
    """Ingest a document into the correct collection based on chatbot type."""
    collection_name = get_collection_name(chatbot_type)
    return ingest_document(file_path, collection_name, category)
