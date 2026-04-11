---
title: Vector Stores
description: Comprehensive comparison of vector databases for RAG — FAISS, Chroma, Pinecone, Weaviate, pgvector, Qdrant — covering index types, filtering, scaling, and production trade-offs.
sidebar:
  order: 6
---

## What a Vector Store Does

A vector store indexes high-dimensional embedding vectors and efficiently answers **approximate nearest-neighbor (ANN)** queries: "given a query vector, find the top-k most similar vectors in the corpus."

Core operations:
- **Upsert:** add/update vectors with associated metadata and a document ID
- **Search:** given a query vector, return top-k nearest neighbors (with optional metadata filtering)
- **Delete:** remove vectors by ID

---

## Index Algorithms

Understanding the underlying algorithms helps you choose the right index type for your use case.

### Flat (Brute-force)

Computes exact cosine/L2 distance to every vector. No approximation → 100% recall.

$$\text{sim}(q, d_i) = \frac{q \cdot d_i}{\|q\| \|d_i\|}$$

**Complexity:** O(n·d) per query (n = corpus size, d = dimensions).  
**Use when:** Corpus < 100K vectors and recall must be 100%.

### IVF (Inverted File Index)

Divides vectors into k clusters (using k-means). At query time, search only the nearest `nprobe` clusters instead of all vectors.

- Training: k-means with k = `nlist` (typically $\sqrt{n}$)
- Query: find nearest `nprobe` clusters → search only those clusters
- Trade-off: `nprobe` controls recall-speed balance

**Complexity:** O(nprobe/nlist · n · d) — much faster than flat for large corpora.

### HNSW (Hierarchical Navigable Small Worlds)

Graph-based ANN algorithm. Builds a multi-layer graph where each node is connected to `M` nearest neighbors. Query traverses the graph greedily top-down.

- **M:** number of neighbors per node (32–64 typical)
- **efConstruction:** graph quality during build (higher = better quality, slower build)
- **ef:** search quality at query time (higher = better recall, slower query)

**Complexity:** O(log n) per query. Excellent recall (>99%) with fast queries. More memory than IVF.

---

## FAISS

**By:** Meta AI Research  
**GitHub:** `facebookresearch/faiss`  
**Type:** In-process library (not a server)

FAISS is the foundational ANN library — embedded directly in your application process. It's what most vector databases use internally.

### Index Types

| Index | When to use | Memory | Recall |
|---|---|---|---|
| `IndexFlatL2` | < 100K vectors, exact search | High | 100% |
| `IndexFlatIP` | Normalized cosine similarity, exact | High | 100% |
| `IndexIVFFlat` | 100K–10M vectors, moderate latency OK | Medium | 90–99% |
| `IndexIVFPQ` | >10M vectors, compressed, some recall loss | Low | 80–95% |
| `IndexHNSWFlat` | Fast low-latency queries, medium corpus | High | 95–99% |

```python
import faiss
import numpy as np

d = 768      # embedding dimension
n = 100_000  # corpus size

# Exact search (100% recall)
index_flat = faiss.IndexFlatIP(d)   # Inner product = cosine for normalized vectors

# HNSW (fast approximate)
index_hnsw = faiss.IndexHNSWFlat(d, 32)    # 32 = M parameter
index_hnsw.hnsw.efConstruction = 200
index_hnsw.hnsw.efSearch = 100             # quality of search at runtime

# IVF + PQ (large-scale, compressed)
quantizer = faiss.IndexFlatL2(d)
index_ivf_pq = faiss.IndexIVFPQ(
    quantizer, d,
    nlist=1024,    # number of clusters (≈ sqrt(n))
    M=8,           # number of sub-quantizers
    nbits=8,       # bits per sub-quantizer
)
index_ivf_pq.train(corpus_embeddings)   # IVF and PQ require training!

# Add vectors
embeddings = np.random.rand(n, d).astype("float32")
faiss.normalize_L2(embeddings)            # normalize for cosine similarity
index_flat.add(embeddings)

# Search: top-5 most similar to query
query = np.random.rand(1, d).astype("float32")
faiss.normalize_L2(query)
distances, indices = index_flat.search(query, k=5)
# distances[0] = [0.98, 0.96, ...], indices[0] = [42, 17, ...]

# Persist
faiss.write_index(index_flat, "corpus.faiss")
index = faiss.read_index("corpus.faiss")
```

### FAISS with LangChain

