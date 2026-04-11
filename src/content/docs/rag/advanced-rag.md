---
title: Advanced RAG
description: Pre- and post-retrieval optimizations for production RAG — query decomposition, step-back prompting, FLARE, parent document retrieval, contextual compression, and reranking pipelines.
sidebar:
  order: 9
---

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

---

## Post-Retrieval Optimizations

### 5. Reranking

Retrieve a broad set (top-50) with a fast method, then score each candidate with a cross-encoder and return only top-5. See [Retrieval Strategies — Reranking](../retrieval-strategies#7-cross-encoder-reranking) for full implementation.

```
Hybrid retrieval → top-50 candidates (fast)
Cross-encoder reranker → score all 50 pairs → top-5 (accurate)
LLM receives top-5 most relevant chunks
```

### 6. Contextual Compression

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

### 7. Long-Context Reordering (Lost in the Middle)

LLMs perform better when relevant context appears at the beginning or end of the prompt — not in the middle. If you pass multiple chunks, reorder them to put the most relevant at the top and bottom.

**Paper:** Liu et al., "Lost in the Middle: How Language Models Use Long Contexts" (2023)

```python
from langchain_community.document_transformers import LongContextReorder

reorder = LongContextReorder()
reordered_docs = reorder.transform_documents(retrieved_docs)
# Places most relevant docs at beginning and end, less relevant in middle
```

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
┌─────────────────────────────────┐
│  Pre-retrieval                  │
│  ① Query Rewriting              │
│  ② Step-back query              │
│  ③ Sub-question decomposition   │
└─────────────────────────────────┘
    │ 3-5 query variants
    ▼
┌─────────────────────────────────┐
│  Retrieval                      │
│  Hybrid (dense + BM25 + RRF)    │
│  Retrieve top-30 per query      │
└─────────────────────────────────┘
    │ up to 150 candidates
    ▼
┌─────────────────────────────────┐
│  Post-retrieval                 │
│  ① Deduplication                │
│  ② Cross-encoder reranking      │
│  ③ Long-context reordering      │
│  ④ Contextual compression       │
└─────────────────────────────────┘
    │ top-5 compressed chunks
    ▼
┌─────────────────────────────────┐
│  Generation                     │
│  LLM with structured prompt     │
│  + citations from metadata      │
└─────────────────────────────────┘
```

---

## See Also

- [Retrieval Strategies](../retrieval-strategies) — dense, sparse, hybrid, MMR, HyDE
- [Agentic RAG](../agentic-rag) — Self-RAG, CRAG, tool-calling, and routing
- [Evaluation](../evaluation) — how to measure if advanced optimizations actually help
- [RAG Types](../rag-types) — interactive comparison of naive vs advanced vs agentic
