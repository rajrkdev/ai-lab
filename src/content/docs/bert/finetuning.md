---
title: Fine-tuning BERT
description: How to fine-tune BERT for text classification, Named Entity Recognition (NER), and extractive Question Answering (QA) — with full code examples and training tips.
sidebar:
  order: 5
---

## Fine-tuning Paradigm

BERT is pre-trained once and then **fine-tuned** for each downstream task by adding a task-specific head on top and training end-to-end on labeled data. Fine-tuning typically takes minutes to hours (vs. days for pre-training) because BERT already encodes rich linguistic knowledge.

```
Pre-trained BERT weights
        ↓
Task-specific head (new linear layer)
        ↓
Fine-tune entire model on labeled dataset
        ↓
Task-specific model
```

**General fine-tuning hyperparameters (from original BERT paper):**

| Parameter | Range | Typical |
|---|---|---|
| Learning rate | 2e-5, 3e-5, 5e-5 | 2e-5 |
| Epochs | 2–4 | 3 |
| Batch size | 16, 32 | 32 |
| Warmup steps | 6–10% of total steps | 10% |
| Weight decay | 0.01 | 0.01 |

Fine-tuning with a larger learning rate risks catastrophic forgetting of pre-trained weights; too small and the task-specific head won't train.

---

## 1. Text Classification

**Task:** Map an input sentence (or pair) to one of C classes.  
**Head:** Linear layer on the `[CLS]` token representation.

$$\hat{y} = \text{softmax}(W_c \, h_{\text{[CLS]}} + b_c)$$

where $W_c \in \mathbb{R}^{C \times H}$ and $h_{\text{[CLS]}} \in \mathbb{R}^H$ is the pooled CLS output.

### Example: Sentiment Analysis

```python
from transformers import BertForSequenceClassification, BertTokenizer, Trainer, TrainingArguments
from datasets import load_dataset
import torch

# 1. Load tokenizer and model
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels=2,          # binary: positive / negative
    id2label={0: "NEG", 1: "POS"},
    label2id={"NEG": 0, "POS": 1},
)

# 2. Tokenize dataset
dataset = load_dataset("imdb")

def tokenize(batch):
    return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=512)

tokenized = dataset.map(tokenize, batched=True)
tokenized = tokenized.rename_column("label", "labels")
tokenized.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

# 3. Training args
training_args = TrainingArguments(
    output_dir="./bert-sentiment",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    learning_rate=2e-5,
    warmup_ratio=0.1,
    weight_decay=0.01,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    fp16=True,
    logging_steps=100,
)

# 4. Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized["train"],
    eval_dataset=tokenized["test"],
)
trainer.train()

# 5. Inference
text = "This movie was absolutely fantastic!"
inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
with torch.no_grad():
    logits = model(**inputs).logits
predicted_class = logits.argmax(dim=-1).item()  # → 1 (POS)
```

### Multi-class and Multi-label

```python
# Multi-class (e.g., 5-star rating)
model = BertForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=5)

# Multi-label (e.g., topic tags — multiple labels per document)
model = BertForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels=10,
    problem_type="multi_label_classification",  # uses BCEWithLogitsLoss instead
)
```

---

## 2. Named Entity Recognition (NER)

**Task:** Assign a label to each token (B-PER, I-PER, B-ORG, O, etc.).  
**Head:** Linear layer applied to every token's hidden state.

$$\hat{y}_i = \text{softmax}(W_{\text{ner}} \, h_i + b_{\text{ner}}) \quad \forall\, i \in [1, n]$$

### BIO Tagging Scheme

| Tag | Meaning | Example |
|---|---|---|
| `O` | Outside any entity | "the", "is", "in" |
| `B-PER` | Beginning of PERSON entity | "Barack" |
| `I-PER` | Inside PERSON entity | "Obama" |
| `B-ORG` | Beginning of ORGANIZATION | "Google" |
| `B-LOC` | Beginning of LOCATION | "London" |

### Handling Subword Tokens in NER

WordPiece splits words into subwords, but NER labels are word-level. Convention: assign label to the **first subword**, mark continuation subwords `-100` (ignore in loss):

```
Word:      Barack  Obama  visited  New    York
Subwords:  Barack  Obama  visited  New    York
Labels:    B-PER   I-PER  O        B-LOC  I-LOC

# If "visiting" → ["visit", "##ing"]:
# "visit" → B-XXX label, "##ing" → -100 (ignored in loss)
```

```python
from transformers import BertForTokenClassification, DataCollatorForTokenClassification
import numpy as np

label_list = ["O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-LOC", "I-LOC"]
model = BertForTokenClassification.from_pretrained(
    "bert-base-cased",   # cased is important for NER!
    num_labels=len(label_list),
)

def tokenize_and_align_labels(examples):
    tokenized = tokenizer(
        examples["tokens"],
        is_split_into_words=True,   # input is already word-tokenized
        truncation=True,
        max_length=512,
    )
    all_labels = []
    for i, labels in enumerate(examples["ner_tags"]):
        word_ids = tokenized.word_ids(batch_index=i)
        aligned_labels = []
        prev_word_id = None
        for word_id in word_ids:
            if word_id is None:                        # [CLS], [SEP], [PAD]
                aligned_labels.append(-100)
            elif word_id != prev_word_id:              # first subword of a word
                aligned_labels.append(labels[word_id])
            else:                                      # continuation subword
                aligned_labels.append(-100)
            prev_word_id = word_id
        all_labels.append(aligned_labels)
    tokenized["labels"] = all_labels
    return tokenized

# Inference and decode
inputs = tokenizer("Barack Obama lives in Washington", return_tensors="pt")
with torch.no_grad():
    logits = model(**inputs).logits
predictions = logits.argmax(dim=-1)[0]
tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
for token, pred in zip(tokens, predictions):
    print(f"{token:15} {label_list[pred]}")
```

