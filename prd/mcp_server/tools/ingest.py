"""Document ingestion — Extract text from PDF/DOCX/TXT/MD/JSON/YAML, chunk, embed, store in ChromaDB.

This module implements the full document ingestion pipeline that populates the
RAG knowledge base.  When a user uploads a document via the /ingest endpoint,
this pipeline runs:

  1. EXTRACT — Read the file and extract raw text (format-specific parsers)
  2. CHUNK   — Split the text into overlapping chunks (~512 tokens each)
  3. EMBED   — Convert each chunk to a 768-dim vector via the embedding model
  4. STORE   — Write chunks + vectors + metadata into the ChromaDB collection

Supported formats: .pdf, .docx, .txt, .md, .json, .yaml, .yml
"""

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
    Overlapping ensures that context at chunk boundaries is not lost.
    """
    words = text.split()
    # Convert token-based sizes to word-based sizes (~0.75 words per token)
    words_per_chunk = int(chunk_size * 0.75)
    words_overlap = int(chunk_overlap * 0.75)

    if words_per_chunk <= 0:
        words_per_chunk = 384
    if words_overlap >= words_per_chunk:
        words_overlap = words_per_chunk // 8

    # Slide a window across the word list, advancing by (chunk_size - overlap)
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
    source_name = Path(file_path).name  # Human-readable filename for metadata

    # --- Step 1: Extract raw text from the file ---
    text = extract_text(file_path)
    if not text.strip():
        return {"chunks_ingested": 0, "status": "empty_document", "source": source_name}

    # --- Step 2: Split text into overlapping chunks ---
    rag_cfg = get_rag_config()
    chunks = chunk_text(
        text,
        chunk_size=rag_cfg.get("chunk_size", 512),
        chunk_overlap=rag_cfg.get("chunk_overlap", 64),
    )
    if not chunks:
        return {"chunks_ingested": 0, "status": "no_chunks", "source": source_name}

    # --- Step 3: Embed all chunks in batches ---
    embeddings = embed_documents(chunks)

    # --- Step 4: Prepare unique IDs and metadata for each chunk ---
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

    # --- Step 5: Store chunks + embeddings in ChromaDB ---
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
