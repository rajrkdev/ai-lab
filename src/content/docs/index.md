---
layout: default
title: Home
---

## Interactive Diagrams

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

## RAG Guides

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

### [Word vs Sentence Embeddings](rag/word-vs-sentence-embeddings.html)
Visual comparison of word-level and sentence-level embedding strategies — how they differ in scope, use case, and representation quality.

### [PageIndex — Vectorless, Reasoning-Based RAG](rag/pageindex-vectorless-rag.html)
Interactive visual guide to PageIndex by Vectify AI: how LLM reasoning over hierarchical document trees replaces vector similarity search, achieving 98.7% accuracy on FinanceBench. Covers architecture, failure modes of vector RAG, and decision framework for insurance/financial documents.

---

## BERT Guides

### [BERT Full Interactive Diagram](bert/bert-full-diagram.html)
End-to-end visual walkthrough of the BERT architecture — embeddings, encoder stack, attention heads, and how tokens flow through the model.

### [BERT Tokenizer Deep Dive](bert/bert-tokenizer-deep-dive.html)
Interactive exploration of WordPiece tokenization: how BERT splits text into subword tokens, handles unknown words, and builds vocabulary.

### [BERT Encoder Block Deep Dive](bert/bert-encoder-deep-dive.html)
Detailed visual breakdown of a single BERT encoder block — multi-head self-attention, feed-forward layers, residual connections, and layer normalization.

---

## LangChain Guides

### [LangChain Reference — From Zero to Pro](langchain/langchain.html)
Interactive end-to-end LangChain course: core primitives, chains, agents, memory, RAG pipelines, and production patterns. Built for developers who already know LLM APIs and want to move fast with LangChain.

### [LangChain Deep Reference Guide](langchain/langchain-reference)
Comprehensive reference covering LangChain architecture, LCEL, retrieval patterns, agents, tool use, and production trade-offs. Includes code examples, decision rationale, and comparisons for every major component.

---

## Cert Prep — Claude Certified Architect

### [Domain Quiz — All Domains](cert/cert-quiz-all-domains.html)
Interactive multiple-choice quiz covering all five exam domains: Agentic Architecture, Tool Design & MCP, Claude Code Config, Prompt Engineering, and Context Management.

### [Visual Learning — All Domains](cert/cert-visual-learning.html)
Comprehensive visual reference covering all five domains in a single tabbed interface — agentic loops, multi-agent patterns, hooks, tool design, config hierarchy, structured output, and context management.

### [Domain 1: Agentic Architecture — Visual Guide](cert/d1-visual-agentic-architecture.html)
Deep visual guide to Domain 1 (27% of exam): agentic loop, stop_reason handling, multi-agent patterns, context passing, hooks system, enforcement, decomposition, sessions, and anti-patterns.

### [Domains 2–5: Visual Learning Guide](cert/d2-d5-visual-learning.html)
Visual learning guide for Domains 2 through 5: Tool Design & MCP, Claude Code Config, Prompt & Output, and Context & Reliability.

### [Complete Study Guide](cert/cert-complete-study-guide)
Comprehensive study guide covering all 28 exam task statements with exact syntax, code examples, and the precise distinctions the exam tests. Covers all five domains with weighting.

### [Gap-Fill Study Reference](cert/cert-gap-fill-reference)
Targeted reference for 28 knowledge gaps across five domains — exact code definitions, JSON structures, API flows, and configuration syntax from official Anthropic documentation.

### [Study Roadmap](cert/cert-study-roadmap)
Detailed study roadmap with honest domain-by-domain assessment, priority weighting, and structured preparation plan for the Claude Certified Architect exam.

### [Domain 1: Agentic Architecture — Study Guide](cert/domain-1-agentic-architecture)
In-depth study guide for Domain 1 (27%): agentic loop internals, Claude Agent SDK specifics, multi-agent orchestration, hooks, and hub-and-spoke coordinator patterns.

### [Domain 2: Tool Design & MCP — Study Guide](cert/domain-2-tool-design-mcp)
Study guide for Domain 2 (18%): tool descriptions, isError flag, tool_choice, MCP configuration, built-in tools, and tool design best practices.

### [Domain 3: Claude Code Config — Study Guide](cert/domain-3-claude-code-config)
Study guide for Domain 3 (20%): CLAUDE.md hierarchy, Rules, Skills, settings.json, and the complete configuration precedence model.

### [Domain 4: Prompt Engineering — Study Guide](cert/domain-4-prompt-engineering)
Study guide for Domain 4 (20%): structured output, XML tags, chain-of-thought, few-shot examples, and prompt engineering patterns.

### [Domain 5: Context Management & Reliability — Study Guide](cert/domain-5-context-reliability)
Study guide for Domain 5 (15%): context window management, token budgets, reliability patterns, and long-horizon task handling.

### [Master Study Guide](cert/master-study-guide)
Concise master reference: exam format, passing score, domain weights, and quick-lookup summaries for all five domains.

---

