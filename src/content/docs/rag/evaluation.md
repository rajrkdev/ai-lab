---
title: RAG Evaluation
description: Complete guide to RAG evaluation — RAGAS framework metrics, faithfulness, answer relevancy, context precision/recall, the evaluation triad, benchmark datasets, and unit testing patterns.
sidebar:
  order: 11
---

## Why Evaluate RAG Systems?

RAG systems have two failure modes:
1. **Retrieval failure:** The retrieved context doesn't contain the answer
2. **Generation failure:** The context contains the answer, but the LLM ignores or misrepresents it

Standard LLM benchmarks don't separate these. RAG-specific evaluation frameworks diagnose both independently, enabling targeted fixes.

---

## The RAG Evaluation Triad

Three core signals — **faithfulness**, **answer relevance**, and **context relevance** — form the foundation of RAG evaluation:

```
           Query
            │
            ▼
       ┌──────────┐         Answer Relevance:
       │ Retrieval│────────── Does the Answer address the Query?
       └────┬─────┘
            │ Context        Context Relevance:
            ▼                Is the Context relevant to the Query?
       ┌──────────┐
       │   LLM    │
       └────┬─────┘
            │ Answer
            ▼
       Faithfulness:
       Is the Answer grounded in the Context?
```

| Metric | Question | Range |
|---|---|---|
| **Faithfulness** | Is every claim in the answer supported by the retrieved context? | 0–1 |
| **Answer Relevance** | Does the answer actually address the question? | 0–1 |
| **Context Precision** | Of the retrieved chunks, what fraction are actually relevant? | 0–1 |
| **Context Recall** | Does the retrieved context contain all information needed to answer? | 0–1 |

---

## RAGAS Framework

**Paper:** Es et al., "RAGAS: Automated Evaluation of Retrieval Augmented Generation" (2023)  
**GitHub:** `explodinggradients/ragas`

RAGAS provides reference-free evaluation — it uses an LLM-as-judge to score each metric, enabling evaluation without human-labeled ground truth answers (except for context recall, which requires ground-truth answers).

### Installation

```bash
pip install ragas langchain-openai
```

### Basic Usage

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from datasets import Dataset

# Your test data
data = {
    "question": [
        "What is the capital of France?",
        "How does BERT's MLM work?",
    ],
    "answer": [
        "The capital of France is Paris.",
        "BERT masks 15% of tokens and predicts them using context from both sides.",
    ],
    "contexts": [
        [
            "Paris is the capital and largest city of France.",
            "France is a country in Western Europe.",
        ],
        [
            "In MLM, BERT randomly masks 15% of tokens in the input and learns to predict them.",
            "80% of selected tokens are replaced with [MASK], 10% with a random token, 10% unchanged.",
        ],
    ],
    "ground_truth": [   # only needed for context_recall
        "Paris is the capital of France.",
        "BERT masks 15% of input tokens and predicts them using bidirectional context.",
    ],
}

dataset = Dataset.from_dict(data)
results = evaluate(
    dataset=dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
)
print(results)
# {'faithfulness': 0.97, 'answer_relevancy': 0.95, 'context_precision': 0.92, 'context_recall': 0.88}
```

---

## Metric Details

### Faithfulness

**Measures:** Whether every factual claim in the answer can be inferred from the retrieved context (hallucination detection).

**Algorithm:**
1. LLM extracts all factual statements from the answer
2. For each statement, LLM checks if it can be inferred from the context
3. Score = (statements supported by context) / (total statements)

```python
from ragas.metrics import faithfulness
from ragas import SingleTurnSample

sample = SingleTurnSample(
    user_input="What year was BERT published?",
    response="BERT was published in 2018 by Google. It later won the Nobel Prize.",  # hallucination!
    retrieved_contexts=["BERT was introduced by Google in October 2018."],
)

# faithfulness = 1/2 = 0.5 (only first claim is supported)
score = await faithfulness.single_turn_ascore(sample)
print(score)  # ~0.5
```

### Answer Relevancy

**Measures:** Whether the answer addresses the question (ignores faithfulness — even a hallucinated answer can be relevant).

**Algorithm:**
1. LLM generates N reverse questions from the answer (what question does this answer?)
2. Embeds original question + each generated question
3. Score = average cosine similarity between original and generated questions

```python
# Low score: answer is off-topic
sample = SingleTurnSample(
    user_input="What is the boiling point of water?",
    response="Water is a liquid at room temperature formed from hydrogen and oxygen.",
    retrieved_contexts=["Water boils at 100°C at standard pressure."]
)
# The answer doesn't say the boiling point → low answer_relevancy
```

### Context Precision

**Measures:** Of the top-k retrieved chunks, what fraction are actually relevant to answering the question? Penalizes noisy retrievals ranked highly.

**Formula:**

$$\text{Context Precision} = \frac{1}{k} \sum_{i=1}^{k} \frac{\text{relevant chunks in top-}i}{i} \times \mathbb{1}[\text{chunk}_i \text{ is relevant}]$$

This is a **weighted precision at rank** — relevant chunks ranked higher contribute more.

### Context Recall

**Measures:** Does the retrieved context contain all the information needed to answer the question?

**Algorithm:**
1. Break ground-truth answer into individual statements
2. For each statement, check if it can be inferred from any retrieved chunk
3. Score = (statements found in context) / (total statements)

**Requires ground-truth answers** — the only metric that needs labels.

---

## Running Evaluation on a Full Pipeline

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

# Configure RAGAS to use your LLM and embedding model
evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o"))
evaluator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())

for metric in [faithfulness, answer_relevancy, context_precision, context_recall]:
    metric.llm = evaluator_llm
    metric.embeddings = evaluator_embeddings

# Run your RAG pipeline over test questions
test_questions = load_test_dataset()    # your eval set
records = []

for q in test_questions:
    # Run actual pipeline
    retrieved_docs = retriever.invoke(q["question"])
    answer = rag_chain.invoke(q["question"])

    records.append({
        "question":     q["question"],
        "answer":       answer,
        "contexts":     [d.page_content for d in retrieved_docs],
        "ground_truth": q["ground_truth"],
    })

dataset = Dataset.from_list(records)
results = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision, context_recall])

# Save results
results.to_pandas().to_csv("evaluation_results.csv", index=False)
print(results.to_pandas()[["faithfulness","answer_relevancy","context_precision","context_recall"]].describe())
```

