# PageIndex and the rise of reasoning-based RAG

**PageIndex is a standalone vectorless RAG framework by Vectify AI — not a LlamaIndex component — that replaces embedding similarity with LLM reasoning over hierarchical document trees, achieving 98.7% accuracy on FinanceBench.** This represents a paradigm shift for structured document retrieval: instead of chunking documents and searching by cosine similarity, PageIndex builds a JSON-based "Table of Contents" tree and lets an LLM reason its way to the correct sections, much like a human expert navigating a 200-page financial filing. The approach is particularly powerful for insurance, legal, and financial documents where **similarity ≠ relevance** — many clauses share identical language but differ critically in applicability. For an InsureChat system, PageIndex's architecture offers a compelling alternative or complement to the standard ChromaDB + Voyage AI vector pipeline.

---

## How PageIndex actually works under the hood

PageIndex operates in two distinct phases that separate expensive structural analysis from fast query-time reasoning.

**Phase 1 — Indexing (offline).** A high-capability model (GPT-4o or equivalent) reads the entire document, identifies structural boundaries — headings, sections, subsections, paragraphs — and generates a recursive JSON tree. Each node contains:

```json
{
  "node_id": "0006",
  "title": "Financial Stability",
  "start_index": 21,
  "end_index": 22,
  "summary": "The Federal Reserve's monitoring of...",
  "metadata": {},
  "sub_nodes": [
    {
      "node_id": "0007",
      "title": "Monitoring Financial Vulnerabilities",
      "start_index": 22,
      "end_index": 28,
      "summary": "The Federal Reserve's monitoring..."
    }
  ]
}
```

The `start_index` and `end_index` fields map to page ranges, enabling precise content retrieval. The `summary` field is an LLM-generated description of that section's content. The tree is stored as a lightweight JSON artifact — **no vector database, no embeddings, no external infrastructure**.

**Phase 2 — Retrieval (online).** A faster, cheaper model (GPT-4o-mini) receives the user query plus the entire tree structure within its context window. This is the critical architectural insight: the tree index is an **in-context index**, living inside the LLM's active reasoning context rather than in an external database. The retrieval follows an iterative loop:

1. The LLM reads the tree's top-level summaries and selects the most promising branch
2. It navigates deeper into that branch, reading sub-node summaries at each level
3. Upon reaching relevant leaf nodes, it retrieves their full raw content via `node_id`
4. If the retrieved information is insufficient, the LLM returns to the tree and explores additional branches
5. Once enough context is assembled, it generates the final answer

This process is inspired by **Monte Carlo Tree Search** (the algorithm behind AlphaGo), where the system strategically explores a decision tree rather than exhaustively scanning all possibilities. The LLM can follow in-document cross-references ("see Appendix G"), integrate chat history for multi-turn conversations, and retrieve semantically coherent sections rather than arbitrary fixed-size chunks.

---

## Five fundamental failures of vector RAG that reasoning solves

The technical motivation for PageIndex centers on five well-documented limitations of vector-based retrieval that become acute with professional documents.

**Query-knowledge space mismatch** is the first and most fundamental problem. Vector retrieval assumes the most semantically similar text is the most relevant, but queries often express intent rather than content. An insurance adjuster asking "What's the maximum payout for water damage on a standard homeowner's policy?" needs the specific coverage table — not the executive summary paragraph that uses similar vocabulary. PageIndex's LLM can reason: *"Coverage limits are typically in the Schedule of Benefits section"* and navigate directly there.

**Similarity without relevance** plagues domain-specific corpora especially. Insurance policies contain dozens of clauses with near-identical language but critically different applicability (e.g., "Coverage A" vs. "Coverage B" exclusions). Embedding models cannot distinguish these based on vector distance alone. **Hard chunking destroys context** — splitting a coverage table across two 512-token chunks severs the header from its data, making both fragments meaningless. PageIndex retrieves complete, natural sections.

