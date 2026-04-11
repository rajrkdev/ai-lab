---
title: "BM25 & Sparse Retrieval"
description: How BM25 keyword scoring works (with the math explained simply), when it beats vector search, SPLADE learned sparse retrieval, Elasticsearch/Typesense integration, and hybrid RRF fusion — with Anthropic SDK and LangChain implementations.
sidebar:
  order: 15
---

## What Is Sparse Retrieval?

Every retrieval method represents documents as numbers. The difference is *how*:

```
  DENSE RETRIEVAL (vectors)              SPARSE RETRIEVAL (keywords)
  ─────────────────────────────          ─────────────────────────────
  "The cat sat on the mat"               "The cat sat on the mat"
        │                                      │
        ▼ embedding model                      ▼ tokenize + score
  [0.23, -0.11, 0.87, 0.04,             {
   0.33,  0.71, -0.22, ...]               "cat": 2.3,
                                           "sat": 1.8,
  768–3072 dimensions                      "mat": 1.9,
  ALL non-zero (dense)                     "the": 0.1,
                                           [all other words]: 0
                                         }
                                         ~50,000 vocab dimensions
                                         MOST are zero (sparse)
```

**Sparse = most values are zero.** A sparse representation only has non-zero scores for words that actually appear in the document (or are semantically related — more on this with SPLADE).

This sparsity is the key advantage: retrieval becomes exact word matching, not approximate geometric search.

---

## TF-IDF — The Foundation

Before BM25, there was **TF-IDF** (Term Frequency–Inverse Document Frequency). Understanding TF-IDF makes BM25 intuitive.

### Term Frequency (TF)

How many times does a word appear in this document?

```
  Document: "Python is great. Python is fast. Python is popular."
  
  TF("Python") = 3/9 = 0.33   (3 occurrences out of 9 total words)
  TF("is")     = 3/9 = 0.33
  TF("great")  = 1/9 = 0.11
```

**Problem with raw TF:** If a document mentions "Python" 100 times, is it 100× more relevant than a document mentioning it once? No — the relevance gain diminishes.

### Inverse Document Frequency (IDF)

How rare is this word across all documents? Rare words are more informative.

```
  Corpus: 10,000 documents

  "Python" appears in 500 documents → IDF = log(10000/500) = 3.0
  "the"    appears in 9999 documents → IDF = log(10000/9999) ≈ 0.0
  "asyncio" appears in 50 documents  → IDF = log(10000/50)  = 5.3

  Insight: "asyncio" is a much stronger signal than "Python",
           which is a stronger signal than "the"
```

### TF-IDF Score

```
  TF-IDF(word, document) = TF(word, document) × IDF(word, corpus)

  For "Python" in our document:
  TF-IDF = 0.33 × 3.0 = 0.99

  For "asyncio" (appears once):
  TF-IDF = 0.11 × 5.3 = 0.58

  Wait — "asyncio" scores lower despite being rarer?
  → That's the TF-IDF limitation BM25 fixes.
```

---

## BM25 — Best Match 25

**BM25** (Okapi BM25, 1994) improves on TF-IDF with two key fixes:

1. **Saturation** — diminishing returns for high term frequency
2. **Document length normalization** — longer documents shouldn't automatically score higher

### The BM25 Formula

```
  BM25(query q, document D) = Σ  IDF(tᵢ) × TF_adjusted(tᵢ, D)
                               tᵢ∈q

  Where:

  IDF(tᵢ) = log( (N - n(tᵢ) + 0.5) / (n(tᵢ) + 0.5) + 1 )

  TF_adjusted = f(tᵢ,D) × (k₁ + 1)
                ─────────────────────────────────────────
                f(tᵢ,D) + k₁ × (1 - b + b × |D|/avgdl)

  Variables:
  N         = total number of documents in corpus
  n(tᵢ)     = number of documents containing term tᵢ
  f(tᵢ,D)   = raw frequency of term tᵢ in document D
  |D|        = length of document D (in words)
  avgdl      = average document length in corpus
  k₁         = term frequency saturation (default: 1.2)
  b          = length normalization weight (default: 0.75)
```

### Understanding k₁ and b