---

## Additional RAGAS Metrics

| Metric | What it measures |
|---|---|
| `answer_correctness` | Factual overlap between answer and ground truth (needs labels) |
| `answer_similarity` | Semantic similarity between answer and ground truth |
| `context_entity_recall` | Fraction of named entities in ground truth found in context |
| `noise_sensitivity` | System's robustness to noisy/irrelevant context |
| `summarization_score` | Quality of summarization when used |

```python
from ragas.metrics import answer_correctness, noise_sensitivity

results = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall, answer_correctness],
)
```

---

## Benchmark Datasets

| Dataset | Size | Domain | Metrics it tests |
|---|---|---|---|
| **BEIR** | 18 datasets, 5.4M docs | Heterogeneous | Retrieval (NDCG@10) |
| **RAGBench** | 100K QA pairs | Multi-domain | End-to-end RAG |
| **FinanceBench** | 10K questions | Financial SEC filings | Retrieval + faithfulness |
| **RGB** | 900 questions | News, bio, general | Noise robustness |
| **CRUD-RAG** | 36K Q4 | Chinese news | Create/Read/Update/Delete |

```python
# Load a BEIR dataset for retrieval evaluation
from beir import util
from beir.datasets.data_loader import GenericDataLoader
from beir.retrieval.evaluation import EvaluateRetrieval

dataset = "nfcorpus"
url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset}.zip"
data_path = util.download_and_unzip(url, "beir_datasets")
corpus, queries, qrels = GenericDataLoader(data_folder=data_path).load(split="test")

from beir.retrieval.search.dense import DenseRetrievalExactSearch as DRES
from beir.retrieval.models import SentenceBERT

model = DRES(SentenceBERT("BAAI/bge-large-en-v1.5"), batch_size=64)
retriever = EvaluateRetrieval(model, score_function="cos_sim")

results = retriever.retrieve(corpus, queries)
ndcg, _map, recall, precision = retriever.evaluate(qrels, results, retriever.k_values)
print(f"NDCG@10: {ndcg['NDCG@10']:.4f}")
```

---

## Unit Testing RAG Pipelines

Treat RAG evaluation like software testing — write assertions against specific known cases:

```python
import pytest
from langchain_community.vectorstores import FAISS

@pytest.fixture
def rag_chain():
    # Build a small test index
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_core.documents import Document

    docs = [
        Document(page_content="The refund window is 30 days from purchase.", metadata={"source": "tos.pdf"}),
        Document(page_content="Shipping takes 5–7 business days.", metadata={"source": "faq.pdf"}),
    ]
    vectorstore = FAISS.from_documents(docs, HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"))
    return build_rag_chain(vectorstore)

def test_refund_answer(rag_chain):
    answer = rag_chain.invoke("What is the refund policy?")
    assert "30 days" in answer.lower(), f"Expected '30 days' in answer, got: {answer}"

def test_sources_cited(rag_chain):
    result = rag_chain.invoke_with_sources("What is the refund policy?")
    assert any("tos.pdf" in s for s in result["sources"]), "Source document not cited"

def test_no_hallucination(rag_chain):
    """Answer to a question not in the index should not invent facts."""
    answer = rag_chain.invoke("What is the exchange rate for euros?")
    # Should say it doesn't know, not invent a rate
    assert any(phrase in answer.lower() for phrase in ["don't know", "not sure", "no information"]), \
        f"Potential hallucination: {answer}"
```

---

## Evaluation Dashboard with Phoenix Arize

```python
import phoenix as px
from phoenix.trace.langchain import LangChainInstrumentor

# Start Phoenix session (opens a local UI at http://localhost:6006)
session = px.launch_app()

# Auto-instrument LangChain
LangChainInstrumentor().instrument()

# Now every LangChain call is traced and visible in Phoenix
response = rag_chain.invoke("What is RAG?")

# View traces at http://localhost:6006
# Phoenix shows: retrieval latency, chunk contents, LLM prompt, token counts
```

---

## Interpreting Results and Taking Action

| Score | What it means | Action |
|---|---|---|
| Faithfulness < 0.7 | LLM is hallucinating beyond the context | Add anti-hallucination instructions; lower temperature; add grounding checks |
| Answer Relevance < 0.7 | LLM is off-topic | Improve prompt; check if question preprocessing (HyDE/rewriting) helps |
| Context Precision < 0.7 | Too many irrelevant chunks retrieved | Add reranking; improve chunking; tune `k` |
| Context Recall < 0.7 | Missing information in retrieved context | Increase `k`; check chunk size isn't too small; add multi-query |

---

## See Also

- [Advanced RAG](./advanced-rag) — improvements likely to raise context precision and recall
- [Retrieval Strategies](./retrieval-strategies) — targeting specific retrieval failures
- [Production RAG](./production-rag) — evaluation in CI/CD pipelines and monitoring in production
