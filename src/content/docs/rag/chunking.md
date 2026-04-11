---
title: Chunking Strategies
description: Complete guide to document chunking for RAG — fixed-size, recursive, semantic, document-structure-aware, and sliding-window strategies with LangChain and LlamaIndex code examples.
sidebar:
  order: 4
---

## Why Chunking Matters

A RAG pipeline embeds text chunks and retrieves the most relevant ones. The quality of those chunks directly determines what context the LLM receives. Too large → noisy, irrelevant text dilutes the answer. Too small → the chunk lacks enough context to be useful. Getting chunking right is often the single highest-leverage optimization in a RAG system.

**The core tension:**

- A 100-token chunk has high precision (focused) but low recall (misses surrounding context)
- A 1,000-token chunk has high recall but low precision (too much noise per chunk)

**Empirical baseline:** For most English prose with SBERT-style embedding models (384–768 dims), chunks of **256–512 tokens** with **10–20% overlap** give good retrieval performance.

---

## 1. Fixed-Size Chunking

Split text into chunks of exactly N characters (or tokens), with optional overlap.

**Pros:** Simple, predictable, fast.  
**Cons:** Ignores sentence/paragraph boundaries — a chunk may start mid-sentence.

```python
from langchain_text_splitters import CharacterTextSplitter

splitter = CharacterTextSplitter(
    chunk_size=512,       # characters
    chunk_overlap=64,     # overlap to preserve context across boundaries
    separator="\n",       # preferred split point
)

chunks = splitter.split_text(document_text)
```

### Token-based Fixed Chunking

Character counting is unreliable across languages. Token-based is more accurate for embedding model limits:

```python
from langchain_text_splitters import TokenTextSplitter

splitter = TokenTextSplitter(
    chunk_size=256,        # tokens (as counted by the embedding model's tokenizer)
    chunk_overlap=32,
    encoding_name="cl100k_base",  # OpenAI tiktoken encoding
)

chunks = splitter.split_text(document_text)
```

---

## 2. Recursive Character Text Splitting

The standard workhorse for unstructured text. Tries to split on a hierarchy of separators in order — only falls back to the next separator if the chunk is still too large.

**Default separator hierarchy:** `["\n\n", "\n", " ", ""]`

This means it first tries to split on double newlines (paragraphs), then single newlines, then spaces, then characters. This produces semantically coherent chunks in practice.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,         # characters
    chunk_overlap=200,
    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
    length_function=len,     # can substitute a token counter
)

doc_chunks = splitter.create_documents(
    texts=[document_text],
    metadatas=[{"source": "company_handbook.pdf", "page": 1}]
)

# Each chunk is a Document object:
# doc_chunks[0].page_content → "..."
# doc_chunks[0].metadata     → {"source": "...", "page": 1}
```

### Language-aware Splitters

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

# Python code — splits respect function/class boundaries
python_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON,
    chunk_size=1000,
    chunk_overlap=100,
)

# Markdown — splits on headers, code blocks, paragraphs
md_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.MARKDOWN,
    chunk_size=1000,
    chunk_overlap=100,
)
```

---

## 3. Document-Structure-Aware Chunking

### Markdown Header Splitting

Preserves document hierarchy by splitting on header levels and propagating header metadata:

```python
from langchain_text_splitters import MarkdownHeaderTextSplitter

headers_to_split_on = [
    ("#",  "H1"),
    ("##", "H2"),
    ("###","H3"),
]
splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

md_text = """
# Company Overview
Acme Corp was founded in 1990.

## Products
We sell anvils.

### Anvil Types
Classic, turbo, and deluxe.
"""

header_splits = splitter.split_text(md_text)
# header_splits[0].page_content = "Acme Corp was founded in 1990."
# header_splits[0].metadata     = {"H1": "Company Overview"}
# header_splits[1].page_content = "We sell anvils."
# header_splits[1].metadata     = {"H1": "Company Overview", "H2": "Products"}
```

### HTML Section Splitting

