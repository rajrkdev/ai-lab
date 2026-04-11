---
title: Sentence-BERT (SBERT)
description: How Sentence-BERT produces fixed-size sentence embeddings using siamese networks, pooling strategies, training objectives, and the sentence-transformers library — with production code examples.
sidebar:
  order: 7
---

## The Problem with Vanilla BERT

Standard BERT requires the full sentence pair to be fed simultaneously to compute a similarity score. For finding the most similar sentence out of 10,000 candidates, this means **10,000 forward passes** — approximately 65 hours on V100 GPU.

BERT's per-token representations also cannot be directly compared across sentences as fixed-size vectors (the `[CLS]` token is not well-calibrated for semantic similarity).

---

## The Sentence-BERT Solution

**Paper:** Reimers & Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks" (2019)  
**Library:** `sentence-transformers`  
**HF Hub:** `sentence-transformers/all-MiniLM-L6-v2`, `sentence-transformers/all-mpnet-base-v2`, etc.

SBERT fine-tunes BERT with a **siamese network** architecture that produces a **fixed-size dense vector** for each sentence independently. Similarity is then computed via cosine similarity — enabling precomputation and fast retrieval.

With SBERT: finding the most similar sentence from 10,000 candidates takes **~5 milliseconds** (precompute all embeddings once, do one cosine search).

---

## Architecture

```
Sentence A              Sentence B
    ↓                       ↓
BERT Encoder            BERT Encoder     ← shared weights (siamese)
    ↓                       ↓
 Pooling                 Pooling          ← convert variable-length → fixed-size
    ↓                       ↓
  u ∈ ℝ^768            v ∈ ℝ^768
    ↓___________________________↓
         Similarity / Loss
```

Both "towers" share the exact same BERT weights — updates to one update the other. This is the defining property of a **siamese network**.

---

## Pooling Strategies

The pooling layer converts the variable-length token output matrix $\mathbf{H} \in \mathbb{R}^{n \times d}$ into a single fixed vector $\mathbf{u} \in \mathbb{R}^d$.

### 1. Mean Pooling (recommended)

$$\mathbf{u} = \frac{1}{\sum_i m_i} \sum_{i=1}^{n} m_i \cdot \mathbf{h}_i$$

where $m_i$ is the attention mask (1 for real tokens, 0 for padding). This is the standard pooling for SBERT — it outperforms CLS pooling for most tasks.

```python
import torch
import torch.nn.functional as F

def mean_pool(token_embeddings, attention_mask):
    # token_embeddings: [batch, seq_len, hidden]
    # attention_mask:   [batch, seq_len]
    mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * mask, dim=1)
    sum_mask = torch.clamp(mask.sum(dim=1), min=1e-9)
    return sum_embeddings / sum_mask
```

### 2. CLS Pooling

$$\mathbf{u} = \mathbf{h}_{\text{[CLS]}}$$

Simple but suboptimal — the CLS token was pre-trained for NSP classification, not semantic similarity.

### 3. Max Pooling

$$u_j = \max_{i} h_{ij}$$

Takes the maximum value across token dimension for each feature. Occasionally useful but rarely outperforms mean pooling.

---

## Training Objectives

### 1. Classification Objective (NLI Training)

Applied to Natural Language Inference datasets (SNLI, MultiNLI). For a sentence pair (u, v):

$$\text{concat}(\mathbf{u},\; \mathbf{v},\; |\mathbf{u} - \mathbf{v}|) \in \mathbb{R}^{3d}$$

This 3d vector passes through a linear layer + softmax to predict Entailment / Contradiction / Neutral.

$$\mathcal{L} = \text{CrossEntropy}(W_c \cdot [\mathbf{u}; \mathbf{v}; |\mathbf{u}-\mathbf{v}|])$$

### 2. Regression Objective (STS-B)

For Semantic Textual Similarity (0–5 continuous score):

$$\mathcal{L} = \text{MSE}\!\left(\text{cos\_sim}(\mathbf{u}, \mathbf{v}),\; \text{label}\right)$$

### 3. Triplet Loss (Hard Negative Mining)

For ranking and retrieval tasks:

$$\mathcal{L} = \max(0,\; d(\mathbf{a}, \mathbf{p}) - d(\mathbf{a}, \mathbf{n}) + \epsilon)$$

where $a$ = anchor, $p$ = positive (similar), $n$ = negative (dissimilar), $\epsilon$ = margin (typically 1.0), and $d$ is Euclidean distance or $1 - \text{cosine}$.

### 4. Multiple Negatives Ranking Loss (modern standard)

Given a batch of (anchor, positive) pairs, all other positives in the batch become **in-batch negatives**. This scales well to large batches:

