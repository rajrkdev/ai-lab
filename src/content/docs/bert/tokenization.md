---
title: WordPiece Tokenization
description: Deep dive into BERT's WordPiece tokenizer — vocabulary construction algorithm, subword tokenization, special tokens, padding, truncation, and attention masks.
sidebar:
  order: 3
---

## What is WordPiece?

BERT uses **WordPiece tokenization**, a subword algorithm that balances vocabulary size against out-of-vocabulary coverage. Instead of keeping full words or splitting into individual characters, WordPiece splits rare/unknown words into smaller pieces while keeping common words intact.

WordPiece was originally developed by Google for the Japanese/Korean segmentation problem (2016), then adapted for BERT's multilingual vocabulary.

---

## The Core Idea

```
"unhappiness"  →  ["un", "##happiness"]         # prefix known
"tokenization" →  ["token", "##ization"]        # common prefix
"huggingface"  →  ["hugging", "##face"]          # split at boundary
"supercalifragilistic" → ["super", "##cal", "##if", "##rag", "##ili", "##stic"]
```

The `##` prefix marks **continuation subwords** — pieces that are not the start of a word.

---

## Vocabulary Construction Algorithm

WordPiece builds the vocabulary offline from a large corpus using a bottom-up greedy merge strategy similar to BPE:

### Step 1: Initialize

Start with every individual character in the corpus as a separate token. Also add special tokens: `[PAD]`, `[UNK]`, `[CLS]`, `[SEP]`, `[MASK]`.

### Step 2: Score candidate merges

For every adjacent pair of tokens $(t_i, t_j)$, compute:

$$\text{score}(t_i, t_j) = \frac{\text{count}(t_i t_j)}{\text{count}(t_i) \times \text{count}(t_j)}$$

This is a **likelihood ratio** — it favors pairs that co-occur far more often than expected by chance.

### Step 3: Merge & repeat

Merge the pair with the highest score into a new token. Add it to the vocabulary. Repeat until vocabulary size reaches the target (30,522 for `bert-base-uncased`, 28,996 for `bert-base-cased`).

**Key difference from BPE:** BPE uses raw co-occurrence count; WordPiece uses the normalized score above, making it more robust to frequent-but-meaningless pairs.

---

## Tokenization Algorithm (Inference)

At inference time, given a new word, BERT tokenizes with a **greedy longest-match-first** (MaxMatch) strategy:

```python
def wordpiece_tokenize(word, vocab, unk="[UNK]"):
    tokens = []
    start = 0
    while start < len(word):
        end = len(word)
        cur_substr = None
        while start < end:
            substr = word[start:end]
            if start > 0:
                substr = "##" + substr
            if substr in vocab:
                cur_substr = substr
                break
            end -= 1
        if cur_substr is None:
            return [unk]  # entire word is unknown
        tokens.append(cur_substr)
        start = end
    return tokens
```

**Complexity:** O(n²) per word in worst case, where n is word length — acceptable since words are short.

---

## Special Tokens

| Token | ID (uncased) | Purpose |
|---|---|---|
| `[PAD]` | 0 | Pads sequences to uniform length |
| `[UNK]` | 100 | Unknown characters/tokens |
| `[CLS]` | 101 | Classification token — always first |
| `[SEP]` | 102 | Separates two sequences |
| `[MASK]` | 103 | Masked position during MLM pre-training |

---

## Full Tokenization Pipeline