**Inability to follow cross-references** represents a structural limitation of flat vector indexes. When a policy states "subject to the limitations described in Section 4.2," vector search cannot follow that reference. PageIndex's tree-aware LLM navigates to Section 4.2 and retrieves the relevant content. Finally, **stateless retrieval** means each vector query is independent — the retriever doesn't know the user just asked about "flood coverage" and now says "what about the deductible?" PageIndex maintains conversational context to refine retrieval across turns.

---

## LlamaIndex index types compared with PageIndex

Since PageIndex is not part of LlamaIndex, understanding the closest equivalents in LlamaIndex is essential for deciding which approach to use in an InsureChat system. The table below maps each index type's core mechanism, cost profile, and ideal use case:

| Index type | Retrieval mechanism | Build cost | Query cost | Best scenario |
|---|---|---|---|---|
| **VectorStoreIndex** | Embedding similarity (top-k ANN) | Embedding only | 1 LLM call | General-purpose semantic search |
| **TreeIndex** (LLM select) | LLM traverses summary tree top-down | O(N/k) summaries | O(log N) LLM calls | Hierarchical docs, reasoning queries |
| **DocumentSummaryIndex** (LLM) | LLM reads doc summaries, selects relevant docs | O(D) summaries | O(D/batch) LLM calls | Multi-document routing |
| **KeywordTableIndex** | Exact keyword matching via lookup table | O(N) keyword extraction | Dictionary lookup + 1 LLM | Domain-specific terminology search |
| **KnowledgeGraphIndex** | Entity-relationship graph traversal | O(N) triplet extraction | Graph traversal + 1 LLM | Entity-relationship queries |
| **SummaryIndex** (default) | Returns ALL nodes, no filtering | Zero | O(N) — every node | Full-document summarization |
| **PageIndex** (Vectify AI) | LLM reasons over JSON tree in-context | O(1) LLM call for tree | Multiple LLM calls for tree search | Long structured professional docs |

**LlamaIndex's TreeIndex is architecturally closest to PageIndex.** Both build hierarchical summary trees and use LLM reasoning to traverse them. The key differences: TreeIndex builds its tree bottom-up by summarizing groups of child nodes, while PageIndex analyzes the document holistically to produce a structure-aware tree. TreeIndex stores its tree in LlamaIndex's internal data structures, while PageIndex keeps everything as a portable JSON artifact. TreeIndex can optionally use embedding-based branch selection; PageIndex is purely reasoning-driven.

**DocumentSummaryIndex** offers a different flavor of LLM-based retrieval. It generates a summary per document (not per section), then presents batches of summaries to the LLM at query time. The LLM selects which documents are relevant and returns all chunks from those documents. This works well as a **first-stage router** in multi-document systems but lacks PageIndex's granular within-document navigation.

**RouterQueryEngine** doesn't index anything itself but uses LLM reasoning to select which underlying query engine handles each query. For InsureChat, this enables routing policy questions to one index, claims questions to another, and regulatory questions to a third — a critical architectural pattern for multi-document-type systems.

---

## The broader landscape of reasoning-based retrieval

PageIndex exists within a rapidly evolving ecosystem of approaches that move beyond pure vector similarity.

**Self-RAG** (Asai et al., ICLR 2024 Oral) trains a single language model to generate special reflection tokens that decide *when* to retrieve, evaluate *whether* retrieved passages are relevant, and check *whether* the generated answer is supported by evidence. The model internally controls the entire retrieval-generation loop without external orchestration. Self-RAG (13B parameters) achieved **55.8% on PopQA** versus 14.7% for vanilla Llama2-13B, demonstrating that learned retrieval decisions dramatically outperform fixed retrieve-then-generate pipelines.

**CRAG** (Corrective RAG) takes a plug-and-play approach: a fine-tuned T5-large evaluator grades retrieved documents as Correct, Incorrect, or Ambiguous, then triggers different strategies — proceeding with refinement, falling back to web search, or combining both. This lightweight correction layer improves any existing RAG pipeline without requiring model retraining.

**RAPTOR** (Stanford, ICLR 2024) constructs hierarchical summary trees similarly to PageIndex but retains vector search at retrieval time. Documents are chunked, embedded, clustered via Gaussian Mixture Models, and summarized recursively. At query time, the query embedding is compared against nodes at **all tree levels** simultaneously, enabling retrieval from any abstraction level. RAPTOR achieved a **20% absolute accuracy improvement** on the QuALITY benchmark when paired with GPT-4.