```
  k₁ — SATURATION PARAMETER
  ─────────────────────────────────────────────────
  Controls how quickly relevance saturates with term frequency

  f(t,D) =  1  →  TF_adjusted ≈ 0.91  (with k₁=1.2)
  f(t,D) =  5  →  TF_adjusted ≈ 1.64
  f(t,D) = 10  →  TF_adjusted ≈ 1.77
  f(t,D) = 50  →  TF_adjusted ≈ 1.93
  f(t,D) = ∞   →  TF_adjusted → k₁+1 = 2.2  (hard ceiling!)

  → No matter how many times a term appears, score is bounded.
  → TF-IDF had no such bound — BM25 is more robust.

  ─────────────────────────────────────────────────
  b — LENGTH NORMALIZATION PARAMETER
  ─────────────────────────────────────────────────
  b = 0:  Document length has NO effect (ignore normalization)
  b = 1:  Full length normalization (penalize long docs strongly)
  b = 0.75: Default — partial normalization

  Example:
  Short doc (50 words), "Python" appears once:  |D|/avgdl = 0.25
  Long doc  (500 words), "Python" appears once: |D|/avgdl = 2.50

  With b=0.75:
  Short doc denominator: 1.2 × (0.25 + 0.75 × 0.25) = 0.525
  Long doc denominator:  1.2 × (0.25 + 0.75 × 2.50) = 2.55

  Short doc scores ~5× higher for same term frequency
  → Prevents long docs from winning just by being verbose
```

### BM25 Step-by-Step Example

```
  QUERY: "python async"
  CORPUS: 3 documents

  Doc 1 (80 words):  "Python async/await makes concurrency simple..."
                      python: 3 times, async: 2 times

  Doc 2 (400 words): "Python is a general programming language...
                      [mentions python 8 times, async 1 time]"

  Doc 3 (60 words):  "JavaScript async promises differ from Python
                      async/await syntax..." [python: 2, async: 4]

  avgdl = (80 + 400 + 60) / 3 = 180

  STEP 1: Compute IDF for each query term
  ─────────────────────────────────────────
  "python": in all 3 docs → IDF = log((3-3+0.5)/(3+0.5)+1) ≈ 0.29
  "async":  in all 3 docs → IDF = log((3-3+0.5)/(3+0.5)+1) ≈ 0.29

  (Low IDF because both terms appear in every document)

  STEP 2: Compute TF_adjusted for each doc
  ─────────────────────────────────────────
  Doc 1 "python": f=3, |D|=80
    TF_adj = 3×2.2 / (3 + 1.2×(0.25+0.75×80/180)) = 1.64

  Doc 2 "python": f=8, |D|=400
    TF_adj = 8×2.2 / (8 + 1.2×(0.25+0.75×400/180)) = 1.52
    (saturated despite 8 occurrences, AND penalized for length)

  Doc 3 "async": f=4, |D|=60
    TF_adj = 4×2.2 / (4 + 1.2×(0.25+0.75×60/180)) = 1.78
    (short doc, 4 occurrences of a relevant term → high score)

  RESULT: Doc 3 ranks highest for "python async" despite
  being shorter and having fewer "python" mentions —
  BM25 correctly identifies it as the most relevant.
```

---

## When BM25 Beats Vector Search

```
  USE BM25 WHEN:                          USE VECTORS WHEN:
  ────────────────────────────────        ─────────────────────────────
  Query contains exact terms to match     Query is conversational/fuzzy
  Searching for product codes, CVEs       Semantic similarity matters
  Searching for proper names (companies)  Cross-language retrieval
  Searching for version numbers           Paraphrase detection
  Technical documentation lookup          Concept-level search
  Short queries (2–5 words)               Long descriptive queries
  Domain-specific jargon                  General knowledge questions

  CONCRETE EXAMPLES:
  ──────────────────────────────────────────────────────────────

  BM25 wins:
  "CVE-2024-43573 vulnerability details"  → exact string match
  "PostgreSQL pg_stat_statements"         → exact technical terms
  "BERT bert-base-uncased model card"     → exact model name
  "Apple Inc AAPL Q3 2023 10-K"          → codes + company name

  Vectors win:
  "how to make database queries faster"   → matches "query optimization"
  "my program crashes on startup"         → matches "initialization errors"
  "explain gradient descent simply"       → matches intuitive explanations
  "difference between let and const"      → conceptual similarity
```

---

## Implementation — Anthropic SDK + rank_bm25

