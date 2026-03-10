---
layout: default
title: Home
---

# Claude Code Mastery

A comprehensive resource for Claude Code — configuration, architecture, interactive diagrams, RAG guides, and training materials.

---

## Interactive Diagrams — Claude Code

Visual tools for understanding how Claude Code loads, prioritizes, and processes its configuration files.

### [Architecture Diagram — Full Lifecycle](diagrams/architecture.html)
Visual flow of how all 16 markdown file types load and connect across the session lifecycle. Includes token budget breakdown and decision guide.

### [File Catalog — Interactive](diagrams/claude-code-architecture.html)
Browse all 16 markdown file types with full details: scope, priority, token cost, who creates them, and usage examples. Includes a clickable session flow diagram.

### [Precedence Diagram — Full Hierarchy Guide](diagrams/claude-code-precedence-diagram.html)
Complete file hierarchy and precedence guide with interactive pyramid, conflict resolution scenarios, loading timeline, settings.json hierarchy, directory map, and override rules table.

### [Override Test Lab](diagrams/override-test-lab.html)
12 hands-on test scenarios for every precedence rule — with exact file contents, prompts, and verification steps to run in your own Claude Code setup.

### [Context Engineering Guide](diagrams/context-engineering-guide.html)
Deep dive into context engineering principles and techniques — how to shape what Claude sees and how it reasons.

---

## Reference Guides

In-depth written documentation on Claude Code configuration, file types, and architecture decisions.

### [Complete Markdown Files Catalog](docs/claude-code-all-markdown-files-catalog)
Every markdown file Claude Code recognizes — complete catalog with locations, priorities, token impact, and examples. Your definitive reference for the entire configuration surface.

### [CLAUDE.md vs Skills vs Rules — Architecture Guide](docs/claude-code-config-guide)
Deep dive into the three core configuration mechanisms: CLAUDE.md (always-on memory), Rules (modular path-scoped instructions), and Skills (on-demand expertise packages). Includes decision frameworks, token budgets, and real-world examples.

### [Claude Code Training Program](docs/Claude-Training)
An 8-module training program covering CLI mastery, agent teams, hooks, MCP servers, prompt engineering, RAG systems, CI/CD integration, and enterprise architecture patterns. Built for experienced developers ready to operate at an elite level.

### [Concept Validation Report](docs/validation-report)
A detailed authenticity review of every major concept in this repository — 119 claims evaluated against official Anthropic documentation, with automated CI checks for links, markdown structure, and key fact patterns.

### [Override Test Lab — Reference Doc](reference/override-test-lab.docx)
Downloadable Word document version of the override test lab for offline reference or sharing with your team.

---

## RAG Interactive Guides

Interactive visual explainers for Retrieval-Augmented Generation — covering architectures, embedding models, and retrieval strategies.

### [RAG Academy](rag/rag-academy.html)
End-to-end interactive course on RAG systems — from basic retrieval concepts to advanced pipeline design.

### [Naive RAG Explainer](rag/naive-rag-explainer.html)
Step-by-step visual walkthrough of how a basic RAG pipeline works: chunking, embedding, retrieval, and generation.

### [RAG Types — Generation Guide](rag/rag-types.html)
Survey of RAG architectures — naive, advanced, modular, and agentic — with diagrams comparing when to use each.

### [Memory-Augmented RAG](rag/memory-rag.html)
Interactive guide to adding persistent memory layers to RAG systems for multi-turn and long-horizon tasks.

### [RAG Speed vs Quality Comparison](rag/rag-speed-quality.html)
Interactive comparison of retrieval strategies across the speed–quality tradeoff spectrum.

### [How Embeddings Work — all-MiniLM-L6-v2](rag/all-MiniLM-L6-v2.html)
Visual, hands-on explainer for the all-MiniLM-L6-v2 embedding model: how text becomes vectors, cosine similarity, and the full RAG pipeline.

### [BGE-small-en-v1.5 — Deep Dive](rag/bge-small-en-v1.5.html)
Detailed interactive guide to BAAI's BGE-small-en-v1.5 embedding model: architecture, instruction-based query prefix, training methodology, benchmarks, and code examples.

---

## Prompts & Templates

Reusable prompt templates and research notes.

### [Learning Prompt Template](prompts/Learning-prompt-template)
A reusable template for creating personalized learning plans for any skill or subject area.

### [Hackathon SLM Prompt Notes](prompts/prompt)
Research and planning notes for building a small language model customer support chatbot in a 5-hour hackathon.

---

## Quick Reference

| Resource | Type | What You'll Find |
|----------|------|-----------------|
| [Architecture Diagram](diagrams/architecture.html) | Diagram | Full session lifecycle and file load order |
| [File Catalog — Interactive](diagrams/claude-code-architecture.html) | Diagram | All 16 file types with scope, priority, token cost |
| [Precedence Diagram](diagrams/claude-code-precedence-diagram.html) | Diagram | Full hierarchy, conflict resolution, override rules |
| [Override Test Lab](diagrams/override-test-lab.html) | Diagram | 12 hands-on test scenarios |
| [Context Engineering Guide](diagrams/context-engineering-guide.html) | Diagram | Context engineering principles and techniques |
| [Markdown Files Catalog](docs/claude-code-all-markdown-files-catalog) | Guide | All 16 file types Claude Code reads |
| [Config Architecture Guide](docs/claude-code-config-guide) | Guide | CLAUDE.md vs Rules vs Skills decision framework |
| [Training Program](docs/Claude-Training) | Guide | 8 modules from CLI shortcuts to multi-agent orchestration |
| [Validation Report](docs/validation-report) | Report | 119 claims reviewed against official documentation |
| [Override Test Lab (docx)](reference/override-test-lab.docx) | Reference | Downloadable Word document |
| [RAG Academy](rag/rag-academy.html) | RAG | End-to-end RAG course |
| [Naive RAG Explainer](rag/naive-rag-explainer.html) | RAG | Basic RAG pipeline visual walkthrough |
| [RAG Types](rag/rag-types.html) | RAG | Comparison of RAG architectures |
| [Memory-Augmented RAG](rag/memory-rag.html) | RAG | Persistent memory in RAG pipelines |
| [RAG Speed vs Quality](rag/rag-speed-quality.html) | RAG | Retrieval strategy tradeoffs |
| [all-MiniLM-L6-v2 Guide](rag/all-MiniLM-L6-v2.html) | RAG | Embedding model visual explainer |
| [BGE-small-en-v1.5 Guide](rag/bge-small-en-v1.5.html) | RAG | BAAI embedding model deep dive |
| [Learning Prompt Template](prompts/Learning-prompt-template) | Prompt | Reusable learning plan template |

---
