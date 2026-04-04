"""FastMCP server — Registers all InsureChat tools for MCP protocol access.

This module creates a FastMCP server instance and registers each tool from
the `mcp_server.tools` package as an MCP-callable tool.  When run directly
(`python -m mcp_server.server`), it starts the MCP server so external MCP
clients (e.g. Claude Desktop) can discover and invoke these tools.

Registered tools (in call order for a typical RAG query):
  1. validate_input    — sanitize user input (length, injection, PII)
  2. classify_intent   — categorize the query (e.g. policy_coverage, claims_process)
  3. embed_query       — convert the query to a 384-dim vector (all-MiniLM-L6-v2)
  4. retrieve_chunks   — find top-k similar document chunks from ChromaDB
  5. call_llm          — send query + context to primary LLM; auto-fallback on failure
  6. validate_output   — mask PII, check hallucination, enforce confidence threshold
  7. log_interaction   — write session/message data to SQLite + JSONL audit log
  8. ingest_document   — extract, chunk, embed, and store a new document
  9. get_config        — read the current config.yaml
  10. update_config    — change LLM routing settings at runtime
"""

from typing import Dict, List, Optional

from fastmcp import FastMCP

# Import all tool modules from the tools sub-package
from mcp_server.tools import (
    analytics_logger,
    config_manager,
    embedder,
    ingest as ingest_tool,
    input_validator,
    intent_classifier,
    llm_router,
    output_validator,
    vector_db,
)

# Create the MCP server instance with a human-readable name
mcp = FastMCP("InsureChat-v3")


# ---------------------------------------------------------------------------
# Tool registrations — each @mcp.tool() decorator exposes a function to MCP
# clients.  The docstring becomes the tool description in the MCP catalog.
# ---------------------------------------------------------------------------

@mcp.tool()
def validate_input(query: str, max_length: int = 500) -> Dict:
    """Validate and sanitize user input — length, injection, PII."""
    return input_validator.validate_input(query, max_length)


@mcp.tool()
def embed_query(text: str) -> List[float]:
    """Embed a query using all-MiniLM-L6-v2 (sentence-transformers). Returns 384-dim vector."""
    return embedder.embed_query(text)


@mcp.tool()
def retrieve_chunks(embedding: List[float], collection: str, top_k: int = 5) -> Dict:
    """Retrieve top-k similar chunks from ChromaDB collection."""
    return vector_db.retrieve_chunks(embedding, collection, top_k)


@mcp.tool()
def call_llm(query: str, chunks: List[str], sources: List[str] = None,
             chatbot_type: str = "microsite", model: str = None) -> Dict:
    """Call LLM with RAG context. Primary provider + automatic fallback."""
    return llm_router.call_llm(query, chunks, sources, chatbot_type, model)


@mcp.tool()
def validate_output(response: str, chunks: List[str], confidence: float) -> Dict:
    """Validate LLM output — PII mask, hallucination check, confidence threshold."""
    return output_validator.validate_output(response, chunks, confidence)


@mcp.tool()
def classify_intent(query: str, chatbot_type: str = "microsite") -> str:
    """Classify query intent using Claude Haiku."""
    return intent_classifier.classify_intent(query, chatbot_type)


@mcp.tool()
def log_interaction(data: Dict) -> Dict:
    """Log interaction to SQLite + JSONL audit log."""
    return analytics_logger.log_interaction(data)


@mcp.tool()
def ingest_document(file_path: str, collection: str, category: str = "general") -> Dict:
    """Ingest document: extract, chunk, embed, store in ChromaDB."""
    return ingest_tool.ingest_document(file_path, collection, category)


@mcp.tool()
def get_config() -> Dict:
    """Read current config.yaml."""
    return config_manager.get_config()


@mcp.tool()
def update_config(mode: str = None, llm: str = None, fallback: str = None) -> Dict:
    """Update LLM routing configuration."""
    return config_manager.update_config(mode, llm, fallback)


# --- Entry point: start the MCP server when run directly ---
if __name__ == "__main__":
    mcp.run()