```python
"""
bm25_retrieval.py — BM25 retrieval with Anthropic SDK for generation
pip install rank-bm25 anthropic nltk
"""
import anthropic
import nltk
from rank_bm25 import BM25Okapi, BM25Plus
from dataclasses import dataclass
import re
import string

# Download required NLTK data (run once)
nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("punkt_tab", quiet=True)
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

client = anthropic.Anthropic()
STOPWORDS = set(stopwords.words("english"))
stemmer = PorterStemmer()


# ─── Text preprocessing ───────────────────────────────────────

def preprocess(text: str, stem: bool = False) -> list[str]:
    """
    Tokenize and clean text for BM25 indexing.
    
    stem=False: faster, exact matching, better for technical terms
    stem=True:  handles plurals/tenses ("running" matches "run")
    """
    # Lowercase
    text = text.lower()
    # Remove punctuation (preserve hyphens in compound terms)
    text = re.sub(r"[^\w\s\-]", " ", text)
    # Tokenize
    tokens = nltk.word_tokenize(text)
    # Remove stopwords (optional — removing hurts exact-match queries)
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    # Stem (optional)
    if stem:
        tokens = [stemmer.stem(t) for t in tokens]
    return tokens


# ─── BM25 index ───────────────────────────────────────────────

@dataclass
class BM25Index:
    documents: list[str]
    metadata: list[dict]
    bm25: BM25Okapi


def build_bm25_index(
    documents: list[str],
    metadata: list[dict] | None = None,
    variant: str = "okapi",   # "okapi" or "plus"
) -> BM25Index:
    """
    Build a BM25 index from a list of document strings.

    BM25Okapi: standard BM25, best for most use cases
    BM25Plus:  improved version that ensures non-zero score for any term match
                (better for short documents)
    """
    tokenized = [preprocess(doc) for doc in documents]

    if variant == "plus":
        bm25 = BM25Plus(tokenized)
    else:
        bm25 = BM25Okapi(tokenized)

    return BM25Index(
        documents=documents,
        metadata=metadata or [{} for _ in documents],
        bm25=bm25,
    )


def bm25_retrieve(
    query: str,
    index: BM25Index,
    k: int = 5,
    score_threshold: float = 0.0,
) -> list[dict]:
    """
    Retrieve top-k documents using BM25 scoring.
    Returns documents with scores and metadata.
    """
    tokenized_query = preprocess(query)
    scores = index.bm25.get_scores(tokenized_query)

    # Get indices sorted by score descending
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

    results = []
    for idx, score in ranked[:k]:
        if score <= score_threshold:
            break
        results.append({
            "document": index.documents[idx],
            "score": float(score),
            "rank": len(results) + 1,
            "metadata": index.metadata[idx],
        })

    return results


# ─── BM25 + Anthropic QA ─────────────────────────────────────

def bm25_rag(
    question: str,
    index: BM25Index,
    k: int = 5,
) -> str:
    """Answer a question using BM25 retrieval + Claude generation."""
    results = bm25_retrieve(question, index, k=k)

    if not results:
        return "No relevant documents found."

    context = "\n\n---\n\n".join(
        f"[Score: {r['score']:.2f}]\n{r['document']}" for r in results
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="Answer the question using the provided context. Be precise.",
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        }],
    )
    return response.content[0].text


# ─── Hybrid BM25 + vector with RRF ───────────────────────────

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss


class HybridBM25VectorRetriever:
    """
    Combines BM25 (exact match) with dense vectors (semantic match)
    using Reciprocal Rank Fusion.

    Best of both worlds:
    - BM25 handles exact terms, codes, names
    - Vectors handle semantic similarity, paraphrases
    - RRF merges both rankings without score normalization
    """

    def __init__(
        self,
        documents: list[str],
        metadata: list[dict] | None = None,
        embed_model: str = "all-MiniLM-L6-v2",
        rrf_k: int = 60,
    ):
        self.documents = documents
        self.metadata = metadata or [{} for _ in documents]
        self.rrf_k = rrf_k

        # BM25 index
        print("Building BM25 index...")
        tokenized = [preprocess(doc) for doc in documents]
        self.bm25 = BM25Okapi(tokenized)

        # Vector index
        print(f"Building vector index ({embed_model})...")
        self.embedder = SentenceTransformer(embed_model)
        embeddings = self.embedder.encode(documents, show_progress_bar=True)
        embeddings = np.array(embeddings, dtype="float32")
        faiss.normalize_L2(embeddings)

        self.vector_index = faiss.IndexFlatIP(embeddings.shape[1])
        self.vector_index.add(embeddings)
        print(f"Ready: {len(documents)} documents indexed")

    def search(
        self,
        query: str,
        k: int = 5,
        bm25_weight: float = 0.5,   # relative weight for BM25 in RRF
        vector_weight: float = 0.5, # relative weight for vectors in RRF
        fetch_k: int = 50,          # candidates from each method before fusion
    ) -> list[dict]:
        """
        Hybrid search with weighted RRF fusion.

        bm25_weight + vector_weight don't need to sum to 1.
        Increase bm25_weight for technical/exact queries.
        Increase vector_weight for semantic/conceptual queries.
        """
        # BM25 search
        tokenized_q = preprocess(query)
        bm25_scores = self.bm25.get_scores(tokenized_q)
        bm25_ranked = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:fetch_k]

        # Vector search
        q_emb = self.embedder.encode([query])
        q_emb = np.array(q_emb, dtype="float32")
        faiss.normalize_L2(q_emb)
        _, vec_indices = self.vector_index.search(q_emb, fetch_k)
        vec_ranked = vec_indices[0].tolist()

        # Weighted RRF fusion
        rrf_scores: dict[int, float] = {}

        for rank, idx in enumerate(bm25_ranked):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + bm25_weight / (rank + 1 + self.rrf_k)

        for rank, idx in enumerate(vec_ranked):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + vector_weight / (rank + 1 + self.rrf_k)

        # Sort and return top-k
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [
            {
                "document": self.documents[idx],
                "rrf_score": score,
                "bm25_score": float(bm25_scores[idx]),
                "metadata": self.metadata[idx],
                "rank": i + 1,
            }
            for i, (idx, score) in enumerate(sorted_results[:k])
        ]

    def rag_answer(self, question: str, k: int = 5) -> str:
        """Answer using hybrid retrieval + Claude."""
        results = self.search(question, k=k)
        context = "\n\n---\n\n".join(r["document"] for r in results)

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system="Answer precisely using the provided context.",
            messages=[{
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            }],
        )
        return response.content[0].text


# ─── Usage ────────────────────────────────────────────────────

if __name__ == "__main__":
    docs = [
        "CVE-2024-43573 affects Windows MSHTML platform versions 10-11.",
        "Python 3.12 introduced the asyncio.TaskGroup API for structured concurrency.",
        "The async/await pattern simplifies asynchronous code in Python.",
        "PostgreSQL 16 adds pg_stat_io for detailed I/O statistics tracking.",
        "Apple reported Q3 FY2023 iPhone revenue of $39,669M, down 2.4% YoY.",
    ]

    # Pure BM25
    index = build_bm25_index(docs)
    result = bm25_rag("CVE-2024-43573 details", index)
    print(result)

    # Hybrid
    hybrid = HybridBM25VectorRetriever(docs)
    answer = hybrid.rag_answer("Python async concurrency patterns")
    print(answer)
```

