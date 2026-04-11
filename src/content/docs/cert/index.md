---
title: "Cert Prep — Claude Certified Architect: Foundations"
description: "Complete exam preparation for the Claude Certified Architect: Foundations certification — all five domains, interactive quizzes, visual guides, and a 21-day study roadmap."
sidebar:
  order: 0
---

# Claude Certified Architect: Foundations — Exam Prep Hub

## What This Certification Tests

The **Claude Certified Architect: Foundations** exam validates your ability to design, build, and configure real-world AI systems using the Claude ecosystem. It goes beyond API knowledge — it tests architectural judgment, tradeoff reasoning, and implementation correctness.

```
┌────────────────────────────────────────────────────────────────────┐
│          EXAM AT A GLANCE                                          │
│                                                                    │
│  Format:        60 multiple-choice questions                       │
│  Passing Score: 720 / 1000                                         │
│  Question Type: One correct answer + three plausible distractors   │
│  Scenarios:     4 random scenarios drawn from a pool of 6          │
│  Guessing:      No penalty — never leave blank                     │
│  Pacing:        ~1–1.5 minutes per question                        │
└────────────────────────────────────────────────────────────────────┘
```

---

## Domain Weights — Where to Spend Your Study Time

```
DOMAIN                                    WEIGHT    APPROX. QUESTIONS
─────────────────────────────────────────────────────────────────────
D1: Agentic Architecture & Orchestration   27%      ~16 questions  ◄ TOP PRIORITY
D3: Claude Code Config & Workflows         20%      ~12 questions
D4: Prompt Engineering & Structured Output 20%      ~12 questions
D2: Tool Design & MCP Integration          18%      ~11 questions
D5: Context Management & Reliability       15%       ~9 questions
─────────────────────────────────────────────────────────────────────
TOTAL                                     100%       60 questions
```

Study D1 first and longest. It covers the most testable concepts and is the hardest to cram.

---

## The 6 Exam Scenarios (One of These Is Your Test)

Each exam draws 4 random scenarios from these 6. Questions are scenario-specific — the context eliminates wrong answers.

| # | Scenario | Primary Domains |
|---|---|---|
| 1 | Customer Support Resolution Agent | D1, D2, D5 |
| 2 | Code Generation Assistant | D3, D4 |
| 3 | Multi-Agent Research Pipeline | D1, D2, D5 |
| 4 | Developer Productivity Tooling | D2, D3 |
| 5 | CI/CD Automation & PR Review | D3, D4 |
| 6 | Structured Data Extraction | D4, D5 |

---

## Study Materials in This Section

### Domain Deep Dives
- **[Domain 1 — Agentic Architecture & Orchestration](./domain-1-agentic-architecture)** · 27% · Agentic loops, multi-agent patterns, hooks, session management
- **[Domain 2 — Tool Design & MCP Integration](./domain-2-tool-design-mcp)** · 18% · Tool descriptions, MCP servers, error handling, tool_choice
- **[Domain 3 — Claude Code Configuration & Workflows](./domain-3-claude-code-config)** · 20% · CLAUDE.md hierarchy, rules, skills, CI/CD
- **[Domain 4 — Prompt Engineering & Structured Output](./domain-4-prompt-engineering)** · 20% · Few-shot, tool_use schemas, batch API, validation loops
- **[Domain 5 — Context Management & Reliability](./domain-5-context-reliability)** · 15% · Context budgets, escalation, error propagation, provenance

### Quick Reference
- **[Master Study Guide](./master-study-guide)** · 20 rules covering 80% of the exam + distractor patterns
- **[Complete Study Guide](./cert-complete-study-guide)** · Every task statement with exact syntax and code examples
- **[Gap-Fill Reference](./cert-gap-fill-reference)** · 28 knowledge gaps with exact type definitions and API flows
- **[21-Day Study Roadmap](./cert-study-roadmap)** · Phase-by-phase plan from foundations to exam simulation