```python
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5")

# Build from documents
vectorstore = FAISS.from_documents(docs, embeddings)

# Save / load
vectorstore.save_local("faiss_index")
vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

# Similarity search with scores
results = vectorstore.similarity_search_with_score("What is RAG?", k=5)
for doc, score in results:
    print(f"{score:.4f}: {doc.page_content[:80]}")

# Filtered search (metadata filter)
results = vectorstore.similarity_search(
    "refund policy", k=5,
    filter={"source": "terms_of_service.pdf"},
)
```

---

## Chroma

**Website:** [trychroma.com](https://www.trychroma.com)  
**Type:** Embedded (in-process) or client-server  
**License:** Apache 2.0

Chroma is the most popular choice for development and small-scale production. Zero infrastructure, no server required, good Python API.

```python
import chromadb
from chromadb.utils import embedding_functions

# Persistent local database
client = chromadb.PersistentClient(path="./chroma_db")

# Use any embedding function
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-large-en-v1.5"
)

collection = client.get_or_create_collection(
    name="my_rag_collection",
    embedding_function=ef,
    metadata={"hnsw:space": "cosine"},   # distance metric
)

# Add documents
collection.add(
    documents=["First chunk text", "Second chunk text"],
    metadatas=[{"source": "doc1.pdf", "page": 1}, {"source": "doc1.pdf", "page": 2}],
    ids=["chunk_0", "chunk_1"],
)

# Query with metadata filter
results = collection.query(
    query_texts=["What is the return policy?"],
    n_results=5,
    where={"source": "terms_of_service.pdf"},    # metadata filter
    include=["documents", "metadatas", "distances"],
)

print(results["documents"][0])    # list of top-5 matching chunks
```

**Limitations:**
- Single-node only (no distributed mode)
- Not designed for > 1M vectors
- No real-time deletion performance guarantees

---

## Pinecone

**Website:** [pinecone.io](https://pinecone.io)  
**Type:** Fully managed cloud service  
**License:** Proprietary (SaaS)

Pinecone is the leading managed vector database — zero infrastructure, auto-scaling, pay-per-use.

```python
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="YOUR_KEY")

# Create serverless index
pc.create_index(
    name="rag-production",
    dimension=1024,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
)

index = pc.Index("rag-production")

# Upsert vectors with metadata
index.upsert(vectors=[
    {"id": "chunk_0", "values": embeddings[0].tolist(), "metadata": {"source": "doc1.pdf", "page": 1}},
    {"id": "chunk_1", "values": embeddings[1].tolist(), "metadata": {"source": "doc2.pdf", "page": 3}},
])

# Query with metadata filter
results = index.query(
    vector=query_embedding.tolist(),
    top_k=10,
    filter={"source": {"$eq": "doc1.pdf"}},   # Pinecone filter syntax
    include_metadata=True,
)

for match in results.matches:
    print(f"{match.score:.4f}: {match.metadata}")
```

**Namespaces:** Logical partitions within an index — useful for multi-tenant RAG:

```python
# Tenant isolation via namespaces
index.upsert(vectors=[...], namespace="tenant_abc")
results = index.query(vector=q_emb, top_k=5, namespace="tenant_abc")
```

---

## Weaviate

**Website:** [weaviate.io](https://weaviate.io)  
**Type:** Open-source (self-host) or managed cloud  
**License:** BSD-3

Weaviate offers **hybrid search** (dense + BM25) natively, multi-modal support, and a GraphQL API.

```python
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import MetadataQuery

client = weaviate.connect_to_weaviate_cloud(
    cluster_url="https://YOUR_CLUSTER.weaviate.network",
    auth_credentials=Auth.api_key("YOUR_KEY"),
)

collection = client.collections.get("Document")

# Hybrid search (dense + BM25)
results = collection.query.hybrid(
    query="refund policy",
    alpha=0.75,              # 0 = pure BM25, 1 = pure vector, 0.75 = mostly dense
    limit=5,
    return_metadata=MetadataQuery(score=True),
)

for obj in results.objects:
    print(obj.metadata.score, obj.properties["text"][:80])

client.close()
```

---

## pgvector (PostgreSQL Extension)

**GitHub:** `pgvector/pgvector`  
**Type:** PostgreSQL extension  
**License:** PostgreSQL License (permissive)

pgvector adds vector similarity search to standard PostgreSQL. Best for teams already running Postgres who want to avoid a separate service.

```sql
-- Install extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table with embedding column
CREATE TABLE documents (
    id       BIGSERIAL PRIMARY KEY,
    content  TEXT,
    metadata JSONB,
    embedding VECTOR(1024)     -- BGE-large-en-v1.5 dimension
);

-- HNSW index for fast approximate search
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- IVFFlat index (alternative)
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
SET ivfflat.probes = 10;  -- quality/speed trade-off

-- Cosine similarity search with metadata filter
SELECT id, content, 1 - (embedding <=> $1) AS similarity
FROM documents
WHERE metadata->>'department' = 'legal'
ORDER BY embedding <=> $1   -- <=> = cosine distance operator
LIMIT 10;
```

```python
# Python with psycopg3
import psycopg
import numpy as np

conn_str = "postgresql://user:pass@localhost/mydb"

def insert_chunk(content: str, embedding: np.ndarray, metadata: dict):
    with psycopg.connect(conn_str) as conn:
        conn.execute(
            "INSERT INTO documents (content, metadata, embedding) VALUES (%s, %s, %s)",
            (content, psycopg.types.json.Jsonb(metadata), embedding.tolist()),
        )

def search(query_embedding: np.ndarray, k: int = 5):
    with psycopg.connect(conn_str) as conn:
        rows = conn.execute(
            "SELECT content, metadata, 1-(embedding<=>%s) AS score FROM documents ORDER BY embedding<=>%s LIMIT %s",
            (query_embedding.tolist(), query_embedding.tolist(), k),
        ).fetchall()
    return rows
```

---

## Qdrant

**Website:** [qdrant.tech](https://qdrant.tech)  
**Type:** Open-source (Rust) or managed cloud  
**License:** Apache 2.0

Qdrant is built in Rust for high performance. Supports **payload filtering** (metadata filters applied directly within the ANN search, not post-filter) and **sparse vectors** for hybrid retrieval.

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

client = QdrantClient("localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="rag_docs",
    vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
)

# Insert with payload (metadata)
client.upsert(
    collection_name="rag_docs",
    points=[
        PointStruct(id=0, vector=embeddings[0].tolist(), payload={"source": "doc1.pdf", "page": 1}),
        PointStruct(id=1, vector=embeddings[1].tolist(), payload={"source": "doc2.pdf", "page": 3}),
    ],
)

# Filtered search — filter applied inside HNSW graph, not post-hoc
results = client.search(
    collection_name="rag_docs",
    query_vector=query_embedding.tolist(),
    query_filter=Filter(
        must=[FieldCondition(key="source", match=MatchValue(value="doc1.pdf"))]
    ),
    limit=5,
    with_payload=True,
)
```

---

## Comparison Summary

| Feature | FAISS | Chroma | Pinecone | Weaviate | pgvector | Qdrant |
|---|---|---|---|---|---|---|
| **Type** | Library | Embedded/server | Managed | OSS/managed | PostgreSQL ext | OSS/managed |
| **Max scale** | Unlimited (sharding) | ~1M | Unlimited | Unlimited | ~10M (w/ tuning) | Unlimited |
| **Native hybrid** | No | No | No | **Yes** | With ext | **Yes (sparse)** |
| **Metadata filter** | Post-hoc | Yes | Yes | Yes | SQL WHERE | In-index |
| **Multi-tenancy** | Manual | Manual | Namespaces | Multi-tenancy | Schema/RLS | Collections |
| **Self-host** | Yes | Yes | No | Yes | Yes | Yes |
| **Infrastructure** | None | None | SaaS | Docker/K8s | Postgres | Docker/K8s |
| **Best for** | Embedded, research | Dev, small prod | Managed prod | Hybrid search | Existing Postgres | High-perf prod |

---

## Choosing a Vector Store

```
Prototyping / small corpus (<100K):   Chroma (simplest)
Already have PostgreSQL:              pgvector (no new infra)
Managed cloud, large scale:           Pinecone (simplest ops)
Hybrid BM25+dense built-in:          Weaviate
Best raw performance, self-hosted:    Qdrant
Custom ANN research:                  FAISS (library)
```

---

## See Also

- [Embedding Models](../embedding-models) — what generates the vectors stored here
- [Retrieval Strategies](../retrieval-strategies) — dense, sparse, hybrid, and reranking patterns
- [Production RAG](../production-rag) — caching, scaling, and cost optimization
