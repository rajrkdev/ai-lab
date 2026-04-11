---
title: BERT Variants
description: Detailed comparison of major BERT-family models — RoBERTa, DistilBERT, ALBERT, DeBERTa v3 — covering architectural changes, training improvements, benchmark results, and when to use each.
sidebar:
  order: 6
---

## Why Variants Exist

The original BERT paper left several training decisions under-explored. Subsequent work showed BERT was **significantly undertrained**: more data, longer training, better masking, and hyperparameter tuning all yielded large gains without architectural changes. Other variants focused on making BERT smaller and faster for deployment.

---

## RoBERTa (2019)

**Paper:** Liu et al., "RoBERTa: A Robustly Optimized BERT Pretraining Approach"  
**By:** Facebook AI Research  
**HF Hub:** `FacebookAI/roberta-base`, `FacebookAI/roberta-large`

### Changes from BERT

| Change | BERT | RoBERTa |
|---|---|---|
| NSP objective | Yes | **Removed** — full-sentence packing instead |
| Training data | 16 GB (Books + Wiki) | **160 GB** (Books, Wiki, CC-News, OpenWebText, Stories) |
| Training steps | 1 M steps | **500K steps** (but larger batches) |
| Batch size | 256 | **8,192** (much larger) |
| Masking | Static (pre-processed once) | **Dynamic** (new mask each epoch) |
| Token encoding | WordPiece (char-level) | **BPE on bytes** (GPT-2 tokenizer, 50,265 vocab) |
| Sequence length during training | 128 mostly, 512 occasionally | Full 512 throughout |

### Why Remove NSP?

NSP was found to be too easy — models could predict `NotNext` by detecting topic shift (different document), not true discourse understanding. Removing NSP and using **full-document packing** (pack multiple sentences from the same document, separated by `[SEP]`) improves downstream performance consistently.

### Performance

| Benchmark | BERT-base | RoBERTa-base |
|---|---|---|
| GLUE | 84.6 | **88.1** |
| SQuAD v2 F1 | 76.3 | **86.8** |
| MNLI-m Acc | 84.6 | **87.6** |

### Usage

```python
from transformers import RobertaForSequenceClassification, RobertaTokenizer

tokenizer = RobertaTokenizer.from_pretrained("FacebookAI/roberta-base")
model = RobertaForSequenceClassification.from_pretrained("FacebookAI/roberta-base", num_labels=2)

# Note: RoBERTa uses token_type_ids=None (no segment embeddings)
inputs = tokenizer("I love this movie!", return_tensors="pt")
# No token_type_ids in output
```

---

## DistilBERT (2019)

**Paper:** Sanh et al., "DistilBERT, a distilled version of BERT"  
**By:** Hugging Face  
**HF Hub:** `distilbert/distilbert-base-uncased`

### Architecture Changes

DistilBERT uses **knowledge distillation** to compress BERT-base:

- **6 layers** (vs. 12) — initialized from every other BERT-base layer
- Same hidden size (768) and attention heads (12)
- Removed token type embeddings (no NSP)
- Removed pooler

### Knowledge Distillation Training

The student (DistilBERT) is trained to mimic the teacher (BERT-base) using three losses:

$$\mathcal{L} = \alpha \mathcal{L}_{\text{CE}} + \beta \mathcal{L}_{\text{MLM}} + \gamma \mathcal{L}_{\text{cos}}$$

| Loss | Formula | Purpose |
|---|---|---|
| $\mathcal{L}_{\text{CE}}$ | KL divergence of soft logits (temperature T=4) | Match teacher's output distribution |
| $\mathcal{L}_{\text{MLM}}$ | Standard MLM cross-entropy | Maintain language modeling ability |
| $\mathcal{L}_{\text{cos}}$ | Cosine distance between student/teacher hidden states | Align internal representations |

**Soft targets with temperature T:** $p_i = \frac{e^{z_i/T}}{\sum_j e^{z_j/T}}$ — higher temperature softens probabilities, carrying more information about teacher's uncertainty.

### Performance vs Size

| Metric | BERT-base | DistilBERT |
|---|---|---|
| Parameters | 110 M | **66 M** (40% smaller) |
| Inference speed | 1× | **~1.6×** faster |
| Memory | 1× | **~0.6×** |
| GLUE score | 84.6 | **82.8** (97% of BERT) |
| SST-2 accuracy | 93.5 | 91.3 |

### When to Use

- Edge deployment / mobile inference
- High-throughput serving where latency matters more than top-1 accuracy
- Embedding generation for semantic search where speed is critical

```python
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer

tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
model = DistilBertForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2)

# Same API as BERT — no token_type_ids
inputs = tokenizer("Fast inference!", return_tensors="pt")
outputs = model(**inputs)
```

---

## ALBERT (2019)

**Paper:** Lan et al., "ALBERT: A Lite BERT for Self-supervised Learning of Language Representations"  
**By:** Google Research  
**HF Hub:** `albert/albert-base-v2`, `albert/albert-xxlarge-v2`

### Two Key Innovations

#### 1. Factorized Embedding Parameterization

Original BERT ties vocabulary size V with hidden size H: embedding matrix is $V \times H = 30522 \times 768 = 23.4\text{M}$ parameters.

ALBERT factorizes this into a small embedding size E (128) projected to H:

$$E_{\text{BERT}} \in \mathbb{R}^{V \times H} \quad \to \quad E_{\text{ALBERT}} \in \mathbb{R}^{V \times E} \cdot \mathbb{R}^{E \times H}$$

For V=30,000, H=768, E=128: $30000 \times 128 + 128 \times 768 = 3.95\text{M}$ (vs 23.4M for BERT). This makes the embedding layer 6× smaller with little accuracy loss.