---

## Implementation — LangChain

```python
"""
bm25_langchain.py — BM25 and hybrid retrieval with LangChain
pip install langchain langchain-community langchain-anthropic rank-bm25
"""
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain.retrievers import EnsembleRetriever
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


# ─── Documents ────────────────────────────────────────────────

docs = [
    Document(page_content="CVE-2024-43573 affects Windows MSHTML...", metadata={"source": "nvd"}),
    Document(page_content="Python asyncio.TaskGroup introduced in 3.11...", metadata={"source": "docs"}),
    Document(page_content="Apple Q3 FY2023 iPhone revenue $39.7B...", metadata={"source": "10-K"}),
]


# ─── BM25 only ────────────────────────────────────────────────

bm25_retriever = BM25Retriever.from_documents(docs)
bm25_retriever.k = 3


# ─── Hybrid: BM25 + FAISS ─────────────────────────────────────

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(docs, embeddings)
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# EnsembleRetriever uses RRF internally
# weights control the contribution of each retriever
hybrid_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.5, 0.5],   # equal weight; increase BM25 weight for technical queries
)


# ─── QA chain ─────────────────────────────────────────────────

llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=1024)

prompt = ChatPromptTemplate.from_template("""Answer using the context below.

Context: {context}
Question: {question}
Answer:""")

def format_docs(docs):
    return "\n\n---\n\n".join(d.page_content for d in docs)

# BM25 chain
bm25_chain = (
    {"context": bm25_retriever | format_docs, "question": RunnablePassthrough()}
    | prompt | llm | StrOutputParser()
)

# Hybrid chain (better for mixed queries)
hybrid_chain = (
    {"context": hybrid_retriever | format_docs, "question": RunnablePassthrough()}
    | prompt | llm | StrOutputParser()
)

# Usage
answer = hybrid_chain.invoke("CVE-2024-43573 vulnerability")
print(answer)
```