**Agentic RAG** represents the most general pattern: an LLM agent orchestrates retrieval as one of multiple tools, deciding when to search, what queries to issue, whether results are sufficient, and when to rewrite queries. LlamaIndex implements this through `ReActAgent` and `OpenAIAgent` with query engine tools, while LangGraph implements it as a state machine with explicit retrieve → grade → rewrite → generate loops.

The emerging consensus is that **hybrid architectures will dominate production systems** — vectors for broad recall across large corpora, metadata filters for structured constraints, reasoning-based methods for precision within complex documents, and reranking as a final quality filter.

---

## Building InsureChat: architecture patterns for insurance RAG

For an insurance domain RAG system using LlamaIndex, ChromaDB, and Voyage AI embeddings, several proven patterns emerge from production deployments.

**Page-level chunking with rich metadata** is the foundation. Insurance documents — policy declarations, endorsements, claims forms — are naturally page-bounded. Each page becomes one chunk, preserving table structures, form layouts, and section context. Metadata should include `policy_type` (auto, home, life, health), `effective_date`, `state`, `page_number`, `section_type` (declarations, coverage, exclusions, conditions), and `document_id`. This enables LlamaIndex's `VectorIndexAutoRetriever` to automatically infer metadata filters from natural language: "What are the auto policy limits in California for 2024?" generates filters `policy_type="auto"`, `state="California"`, `year=2024` before vector search even begins.

**A multi-tier retrieval architecture** combines the strengths of multiple approaches:

```
Tier 1: Query Classification → RouterQueryEngine routes to appropriate index
  ├── Policy Documents (VectorStoreIndex + ChromaDB + Voyage AI)
  ├── Claims Records (VectorStoreIndex + metadata filtering)  
  ├── Regulatory Documents (SummaryIndex for full-context synthesis)
  └── Cross-document Analysis (SubQuestionQueryEngine for decomposition)

Tier 2: Within-document Retrieval
  ├── Vector similarity (Voyage AI embeddings via ChromaDB)
  ├── BM25 keyword matching (for policy numbers, coverage codes)
  └── Metadata filtering (date, state, coverage type)

Tier 3: Reranking + Context Assembly
  ├── Cross-encoder reranking for precision
  └── Parent-document retrieval (expand chunks to full pages)
```

The **ChromaDB + Voyage AI integration** in LlamaIndex is straightforward:

```python
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.voyageai import VoyageEmbedding
import chromadb

db = chromadb.PersistentClient(path="./chroma_db")
collection = db.get_or_create_collection("insurance_policies")
vector_store = ChromaVectorStore(chroma_collection=collection)

embed_model = VoyageEmbedding(model_name="voyage-3-large")
Settings.embed_model = embed_model

index = VectorStoreIndex.from_documents(
    documents, 
    storage_context=StorageContext.from_defaults(vector_store=vector_store)
)
```

For **hybrid retrieval combining BM25 and vector search** — essential for insurance documents with specific policy numbers and coverage codes — use `QueryFusionRetriever` with reciprocal rank fusion:

```python
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever

hybrid_retriever = QueryFusionRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    similarity_top_k=5,
    mode="reciprocal_rerank",
)
```

**Integrating PageIndex-style reasoning** into a LlamaIndex pipeline is possible through a custom reasoning → page selection → answer pattern. Pre-generate page summaries during indexing, store them alongside the vector index, then at query time have the LLM reason over summaries to identify candidate pages before performing targeted vector search within those pages. This hybrid captures the precision of reasoning-based retrieval with the scalability of vector search.

---

## The query-to-answer flow in a reasoning-based system

The complete retrieval flow in a PageIndex-style reasoning system differs fundamentally from vector RAG at every stage:

**Vector RAG flow:** Query → Embed query → ANN search in vector DB → Return top-k chunks → Synthesize answer. Total LLM calls: **1** (synthesis only). Retrieval is entirely mathematical — no reasoning involved.

