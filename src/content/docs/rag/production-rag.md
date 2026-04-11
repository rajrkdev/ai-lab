---
title: Production RAG
description: Operating RAG systems at scale — latency optimization, semantic caching, async retrieval, cost control, observability, guardrails, and CI/CD for RAG pipelines.
sidebar:
  order: 12
---

## Production RAG vs Prototype RAG

A RAG proof-of-concept works end-to-end in hours. A production RAG system must handle:

- **Latency SLAs:** p99 < 3 seconds for interactive applications
- **Cost at scale:** 1M queries/month at $0.001/query vs $0.10/query is a 100× cost difference
- **Reliability:** graceful degradation when retrieval returns poor results
- **Observability:** knowing *why* an answer was wrong
- **Safety:** preventing prompt injection, topic drift, and harmful outputs

---

## Latency Budget

Profile every step to find the bottleneck. A typical advanced RAG call:

| Step | Latency (p50) | Optimization target |
|---|---|---|
| Query embedding | 5–20 ms | GPU acceleration, cached |
| Vector search (HNSW) | 2–10 ms | Usually fast already |
| Reranking (cross-encoder) | 50–200 ms | Batch size, smaller model |
| LLM generation (gpt-4o) | 500–2000 ms | **Biggest bottleneck** |
| LLM generation (local) | 200–800 ms | GPU, quantization |

**Total:** typical end-to-end p50 is 800ms–3s. Most latency is in LLM generation.

---

## 1. Semantic Caching

Cache LLM responses for semantically similar (not just identical) queries. If a new query is within cosine distance threshold of a cached query, return the cached answer.

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.globals import set_llm_cache
from langchain_community.cache import GPTCache
from gptcache import cache
from gptcache.adapter.api import init_similar_cache

# Initialize semantic cache (uses FAISS internally)
init_similar_cache(
    data_manager_dir="./gptcache_data",
    threshold=0.85,   # cosine similarity threshold: queries above this share a cached response
)
set_llm_cache(GPTCache(init_similar_cache))

llm = ChatOpenAI(model="gpt-4o")

# First call: hits LLM (~800ms)
r1 = llm.invoke("What is BERT?")

# Semantically similar query: hits cache (<5ms)
r2 = llm.invoke("Can you explain what BERT is?")   # ← cache hit
r3 = llm.invoke("Describe the BERT model")          # ← cache hit
```

### Custom Redis Semantic Cache

For production multi-instance deployment, use Redis as the cache backend:

```python
from langchain_community.cache import RedisSemanticCache
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.globals import set_llm_cache

embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

set_llm_cache(RedisSemanticCache(
    redis_url="redis://localhost:6379",
    embedding=embedding,
    score_threshold=0.2,  # Redis uses cosine distance (lower = more similar)
))
```

---

## 2. Embedding Cache

Caching query embeddings avoids re-encoding the same queries. Since embedding is fast, prioritize caching document corpus embeddings — recomputing 1M chunks on re-index is expensive.

```python
from langchain.storage import LocalFileStore
from langchain_community.embeddings import CacheBackedEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

base_embedder = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5")
store = LocalFileStore("./embedding_cache")

# Automatically caches embeddings by content hash
cached_embedder = CacheBackedEmbeddings.from_bytes_store(
    base_embedder,
    store,
    namespace=base_embedder.model_name,
)

# First call: computes embeddings
vstore = FAISS.from_documents(docs, cached_embedder)

# Re-run: loads from disk cache (near-zero cost)
vstore2 = FAISS.from_documents(docs, cached_embedder)
```

---

## 3. Async and Parallel Retrieval

For pipelines that search multiple sources (vector store + BM25 + web), run retrievals in parallel:

```python
import asyncio
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

async def parallel_retrieve(query: str) -> list:
    """Retrieve from multiple sources concurrently."""
    dense_task  = asyncio.create_task(vectorstore.asimilarity_search(query, k=10))
    sparse_task = asyncio.create_task(bm25_retriever.ainvoke(query))
    web_task    = asyncio.create_task(web_search_tool.ainvoke(query))

    dense_docs, sparse_docs, web_docs = await asyncio.gather(
        dense_task, sparse_task, web_task,
        return_exceptions=True,  # don't fail everything if one source fails
    )

    # Handle exceptions gracefully
    all_docs = []
    for result in [dense_docs, sparse_docs, web_docs]:
        if isinstance(result, Exception):
            continue   # skip failed sources
        all_docs.extend(result)

    return deduplicate(all_docs)