---

## SPLADE — Learned Sparse Retrieval

**SPLADE** (Sparse Lexical and Expansion Model, Formal et al., 2022) is a neural approach that *learns* sparse representations. It expands queries and documents with semantically related terms, giving sparse retrieval semantic capabilities.

```
  BM25 (statistical):               SPLADE (learned):
  ────────────────────────          ──────────────────────────────
  "Python async"                    "Python async"
  → sparse vector:                  → sparse vector:
  {                                 {
    "python": 2.3,                    "python": 3.1,
    "async": 1.8,                     "async": 2.9,
    [all other terms]: 0              "asyncio": 1.4,    ← expanded
  }                                   "concurrency": 1.2, ← expanded
                                      "coroutine": 0.8,  ← expanded
  Cannot match "coroutine"            "await": 0.7,      ← expanded
  if it's not in query                [all other terms]: 0
                                    }
                                    CAN match "coroutine" docs!
```

**SPLADE combines BM25's inverted index efficiency with the semantic reach of dense vectors.**

```python
# SPLADE with HuggingFace Transformers
# pip install transformers torch

from transformers import AutoModelForMaskedLM, AutoTokenizer
import torch
import scipy.sparse as sp
import numpy as np

model_id = "naver/splade-cocondenser-ensembledistil"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForMaskedLM.from_pretrained(model_id)
model.eval()

def encode_splade(text: str) -> dict[str, float]:
    """Encode text into a SPLADE sparse vector (word → weight)."""
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True,
    )
    with torch.no_grad():
        outputs = model(**inputs)

    # SPLADE activation: log(1 + ReLU(logits)) aggregated over tokens
    logits = outputs.logits
    activations = torch.log1p(torch.relu(logits))
    # Max pooling over token dimension
    sparse_vec = torch.max(activations, dim=1).values.squeeze()

    # Convert to dictionary of (token → weight) for non-zero terms
    indices = sparse_vec.nonzero().squeeze(-1).tolist()
    weights = sparse_vec[indices].tolist()

    if isinstance(indices, int):    # handle single-term edge case
        indices, weights = [indices], [weights]

    vocab = tokenizer.convert_ids_to_tokens(indices)
    return {token: weight for token, weight in zip(vocab, weights) if weight > 0.01}


# SPLADE retrieval
def splade_score(query_vec: dict, doc_vec: dict) -> float:
    """Dot product of sparse SPLADE vectors."""
    return sum(
        query_vec.get(term, 0) * weight
        for term, weight in doc_vec.items()
    )


if __name__ == "__main__":
    docs = [
        "Python asyncio provides cooperative multitasking via coroutines.",
        "JavaScript promises and async/await for asynchronous programming.",
    ]

    # Encode all docs at indexing time
    doc_vecs = [encode_splade(doc) for doc in docs]

    # Query
    query = "Python async"
    query_vec = encode_splade(query)
    print("SPLADE query expansion:", dict(list(query_vec.items())[:10]))

    # Score and rank
    scores = [(i, splade_score(query_vec, dv)) for i, dv in enumerate(doc_vecs)]
    scores.sort(key=lambda x: x[1], reverse=True)
    print(f"Top result: {docs[scores[0][0]]}")
```

---

## Full-Text Search Engines

For production systems, use a purpose-built search engine rather than in-process BM25:

```
  ENGINE COMPARISON
  ────────────────────────────────────────────────────────────────────
  Engine           License    BM25  Neural  Scale       Best for
  ────────────────────────────────────────────────────────────────────
  Elasticsearch    Elastic    ✓     ✓       Petabyte    Enterprise search
  OpenSearch       Apache 2   ✓     ✓       Petabyte    AWS deployments
  Typesense        GPL-3      ✓     ✗       Millions    Typo-tolerant search
  Meilisearch      MIT        ✓     ✗       Millions    Developer-friendly
  Tantivy          MIT        ✓     ✗       Millions    Rust-based, embedded
  PostgreSQL FTS   PostgreSQL ✓     ✗       Millions    Already using Postgres
  ────────────────────────────────────────────────────────────────────
```

### PostgreSQL Full-Text Search

If your data is already in PostgreSQL, use built-in FTS before adding a search engine:

```sql
-- Create a tsvector column for fast FTS
ALTER TABLE documents ADD COLUMN ts_content tsvector;

-- Populate it from the text column
UPDATE documents 
SET ts_content = to_tsvector('english', content);

-- Create GIN index for fast BM25-style search
CREATE INDEX documents_ts_idx ON documents USING GIN(ts_content);

-- Query: returns ranked results
SELECT 
    id,
    title,
    content,
    ts_rank(ts_content, query) AS rank
FROM 
    documents,
    to_tsquery('english', 'python & async') query
WHERE 
    ts_content @@ query
ORDER BY rank DESC
LIMIT 10;
```

```python
# PostgreSQL FTS from Python
import psycopg2
import anthropic

client = anthropic.Anthropic()

def postgres_fts_rag(
    question: str,
    conn_string: str,
    k: int = 5,
) -> str:
    """RAG using PostgreSQL full-text search."""
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    # Convert natural language to tsquery
    # Simple: split into words joined by &
    words = [w.strip("?.,!") for w in question.lower().split() if len(w) > 3]
    tsquery = " & ".join(words[:5])   # use first 5 meaningful words

    cur.execute("""
        SELECT content, ts_rank(ts_content, to_tsquery('english', %s)) AS rank
        FROM documents
        WHERE ts_content @@ to_tsquery('english', %s)
        ORDER BY rank DESC
        LIMIT %s
    """, (tsquery, tsquery, k))

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return "No relevant documents found."

    context = "\n\n---\n\n".join(row[0] for row in rows)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="Answer using the provided context.",
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        }],
    )
    return response.content[0].text
```

---

## BM25 vs. Vector vs. SPLADE — Head to Head

```
  QUERY TYPE PERFORMANCE MATRIX
  ────────────────────────────────────────────────────────────────
  Query type                   BM25   Vector   SPLADE   Hybrid
  ────────────────────────────────────────────────────────────────
  Exact code: "CVE-2024-43573" ★★★★★  ★★☆☆☆   ★★★★☆   ★★★★★
  Product codes / SKUs         ★★★★★  ★★☆☆☆   ★★★★☆   ★★★★★
  Named entities (companies)   ★★★★☆  ★★★☆☆   ★★★★☆   ★★★★★
  Technical jargon             ★★★★☆  ★★★☆☆   ★★★★★   ★★★★★
  Semantic similarity          ★★☆☆☆  ★★★★★   ★★★★☆   ★★★★★
  Cross-language               ★☆☆☆☆  ★★★★★   ★★★☆☆   ★★★★☆
  Short queries (2-3 words)    ★★★★☆  ★★★☆☆   ★★★★☆   ★★★★★
  Long conversational queries  ★★☆☆☆  ★★★★★   ★★★★☆   ★★★★★
  Negation ("not affected")    ★★★☆☆  ★★☆☆☆   ★★★☆☆   ★★★☆☆
  Numbers / dates              ★★★★★  ★★☆☆☆   ★★★☆☆   ★★★★★
  ────────────────────────────────────────────────────────────────
  ★ = poor  ★★★ = adequate  ★★★★★ = excellent
```

**Recommendation:** Start with hybrid BM25 + vector. Add SPLADE if you need semantic expansion without the cost of dense retrieval at scale.

---

## See Also

- [Vectorless RAG Hub](./pageindex-vectorless-rag) — all vectorless approaches overview
- [Contextual Retrieval](./contextual-retrieval) — adding context to chunks, BM25 + contextual hybrid
- [Retrieval Strategies](./retrieval-strategies) — dense, hybrid, HyDE, reranking
- [GraphRAG](./graph-rag) — entity graph retrieval