#### 2. Cross-Layer Parameter Sharing

ALBERT shares **all** parameters across all 12 encoder layers (attention + FFN). The model has 12 layers in the computation graph but they are the same layer applied 12 times.

```
Layer 1 weights = Layer 2 weights = ... = Layer 12 weights
```

This reduces parameters dramatically while maintaining representational capacity.

#### 3. Sentence Order Prediction (SOP) replaces NSP

SOP is a harder task: given two consecutive sentences, predict which ordering is correct (original vs. swapped). Compared to NSP, SOP cannot be solved by topic detection alone.

### Model Variants

| Model | Parameters | GLUE |
|---|---|---|
| ALBERT-base | 12 M | 84.6 |
| ALBERT-large | 18 M | 86.5 |
| ALBERT-xlarge | 60 M | 87.9 |
| ALBERT-xxlarge | 235 M | **90.9** |

Note: parameter count is misleading — shared layers mean ALBERT-xxlarge has the same inference compute as a 235M non-shared model.

```python
from transformers import AlbertForSequenceClassification, AlbertTokenizer

tokenizer = AlbertTokenizer.from_pretrained("albert/albert-base-v2")
model = AlbertForSequenceClassification.from_pretrained("albert/albert-base-v2", num_labels=3)
```

---

## DeBERTa v3 (2021)

**Paper:** He et al., "DeBERTaV3: Improving DeBERTa using ELECTRA-Style Pre-Training with Gradient-Disentangled Embedding Sharing"  
**By:** Microsoft Research  
**HF Hub:** `microsoft/deberta-v3-base`, `microsoft/deberta-v3-large`

### Disentangled Attention (DeBERTa v1)

Standard BERT encodes each token as a single vector combining content and position. DeBERTa uses **two separate vectors** per token — one for content ($H_i$) and one for position ($P_i$) — and computes attention using all four combinations:

$$A_{i,j} = H_i H_j^\top + H_i P_{j-i}^\top + P_{i-j} H_j^\top$$

| Term | Meaning |
|---|---|
| $H_i H_j^\top$ | content-to-content |
| $H_i P_{j-i}^\top$ | content-to-position |
| $P_{i-j} H_j^\top$ | position-to-content |

Position vectors are relative (distance $j-i$), not absolute. This explicitly models the interaction between a token's content and its position relative to other tokens.

### ELECTRA-Style Pre-training (DeBERTa v3)

DeBERTa v3 replaces MLM with **Replaced Token Detection (RTD)**:

1. A small generator (DeBERTa-small) fills `[MASK]` positions with plausible tokens
2. The main discriminator DeBERTa-large must detect which tokens are "fake" (generated) vs "real"
3. Loss is binary classification for every token — uses **all** tokens, not just 15% masked positions

This is more sample-efficient than MLM: every token in every sequence contributes to the loss.

### Gradient-Disentangled Embedding Sharing (GDES)

DeBERTa v3 shares token embeddings between generator and discriminator but blocks gradients flowing from the discriminator back through the shared embeddings (to prevent the generator from becoming too good, which would make the discriminator's task trivial).

### Performance

| Task | BERT-base | RoBERTa-base | DeBERTa-v3-base |
|---|---|---|---|
| MNLI (acc) | 84.6 | 87.6 | **90.6** |
| SQuAD v2 (F1) | 76.3 | 86.8 | **88.4** |
| RACE (acc) | 65.0 | 73.0 | **81.8** |
| GLUE (avg) | 84.6 | 88.1 | **91.9** |

DeBERTa-v3-large achieves **SuperGLUE score of 90.3**, matching human performance on some tasks.

```python
from transformers import DebertaV2ForSequenceClassification, DebertaV2Tokenizer

tokenizer = DebertaV2Tokenizer.from_pretrained("microsoft/deberta-v3-base")
model = DebertaV2ForSequenceClassification.from_pretrained(
    "microsoft/deberta-v3-base",
    num_labels=3,
)
```

---

## Head-to-Head Comparison

| Model | Params | GLUE | Speed (rel) | Key innovation |
|---|---|---|---|---|
| BERT-base | 110 M | 84.6 | 1.0× | Original bidirectional encoder |
| RoBERTa-base | 125 M | 88.1 | 1.0× | Better training recipe, more data |
| DistilBERT | 66 M | 82.8 | 1.6× | Knowledge distillation |
| ALBERT-base | 12 M | 84.6 | 0.9× | Parameter sharing, factored embeddings |
| ALBERT-xxlarge | 235 M | 90.9 | 0.4× | SOP + large capacity |
| DeBERTa-v3-base | 86 M | 91.9 | 0.85× | Disentangled attention + RTD |

---

## Practical Selection Guide

```
Need best accuracy?            → DeBERTa-v3-large or DeBERTa-v3-base
General production NLP?        → RoBERTa-base (robust, well-supported)
Fast inference / edge?         → DistilBERT or DistilRoBERTa
Parameter-efficient deployment → ALBERT-base (only 12M params)
Multilingual?                  → bert-base-multilingual-cased or XLM-RoBERTa-base
Domain-specific tasks?
  Biomedical:  BioBERT / PubMedBERT
  Legal:       legal-bert-base-uncased
  Financial:   FinBERT / FLANG-BERT
  Scientific:  SciBERT
```

---

## See Also

- [BERT Architecture](../architecture) — baseline architecture all variants build on
- [Sentence-BERT](../sbert) — variants optimized for semantic similarity and embeddings
- [BERT in RAG](../bert-in-rag) — which BERT family model to use for retrieval vs. reranking
