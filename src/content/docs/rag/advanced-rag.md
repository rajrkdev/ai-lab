---
title: Advanced RAG
description: Complete 2025 guide — pre/post retrieval optimizations, RAG-Fusion, HyDE, Proposition Indexing, RAPTOR, FLARE, contextual compression, and reranking pipelines for production RAG systems.
sidebar:
  order: 9
---

> **Current as of April 2026.**

## What Is "Advanced RAG"?

Advanced RAG adds **pre-retrieval** (query optimization before searching) and **post-retrieval** (result refinement after searching) stages to the basic naive pipeline.

```
Naive RAG:     query → embed → retrieve top-k → LLM
Advanced RAG:  query → [pre-retrieval] → retrieve → [post-retrieval] → LLM
```

The goal: improve retrieval precision and recall without changing the underlying vector store.

---

## Pre-Retrieval Optimizations

### 1. Query Rewriting

User queries are often ambiguous, conversational, or poorly formed. An LLM rewrites the query into a cleaner, more searching-friendly version.

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a query optimization assistant. Rewrite the user's question into a precise, search-optimized query. Preserve all intent. Output only the rewritten query."),
    ("human", "{question}"),
])

rewrite_chain = rewrite_prompt | llm | StrOutputParser()

original = "um, how does the thing with keys work in python dictionaries?"
rewritten = rewrite_chain.invoke({"question": original})
# → "How does key hashing and lookup work in Python dictionaries?"
```

### 2. Step-Back Prompting

Instead of answering the specific question directly, first ask a broader "step-back" question and retrieve context for both. The broader query often surfaces foundational information missed by a narrow search.

**Paper:** Zheng et al., "Take a Step Back: Evoking Reasoning via Abstraction in Large Language Models" (2023)

```
Original:    "What was the temperature at Cape Canaveral on January 28, 1986?"
Step-back:   "What are the temperature and weather conditions relevant to the Challenger disaster?"
```

```python
stepback_prompt = ChatPromptTemplate.from_messages([
    ("system", "Your task is to step back and paraphrase a question to a more generic step-back question which is easier to answer. Here are some examples:\nOriginal: What happens to the volume of water when it freezes?\nStep-back: What are the physical properties of water during phase transitions?\n"),
    ("human", "{question}"),
])

stepback_chain = stepback_prompt | llm | StrOutputParser()

from langchain_core.runnables import RunnableParallel, RunnablePassthrough

full_chain = (
    RunnableParallel(
        original=RunnablePassthrough(),
        stepback=stepback_chain,
    )
    | (lambda x: {
        "context": (
            retriever.invoke(x["original"]["question"]) +
            retriever.invoke(x["stepback"])
        ),
        "question": x["original"]["question"],
    })
    | answer_chain
)
```

### 3. Query Decomposition / Sub-question Generation

For multi-hop questions that require synthesizing information from multiple documents, decompose into simpler sub-questions, retrieve for each, and synthesize.

```
Complex:   "Compare the environmental impact and cost of solar vs. nuclear energy."
Sub-q 1:   "What are the environmental impacts of solar energy?"
Sub-q 2:   "What are the environmental impacts of nuclear energy?"
Sub-q 3:   "What is the cost per kWh for solar energy?"
Sub-q 4:   "What is the cost per kWh for nuclear energy?"
```

```python
from langchain.retrievers.multi_query import MultiQueryRetriever

decompose_prompt = ChatPromptTemplate.from_messages([
    ("system", "Decompose the following question into 2-4 simpler sub-questions that together answer the original. Output one sub-question per line."),
    ("human", "{question}"),
])

def decompose_and_retrieve(question: str) -> list:
    raw = (decompose_prompt | llm | StrOutputParser()).invoke({"question": question})
    sub_questions = [q.strip() for q in raw.strip().split("\n") if q.strip()]
    all_docs = []
    for sq in sub_questions:
        all_docs.extend(retriever.invoke(sq))
    return deduplicate(all_docs)
```

### 4. Multi-Query Retrieval

Generate 3 semantically varied reformulations of the query, retrieve documents for each, and take the union (deduplicated). This increases recall by avoiding the vocabulary mismatch between a single phrasing and indexed documents.

```python
from langchain.retrievers.multi_query import MultiQueryRetriever