```

### Async LangChain Chain

```python
from langchain_core.runnables import RunnableParallel

# Run retrieval and query rewriting in parallel
parallel_steps = RunnableParallel(
    docs=retriever,
    rewritten_query=rewrite_chain,
)

chain = parallel_steps | combine_and_generate

# Async streaming
async for chunk in chain.astream("What is the refund policy?"):
    print(chunk, end="", flush=True)
```

---

## 4. Streaming Responses

Never make users wait for the full response when streaming is available:

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import sys

llm = ChatOpenAI(model="gpt-4o", streaming=True)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | ChatPromptTemplate.from_template(
        "Answer based on context:\n\n{context}\n\nQuestion: {question}"
    )
    | llm
    | StrOutputParser()
)

# Stream tokens as they arrive
for token in rag_chain.stream("What is HNSW?"):
    sys.stdout.write(token)
    sys.stdout.flush()
```

---

## 5. Cost Optimization

### Model Tiering

Route queries to cheaper models when expensive models are unnecessary:

```python
from langchain_openai import ChatOpenAI

def tiered_llm(query: str, context: str) -> str:
    # Classify query complexity
    complexity_score = estimate_complexity(query)

    if complexity_score < 0.4:
        # Simple factual → cheap fast model
        llm = ChatOpenAI(model="gpt-4o-mini")
    elif complexity_score < 0.8:
        # Medium → balanced model
        llm = ChatOpenAI(model="gpt-4o")
    else:
        # Complex reasoning → best model
        llm = ChatOpenAI(model="o3")

    return llm.invoke(f"Context: {context}\n\nQuestion: {query}").content
```

### Chunk Size vs Cost Trade-off

Smaller chunks → smaller context window → fewer tokens → lower cost. But too small loses context. Use `k × chunk_size` to estimate token cost:

```python
# Cost estimation
def estimate_cost(
    chunks: list[str],
    k: int = 5,
    model: str = "gpt-4o",
    queries_per_day: int = 10_000,
) -> float:
    avg_chunk_tokens = sum(len(c.split()) * 1.3 for c in chunks[:100]) / min(100, len(chunks))
    tokens_per_query = k * avg_chunk_tokens + 500  # 500 for prompt + question
    tokens_per_day   = tokens_per_query * queries_per_day
    # gpt-4o: $2.50/1M input tokens, $10/1M output tokens
    input_cost_per_day = (tokens_per_day / 1_000_000) * 2.50
    return input_cost_per_day

print(f"Estimated input cost/day: ${estimate_cost(chunks, k=5):.2f}")
```

---

## 6. Observability with LangSmith

LangSmith traces every LangChain call — inputs, outputs, latency, token counts, nested chains:

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"]    = "YOUR_KEY"
os.environ["LANGCHAIN_PROJECT"]    = "my-rag-production"

# No code change needed — LangChain auto-reports to LangSmith
result = rag_chain.invoke("What is the warranty period?")

# In LangSmith UI you'll see:
# - Retrieval: 3 chunks retrieved (with content)
# - Total tokens: 1,847
# - Latency breakdown: 12ms embed + 8ms search + 950ms LLM
# - Full prompt sent to LLM
# - Model temperature, model name
```

### Custom Spans

```python
from langsmith import traceable

@traceable(name="custom_rerank", tags=["retrieval"])
def rerank_with_tracing(query: str, docs: list, top_n: int = 5) -> list:
    scores = cross_encoder.predict([(query, d.page_content) for d in docs])
    ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
    return [d for d, _ in ranked[:top_n]]
```

---

## 7. Phoenix Arize (Open-source Observability)

Free alternative to LangSmith, with built-in RAGAS-style evaluation in the UI:

```python
import phoenix as px
from phoenix.trace.langchain import LangChainInstrumentor
from openinference.instrumentation.langchain import LangChainInstrumentor as OILangChainInstrumentor

session = px.launch_app()  # opens http://localhost:6006