$$\mathcal{L} = -\frac{1}{B} \sum_{i=1}^{B} \log \frac{e^{\text{sim}(\mathbf{u}_i, \mathbf{v}_i)/\tau}}{\sum_{j=1}^{B} e^{\text{sim}(\mathbf{u}_i, \mathbf{v}_j)/\tau}}$$

where $\tau$ is a temperature parameter (typically 0.05).

---

## sentence-transformers Library

```python
from sentence_transformers import SentenceTransformer, util

# Load a pre-trained SBERT model
model = SentenceTransformer("all-mpnet-base-v2")   # 768 dims, best quality
# model = SentenceTransformer("all-MiniLM-L6-v2")  # 384 dims, fast

# Encode sentences → embeddings
sentences = [
    "The cat sat on the mat.",
    "A feline rested on the rug.",
    "The stock market crashed today.",
]
embeddings = model.encode(sentences, normalize_embeddings=True)
# shape: (3, 768)

# Pairwise cosine similarity
cos_scores = util.cos_sim(embeddings, embeddings)
print(cos_scores)
# [[1.00, 0.87, 0.12],
#  [0.87, 1.00, 0.11],
#  [0.12, 0.11, 1.00]]

# Semantic search: find top-k most similar to a query
query = "Where did the cat sit?"
query_emb = model.encode(query, normalize_embeddings=True)
hits = util.semantic_search(query_emb, embeddings, top_k=2)
# hits[0] → [{'corpus_id': 0, 'score': 0.86}, {'corpus_id': 1, 'score': 0.79}]
```

---

## Choosing a Model

| Model | Dims | Params | Speed | Quality | Best for |
|---|---|---|---|---|---|
| `all-MiniLM-L6-v2` | 384 | 22 M | Very fast | Good | High-volume search, RAG retrieval |
| `all-MiniLM-L12-v2` | 384 | 33 M | Fast | Better | Balanced speed/quality |
| `all-mpnet-base-v2` | 768 | 109 M | Moderate | Best SBERT | Quality-critical semantic search |
| `multi-qa-mpnet-base-dot-v1` | 768 | 109 M | Moderate | Best for QA | Asymmetric Q&A retrieval |
| `paraphrase-multilingual-mpnet-base-v2` | 768 | 278 M | Slow | Best multilingual | 50+ language support |

---

## Fine-tuning Your Own SBERT Model

```python
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

# 1. Load base model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 2. Prepare training pairs
train_examples = [
    InputExample(texts=["What is the capital of France?", "Paris is the capital of France."], label=1.0),
    InputExample(texts=["How to reset password?", "Click Forgot Password on the login page."], label=0.9),
    InputExample(texts=["What is SQL?", "It rained heavily last Tuesday."], label=0.0),
]

train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=32)

# 3. Loss function — Multiple Negatives Ranking for pairs without labels,
# CosineSimilarityLoss for labeled pairs
train_loss = losses.CosineSimilarityLoss(model)

# 4. Train
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=3,
    warmup_steps=100,
    output_path="./my-sbert-model",
    show_progress_bar=True,
)
```

---

## Asymmetric Retrieval: Bi-encoder Setup

For query-document retrieval, query and document may use **different models** or encoders:

```python
from sentence_transformers import SentenceTransformer

# Asymmetric: query and document models are different
query_model = SentenceTransformer("multi-qa-mpnet-base-dot-v1")
doc_model   = SentenceTransformer("multi-qa-mpnet-base-dot-v1")  # same here, but can differ

# Encode corpus once, store, reuse
corpus = ["Document A text...", "Document B text...", "Document C text..."]
corpus_embeddings = doc_model.encode(corpus, batch_size=64, show_progress_bar=True)

# At query time
query = "How does retrieval work?"
query_embedding = query_model.encode(query)

hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=5)
```

---

## SBERT vs Cross-Encoder

| | Bi-encoder (SBERT) | Cross-encoder |
|---|---|---|
| **How** | Encodes query and doc independently | Encodes (query, doc) jointly |
| **Speed** | O(1) lookup after precomputation | O(n) — must process each pair |
| **Accuracy** | ~87-94% of cross-encoder | Top accuracy on reranking |
| **Use case** | First-stage retrieval (recall) | Reranking top-k candidates (precision) |

In production RAG, the standard pattern is: **SBERT bi-encoder retrieval → cross-encoder reranking**.

---

## See Also

- [BERT in RAG](./bert-in-rag) — bi-encoder + cross-encoder reranking pipeline in detail
- [BERT Variants](./variants) — which base model to use for SBERT fine-tuning
- [Embedding Models Comparison](../rag/embedding-models) — SBERT vs. dedicated embedding APIs