```python
from transformers import BertTokenizer

tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

# ─── Single sentence ────────────────────────────────────────
text = "The quick brown fox"
tokens = tokenizer.tokenize(text)
# ['the', 'quick', 'brown', 'fox']

ids = tokenizer.convert_tokens_to_ids(tokens)
# [1996, 4248, 2829, 4419]

# ─── Full encode (adds [CLS], [SEP], padding, attention_mask)
enc = tokenizer(
    text,
    max_length=16,
    padding="max_length",
    truncation=True,
    return_tensors="pt",
)
# enc.input_ids:      [[101, 1996, 4248, 2829, 4419, 102, 0, 0, ...]]
# enc.attention_mask: [[1,   1,    1,    1,    1,    1,  0, 0, ...]]
# enc.token_type_ids: [[0,   0,    0,    0,    0,    0,  0, 0, ...]]  ← segment A

# ─── Two sentences ──────────────────────────────────────────
enc2 = tokenizer(
    "The cat sat.",
    "The dog ran.",
    max_length=20,
    padding="max_length",
    truncation=True,
    return_tensors="pt",
)
# input_ids:      [CLS] The cat sat . [SEP] the dog ran . [SEP] [PAD] ...
# token_type_ids: 0     0   0   0  0  0     1   1   1  1  1     0    ...
```

---

## Attention Mask

The `attention_mask` is a binary tensor that tells the model which positions are real tokens (1) and which are padding (0). BERT's self-attention applies a large negative number (−10,000) to masked positions before the softmax so they contribute ~0 to the output:

$$\text{score}_{ij} = \frac{Q_i \cdot K_j}{\sqrt{d_k}} + M_{ij}$$

where $M_{ij} = 0$ for real tokens and $M_{ij} = -10^4$ for padding positions.

---

## Handling Long Documents

BERT's maximum sequence length is **512 tokens** (including `[CLS]` and `[SEP]`). For longer documents:

| Strategy | Description |
|---|---|
| **Truncation** | Keep first 510 tokens (default) |
| **Sliding window** | Overlap windows, aggregate predictions |
| **Hierarchical** | Chunk → encode chunks → attend over chunk vectors |
| **Long-sequence models** | Longformer (4,096), BigBird (4,096), LED (16,384) |

```python
# Sliding window for long documents
from transformers import BertTokenizerFast

tokenizer = BertTokenizerFast.from_pretrained("bert-base-uncased")
long_text = "..." * 2000  # very long document

# Stride overlaps by 128 tokens to avoid losing context at boundaries
encoding = tokenizer(
    long_text,
    max_length=512,
    stride=128,
    return_overflowing_tokens=True,
    return_offsets_mapping=True,
    padding="max_length",
    truncation=True,
)
# encoding["input_ids"] is now a list of windows
print(f"Number of windows: {len(encoding['input_ids'])}")
```

---

## Casing: Uncased vs Cased

| Model | Lowercases input | Strips accents | Use when |
|---|---|---|---|
| `bert-base-uncased` | Yes | Yes | Most English tasks (casing rarely matters) |
| `bert-base-cased` | No | No | NER, POS, tasks where casing is a signal |
| `bert-base-multilingual-cased` | No | No | 104 languages, always prefer cased for multilingual |

---

## Subword Statistics (bert-base-uncased)

- Vocabulary size: **30,522**
- Character tokens: ~100 (a–z, digits, punctuation)
- Single-character subwords (##a, ##b, ...): ~100
- Common full words: ~20,000
- Rare/compound continuation tokens: ~10,000

Average English text tokenizes at roughly **1.3 tokens per word** with BERT's WordPiece (vs. ~1.0 for character-level, ~1.0 for word-level on in-vocabulary text).

---

## Fast vs Slow Tokenizer

Hugging Face provides two implementations:

| | `BertTokenizer` (slow) | `BertTokenizerFast` (fast) |
|---|---|---|
| Backend | Pure Python | Rust (via tokenizers library) |
| Speed | ~1,000 words/s | ~100,000 words/s |
| Offset mapping | Manual | Built-in |
| Recommended for | Debugging | Production |

```python
from transformers import BertTokenizerFast
tokenizer = BertTokenizerFast.from_pretrained("bert-base-uncased")
enc = tokenizer("Hello world", return_offsets_mapping=True)
print(enc.offset_mapping)  # [(0,5), (6,11)] — character spans
```

---

## See Also

- [BERT Architecture](./architecture) — how token IDs flow through the encoder
- [Pre-training Objectives](./pretraining) — the \[MASK\] token's role in MLM
