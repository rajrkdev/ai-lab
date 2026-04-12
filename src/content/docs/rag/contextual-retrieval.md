---
title: "Contextual Retrieval"
description: Anthropic's November 2024 technique that adds LLM-generated context to each chunk before embedding — reducing retrieval failures by 67% and 49% further with reranking, using BM25 alongside vector search.
sidebar:
  order: 15
---

## The Problem This Solves

Standard RAG splits documents into chunks and embeds each chunk independently. The problem: **chunks lose their context** when separated from the surrounding document.

```
  ORIGINAL DOCUMENT (legal contract, 80 pages)
  ─────────────────────────────────────────────

  Page 1:  "This Agreement is between Acme Corp (the Licensor)
            and Globex Inc (the Licensee)..."

  ...

  Page 47, Chunk 23 (what gets embedded):
  ┌──────────────────────────────────────────────────────────┐
  │  "The termination clause shall apply when the party       │
  │   fails to meet payment obligations within 30 days.      │
  │   In such cases, the non-defaulting party may..."        │
  └──────────────────────────────────────────────────────────┘

  What's MISSING from this chunk's embedding:
  - Which company is "the party"?
  - Termination clause of WHAT agreement?
  - What section is this in?
  - Is this about the Licensor or Licensee?
```

When a user asks *"What happens if Globex doesn't pay on time?"*, the chunk above is the answer — but it scores poorly in vector search because it doesn't mention "Globex" or "payment."

**Contextual Retrieval** (Anthropic, November 2024) fixes this by prepending a contextual summary to every chunk *before* embedding it.

---

## How Contextual Retrieval Works

```
  STANDARD RAG vs. CONTEXTUAL RETRIEVAL
  ────────────────────────────────────────────────────────────

  STANDARD RAG:
  Document → Split into chunks → Embed chunks → Store
                                 [chunk text only]

  CONTEXTUAL RETRIEVAL:
  Document → Split into chunks → Add context → Embed → Store
                                 [context + chunk text]
                                       ↑
                               LLM-generated summary
                               explaining this chunk's
                               role in the document

  ──────────────────────────────────────────────────────────
  STANDARD chunk (embedded as-is):
  "The termination clause shall apply when the party
   fails to meet payment obligations within 30 days..."

  CONTEXTUAL chunk (prepended context + original):
  "This chunk is from a software licensing agreement between
   Acme Corp (Licensor) and Globex Inc (Licensee), Section 8:
   Termination. It describes the consequences of payment
   default by the Licensee."
  +
  "The termination clause shall apply when the party
   fails to meet payment obligations within 30 days..."
  ──────────────────────────────────────────────────────────

  Now when a user asks "What happens if Globex doesn't pay?",
  the contextual chunk's embedding contains:
  - "Globex" → matches query directly
  - "payment" → matches query
  - "Termination" → relevant topic
  - "Section 8" → navigation hint
```

---

## The BM25 Component

Contextual Retrieval also pairs the contextualized embeddings with **BM25 keyword retrieval**. This is the hybrid that drives the biggest accuracy gains.

```
  CONTEXTUAL RETRIEVAL FULL PIPELINE
  ────────────────────────────────────────────────────────────

  INDEXING:
  ┌─────────────┐
  │  Document   │
  └──────┬──────┘
         │
         ▼
  ┌─────────────────────────┐
  │  Split into chunks      │  ~500 tokens each
  └──────────┬──────────────┘
             │
             ▼
  ┌─────────────────────────┐
  │  LLM adds context       │  "This chunk is from Section X
  │  to each chunk          │   and discusses Y..."
  └──────────┬──────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
  ┌──────────────┐  ┌─────────────────┐
  │ Embed chunk  │  │  Index chunk in  │
  │ with context │  │  BM25 keyword    │
  │ → vector DB  │  │  index           │
  └──────────────┘  └─────────────────┘

  QUERYING:
  User query
       │
  ┌────┴────────────────────────┐
  ▼                             ▼
  Vector search             BM25 keyword search
  (semantic similarity)     (exact term matching)
       │                         │
       └──────────┬──────────────┘
                  ▼
          Reciprocal Rank
          Fusion (RRF)
          merge results
                  │
                  ▼
          Reranker (optional)
          cross-encoder scoring
                  │
                  ▼
          Top-k chunks → LLM → Answer
```