multi_retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    llm=llm,
)
# Automatically generates 3 query variants and retrieves for each
docs = multi_retriever.invoke("How does BERT's attention mechanism work?")
```

### 5. RAG-Fusion

**Paper / Implementation:** Zackary Rackauckas, "RAG-Fusion" (2023)

RAG-Fusion extends multi-query retrieval with **Reciprocal Rank Fusion (RRF)** to merge ranked result lists from multiple queries — rather than a naive union. Documents that rank highly across multiple query variants get promoted; one-off matches get demoted.

```
Query
  ↓
Generate N query variants (LLM)
  ↓
Retrieve top-K per variant (parallel)
  ↓
       Query 1 results: [D3, D1, D5, D2, D7]
       Query 2 results: [D1, D3, D8, D5, D4]
       Query 3 results: [D3, D5, D1, D9, D2]
  ↓
RRF score = Σ 1/(rank + 60) for each doc across lists
  ↓
       D3: 1/61 + 1/62 + 1/61 = 0.0491   (top across all)
       D1: 1/62 + 1/61 + 1/63 = 0.0484
       D5: 1/63 + 1/64 + 1/62 = 0.0474
  ↓
Return re-ranked fused list → LLM
```

```python
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.documents import Document

def reciprocal_rank_fusion(results: list[list[Document]], k: int = 60) -> list[Document]:
    """Fuse multiple ranked result lists using RRF."""
    scores: dict[str, float] = {}
    doc_map: dict[str, Document] = {}

    for result_list in results:
        for rank, doc in enumerate(result_list):
            # Use content hash as dedup key
            doc_id = hash(doc.page_content[:200])
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rank + k)
            doc_map[doc_id] = doc

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_map[doc_id] for doc_id, _ in ranked]

def rag_fusion_retrieve(question: str, retriever, llm, n_queries: int = 4, top_k: int = 5) -> list[Document]:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    query_gen_prompt = ChatPromptTemplate.from_messages([
        ("system", f"Generate {n_queries} different search queries for the same information need. Output one query per line, no numbering."),
        ("human", "{question}"),
    ])
    query_gen = query_gen_prompt | llm | StrOutputParser()

    # Generate query variants
    raw = query_gen.invoke({"question": question})
    queries = [question] + [q.strip() for q in raw.strip().split("\n") if q.strip()]

    # Retrieve in parallel for each query
    all_results = [retriever.invoke(q) for q in queries[:n_queries + 1]]

    # Fuse with RRF
    fused = reciprocal_rank_fusion(all_results)
    return fused[:top_k]