## Prompts & Templates

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
| [Word vs Sentence Embeddings](rag/word-vs-sentence-embeddings.html) | RAG | Word-level vs sentence-level embedding comparison |
| [PageIndex — Vectorless RAG](rag/pageindex-vectorless-rag.html) | RAG | Reasoning-based RAG replacing vector similarity |
| [LangChain Reference](langchain/langchain.html) | LangChain | End-to-end interactive LangChain course |
| [LangChain Reference Guide](langchain/langchain-reference) | LangChain | Architecture, LCEL, agents, production patterns |
| [BERT Full Diagram](bert/bert-full-diagram.html) | BERT | End-to-end BERT architecture walkthrough |
| [BERT Tokenizer](bert/bert-tokenizer-deep-dive.html) | BERT | WordPiece tokenization interactive guide |
| [BERT Encoder Block](bert/bert-encoder-deep-dive.html) | BERT | Single encoder block visual breakdown |
| [Cert Quiz — All Domains](cert/cert-quiz-all-domains.html) | Cert | Interactive multiple-choice quiz for all 5 domains |
| [Visual Learning — All Domains](cert/cert-visual-learning.html) | Cert | Tabbed visual reference for all 5 exam domains |
| [D1 Visual — Agentic Architecture](cert/d1-visual-agentic-architecture.html) | Cert | Domain 1 deep visual guide (27% of exam) |
| [D2–D5 Visual Learning](cert/d2-d5-visual-learning.html) | Cert | Visual guide for Domains 2–5 |
| [Complete Study Guide](cert/cert-complete-study-guide) | Cert | All 28 task statements with code examples |
| [Gap-Fill Reference](cert/cert-gap-fill-reference) | Cert | 28 knowledge gaps with exact syntax |
| [Study Roadmap](cert/cert-study-roadmap) | Cert | Structured prep plan with domain assessment |
| [Domain 1 Guide](cert/domain-1-agentic-architecture) | Cert | Agentic Architecture & Orchestration |
| [Domain 2 Guide](cert/domain-2-tool-design-mcp) | Cert | Tool Design & MCP Integration |
| [Domain 3 Guide](cert/domain-3-claude-code-config) | Cert | Claude Code Configuration |
| [Domain 4 Guide](cert/domain-4-prompt-engineering) | Cert | Prompt Engineering & Structured Output |
| [Domain 5 Guide](cert/domain-5-context-reliability) | Cert | Context Management & Reliability |
| [Master Study Guide](cert/master-study-guide) | Cert | Exam format, weights, and quick summaries |
| [Learning Prompt Template](prompts/Learning-prompt-template) | Prompt | Reusable learning plan template |

---

## Current File Metadata

**File Name:** index.md
**Path:** `c:\Users\dearr\Documents\github\personal\index.md`

**Content:**
````markdown
---
layout: default
title: Home
---

## Interactive Diagrams

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

## RAG Guides

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

### [Word vs Sentence Embeddings](rag/word-vs-sentence-embeddings.html)
Visual comparison of word-level and sentence-level embedding strategies — how they differ in scope, use case, and representation quality.

### [PageIndex — Vectorless, Reasoning-Based RAG](rag/pageindex-vectorless-rag.html)
Interactive visual guide to PageIndex by Vectify AI: how LLM reasoning over hierarchical document trees replaces vector similarity search, achieving 98.7% accuracy on FinanceBench. Covers architecture, failure modes of vector RAG, and decision framework for insurance/financial documents.

---

## BERT Guides

### [BERT Full Interactive Diagram](bert/bert-full-diagram.html)
End-to-end visual walkthrough of the BERT architecture — embeddings, encoder stack, attention heads, and how tokens flow through the model.

### [BERT Tokenizer Deep Dive](bert/bert-tokenizer-deep-dive.html)
Interactive exploration of WordPiece tokenization: how BERT splits text into subword tokens, handles unknown words, and builds vocabulary.

### [BERT Encoder Block Deep Dive](bert/bert-encoder-deep-dive.html)
Detailed visual breakdown of a single BERT encoder block — multi-head self-attention, feed-forward layers, residual connections, and layer normalization.

---

## LangChain Guides

### [LangChain Reference — From Zero to Pro](langchain/langchain.html)
Interactive end-to-end LangChain course: core primitives, chains, agents, memory, RAG pipelines, and production patterns. Built for developers who already know LLM APIs and want to move fast with LangChain.

### [LangChain Deep Reference Guide](langchain/langchain-reference)
Comprehensive reference covering LangChain architecture, LCEL, retrieval patterns, agents, tool use, and production trade-offs. Includes code examples, decision rationale, and comparisons for every major component.

---

## Cert Prep — Claude Certified Architect

### [Domain Quiz — All Domains](cert/cert-quiz-all-domains.html)
Interactive multiple-choice quiz covering all five exam domains: Agentic Architecture, Tool Design & MCP, Claude Code Config, Prompt Engineering, and Context Management.

### [Visual Learning — All Domains](cert/cert-visual-learning.html)
Comprehensive visual reference covering all five domains in a single tabbed interface — agentic loops, multi-agent patterns, hooks, tool design, config hierarchy, structured output, and context management.