---

## Benchmark Results

From Anthropic's November 2024 blog post:

```
  RETRIEVAL FAILURE RATES (lower = better)
  ──────────────────────────────────────────────────────────────

  Standard embedding retrieval          ████████████  baseline
  Contextual embedding                  █████░░░░░░░  -35% failures
  BM25 only                             ████████░░░░  -~20% failures
  Contextual embedding + BM25           ████░░░░░░░░  -49% failures
  Contextual + BM25 + reranker          ███░░░░░░░░░  -67% failures
  ──────────────────────────────────────────────────────────────

  Key findings:
  • Context alone: -35% failures
  • Adding BM25 hybrid: -49% failures
  • Adding cross-encoder reranker: -67% failures
  • Reranker alone (without context): smaller gain
  • Combined effect exceeds individual gains (multiplicative)
```

---

## Implementation — Anthropic SDK

```python
"""
contextual_retrieval.py — Anthropic SDK implementation
"""
import anthropic
from rank_bm25 import BM25Okapi
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from pathlib import Path

client = anthropic.Anthropic()


# ─── Step 1: Split document into chunks ──────────────────────

def split_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Simple token-approximate chunking with overlap.
    In production, use semantic chunking or paragraph boundaries.
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap   # overlap to avoid cutting sentences

    return chunks


# ─── Step 2: Generate context for each chunk ─────────────────

CONTEXT_PROMPT = """<document>
{full_document}
</document>

Here is the chunk we want to situate within the whole document:
<chunk>
{chunk}
</chunk>

Please give a short succinct context to situate this chunk within the overall document
for the purposes of improving search retrieval of the chunk.
Answer only with the succinct context and nothing else."""

def generate_chunk_context(
    full_document: str,
    chunk: str,
    model: str = "claude-haiku-4-5-20251001",
) -> str:
    """
    Use Claude to generate a contextual summary for a single chunk.
    Uses claude-haiku for cost efficiency (fractions of a cent per chunk).
    """
    response = client.messages.create(
        model=model,
        max_tokens=150,
        messages=[{
            "role": "user",
            "content": CONTEXT_PROMPT.format(
                full_document=full_document[:20000],   # trim if very large
                chunk=chunk,
            ),
        }],
    )
    return response.content[0].text.strip()


# ─── Step 3: Context generation with prompt caching ──────────
#
# KEY OPTIMIZATION: The full document is the same for every chunk.
# Use Anthropic's prompt caching to avoid re-processing it N times.
# At $3/MTok input vs $0.30/MTok cached, this saves ~90% on the
# document portion for typical 100-chunk documents.

def generate_contexts_with_caching(
    full_document: str,
    chunks: list[str],
    model: str = "claude-haiku-4-5-20251001",
) -> list[str]:
    """
    Generate contexts for all chunks with prompt caching.
    The document is cached after the first call — subsequent chunks
    reuse the cache, reducing cost by ~90%.
    """
    contexts = []

    for i, chunk in enumerate(chunks):
        response = client.messages.create(
            model=model,
            max_tokens=150,
            system=[{
                "type": "text",
                "text": "You generate concise search context for document chunks.",
                "cache_control": {"type": "ephemeral"},   # cache the system prompt
            }],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"<document>\n{full_document}\n</document>",
                            "cache_control": {"type": "ephemeral"},   # cache the doc
                        },
                        {
                            "type": "text",
                            "text": f"Situate this chunk for search retrieval:\n<chunk>\n{chunk}\n</chunk>\nAnswer with only the context, no preamble.",
                        },
                    ],
                }
            ],
        )
        contexts.append(response.content[0].text.strip())

        if (i + 1) % 10 == 0:
            print(f"  Contextualized {i+1}/{len(chunks)} chunks")

    return contexts


# ─── Step 4: Build the contextual chunk corpus ────────────────

def build_contextual_chunks(
    full_document: str,
    chunks: list[str],
    contexts: list[str],
) -> list[str]:
    """
    Prepend the generated context to each chunk.
    This combined text is what gets embedded and indexed.
    """
    contextual_chunks = []
    for chunk, ctx in zip(chunks, contexts):
        # Context goes first so it influences the embedding strongly
        contextual_chunks.append(f"{ctx}\n\n{chunk}")
    return contextual_chunks


# ─── Step 5: Build dual index (vector + BM25) ─────────────────

class ContextualRetrievalIndex:
    """
    Dual index: FAISS for vector search + BM25 for keyword search.
    Both use contextualized chunk text.
    """

    def __init__(self, contextual_chunks: list[str], original_chunks: list[str]):
        self.contextual_chunks = contextual_chunks
        self.original_chunks = original_chunks

        # Vector index (FAISS + sentence-transformers)
        print("Building vector index...")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = self.embedder.encode(contextual_chunks, show_progress_bar=True)
        embeddings = np.array(embeddings, dtype="float32")
        faiss.normalize_L2(embeddings)

        self.vector_index = faiss.IndexFlatIP(embeddings.shape[1])
        self.vector_index.add(embeddings)

        # BM25 index
        print("Building BM25 index...")
        tokenized = [chunk.lower().split() for chunk in contextual_chunks]
        self.bm25 = BM25Okapi(tokenized)

        print(f"Index ready: {len(contextual_chunks)} contextual chunks")

    def vector_search(self, query: str, k: int = 20) -> list[tuple[int, float]]:
        q_emb = self.embedder.encode([query])
        q_emb = np.array(q_emb, dtype="float32")
        faiss.normalize_L2(q_emb)
        scores, indices = self.vector_index.search(q_emb, k)
        return list(zip(indices[0].tolist(), scores[0].tolist()))

    def bm25_search(self, query: str, k: int = 20) -> list[tuple[int, float]]:
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1][:k]
        return [(int(i), float(scores[i])) for i in top_indices]

    def hybrid_search(
        self,
        query: str,
        k: int = 5,
        vector_k: int = 20,
        bm25_k: int = 20,
        rrf_k: int = 60,
    ) -> list[dict]:
        """
        Reciprocal Rank Fusion (RRF) hybrid search.
        Combines vector and BM25 rankings without needing score normalization.
        """
        vec_results = self.vector_search(query, k=vector_k)
        bm25_results = self.bm25_search(query, k=bm25_k)

        # RRF scoring: score = Σ 1/(rank + rrf_k)
        rrf_scores: dict[int, float] = {}

        for rank, (idx, _) in enumerate(vec_results):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1.0 / (rank + 1 + rrf_k)

        for rank, (idx, _) in enumerate(bm25_results):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1.0 / (rank + 1 + rrf_k)

        # Sort by RRF score, return top-k
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        return [
            {
                "chunk": self.original_chunks[idx],
                "context_chunk": self.contextual_chunks[idx],
                "rrf_score": score,
                "index": idx,
            }
            for idx, score in sorted_results[:k]
        ]

    def save(self, path: str):
        data = {
            "contextual_chunks": self.contextual_chunks,
            "original_chunks": self.original_chunks,
        }
        Path(path).with_suffix(".pkl").write_bytes(pickle.dumps(data))
        faiss.write_index(self.vector_index, path + ".faiss")


# ─── Step 6: Answer generation ───────────────────────────────

def answer_with_contextual_retrieval(
    question: str,
    index: ContextualRetrievalIndex,
    k: int = 5,
) -> dict:
    """Answer a question using contextual retrieval."""
    results = index.hybrid_search(question, k=k)

    # Format context for the LLM (use original chunks, not context+chunk)
    context = "\n\n---\n\n".join(
        f"[Chunk {i+1}]\n{r['chunk']}" for i, r in enumerate(results)
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="Answer the question using the provided context chunks. Be precise.",
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        }],
    )

    return {
        "answer": response.content[0].text,
        "chunks_used": len(results),
        "top_chunk_preview": results[0]["chunk"][:200] if results else "",
    }


# ─── Full pipeline ────────────────────────────────────────────

def build_contextual_retrieval_index(
    document: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> ContextualRetrievalIndex:
    """
    End-to-end: document text → contextual retrieval index.
    """
    print("Step 1: Splitting document into chunks...")
    chunks = split_into_chunks(document, chunk_size, overlap)
    print(f"  {len(chunks)} chunks created")

    print("Step 2: Generating contextual summaries (with caching)...")
    contexts = generate_contexts_with_caching(document, chunks)

    print("Step 3: Building contextual chunk texts...")
    contextual_chunks = build_contextual_chunks(document, chunks, contexts)

    print("Step 4: Building dual index (FAISS + BM25)...")
    return ContextualRetrievalIndex(contextual_chunks, chunks)


# ─── Usage ────────────────────────────────────────────────────

if __name__ == "__main__":
    document = open("contract.txt").read()

    index = build_contextual_retrieval_index(document)

    result = answer_with_contextual_retrieval(
        "What happens if Globex fails to pay within 30 days?",
        index,
    )
    print(result["answer"])
```