# Usage
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
docs = rag_fusion_retrieve("How does transformer attention scale with sequence length?", retriever, llm)
```

### 6. HyDE — Hypothetical Document Embeddings

**Paper:** Gao et al., "Precise Zero-Shot Dense Retrieval without Relevance Labels" (2022)

The core problem: a user query ("what is X?") is semantically distant from documents that answer it ("X is defined as…"). HyDE bridges this gap by asking the LLM to generate a **hypothetical document** that would answer the query, then embedding that document for retrieval — matching document-to-document rather than query-to-document.

```
Standard:  embed("What causes inflation?") → retrieve by similarity to query vector
HyDE:      LLM generates hypothetical answer →
           embed("Inflation is caused by excess money supply relative to goods,
                  typically triggered by central bank policy…") →
           retrieve by similarity to answer vector
```

```python
from langchain.retrievers import HypotheticalDocumentEmbedder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# LangChain built-in HyDE retriever
hyde_embeddings = HypotheticalDocumentEmbedder.from_llm(
    llm=llm,
    embeddings=embeddings,
    n=1,   # number of hypothetical docs to generate (averaged)
)

# Drop-in replacement for standard embeddings in any vector store retriever
hyde_retriever = vectorstore.as_retriever(
    search_kwargs={"k": 5},
    # Uses hyde_embeddings.embed_query() which generates hypothetical doc first
)
```

**Manual HyDE implementation with Anthropic SDK:**

```python
import anthropic
import numpy as np

client = anthropic.Anthropic()

def hyde_embed(query: str, embedder) -> np.ndarray:
    """Generate a hypothetical answer and embed it."""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": f"""Write a short factual passage (2-3 sentences) that would directly answer this question.
Write as if it's an excerpt from a reference document.
Question: {query}
Answer:"""
        }]
    )
    hypothetical_doc = response.content[0].text
    return np.array(embedder.embed_query(hypothetical_doc))

def hyde_retrieve(query: str, embedder, vectorstore, k: int = 5):
    hyp_embedding = hyde_embed(query, embedder)
    # Search using hypothetical doc embedding instead of query embedding
    return vectorstore.similarity_search_by_vector(hyp_embedding, k=k)
```

**When HyDE helps vs. hurts:**

| Scenario | HyDE Effect |
|---|---|
| Domain mismatch (query style ≠ doc style) | Significant gain |
| Technical questions from non-experts | Gain — LLM produces expert phrasing |
| Short factual queries with clear vocabulary | Minimal gain |
| Ambiguous queries | Risk — LLM may hallucinate wrong hypothetical |
| Real-time or rapidly changing information | Risk — hallucinated facts misdirect search |

---

## Post-Retrieval Optimizations

### 7. Reranking

Retrieve a broad set (top-50) with a fast method, then score each candidate with a cross-encoder and return only top-5. See [Retrieval Strategies — Reranking](../retrieval-strategies#7-cross-encoder-reranking) for full implementation.

```
Hybrid retrieval → top-50 candidates (fast)
Cross-encoder reranker → score all 50 pairs → top-5 (accurate)
LLM receives top-5 most relevant chunks
```

### 8. Contextual Compression

After retrieval, extract only the sentences directly relevant to the query from each chunk, reducing noise for the LLM.

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor, EmbeddingsFilter

# Option A: LLM extraction (slower, more accurate)
llm_compressor = LLMChainExtractor.from_llm(llm)

# Option B: Embedding filter (fast, removes off-topic sentences)
embeddings_filter = EmbeddingsFilter(
    embeddings=embedding_model,
    similarity_threshold=0.76,   # keep sentences above this cosine similarity to query
)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=embeddings_filter,   # or llm_compressor
    base_retriever=retriever,
)
```

### 9. Long-Context Reordering (Lost in the Middle)

LLMs perform better when relevant context appears at the beginning or end of the prompt — not in the middle. If you pass multiple chunks, reorder them to put the most relevant at the top and bottom.

**Paper:** Liu et al., "Lost in the Middle: How Language Models Use Long Contexts" (2023)

```python
from langchain_community.document_transformers import LongContextReorder

reorder = LongContextReorder()
reordered_docs = reorder.transform_documents(retrieved_docs)
# Places most relevant docs at beginning and end, less relevant in middle
```

---

## Proposition Indexing (Dense X Retrieval)

**Paper:** Chen et al., "Dense X Retrieval: What Retrieval Granularity Should We Use?" (2023)

Standard chunking splits text by token count or paragraph boundaries — often leaving atomic facts split across chunks. **Proposition indexing** decomposes each chunk into **propositions**: self-contained, atomic, single-fact statements. These are indexed instead of (or alongside) raw chunks.

### Standard Chunk vs. Proposition Index

```
Standard chunk (1 node in index):
  "BERT was introduced by Devlin et al. in 2018. It uses bidirectional
   transformers trained on masked language modeling and next sentence
   prediction tasks. BERT achieved state-of-the-art results on 11
   NLP tasks upon release."

Proposition index (3 nodes, each retrievable individually):
  P1: "BERT was introduced by Devlin et al. in 2018."
  P2: "BERT uses bidirectional transformers trained on masked language
       modeling and next sentence prediction."
  P3: "BERT achieved state-of-the-art results on 11 NLP tasks upon release."
```

When a query asks "When was BERT introduced?", proposition P1 has near-perfect similarity to the query — far higher than the whole chunk average. The parent chunk is returned for full context, but retrieved via the precise proposition.

```python
from anthropic import Anthropic
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

client = Anthropic()
embedder = OpenAIEmbeddings(model="text-embedding-3-large")

def extract_propositions(chunk: str) -> list[str]:
    """Decompose a text chunk into atomic propositions."""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Decompose the following passage into a list of atomic propositions.
Each proposition must:
- Be a single self-contained fact (one sentence)
- Be understandable without additional context
- Preserve all key entities, numbers, and relationships
- Not introduce facts not present in the original text

Passage:
{chunk}

Return one proposition per line, no numbering or bullets:"""
        }]
    )
    return [line.strip() for line in response.content[0].text.strip().split("\n") if line.strip()]