### Interactive Tools
- **[Domain Quiz — All Domains](./cert-quiz)** · Practice questions with explanations
- **[Visual Learning — All Domains](./cert-visual)** · Tabbed visual reference
- **[Domain 1 Visual Guide](./d1-visual)** · Deep dive on the highest-weight domain
- **[Domains 2–5 Visual Guide](./d2-d5-visual)** · Tool design through context management

---

## The 5 Cross-Cutting Exam Patterns

Every hard question is a tradeoff. Know these patterns cold — they appear across all domains.

```
PATTERN 1: DETERMINISTIC vs PROBABILISTIC
  Hooks = guaranteed compliance (always)
  Prompt instructions = probabilistic compliance (sometimes fails)
  → When financial/compliance stakes exist → always choose hooks

PATTERN 2: ISOLATION
  Subagent context isolation (D1) — subagents start fresh, no parent history
  context: fork for skills (D3) — isolates verbose output from main context
  Independent review instances (D4) — fresh session reviews code better
  Session context isolation in CI (D3) — generate and review are separate

PATTERN 3: STRUCTURED METADATA
  Claim-source mappings (D5) — preserve attribution through synthesis
  Structured errors with errorCategory (D2) — enables smart recovery
  detected_pattern fields (D4) — powers false positive analysis
  custom_id for batch correlation (D4) — connects requests to results

PATTERN 4: PROPORTIONATE RESPONSE
  Fix tool descriptions BEFORE building routing layers (D2)
  Add explicit criteria BEFORE deploying classifiers (D5)
  Test on sample BEFORE batch-processing 10K documents (D4)
  Use existing tools BEFORE creating new abstractions

PATTERN 5: ANTI-PATTERNS AS DISTRACTORS
  Same-session self-review | Sentiment-based escalation
  "Be conservative" instructions | Arbitrary iteration caps
  Suppressing errors as success | Parsing natural language for routing
```

---

## Exam Day Elimination Strategy

```
STEP 1: Read the scenario description fully before any questions
        → Key details in the scenario text eliminate 1–2 wrong answers

STEP 2: On each question, eliminate distractors:
        ✗ Over-engineered option (ML classifier when description fix exists)
        ✗ Prompt-only fix for compliance/financial scenario (hooks needed)
        ✗ Option that blames downstream when coordinator is the problem
        ✗ Non-existent flags (CLAUDE_HEADLESS=true, --batch)

STEP 3: "Most effective FIRST STEP" → always the lowest-effort, highest-leverage fix

STEP 4: Stuck? Eliminate what you can → pick best remaining → move on
        (No penalty for guessing — always answer)
```

---

## One-Page Cheat Sheet

| Domain | The One Thing | Exam Trap |
|---|---|---|
| **D1** | `stop_reason` drives the loop — never parse text | "Check if response contains 'done'" |
| **D1** | Hooks = deterministic; prompts = probabilistic | "Add mandatory instruction to system prompt" |
| **D1** | Subagents don't inherit coordinator context | Assuming subagents see parent conversation |
| **D2** | Tool descriptions are the #1 selection mechanism | "Add few-shot examples" as first fix |
| **D2** | `isError: true` for failures; `isError: false` for empty results | Conflating timeout with no-results |
| **D2** | `tool_choice: "any"` guarantees structured output | Using "auto" when structured output required |
| **D3** | `~/.claude/CLAUDE.md` NOT shared via version control | Thinking user-level config applies to team |
| **D3** | `-p` flag for CI non-interactive mode | `CLAUDE_HEADLESS=true` (doesn't exist) |
| **D4** | `tool_use` eliminates syntax errors, not semantic errors | "Schema validates all correctness" |
| **D4** | Batch API: 50% savings, 24hr, no multi-turn | Using batch for pre-merge blocking checks |
| **D5** | Extract case facts to persistent block outside summarized history | "Increase context window" |
| **D5** | 97% aggregate accuracy can mask 72% on one segment | Automating on aggregate accuracy alone |