---

## Implementation — LangChain

```python
"""
contextual_retrieval_langchain.py — LangChain implementation
"""
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_anthropic import ChatAnthropic
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import Field
import anthropic


# ─── Context generation ───────────────────────────────────────

def add_context_to_documents(
    documents: list[Document],
    full_document_text: str,
) -> list[Document]:
    """
    Add LLM-generated context to each LangChain Document.
    Returns new Documents with context prepended to page_content.
    """
    anth_client = anthropic.Anthropic()
    contextualized_docs = []

    for i, doc in enumerate(documents):
        response = anth_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"<document>\n{full_document_text[:15000]}\n</document>",
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": f"Situate this chunk for retrieval in 1-2 sentences:\n<chunk>\n{doc.page_content}\n</chunk>",
                    },
                ],
            }],
        )
        context = response.content[0].text.strip()
        contextualized_docs.append(Document(
            page_content=f"{context}\n\n{doc.page_content}",
            metadata={**doc.metadata, "context": context},
        ))

        if (i + 1) % 10 == 0:
            print(f"  Contextualized {i+1}/{len(documents)} docs")

    return contextualized_docs


# ─── Hybrid retriever ─────────────────────────────────────────

class ContextualHybridRetriever(BaseRetriever):
    """
    Hybrid retriever combining contextualized vector search + BM25.
    Uses RRF to merge results from both methods.
    """

    vector_retriever: object
    bm25_retriever: BM25Retriever
    k: int = 5
    rrf_k: int = 60

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_documents(
        cls,
        documents: list[Document],
        full_document_text: str,
        k: int = 5,
    ) -> "ContextualHybridRetriever":
        """
        Build the retriever from a list of LangChain Documents.
        Automatically adds context to each document before indexing.
        """
        print("Adding context to documents...")
        contextualized_docs = add_context_to_documents(documents, full_document_text)

        print("Building vector store...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = FAISS.from_documents(contextualized_docs, embeddings)
        vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 20})

        print("Building BM25 index...")
        bm25_retriever = BM25Retriever.from_documents(contextualized_docs)
        bm25_retriever.k = 20

        return cls(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            k=k,
        )

    def _reciprocal_rank_fusion(
        self,
        vec_docs: list[Document],
        bm25_docs: list[Document],
    ) -> list[Document]:
        """Merge two ranked lists using RRF."""
        scores: dict[str, float] = {}
        doc_map: dict[str, Document] = {}

        for rank, doc in enumerate(vec_docs):
            key = doc.page_content[:100]
            scores[key] = scores.get(key, 0) + 1.0 / (rank + 1 + self.rrf_k)
            doc_map[key] = doc

        for rank, doc in enumerate(bm25_docs):
            key = doc.page_content[:100]
            scores[key] = scores.get(key, 0) + 1.0 / (rank + 1 + self.rrf_k)
            doc_map[key] = doc

        sorted_keys = sorted(scores, key=scores.get, reverse=True)
        return [doc_map[k] for k in sorted_keys[:self.k]]

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        vec_docs = self.vector_retriever.invoke(query)
        bm25_docs = self.bm25_retriever.invoke(query)
        return self._reciprocal_rank_fusion(vec_docs, bm25_docs)


# ─── Full QA chain ────────────────────────────────────────────

from langchain_core.runnables import RunnablePassthrough

def build_contextual_qa_chain(
    full_document_text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
):
    """Build a complete QA chain with contextual retrieval."""

    # Split
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    docs = splitter.create_documents([full_document_text])

    # Build retriever
    retriever = ContextualHybridRetriever.from_documents(docs, full_document_text)

    # Build chain
    llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=1024)
    prompt = ChatPromptTemplate.from_template("""Answer using the context below.

Context:
{context}

Question: {question}

Answer:""")

    def format_docs(docs):
        return "\n\n---\n\n".join(d.page_content for d in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


# ─── Usage ────────────────────────────────────────────────────

if __name__ == "__main__":
    document_text = open("contract.txt").read()
    chain = build_contextual_qa_chain(document_text)
    answer = chain.invoke("What happens if Globex fails to pay within 30 days?")
    print(answer)
```