def build_proposition_index(documents: list[Document]) -> tuple[FAISS, dict[str, str]]:
    """Build a vector index over propositions, with mapping back to parent chunks."""
    proposition_docs = []
    prop_to_parent: dict[str, str] = {}

    for doc in documents:
        propositions = extract_propositions(doc.page_content)
        for prop in propositions:
            prop_doc = Document(
                page_content=prop,
                metadata={**doc.metadata, "parent_content": doc.page_content},
            )
            proposition_docs.append(prop_doc)
            prop_to_parent[prop] = doc.page_content

    vectorstore = FAISS.from_documents(proposition_docs, embedder)
    return vectorstore, prop_to_parent

def proposition_retrieve(query: str, prop_vectorstore: FAISS, k: int = 5) -> list[Document]:
    """Retrieve by proposition similarity, return parent chunks (deduped)."""
    prop_hits = prop_vectorstore.similarity_search(query, k=k * 2)
    seen, results = set(), []
    for hit in prop_hits:
        parent = hit.metadata.get("parent_content", hit.page_content)
        if parent not in seen:
            seen.add(parent)
            results.append(Document(page_content=parent, metadata=hit.metadata))
        if len(results) == k:
            break
    return results

# Build
prop_store, _ = build_proposition_index(raw_documents)

# Query
docs = proposition_retrieve("When was BERT released?", prop_store)
```

**Proposition Indexing vs. Standard Chunking:**

| Metric | Standard chunks | Proposition Index |
|---|---|---|
| Index size | 1× | ~3-5× more nodes |
| Retrieval precision | Moderate | High (atomic matching) |
| Build cost | Low | High (LLM per chunk) |
| Build time | Fast | Slow |
| Best for | General use | Precision-critical, fact-dense docs |

---

## FLARE — Forward-Looking Active Retrieval

**Paper:** Jiang et al., "Active Retrieval Augmented Generation" (2023)

Unlike standard RAG which retrieves only once before generation, FLARE retrieves **iteratively during generation** — when the model is about to generate uncertain tokens, it pauses, retrieves more context, and continues.

**Algorithm:**
1. Generate text token-by-token (or sentence-by-sentence)
2. After each sentence, check confidence: if any token has probability < threshold, mark the sentence as "uncertain"
3. Use the uncertain sentence as a new retrieval query
4. Retrieve additional context
5. Regenerate the uncertain sentence with the new context
6. Continue

```python
from langchain.chains import FlareChain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

llm = ChatOpenAI(model="gpt-4o", temperature=0)
vectorstore = FAISS.load_local("corpus", OpenAIEmbeddings())

flare = FlareChain.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    max_generation_len=164,
    min_prob=0.2,   # retrieve when any token prob < 0.2
)

response = flare.invoke({"question": "Explain the history of quantum computing."})
```

**When FLARE is best:**
- Long-form generation requiring multiple facts
- Documents too large to retrieve all at once
- Topics where uncertainty is high (historical, technical)

---

## RAPTOR — Recursive Abstractive Processing for Tree-Organized Retrieval

**Paper:** Sarthi et al., "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval" (2024)

RAPTOR builds a **hierarchical tree** of summaries from the bottom up:

1. Chunk documents (leaf nodes)
2. Cluster semantically similar chunks
3. Summarize each cluster → intermediate nodes
4. Repeat clustering/summarizing on summaries → higher nodes
5. At retrieval time, search across all levels of the hierarchy

This allows retrieval of both fine-grained chunks (for specific facts) and high-level summaries (for abstract questions), in a single index.

```python
from langchain_community.document_loaders import DirectoryLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import numpy as np
from sklearn.mixture import GaussianMixture