```python
from langchain_text_splitters import HTMLHeaderTextSplitter

headers_to_split_on = [("h1", "Header1"), ("h2", "Header2"), ("h3", "Header3")]
html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
html_splits = html_splitter.split_text(html_content)
```

### PDF with Page/Section Metadata

```python
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

loader = PyPDFLoader("report.pdf")
pages = loader.load()   # one Document per page

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(pages)
# chunks[i].metadata["page"] = page number from PyPDF
```

---

## 4. Semantic Chunking

Instead of splitting at fixed sizes, split at **semantic boundary shifts** — identified by a sudden drop in embedding similarity between adjacent sentences.

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

# Uses embedding cosine similarity to detect topic shifts
splitter = SemanticChunker(
    embeddings=OpenAIEmbeddings(),
    breakpoint_threshold_type="percentile",  # "standard_deviation", "interquartile"
    breakpoint_threshold_amount=95,          # split when similarity drops below 95th percentile
)

chunks = splitter.split_text(long_document)
```

**Algorithm:**
1. Split text into sentences
2. Embed each sentence
3. Compute cosine similarity between consecutive sentence pairs
4. Find points where similarity drops sharply (breakpoints)
5. Split at breakpoints

**Trade-offs:**

| | Fixed-size | Semantic |
|---|---|---|
| Speed | Very fast | Slow (embeds every sentence) |
| Chunk size variance | Predictable | Variable (0.5× to 3× target) |
| Semantic coherence | Poor | Excellent |
| Recommended for | High-volume pipelines | Quality-critical RAG |

---

## 5. Sliding Window (Overlapping Windows)

Create overlapping windows that step through the document:

```python
def sliding_window_chunks(text: str, window_size: int = 512, stride: int = 256) -> list[str]:
    """window_size and stride in characters."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + window_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += stride
    return chunks

chunks = sliding_window_chunks(document, window_size=1000, stride=500)
```

Overlap (window_size - stride) ensures that answers spanning a boundary are captured.

---

## 6. Parent Document Retrieval

A powerful pattern: store **small chunks** in the vector index for precise retrieval, but return **large parent chunks** to the LLM for rich context.

```python
from langchain.storage import InMemoryStore
from langchain_community.vectorstores import Chroma
from langchain.retrievers import ParentDocumentRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

# Small child chunks for retrieval (high precision)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=40)

# Large parent chunks passed to LLM (high context)
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)

vectorstore = Chroma(embedding_function=OpenAIEmbeddings())
store = InMemoryStore()

retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)

retriever.add_documents(documents)

# Retrieves child chunk for matching, returns parent chunk to LLM
results = retriever.get_relevant_documents("What is the refund policy?")
```

---

## Chunking Strategy Selection Guide

| Document type | Recommended strategy | chunk_size | overlap |
|---|---|---|---|
| Prose articles / blogs | Recursive character | 1000 chars | 200 chars |
| Technical documentation | Markdown header split → recursive | 1000–2000 | 200 |
| Legal / financial contracts | Recursive character or semantic | 512 chars | 100 |
| Source code | Language-aware (RecursiveCharacterTextSplitter + Language) | 1000 | 200 |
| Short FAQ / structured data | Fixed-size | 256 chars | 0 |
| Long-form reports | Parent document retrieval | 200 (child), 2000 (parent) | 40 / 200 |

---

## Chunk Metadata: Non-negotiable

Always attach metadata to chunks. At retrieval time, metadata enables filtering, attribution, and debugging:

```python
chunk = Document(
    page_content="The refund window is 30 days from purchase.",
    metadata={
        "source":   "terms_of_service.pdf",
        "page":     5,
        "section":  "Refund Policy",
        "doc_id":   "tos-v2.1",
        "ingested": "2025-01-15",
    }
)
```

---

## See Also

- [Embedding Models](../embedding-models) — the model receiving your chunks
- [Retrieval Strategies](../retrieval-strategies) — how chunks are retrieved once embedded
- [Naive RAG Explainer](../naive-rag) — see chunking and retrieval in an interactive walkthrough