---

## 3. Extractive Question Answering

**Task:** Given a (question, context) pair, predict the start and end token positions of the answer span within the context.  
**Head:** Two linear layers — one predicts start logits, one predicts end logits for each token position.

$$s_i = W_s \, h_i, \quad e_i = W_e \, h_i$$

$$\text{start} = \arg\max_i \, s_i, \quad \text{end} = \arg\max_j \, e_j \quad (j \geq \text{start})$$

### SQuAD Format

```json
{
  "question": "What is the boiling point of water?",
  "context": "Water boils at 100 degrees Celsius at standard pressure.",
  "answers": {"answer_start": [15], "text": ["100 degrees Celsius"]}
}
```

### Fine-tuning on SQuAD

```python
from transformers import BertForQuestionAnswering, DefaultDataCollator

model = BertForQuestionAnswering.from_pretrained("bert-base-uncased")

def preprocess_qa(examples):
    # Tokenize question + context as a pair
    tokenized = tokenizer(
        examples["question"],
        examples["context"],
        max_length=384,
        stride=128,              # sliding window for long contexts
        truncation="only_second",
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding="max_length",
    )

    offset_mapping = tokenized.pop("offset_mapping")
    sample_map = tokenized.pop("overflow_to_sample_mapping")
    answers = examples["answers"]

    start_positions, end_positions = [], []
    for i, offset in enumerate(offset_mapping):
        sample_idx = sample_map[i]
        answer = answers[sample_idx]
        start_char = answer["answer_start"][0]
        end_char = start_char + len(answer["text"][0])

        sequence_ids = tokenized.sequence_ids(i)
        # Find start/end token indices within context (sequence_id == 1)
        context_start = next(j for j, s in enumerate(sequence_ids) if s == 1)
        context_end   = next(j for j in range(len(sequence_ids)-1, -1, -1) if sequence_ids[j] == 1)

        # Check if answer is within this window
        if offset[context_start][0] > end_char or offset[context_end][1] < start_char:
            start_positions.append(0); end_positions.append(0)
        else:
            start_idx = next(j for j in range(context_start, context_end+1) if offset[j][0] >= start_char)
            end_idx   = next(j for j in range(context_end, context_start-1, -1) if offset[j][1] <= end_char)
            start_positions.append(start_idx); end_positions.append(end_idx)

    tokenized["start_positions"] = start_positions
    tokenized["end_positions"]   = end_positions
    return tokenized

# Inference
question = "What is the boiling point of water?"
context  = "Water boils at 100 degrees Celsius at standard pressure."

inputs = tokenizer(question, context, return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)

start = outputs.start_logits.argmax()
end   = outputs.end_logits.argmax()
answer_tokens = inputs["input_ids"][0][start : end + 1]
print(tokenizer.decode(answer_tokens))  # "100 degrees Celsius"
```

---

## 4. Natural Language Inference (NLI)

**Task:** Given premise + hypothesis, classify as Entailment / Contradiction / Neutral.  
Uses the same `BertForSequenceClassification` with `num_labels=3`.

```python
model = BertForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=3)
# Input: encode (premise, hypothesis) as a sentence pair → [CLS] premise [SEP] hypothesis [SEP]
```

---

## 5. Sentence-Pair Regression

**Task:** Predict similarity score (e.g., STS-B: 0–5 float).  
Use `num_labels=1` + MSE loss:

```python
model = BertForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels=1,
    problem_type="regression",  # uses MSELoss automatically
)
```

---

## Training Tips

| Tip | Details |
|---|---|
| **Use fp16** | `fp16=True` in TrainingArguments — 2× faster, same accuracy |
| **Gradient accumulation** | Use `gradient_accumulation_steps=4` if GPU memory is limited |
| **Layer-wise LR decay** | Lower LR for early layers (they should change less) |
| **Early stopping** | `EarlyStoppingCallback(early_stopping_patience=2)` |
| **Seed everything** | BERT fine-tuning has high variance — run with 3 seeds and report mean ± std |
| **Cased vs uncased** | Use cased for NER and tasks where capital letters matter |

```python
# Layer-wise LR decay (LLRD)
def get_optimizer_grouped_parameters(model, learning_rate=2e-5, weight_decay=0.01, lr_decay=0.95):
    no_decay = ["bias", "LayerNorm.weight"]
    layers = [model.bert.embeddings] + list(model.bert.encoder.layer)
    layers_lrs = [learning_rate * (lr_decay ** (len(layers) - 1 - i)) for i in range(len(layers))]
    params = []
    for layer, lr in zip(layers, layers_lrs):
        params += [
            {"params": [p for n, p in layer.named_parameters() if not any(nd in n for nd in no_decay)], "lr": lr, "weight_decay": weight_decay},
            {"params": [p for n, p in layer.named_parameters() if any(nd in n for nd in no_decay)], "lr": lr, "weight_decay": 0.0},
        ]
    return params
```

---

## See Also

- [BERT Architecture](./architecture) — understanding the encoder that produces `h_[CLS]` and per-token vectors
- [BERT Variants](./variants) — RoBERTa, DistilBERT, ALBERT, DeBERTa as drop-in alternatives
- [BERT in RAG](./bert-in-rag) — using BERT-family models for retrieval and reranking
