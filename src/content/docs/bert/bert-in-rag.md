---
title: BERT in RAG Pipelines
description: How BERT-family models power RAG systems — bi-encoder retrieval, cross-encoder reranking, ColBERT late interaction, and practical pipeline patterns with performance benchmarks.
sidebar:
  order: 8
---

## BERT's Role in RAG

BERT-family models are central to production RAG systems in two distinct roles:

| Role | Model type | When used | Latency |
|---|---|---|---|
| **Bi-encoder** (retrieval) | SBERT / DPR / E5 | First-stage: retrieve top-k candidates from corpus | O(1) with precomputed index |
| **Cross-encoder** (reranking) | BERT fine-tuned on pairs | Second-stage: rerank top-k for precision | O(k) — must process each pair |

The two stages complement each other: bi-encoder maximizes **recall** cheaply, cross-encoder maximizes **precision** on the shortlist.

---

## Stage 1: Bi-encoder Retrieval

### Architecture

Both query and document are encoded **independently** into dense vectors, then compared via dot product or cosine similarity:

$$\text{score}(q, d) = \text{sim}(\text{Enc}_Q(q),\; \text{Enc}_D(d))$$

Because document embeddings are computed offline and stored in a vector index, retrieval at query time is a single nearest-neighbor search — $O(\log n)$ or $O(1)$ with HNSW.

### Dense Passage Retrieval (DPR)

DPR (Karpukhin et al., 2020) was the first major bi-encoder system for open-domain QA. It uses two separate BERT models — one for queries, one for passages — trained with in-batch negatives:

```python
from transformers import DPRQuestionEncoder, DPRContextEncoder, DPRTokenizer
import torch

# Load DPR bi-encoder
q_tokenizer  = DPRTokenizer.from_pretrained("facebook/dpr-question_encoder-single-nq-base")
ctx_tokenizer = DPRTokenizer.from_pretrained("facebook/dpr-ctx_encoder-single-nq-base")

q_model   = DPRQuestionEncoder.from_pretrained("facebook/dpr-question_encoder-single-nq-base")
ctx_model = DPRContextEncoder.from_pretrained("facebook/dpr-ctx_encoder-single-nq-base")

# Encode query
question = "Who invented the telephone?"
q_inputs = q_tokenizer(question, return_tensors="pt")
with torch.no_grad():
    q_embedding = q_model(**q_inputs).pooler_output  # [1, 768]

# Encode passages (done offline for corpus)
passages = ["Alexander Graham Bell invented the telephone.", "The telephone was patented in 1876."]
ctx_inputs = ctx_tokenizer(passages, return_tensors="pt", padding=True, truncation=True, max_length=256)
with torch.no_grad():
    ctx_embeddings = ctx_model(**ctx_inputs).pooler_output  # [2, 768]

# Compute similarity
scores = torch.matmul(q_embedding, ctx_embeddings.T).squeeze()
print(scores)          # [0.87, 0.69]
best_passage = passages[scores.argmax()]
```

### E5 / BGE: Modern Bi-encoders

More recent bi-encoders (E5, BGE, GTE) outperform DPR on BEIR benchmarks:

```python
from sentence_transformers import SentenceTransformer

# E5 requires the "query: " / "passage: " prefix
model = SentenceTransformer("intfloat/e5-base-v2")

query   = "query: Who invented the telephone?"
passage = "passage: Alexander Graham Bell invented the telephone in 1876."

q_emb = model.encode(query,   normalize_embeddings=True)
d_emb = model.encode(passage, normalize_embeddings=True)
score = (q_emb * d_emb).sum()   # cosine similarity (normalized)
print(score)  # ~0.91
```

---

## Stage 2: Cross-encoder Reranking

### Architecture

A cross-encoder takes the **concatenated** (query, document) pair as input — they interact through all attention layers:

```
Input:  [CLS] query tokens [SEP] document tokens [SEP]
Output: score ∈ ℝ  (from [CLS] linear head)
```

This joint encoding allows the model to compare query and document through every attention layer, capturing fine-grained relevance signals that a bi-encoder misses.

### Why Reranking Works

Bi-encoders compress everything into a single fixed vector — information bottleneck. Cross-encoders can directly compare "which word in the document answers this specific question." The accuracy gap is significant:

| System | TREC DL 2020 NDCG@10 | Latency per query |
|---|---|---|
| BM25 | 0.487 | <1 ms |
| Bi-encoder (DPR) | 0.611 | ~5 ms |
| BM25 → cross-encoder rerank | 0.682 | ~150 ms |
| Bi-encoder → cross-encoder | **0.714** | ~200 ms |

### Cross-encoder with sentence-transformers