### [Domain 1: Agentic Architecture — Visual Guide](cert/d1-visual-agentic-architecture.html)
Deep visual guide to Domain 1 (27% of exam): agentic loop, stop_reason handling, multi-agent patterns, context passing, hooks system, enforcement, decomposition, sessions, and anti-patterns.

### [Domains 2–5: Visual Learning Guide](cert/d2-d5-visual-learning.html)
Visual learning guide for Domains 2 through 5: Tool Design & MCP, Claude Code Config, Prompt & Output, and Context & Reliability.

### [Complete Study Guide](cert/cert-complete-study-guide)
Comprehensive study guide covering all 28 exam task statements with exact syntax, code examples, and the precise distinctions the exam tests. Covers all five domains with weighting.

### [Gap-Fill Study Reference](cert/cert-gap-fill-reference)
Targeted reference for 28 knowledge gaps across five domains — exact code definitions, JSON structures, API flows, and configuration syntax from official Anthropic documentation.

### [Study Roadmap](cert/cert-study-roadmap)
Detailed study roadmap with honest domain-by-domain assessment, priority weighting, and structured preparation plan for the Claude Certified Architect exam.

### [Domain 1: Agentic Architecture — Study Guide](cert/domain-1-agentic-architecture)
In-depth study guide for Domain 1 (27%): agentic loop internals, Claude Agent SDK specifics, multi-agent orchestration, hooks, and hub-and-spoke coordinator patterns.

### [Domain 2: Tool Design & MCP — Study Guide](cert/domain-2-tool-design-mcp)
Study guide for Domain 2 (18%): tool descriptions, isError flag, tool_choice, MCP configuration, built-in tools, and tool design best practices.

### [Domain 3: Claude Code Config — Study Guide](cert/domain-3-claude-code-config)
Study guide for Domain 3 (20%): CLAUDE.md hierarchy, Rules, Skills, settings.json, and the complete configuration precedence model.

### [Domain 4: Prompt Engineering — Study Guide](cert/domain-4-prompt-engineering)
Study guide for Domain 4 (20%): structured output, XML tags, chain-of-thought, few-shot examples, and prompt engineering patterns.

### [Domain 5: Context Management & Reliability — Study Guide](cert/domain-5-context-reliability)
Study guide for Domain 5 (15%): context window management, token budgets, reliability patterns, and long-horizon task handling.

### [Master Study Guide](cert/master-study-guide)
Concise master reference: exam format, passing score, domain weights, and quick-lookup summaries for all five domains.

---

## Prompts & Templates

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
| [Word vs Sentence Embeddings](rag/word-vs-sentence-embeddings.html) | RAG | Word-level vs sentence-level embedding comparison |
| [PageIndex — Vectorless RAG](rag/pageindex-vectorless-rag.html) | RAG | Reasoning-based RAG replacing vector similarity |
| [LangChain Reference](langchain/langchain.html) | LangChain | End-to-end interactive LangChain course |
| [LangChain Reference Guide](langchain/langchain-reference) | LangChain | Architecture, LCEL, agents, production patterns |
| [BERT Full Diagram](bert/bert-full-diagram.html) | BERT | End-to-end BERT architecture walkthrough |
| [BERT Tokenizer](bert/bert-tokenizer-deep-dive.html) | BERT | WordPiece tokenization interactive guide |
| [BERT Encoder Block](bert/bert-encoder-deep-dive.html) | BERT | Single encoder block visual breakdown |
| [Cert Quiz — All Domains](cert/cert-quiz-all-domains.html) | Cert | Interactive multiple-choice quiz for all 5 domains |
| [Visual Learning — All Domains](cert/cert-visual-learning.html) | Cert | Tabbed visual reference for all 5 exam domains |
| [D1 Visual — Agentic Architecture](cert/d1-visual-agentic-architecture.html) | Cert | Domain 1 deep visual guide (27% of exam) |
| [D2–D5 Visual Learning](cert/d2-d5-visual-learning.html) | Cert | Visual guide for Domains 2–5 |
| [Complete Study Guide](cert/cert-complete-study-guide) | Cert | All 28 task statements with code examples |
| [Gap-Fill Reference](cert/cert-gap-fill-reference) | Cert | 28 knowledge gaps with exact syntax |
| [Study Roadmap](cert/cert-study-roadmap) | Cert | Structured prep plan with domain assessment |
| [Domain 1 Guide](cert/domain-1-agentic-architecture) | Cert | Agentic Architecture & Orchestration |
| [Domain 2 Guide](cert/domain-2-tool-design-mcp) | Cert | Tool Design & MCP Integration |
| [Domain 3 Guide](cert/domain-3-claude-code-config) | Cert | Claude Code Configuration |
| [Domain 4 Guide](cert/domain-4-prompt-engineering) | Cert | Prompt Engineering & Structured Output |
| [Domain 5 Guide](cert/domain-5-context-reliability) | Cert | Context Management & Reliability |
| [Master Study Guide](cert/master-study-guide) | Cert | Exam format, weights, and quick summaries |
| [Learning Prompt Template](prompts/Learning-prompt-template) | Prompt | Reusable learning plan template |

---
````