**PageIndex reasoning flow:** Query → LLM reads tree index in context → LLM reasons about document structure → Selects promising branches → Navigates to leaf nodes → Retrieves full section content → Evaluates sufficiency → (If insufficient: navigates to additional sections) → Assembles context → Generates answer with citations. Total LLM calls: **3-8** depending on tree depth and query complexity. Every retrieval decision involves explicit reasoning.

**Hybrid flow for InsureChat:** Query → LLM classifies query type and extracts metadata filters → Metadata pre-filtering narrows document set → Vector search within filtered set → BM25 keyword search in parallel → Reciprocal rank fusion → Cross-encoder reranking → Page-boundary context expansion → Answer generation with page citations. Total LLM calls: **2-3** (classification + reranking + synthesis). Balances reasoning precision with vector efficiency.

The key architectural insight is that **reasoning and vector retrieval are complementary, not competing**. Reasoning excels at navigating within complex documents and following structural cues. Vector search excels at broad recall across large corpora. The optimal InsureChat architecture likely uses vector search to identify the right 3-5 documents from hundreds, then reasoning-based navigation to find the precise answer within those documents.

---

## Trade-offs that determine when to use each approach

The decision between vector-based, reasoning-based, and hybrid approaches depends on five critical dimensions.

**Latency** strongly favors vector search. An ANN query returns results in **single-digit milliseconds**; PageIndex's multi-step LLM reasoning takes **2-10 seconds** per query depending on tree depth. For real-time chat interfaces, pure reasoning-based retrieval may feel sluggish. Hybrid approaches mitigate this by limiting reasoning to a pre-filtered subset.

**Cost per query** scales with LLM token usage. Vector search costs only embedding computation (~$0.001/query with Voyage AI). PageIndex consumes tokens for the tree structure in context plus multiple reasoning steps — roughly **$0.02-0.10/query** with GPT-4o-mini. For high-volume applications, this 20-100x cost increase is significant. For high-value, low-volume professional analysis (insurance underwriting, legal review), the accuracy improvement justifies the cost.

**Accuracy** is where PageIndex excels. Its **98.7% on FinanceBench** significantly outperforms standard vector RAG baselines on structured professional documents. The advantage is most pronounced for queries requiring structural navigation, cross-referencing, or distinguishing between similar but contextually different passages — exactly the patterns common in insurance documents.

**Scalability** limits pure reasoning approaches. The tree index must fit within the LLM's context window, which constrains corpus size. Vector databases scale to billions of documents effortlessly. For InsureChat with hundreds of policy documents, a two-stage architecture — vector search for document selection, reasoning for within-document navigation — provides the best balance.

**Explainability** is a clear win for reasoning-based approaches. PageIndex produces a reasoning trace showing exactly *why* each section was selected, which pages were consulted, and how the answer was derived. This audit trail is invaluable for insurance applications where regulatory compliance requires traceable decision-making. Vector search offers only similarity scores — opaque and difficult to explain to regulators or customers.

---

## Conclusion: a practical decision framework for InsureChat

The research reveals that PageIndex represents a genuine architectural innovation, not just an incremental improvement. Its core insight — that **retrieval is a reasoning problem, not a similarity problem** — is particularly well-validated for the insurance domain, where document structure carries critical semantic information that chunking destroys and embeddings cannot capture.

For InsureChat specifically, the recommended architecture combines three layers: **Voyage AI embeddings in ChromaDB** for fast, scalable semantic search across the full policy corpus; **LlamaIndex's RouterQueryEngine** for intelligent query classification and routing across document types; and **reasoning-based within-document navigation** (via PageIndex directly, LlamaIndex's TreeIndex, or a custom summary-based approach) for precise answer extraction from long, complex policy documents. The emerging academic evidence from Self-RAG, CRAG, RAPTOR, and the PwC systematic evaluation of vector vs. non-vector RAG architectures consistently shows that reasoning-augmented retrieval outperforms pure vector approaches on complex professional documents — the exact documents InsureChat must handle. The practical path forward is not choosing between vectors and reasoning but orchestrating both: vectors for breadth, reasoning for depth, metadata for precision, and reranking for quality assurance.