```python
from sentence_transformers import CrossEncoder

# Load cross-encoder fine-tuned for MS-MARCO passage ranking
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)

query   = "What year was Python created?"
# Top-10 candidates from bi-encoder retrieval
candidates = [
    "Python was created by Guido van Rossum and first released in 1991.",
    "The Python programming language is known for its readability.",
    "Snakes of the genus Python are native to Africa and Asia.",
    "Python 3 was released in 2008 with major improvements.",
    "Guido van Rossum began working on Python in 1989.",
]

# Score all (query, document) pairs
pairs = [[query, doc] for doc in candidates]
scores = reranker.predict(pairs)       # [0.89, 0.73, 0.02, 0.81, 0.85]

# Sort by score
ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
for doc, score in ranked:
    print(f"{score:.3f}  {doc[:60]}")
```

---

## Full Bi-encoder + Reranking Pipeline

```python
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

# ─── Offline: Build index ────────────────────────────────────
bi_encoder = SentenceTransformer("all-MiniLM-L6-v2")

corpus = [...]  # your document chunks
corpus_embeddings = bi_encoder.encode(corpus, batch_size=64, normalize_embeddings=True)
corpus_embeddings = np.array(corpus_embeddings, dtype="float32")

# FAISS HNSW index — fast approximate nearest neighbor
dimension = corpus_embeddings.shape[1]   # 384
index = faiss.IndexHNSWFlat(dimension, 32)   # 32 neighbors per node
index.hnsw.efConstruction = 200
index.add(corpus_embeddings)

# ─── Online: Query ───────────────────────────────────────────
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def retrieve_and_rerank(query: str, top_k_retrieve: int = 50, top_k_rerank: int = 5):
    # Stage 1: Bi-encoder retrieval
    q_emb = bi_encoder.encode([query], normalize_embeddings=True).astype("float32")
    distances, indices = index.search(q_emb, top_k_retrieve)
    candidates = [corpus[i] for i in indices[0]]

    # Stage 2: Cross-encoder reranking
    pairs  = [[query, doc] for doc in candidates]
    scores = cross_encoder.predict(pairs)

    # Return top-k reranked
    ranked_indices = np.argsort(scores)[::-1][:top_k_rerank]
    return [(candidates[i], float(scores[i])) for i in ranked_indices]

results = retrieve_and_rerank("How does transformer attention work?")
```

---

## ColBERT: Late Interaction

ColBERT (Khattab & Zaharia, 2020) is a hybrid approach — it stores **all** token embeddings (not just the pooled vector), computing relevance via **MaxSim** aggregation:

$$\text{score}(q, d) = \sum_{i \in q} \max_{j \in d} \mathbf{E}_i \cdot \mathbf{E}_j$$

For each query token $i$, find the most similar document token $j$ (MaxSim), then sum. This preserves fine-grained token-level matching while still allowing fast indexing.

```python
# ColBERT via RAGatouille
from ragatouille import RAGPretrainedModel

RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")

# Index documents
RAG.index(
    collection=["Document 1 text", "Document 2 text", "Document 3 text"],
    index_name="my_index",
    max_document_length=180,
    split_documents=True,
)

# Search
results = RAG.search(query="What is attention in transformers?", k=5)
for r in results:
    print(r["score"], r["content"][:80])
```

### ColBERT Trade-offs

| | Bi-encoder | ColBERT | Cross-encoder |
|---|---|---|---|
| Storage per doc | 1 vector (384 dims) | ~180 vectors (128 dims each) | None (no precomputation) |
| Latency | <1 ms | ~5 ms | 50–200 ms |
| Accuracy | Good | Very good | Best |
| Scales to | Billions of docs | Hundreds of millions | Thousands (reranking only) |

---

## Retrieval Benchmarks (BEIR)

BEIR (Thakur et al., 2021) evaluates zero-shot retrieval across 18 heterogeneous datasets.

| Model | BEIR Average NDCG@10 |
|---|---|
| BM25 | 0.428 |
| DPR (bi-encoder) | 0.313 |
| SBERT all-mpnet-base-v2 | 0.434 |
| E5-base-v2 | 0.471 |
| BGE-large-en-v1.5 | 0.489 |
| ColBERT v2 | 0.497 |
| **E5-mistral-7b** | **0.567** |

*Note: Larger LLM-based embedding models (E5-mistral, SFR-Embedding) now top BEIR, but BERT-sized models remain preferred for latency-sensitive applications.*

---

## Design Decisions: Choosing Models

```
Corpus size < 1M docs:
  → all-MiniLM-L6-v2 bi-encoder + ms-marco cross-encoder reranker
  → Simple, fast, great for most RAG applications

Corpus size 1M–100M docs:
  → BGE-large-en-v1.5 or E5-large bi-encoder
  → FAISS IVF or HNSW index
  → Optional: BGE reranker (bge-reranker-large)

Corpus > 100M docs or multilingual:
  → Consider ColBERT with distributed index
  → For multilingual: paraphrase-multilingual-mpnet-base-v2

Highest-accuracy domain-specific:
  → Fine-tune bi-encoder on domain pairs + MS-MARCO cross-encoder reranker
```

---

## See Also

- [Sentence-BERT](./sbert) — bi-encoder architecture and training in detail
- [Retrieval Strategies](../rag/retrieval-strategies) — dense, sparse, hybrid retrieval patterns
- [Advanced RAG](../rag/advanced-rag) — how reranking fits into the full advanced pipeline
