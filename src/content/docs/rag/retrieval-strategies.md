---
title: Retrieval Strategies
description: Complete guide to RAG retrieval — dense vector search, BM25 sparse retrieval, hybrid RRF fusion, HyDE, MMR, and cross-encoder reranking — with code examples and performance benchmarks.
sidebar:
  order: 7
---

## Retrieval Overview

Retrieval is the core of RAG — it determines what context the LLM sees. A bad retriever guarantees a bad answer. A good retriever makes the generator's job easy.

The retrieval pipeline has evolved from basic cosine similarity to multi-stage hybrid systems. This page covers each strategy, when to use it, and how to implement it.

---

## 1. Dense Retrieval (Vector Search)

The baseline: embed query and documents with the same model, retrieve by cosine similarity.

$$\text{score}(q, d) = \frac{\mathbf{q} \cdot \mathbf{d}}{\|\mathbf{q}\| \|\mathbf{d}\|}$$

**Strengths:** Semantic understanding — finds paraphrases, synonyms, related concepts.  
**Weaknesses:** Poor at exact phrase matching ("CVE-2024-43573"), rare terms, proper nouns.

```python
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5")
vectorstore = FAISS.load_local("my_index", embeddings, allow_dangerous_deserialization=True)

# Basic dense retrieval
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 10},
)

docs = retriever.invoke("What is the refund policy?")
```

---

## 2. Sparse Retrieval — BM25

**BM25** (Best Match 25) is the standard keyword-based retrieval algorithm used by search engines (Elasticsearch, Solr, Lucene). It scores documents based on term frequency (TF) with saturation and inverse document frequency (IDF).

$$\text{BM25}(q, d) = \sum_{t \in q} \text{IDF}(t) \cdot \frac{f(t,d) \cdot (k_1 + 1)}{f(t,d) + k_1 \cdot \left(1 - b + b \cdot \frac{|d|}{\text{avgdl}}\right)}$$

| Parameter | Typical value | Effect |
|---|---|---|
| $k_1$ | 1.2–2.0 | TF saturation (higher = slower saturation) |
| $b$ | 0.75 | Document length normalization (0 = none, 1 = full) |

**Strengths:** Exact phrase matching, rare terms, proper nouns, IDs, error codes.  
**Weaknesses:** Zero understanding of synonyms or semantics.

```python
# BM25 with LangChain + rank_bm25
from langchain_community.retrievers import BM25Retriever

# Build BM25 index from documents
bm25_retriever = BM25Retriever.from_documents(docs, k=10)
bm25_retriever.k = 10

results = bm25_retriever.invoke("CVE-2024-43573 vulnerability fix")
```

### BM25 with Elasticsearch

```python
from langchain_elasticsearch import ElasticsearchStore

es_store = ElasticsearchStore(
    es_url="http://localhost:9200",
    index_name="rag_docs",
    query_field="text",
    vector_query_field="embedding",
    embedding=embeddings,
    strategy=ElasticsearchStore.BM25RetrievalStrategy(),
)
```

---

## 3. Hybrid Retrieval

The best of both worlds: dense retrieval catches semantic matches, BM25 catches keyword matches. Hybrid retrieval with **Reciprocal Rank Fusion (RRF)** is the standard production approach.

### Reciprocal Rank Fusion (RRF)

Given results ranked by two (or more) retrievers, RRF assigns a combined score:

$$\text{RRF}(d) = \sum_{r \in R} \frac{1}{k + \text{rank}_r(d)}$$

where $R$ is the set of retrievers, $\text{rank}_r(d)$ is the position of document $d$ in retriever $r$'s ranking, and $k = 60$ is a smoothing constant.

**Why RRF?** It's robust to outlier scores — you don't need to normalize scores across different retrievers. A document ranked #1 by dense and #3 by BM25 gets a high combined score regardless of the raw similarity values.

```python
from langchain.retrievers import EnsembleRetriever

# Dense retriever
dense_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# BM25 retriever
bm25_retriever = BM25Retriever.from_documents(all_docs, k=10)

# RRF ensemble (50/50 weight by default)
hybrid_retriever = EnsembleRetriever(
    retrievers=[dense_retriever, bm25_retriever],
    weights=[0.6, 0.4],   # customize: 0.6 for dense (semantic), 0.4 for BM25 (keyword)
)

results = hybrid_retriever.invoke("Python memory management garbage collection")
```

### Weaviate Hybrid Search

Weaviate implements hybrid natively with the `alpha` parameter:

```python
results = collection.query.hybrid(
    query="memory management",
    alpha=0.75,          # 0 = BM25 only, 1 = vector only
    limit=10,
)
```

---

## 4. HyDE — Hypothetical Document Embeddings

**Paper:** Gao et al., "Precise Zero-Shot Dense Retrieval without Relevance Labels" (2022)

Instead of directly embedding the user's query (often short and ambiguous), ask an LLM to generate a **hypothetical answer document**, then embed that document to search the corpus.

```
User query: "What causes the seasons?"
          ↓ LLM generates
Hypothetical: "The seasons are caused by Earth's axial tilt of 23.5 degrees.
               As the Earth orbits the Sun, the tilt means different hemispheres
               receive more direct sunlight at different times of year..."
          ↓ embed the hypothetical document
          ... retrieve real documents with similar embedding
```

The hypothetical document's embedding is closer to real relevant documents than the short query embedding is.