---

## Cost Analysis — Prompt Caching

Without caching, generating context for 100 chunks from a 100-page document sends the full document 100 times:

```
  WITHOUT CACHING:
  ─────────────────────────────────────────────────────────
  Document tokens:     20,000 tokens × 100 chunks = 2,000,000
  Chunk tokens:           500 tokens × 100 chunks =    50,000
  Total input tokens:                               2,050,000
  Cost (Haiku $0.80/MTok):                              $1.64
  ─────────────────────────────────────────────────────────

  WITH PROMPT CACHING:
  ─────────────────────────────────────────────────────────
  First call (cache miss):  20,500 tokens = $0.016
  Calls 2-100 (cache hit):  500 tokens each × $0.08/MTok
                            = 49,500 tokens = $0.004
  Total:                                        ~$0.02
  ─────────────────────────────────────────────────────────

  Savings: ~$1.62 (98.8% reduction) for a 100-chunk document
  Savings scale linearly with document size
```

---

## Contextual Retrieval vs. PageIndex

```
  ┌──────────────────────┬────────────────────────┬──────────────────────┐
  │                      │  Contextual Retrieval  │      PageIndex        │
  ├──────────────────────┼────────────────────────┼──────────────────────┤
  │ Document type        │ Any text (prose, docs) │ Structured PDFs      │
  │ Chunking             │ Still chunks doc       │ No chunking          │
  │ Table handling       │ Poor (chunks tables)   │ Excellent (full page)│
  │ Cross-references     │ Partial                │ Full resolution      │
  │ Index size           │ Vector DB              │ Text file (~15k tok) │
  │ Query cost           │ Low (vector lookup)    │ Medium (LLM nav)     │
  │ Indexing cost        │ Medium (LLM per chunk) │ Medium (LLM per page)│
  │ Accuracy improvement │ +35–67% vs baseline    │ +30–40% vs adv. RAG  │
  │ Best for             │ General document QA    │ Financial, legal PDFs│
  └──────────────────────┴────────────────────────┴──────────────────────┘
```

**When to use Contextual Retrieval instead of PageIndex:**
- Documents don't have clear page structure (web articles, transcripts, books)
- You already have a vector RAG system and want an easy improvement
- Sub-second query latency is required
- Documents are too large even for hierarchical page-level indexing

---

## See Also

- [Vectorless RAG Hub](../pageindex-vectorless-rag) — overview of all vectorless approaches
- [BM25 & Sparse Retrieval](../bm25-sparse-retrieval) — how BM25 scoring works under the hood
- [Retrieval Strategies](../retrieval-strategies) — hybrid, HyDE, MMR, reranking pipelines
- [Advanced RAG](../advanced-rag) — FLARE, RAPTOR, CRAG, query decomposition