# Simplified RAPTOR cluster+summarize loop
def raptor_cluster_summarize(embeddings, texts, llm, level=0, max_levels=3):
    if level >= max_levels or len(texts) <= 1:
        return texts

    # Cluster
    n_clusters = max(1, len(texts) // 10)
    gm = GaussianMixture(n_components=n_clusters, covariance_type="full")
    labels = gm.fit_predict(embeddings)

    # Summarize each cluster
    summaries = []
    for cluster_id in range(n_clusters):
        cluster_texts = [t for t, l in zip(texts, labels) if l == cluster_id]
        summary = llm.invoke(f"Summarize these texts concisely:\n" + "\n---\n".join(cluster_texts))
        summaries.append(summary.content)

    # Recurse on summaries
    summary_embeddings = np.array([embed(s) for s in summaries])
    return texts + raptor_cluster_summarize(summary_embeddings, summaries, llm, level+1)
```

---

## Corrective RAG (CRAG)

**Paper:** Yan et al., "Corrective Retrieval Augmented Generation" (2024)

CRAG evaluates retrieval quality using a relevance classifier. If retrieved documents are irrelevant, it falls back to a web search (or alternative knowledge source) before generation.

```python
from langchain.schema import Document

def evaluate_relevance(query: str, docs: list[Document]) -> str:
    """Returns 'CORRECT', 'INCORRECT', or 'AMBIGUOUS'"""
    prompt = f"Question: {query}\nDocuments: {[d.page_content[:200] for d in docs]}\nAre these documents relevant? Answer: CORRECT, INCORRECT, or AMBIGUOUS."
    return llm.invoke(prompt).content.strip()

def crag_retrieve(query: str) -> list[Document]:
    docs = retriever.invoke(query)
    relevance = evaluate_relevance(query, docs)

    if relevance == "CORRECT":
        return docs
    elif relevance == "INCORRECT":
        # Fall back to web search
        return web_search_retriever.invoke(query)
    else:  # AMBIGUOUS
        # Combine both
        return docs + web_search_retriever.invoke(query)
```

---

## Advanced RAG Architecture Pattern

A production advanced RAG pipeline combining the above techniques:

```
User Query
    │
    ▼
┌──────────────────────────────────────┐
│  Pre-retrieval                       │
│  ① Query Rewriting (clean phrasing)  │
│  ② HyDE (doc-to-doc matching)        │
│  ③ Step-back (broader context)       │
│  ④ RAG-Fusion (N query variants)     │
│  ⑤ Sub-question decomposition        │
└──────────────────────────────────────┘
    │ 4-6 query variants + hypothetical doc
    ▼
┌──────────────────────────────────────┐
│  Retrieval                           │
│  Index type: Proposition or RAPTOR   │
│  Hybrid (dense + BM25 + RRF)         │
│  Retrieve top-30 per variant         │
└──────────────────────────────────────┘
    │ up to 150 candidates
    ▼
┌──────────────────────────────────────┐
│  Post-retrieval                      │
│  ① RRF fusion across query variants  │
│  ② Deduplication                     │
│  ③ Cross-encoder reranking           │
│  ④ Long-context reordering           │
│  ⑤ Contextual compression            │
└──────────────────────────────────────┘
    │ top-5 compressed chunks
    ▼
┌──────────────────────────────────────┐
│  Generation                          │
│  LLM with structured prompt          │
│  + citations from metadata           │
│  FLARE: re-retrieve on uncertainty   │
└──────────────────────────────────────┘
```

### Technique Selection Guide

| Scenario | Recommended techniques |
|---|---|
| Poorly phrased user queries | Query Rewriting, Multi-Query |
| Vocabulary mismatch (user ≠ docs) | HyDE, Step-back |
| Multi-hop factual questions | Query Decomposition, RAG-Fusion |
| Fact-dense structured documents | Proposition Indexing |
| Large document corpora | RAPTOR (hierarchical) |
| Long-form generation tasks | FLARE |
| Unreliable vector retrieval | CRAG (web fallback) |
| Production: mixed query types | Query Rewriting + Hybrid + Reranking |

---

## See Also

- [Retrieval Strategies](../retrieval-strategies) — dense, sparse, hybrid, MMR, HyDE
- [Agentic RAG](../agentic-rag) — Self-RAG, CRAG, tool-calling, and routing
- [Evaluation](../evaluation) — how to measure if advanced optimizations actually help
- [RAG Types](../rag-types) — interactive comparison of naive vs advanced vs agentic