```python
from langchain.retrievers import HyDEDocumentChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

hyde_prompt = ChatPromptTemplate.from_template(
    "Write a paragraph that would answer this question: {question}"
)

hyde_chain = (
    hyde_prompt
    | llm
    | StrOutputParser()
    | vectorstore.as_retriever(search_kwargs={"k": 5})
)

# The chain: generates hypothetical doc → embeds it → retrieves real docs
results = hyde_chain.invoke({"question": "What causes the seasons?"})
```

**When HyDE helps:**
- Queries are very short (< 5 words)
- Domain-specific terminology where queries use different vocabulary than documents
- Cross-lingual retrieval

**When HyDE hurts:**
- Factual queries where hallucination could mislead (the generated hypothesis may be wrong)
- Very fast latency requirements (one extra LLM call)

---

## 5. Multi-Query Retrieval

Generate multiple reformulations of the user's query, retrieve for each, and deduplicate results. Reduces the chance that a single phrasing misses relevant documents.

```python
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

multi_retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    llm=llm,
)
# Internally generates 3 variations of the query, retrieves for each, deduplicates
docs = multi_retriever.invoke("How does attention work in BERT?")
```

Default prompt generates 3 variations. You can also provide a custom prompt.

---

## 6. MMR — Maximal Marginal Relevance

Standard similarity retrieval returns the top-k most similar chunks — which often cluster around the same information. MMR balances **relevance** against **diversity**:

$$\text{MMR}(d) = \arg\max_{d_i \in C \setminus S} \left[\lambda \cdot \text{sim}(q, d_i) - (1-\lambda) \cdot \max_{d_j \in S} \text{sim}(d_i, d_j)\right]$$

- $S$: already selected documents
- $C \setminus S$: candidates not yet selected
- $\lambda$: trade-off (λ=1 is pure similarity, λ=0 is pure diversity)

```python
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5,
        "fetch_k": 20,   # fetch 20 candidates, MMR selects best 5
        "lambda_mult": 0.7,  # 0 = max diversity, 1 = max relevance
    },
)
```

**Use when:** The corpus has many near-duplicate chunks (e.g., repeated policy boilerplate), and you don't want all 5 retrieved chunks to be the same paragraph.

---

## 7. Cross-Encoder Reranking

A two-stage pattern: first retrieve broadly with a fast method (bi-encoder, BM25, or hybrid), then rerank the candidate list with a more accurate cross-encoder.

```
Stage 1: Hybrid retrieval → top-50 candidates (fast, ~5ms)
Stage 2: Cross-encoder reranking → top-5 (accurate, ~100ms)
```

```python
from sentence_transformers import CrossEncoder
from langchain_core.documents import Document

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)

def rerank(query: str, docs: list[Document], top_n: int = 5) -> list[Document]:
    pairs  = [(query, doc.page_content) for doc in docs]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in ranked[:top_n]]

# Usage: first retrieve 30, then rerank to top 5
candidates = hybrid_retriever.invoke(query)   # 30 docs
final_docs  = rerank(query, candidates, top_n=5)
```

### BGE Reranker (stronger)

```python
from FlagEmbedding import FlagReranker

reranker = FlagReranker("BAAI/bge-reranker-large", use_fp16=True)
pairs = [[query, doc.page_content] for doc in candidates]
scores = reranker.compute_score(pairs)
```

---

## 8. Contextual Compression

After retrieval, extract only the relevant sentences from each chunk instead of passing the full chunk:

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
compressor = LLMChainExtractor.from_llm(llm)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=hybrid_retriever,
)

# Returns only the relevant sentences extracted from each chunk
compressed_docs = compression_retriever.invoke("What is the refund deadline?")
```

---

## Combining Strategies: Production Pipeline

```python
# Recommended production retrieval pipeline

# 1. Multi-query expansion
queries = generate_queries(user_question)  # 3 query variants

# 2. Hybrid retrieval for each query
all_candidates = []
for q in queries:
    all_candidates += hybrid_retriever.invoke(q)

# 3. Deduplicate by document ID
seen_ids = set()
unique_candidates = []
for doc in all_candidates:
    doc_id = doc.metadata.get("doc_id") or doc.page_content[:50]
    if doc_id not in seen_ids:
        unique_candidates.append(doc)
        seen_ids.add(doc_id)

# 4. Cross-encoder rerank
final_docs = rerank(user_question, unique_candidates, top_n=5)

# 5. Generate
answer = llm.invoke(build_prompt(user_question, final_docs))
```

---

## Retrieval Strategy Comparison

| Strategy | Recall | Precision | Latency | Complexity | Best for |
|---|---|---|---|---|---|
| Dense (bi-encoder) | High | Medium | Very fast | Low | Prototypes, semantic queries |
| BM25 | Medium | High (keywords) | Very fast | Low | Exact terms, IDs, code |
| Hybrid (RRF) | Very high | High | Fast | Medium | Production |
| HyDE | High | Medium | Medium (+LLM) | Medium | Short/ambiguous queries |
| Multi-query | Very high | Medium | Medium (+LLM) | Medium | Broad topics |
| MMR | High | Medium | Fast | Low | Diverse sources needed |
| Reranking | Very high | Very high | Slow (+model) | High | Quality-critical |

---

## See Also

- [Embedding Models](./embedding-models) — choosing the bi-encoder
- [Vector Stores](./vector-stores) — FAISS, Weaviate, Qdrant implementations
- [Advanced RAG](./advanced-rag) — query rewriting, FLARE, step-back prompting
- [BERT in RAG](../bert/bert-in-rag) — bi-encoder vs cross-encoder architecture details