LangChainInstrumentor().instrument()

# Every RAG call is now traced
result = rag_chain.invoke("How does hybrid search work?")

# Phoenix shows:
# - Span tree: chain → retrieval → LLM
# - Embeddings visualized in 2D (UMAP)
# - Token-level latency heatmaps
```

---

## 8. Guardrails

### Input Guardrails (prompt injection prevention)

```python
from guardrails import Guard
from guardrails.hub import DetectPII, ToxicLanguage

guard = Guard().use(DetectPII, pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER"])

def safe_rag(query: str) -> str:
    # Validate input
    result = guard.validate(query)
    if not result.validation_passed:
        return "I cannot process requests containing personal information."

    # Check for prompt injection patterns
    injection_patterns = [
        "ignore previous instructions",
        "disregard all prior",
        "you are now",
        "forget everything",
    ]
    if any(p in query.lower() for p in injection_patterns):
        return "I cannot process that request."

    return rag_chain.invoke(query)
```

### Output Guardrails (hallucination check)

```python
def rag_with_grounding_check(query: str) -> str:
    docs = retriever.invoke(query)
    context = "\n\n".join([d.page_content for d in docs])
    answer = llm.invoke(f"Context:\n{context}\n\nQuestion: {query}").content

    # Verify every claim in the answer is in the context
    check_prompt = f"""
    Context: {context}
    Answer: {answer}
    
    Is every factual claim in the answer directly supported by the context?
    If any claim is NOT supported, list it. If all are supported, say "GROUNDED".
    """
    verification = llm.invoke(check_prompt).content

    if "GROUNDED" not in verification:
        # Fall back to a conservative answer
        return "Based on available information: " + conservative_answer(query, docs)

    return answer
```

---

## 9. Re-indexing Strategy

Plan for your corpus to change:

| Strategy | When to use | Trade-off |
|---|---|---|
| Full re-index | Weekly, or when embedding model changes | Simple, consistent |
| Incremental (upsert new docs) | Daily or event-driven | Faster, but stale deletions |
| Dual-index | Zero-downtime re-index | Complex, requires swap logic |

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def reindex_job():
    """Runs nightly to pick up new documents."""
    new_docs = fetch_documents_updated_since(last_run_time())
    if not new_docs:
        return
    chunks = splitter.split_documents(new_docs)
    vectorstore.add_documents(chunks)
    log_reindex(len(chunks))

scheduler.add_job(reindex_job, "cron", hour=2, minute=0)  # 2AM nightly
scheduler.start()
```

---

## 10. CI/CD for RAG

Prevent regressions by running RAGAS metrics on every deployment:

```yaml
# .github/workflows/rag-eval.yml
name: RAG Evaluation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - name: Run RAGAS Evaluation
        run: python scripts/eval_rag.py --output results.json
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      - name: Assert Thresholds
        run: |
          python - <<'EOF'
          import json
          results = json.load(open("results.json"))
          assert results["faithfulness"]    >= 0.85, f"Faithfulness below threshold: {results['faithfulness']}"
          assert results["answer_relevancy"] >= 0.80, f"Answer relevancy below threshold: {results['answer_relevancy']}"
          assert results["context_precision"] >= 0.75, f"Context precision below threshold: {results['context_precision']}"
          print("All evaluation thresholds passed!")
          EOF
```

---

## Production Checklist

- [ ] Embedding model pinned to a specific version (model drift = index invalidation)
- [ ] Vector index persisted and backed up
- [ ] Semantic cache deployed (Redis/GPTCache)
- [ ] Async retrieval implemented
- [ ] Response streaming enabled
- [ ] LangSmith or Phoenix tracing active
- [ ] RAGAS evaluation in CI/CD pipeline
- [ ] Input validation and prompt injection detection
- [ ] Output grounding verification
- [ ] Fallback responses for retrieval failures
- [ ] Cost monitoring and alerting
- [ ] Nightly re-indexing job

---

## See Also

- [Evaluation](./evaluation) — RAGAS metrics and testing patterns
- [Retrieval Strategies](./retrieval-strategies) — the retrieval optimizations that most affect latency
- [Agentic RAG](./agentic-rag) — when latency trade-offs of agentic approaches are acceptable
