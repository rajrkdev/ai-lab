---
title: "Claude Code: Context, Cost & Token Efficiency — Reference"
description: "Complete reference for context management, prompt caching, token budgets, model selection, and effort controls in Claude Code v2.1.92+. Covers all five CCA-F exam domains."
---

# Claude Code: Context, Cost & Token Efficiency — Complete Reference

> **Version:** April 2026 · Claude Code v2.1.92+  
> **CCA-F Domains:** D1 (Agentic Architecture), D2 (Claude Code Config), D3 (Prompt Engineering), D4 (Tool Design & MCP), D5 (Context Management & Reliability)  
> **Target audience:** Developers optimizing Claude Code usage for cost and token efficiency

---

## 1. Context Window Architecture

### 1.1 The Stateless Reconstruction Model

Claude Code is **stateless between turns**. Every API call reconstructs the entire payload from scratch — there is no persistent server-side conversation state. The full context is assembled in a deliberate order designed to maximize prompt cache prefix matching (most stable content first, most volatile last):

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Tool definitions         (all built-in + MCP tools)      │ ← Shared across ALL users (best cache)
│ 2. System prompt            (Anthropic internal instructions)│ ← Shared across all users
│ 3. CLAUDE.md content        (full project hierarchy)        │ ← Shared per-project
│ 4. Auto-memory              (MEMORY.md, ≤200 lines / 25KB) │ ← Per-project
│ 5. Loaded skill descriptions (from .claude/commands/)       │ ← On-demand (when invoked)
│ 6. MCP server instructions  (per-server guidance text)      │ ← Per-session config
│ 7. Conversation history     (all messages + tool results)   │ ← Unique per-session, grows each turn
│ 8. Path-scoped rules        (.claude/rules/ with paths)     │ ← On-demand per directory
└─────────────────────────────────────────────────────────────┘
Reserved buffer: 33K–45K tokens for system overhead
```

**Key metrics:**
- Standard context window: **200K tokens**
- Extended context window: **1M tokens** (Opus 4.6 and Sonnet 4.6, at standard pricing since March 14, 2026 — no surcharge)
- Average API cost: **~$6/developer/day** (90th percentile under $12)
- Input tokens account for **85–92%** of total API costs in typical coding sessions

### 1.2 Hidden Token Costs

These are the costs developers most frequently underestimate:

| Source | Token cost | Impact |
|--------|-----------|--------|
| GitHub MCP server (91 tools) | ~46,000 tokens | 23% of 200K window consumed before any work |
| A 5,000-token CLAUDE.md | 5,000 tokens × every turn | Compounds across entire session |
| Redundant file re-reads | 40–60% of all Read tokens | Studies show most Read tokens are re-reads |
| System overhead buffer | 33K–45K tokens | Effective usable space is smaller than raw window |

### 1.3 Monitoring Commands

| Command | What it shows | Scope |
|---------|--------------|-------|
| `/context` | Live breakdown: system prompt, system tools, MCP tools, custom agents, skills, messages, free space, autocompact buffer | Current snapshot |
| `/cost` | Per-model input/output/cache-read/cache-write tokens + dollar cost (v2.1.92: per-model breakdown with cache-hit accounting) | Cumulative session |
| `/clear` | Resets conversation; preserves tools, CLAUDE.md, and memory | Destructive reset |
| `/compact [focus]` | Summarizes conversation with optional focus topic | Lossy compression |
| `Esc+Esc` or `/rewind` | Partial compaction — select a message checkpoint and summarize from there | Selective compression |

---

## 2. Prompt Caching Economics

### 2.1 How Prompt Caching Works

Per Thariq Shihipar (Claude Code engineering team): *"We build our entire harness around prompt caching. A high prompt cache hit rate decreases costs and helps us create more generous rate limits for our subscription plans, so we run alerts on our prompt cache hit rate and declare SEVs if they're too low."*

The system stores **KV (key-value) attention cache tensors** server-side. When a new request shares the same byte-level prefix as a cached request, the model skips recomputation for that prefix. The context reconstruction order (Section 1.1) is deliberately arranged to maximize the length of the shared prefix — tool definitions and system prompts (shared by all users) come first, while per-session conversation history (unique and growing) comes last.

Each cache entry has a **5-minute TTL** that refreshes on every hit. Active sessions with turns less than 5 minutes apart keep the cache warm indefinitely. The cache is **per-model** — switching models mid-session means a complete cache miss where the entire context must be re-cached at write cost.

### 2.2 Pricing Multipliers (April 2026)

| Token type | Multiplier vs base | Sonnet 4.6 | Opus 4.6 | Haiku 4.5 |
|------------|-------------------|------------|----------|-----------|
| Standard input (no cache) | 1.0× | $3.00/MTok | $15.00/MTok | $1.00/MTok |
| 5-minute cache write | 1.25× | $3.75/MTok | $18.75/MTok | $1.25/MTok |
| 1-hour cache write | 2.0× | $6.00/MTok | $30.00/MTok | $2.00/MTok |
| **Cache read (hit)** | **0.1×** | **$0.30/MTok** | **$1.50/MTok** | **$0.08/MTok** |
| Output tokens | — | $15.00/MTok | $75.00/MTok | $5.00/MTok |

**CCA-F formula:** Effective input cost = `(miss_tokens × write_rate) + (hit_tokens × 0.1 × base_rate)`. At 90% hit rate over a 20-turn session with 100K context on Sonnet, caching delivers **~84% savings** ($0.945 vs $6.00 without caching).

### 2.3 The `--resume` Cache Regression (v2.1.69 → v2.1.90)

Between v2.1.69 and v2.1.90, `--resume` sessions suffered a critical bug causing a **~20× cost increase** per message. Only the internal system prompt (~14.5K tokens) was cached; all conversation history rebuilt from scratch on every turn.

**Root cause:** The session resume function maintained an allowlist of attachment types to preserve across serialization. Two critical types were missing: `deferred_tools_delta` (tracks which ToolSearch tools have been announced to the model) and `mcp_instructions_delta` (MCP server instructions). When stripped during resume, tools got re-announced on the next turn — inserting new messages that shifted the byte-level prefix hash and broke cache matching for the entire conversation history.

**Fixed in v2.1.90 (April 1, 2026).** This bug connects three CCA-F domains: D4 (ToolSearch's deferred_tools_delta), D5 (prompt caching prefix sensitivity), and D2 (session management with --resume).

### 2.4 Rules for Maximizing Cache Hits

| Rule | Why it matters | Cost of violation |
|------|---------------|-------------------|
| Never modify system prompt mid-session | Shifts byte-level prefix hash | 1.25× write cost on entire context |
| Never switch models mid-session | Caches are per-model; new model = cold start | Full context rebuild + 1.25× write |
| Never add/remove tools mid-session | Tool definitions are in the cached prefix | Prefix invalidation → full re-cache |
| Keep messages within 5-min TTL | Cache expires after 5 min of inactivity | Full cold start on next turn |
| Disable unused MCP servers via `/mcp` | Each server adds tool schemas to prefix | Wasted prefix tokens every turn |
| Prefer CLI tools (gh, aws, gcloud) | No per-tool definition overhead in prefix | MCP tools add schema tokens |
| Use subagents for different-model tasks | Subagent uses separate API call — parent cache stays warm | Switching main model kills parent cache |

---

## 3. ToolSearch (Lazy Tool Loading)

### 3.1 Architecture

ToolSearch (shipped v2.1.7, January 2026) solves the "startup tax" problem where MCP tool definitions consumed tens of thousands of tokens before any work began. It activates automatically when total MCP tool descriptions exceed **10K tokens** (~10% of 200K context).

**Step-by-step flow:**

```
STARTUP:
  1. Build lightweight index: tool name + 1-line description per tool
  2. MCP tools marked defer_loading: true
  3. Sent to API as lightweight stubs (name + desc, no schema)
  4. Token cost: ~100 tokens/tool (vs ~500–2000 for full schema)

RUNTIME (when Claude needs a tool):
  5. Claude calls ToolSearch tool (regex or BM25 search variant)
  6. ToolSearch searches the catalog index
  7. Returns 3–5 most relevant tool matches
  8. Full definitions injected as tool_reference blocks

CRITICAL PLACEMENT:
  9. tool_reference blocks go into CONVERSATION HISTORY
     ├── NOT into the tool definitions prefix
     ├── Cached prefix hash stays UNTOUCHED
     └── ToolSearch + prompt caching work TOGETHER ✓
```

**Impact:** Token reduction of **85%+** in tool definition tokens. Tool selection accuracy actually *improved* (Opus 4.5: 79.5% → 88.1%) because Claude selects from a focused, relevant set rather than a massive list. The system supports up to **10,000 tools** in the catalog.

**CCA-F key point (frequently tested):** Discovered tool definitions go into conversation history, NOT the tool definitions prefix. This architectural choice means ToolSearch never invalidates the prompt cache. This is the most elegant design tradeoff in the system.

### 3.2 Configuration

ToolSearch is automatic by default — zero configuration needed. For servers where you always need tools immediately:

```json
{
  "mcpServers": {
    "critical-server": {
      "command": "...",
      "enableToolSearch": false    // tools loaded eagerly
    }
  }
}
```

Additional details: only MCP tools (`mcp__` prefix) are eligible for deferral; built-in tools (Read, Edit, Bash, Write, Glob, Grep, WebSearch, WebFetch) are never deferred. Tool descriptions and server instructions are capped at **2KB** (v2.1.84) to prevent OpenAPI-generated servers from bloating context.

---

## 4. Model Selection for Cost Optimization

### 4.1 Model Comparison (April 2026)

| Dimension | Opus 4.6 | Sonnet 4.6 | Haiku 4.5 |
|-----------|----------|------------|-----------|
| Input $/MTok | $15 | $3 | $1 |
| Output $/MTok | $75 | $15 | $5 |
| Cache read $/MTok | $1.50 | $0.30 | $0.08 |
| Context window | 1M (standard pricing) | 1M (standard pricing) | 200K |
| Max output (default / upper) | 64K / 128K | 64K / 128K | 64K |
| SWE-bench Verified | 80.8% | 79.6% | — |
| Extended thinking | low / med / high / max | low / med / high | Not supported |
| Cost relative to Opus | 1× | 0.2× (80% cheaper) | 0.07× (93% cheaper) |

**Sonnet handles ~90% of coding tasks** at 80% lower cost than Opus. The SWE-bench delta is only 1.2 percentage points.

### 4.2 The `opusplan` Alias

The single highest-ROI model strategy. It uses Opus only during Plan mode (design and architecture) and Sonnet for all implementation, managing cache implications internally:

```bash
claude --model opusplan
# In-session: /model opusplan
# Plan mode toggle: Shift+Tab×2 or /plan
```

This avoids the cache invalidation problem of manual model switching — `opusplan` routes specific turns to Opus while keeping the main session on Sonnet.

### 4.3 Subagent Model Routing

```bash
# Global default: all subagents use Haiku (~93% cheaper)
export CLAUDE_CODE_SUBAGENT_MODEL=haiku

# Main session on Opus for coordination
claude --model opus

# Per-subagent override in frontmatter:
---
name: security-scan
model: opus           # override for complex tasks
effort: high
---

# Priority: frontmatter > CLAUDE_CODE_SUBAGENT_MODEL > "inherit"
# Built-in Explore subagent uses Haiku by default
```

### 4.4 Output Tokens and Hidden Thinking Costs

Extended thinking tokens are allocated from the **output budget** and billed at **output rates** ($15–75/MTok). With `MAX_THINKING_TOKENS` defaulting to ~32K, a single complex turn on Opus costs $2.40 in thinking alone.

```bash
# Default: ~32K thinking → ~32K for code on 64K limit
# Optimized: 10K thinking → ~54K for code, ~70% less thinking cost
export MAX_THINKING_TOKENS=10000

# This is arguably the single highest-ROI environment variable.
# For one-off deep reasoning, include "ultrathink" in the prompt.
```

---

## 5. Effort Frontmatter

Effort levels control adaptive reasoning — dynamically allocating thinking tokens based on task complexity.

| Level | Thinking tokens | Use cases | Token impact |
|-------|----------------|-----------|-------------|
| low | 0–500 (may skip entirely) | Formatting, linting, lookups, file moves | Saves thousands of output tokens per turn |
| medium | Balanced (default) | Most coding: features, tests, docs, refactoring | Standard allocation |
| high | Deep reasoning (2–4× more) | Complex debugging, architecture decisions | Expensive but justified |
| max | Unconstrained (Opus 4.6 only) | Novel algorithms, research-grade problems | Maximum possible cost |

```yaml
# In skill frontmatter: .claude/commands/quick-format.md
---
name: quick-format
description: Quick code formatting check
effort: low
---

# In subagent frontmatter: .claude/agents/reviewer.md
---
name: code-reviewer
model: sonnet
effort: low
---
```

**Priority order:** `CLAUDE_CODE_EFFORT_LEVEL` env var (highest) → skill/subagent frontmatter → session `/effort` command → model default (medium). Including "ultrathink" in a prompt triggers high effort for that single turn only.

---

## 6. `--bare` Mode for CI and Scripted Calls

The `--bare` flag (v2.1.81, March 2026) creates a minimal, deterministic execution environment by skipping:

| Skipped | Why it matters |
|---------|---------------|
| Hooks (PreToolUse/PostToolUse) | No hook execution overhead |
| LSP connections | No language server startup (~200-500ms) |
| Plugin sync | No marketplace git pull (~1-3s) |
| Skill directory walks | No .claude/commands/ scanning |
| MCP servers | No tool schema tokens in context |
| Auto-memory (MEMORY.md) | No memory file injection |
| CLAUDE.md files (entire hierarchy) | No per-turn CLAUDE.md cost |
| OAuth / keychain reads | No auth token refresh |

Available tools in bare mode: **only Bash, Read, and Edit**. Performance: **~14% faster to first API request** (official); community reports up to 10× faster. Will become the default for `-p` mode in a future release.

```bash
# Minimal CI diff review
git diff origin/main...HEAD | claude -p "Review this diff" \
  --bare --allowedTools "Bash(git:*),Read" --output-format json

# Add specific context when needed
claude -p "Fix lint errors" --bare \
  --append-system-prompt "Use ESLint from .eslintrc" \
  --mcp-config ./ci-mcp.json
```

---

## 7. CLAUDE.md Best Practices

### 7.1 Token Impact

CLAUDE.md files are injected into **every single API call** as input tokens. A 100-token unnecessary paragraph costs 5,000 tokens over a 50-turn session. The loading hierarchy:

```
1. Managed policy              ← IT-administered (cannot exclude)
2. Project ./CLAUDE.md          ← Repository root
3. User ~/.claude/CLAUDE.md     ← Personal global
4. Local ./CLAUDE.local.md      ← git-ignored overrides
5. Subdirectory CLAUDE.md       ← ON-DEMAND when files accessed
6. .claude/rules/ with paths    ← ON-DEMAND, scoped to directories
```

**Target: under 200 lines per file.** For each line, ask: "Would removing this cause Claude to make mistakes?" If not, cut it.

### 7.2 Optimization Techniques

| Technique | How | Impact |
|-----------|-----|--------|
| Move workflows to skills | `.claude/commands/` files load only when invoked | Saves tokens every non-skill turn |
| Use `.claude/rules/` with paths | Topic-specific rules load only for matching files | Scoped injection vs global |
| `@import` for modularity | Reference external files (max depth: 5 hops) | Keep root CLAUDE.md lean |
| HTML comments `<!-- -->` | Stripped before injection into API calls | Zero token cost — free human notes |
| `claudeMdExcludes` setting | Skip irrelevant CLAUDE.md in monorepos | Avoid unrelated project instructions |
| `.claudeignore` | Like `.gitignore` — block build artifacts, lock files | Prevent accidental large file reads |

### 7.3 Recommended Structure (Anthropic's Scientific Computing Guide)

```markdown
# Project: InsureChat v3.0

## Architecture
- FastAPI + ChromaDB + Voyage AI voyage-3.5 embeddings
- Claude Sonnet for generation, Haiku for intent classification
- Microsoft Presidio for PII detection

## Conventions
- API routes: /src/api/ | Tests: /tests/ | Lint: ruff check src/
- Run tests: pytest tests/ -x --tb=short

## Current Focus
- [ACTIVE] Hybrid search: BM25 + semantic + RRF
- [DONE] PII detection pipeline

## Known Failures (DO NOT RE-ATTEMPT)
- sentence-transformers: incompatible with Python 3.12
- rank_bm25 BM25Okapi: OOM on docs > 50K tokens
- ChromaDB batch upsert > 5000: silent data loss

# Compact Instructions
Preserve: API schema decisions, test commands, known failures
Discard: verbose debugging output, exploratory file reads
```

The **"Known Failures"** section prevents successive sessions from re-attempting dead ends. A separate CHANGELOG.md serves as portable long-term memory including failed approaches and why they didn't work.

---

## 8. Subagents vs. Agent Teams

| Dimension | Subagents (Task tool) | Agent Teams (Teammates) |
|-----------|----------------------|------------------------|
| Process model | Within parent session's process | Separate instances (2–16) |
| Context window | Scoped subset of parent | Own full 1M window each |
| Communication | Vertical only (→ parent) | Lateral (mailbox + shared task list) |
| Cost multiplier | ~1× (efficient) | ~3–7× (commonly ~5×) |
| Context inheritance | **NONE** — must explicitly pass all info | **NONE** — each independent |
| Best for | Focused subtasks, exploration, linting | Multi-file refactors, cross-layer features |

**CCA-F exam trap:** "Subagent inherits parent context" is **WRONG**. All information must be explicitly passed in the task description.

**CCA-F design principle:** Tool descriptions are the primary routing mechanism (not function names). Keep tools to 4–5 per agent for optimal selection accuracy.

### Cost-Efficient Agent Architecture

```
TIER 1 — Main session (opusplan or Sonnet)
  └── Coordination, architecture, task decomposition

TIER 2 — Subagents (Haiku or Sonnet per frontmatter)
  └── CLAUDE_CODE_SUBAGENT_MODEL=haiku (global default)
  └── ~1× cost (same process, scoped context)

TIER 3 — Agent Teams (only when lateral comms needed)
  └── 2–4 teammates max, ~5× cost
  └── Use isolation: "worktree" for parallel changes
```

---

## 9. Compaction System

### 9.1 Three-Layer Architecture

**Layer 1 — Microcompaction (automatic):** Large tool outputs are saved to disk; recent results stay inline ("hot tail"), older ones become disk references. Applies to Read, Bash, Grep, Glob, WebSearch, WebFetch, Edit, Write.

**Layer 2 — Auto-compaction:** Triggers at ~83.5% of window limit (configurable via `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`, values 1–100). Clears older tool outputs first, then summarizes conversation if still over threshold. Preserves user requests, key code, recent files, task state. After summary: re-reads recent files, restores todo list, re-injects CLAUDE.md from disk. **Circuit breaker** (v2.1.89): stops after 3 consecutive immediate-refill cycles.

**Layer 3 — Manual (`/compact`):** `/compact Focus on API changes` for guided preservation. `Esc+Esc` or `/rewind` for partial compaction. Customizable via `# Compact Instructions` in CLAUDE.md.

### 9.2 Idle-Return `/clear` Hint

After 75+ minutes idle, Claude Code suggests `/clear` with token savings displayed. Addresses the anti-pattern of resuming stale sessions where the 5-min cache TTL has expired. Bug fix in v2.1.92: now shows current context size (not cumulative session tokens).

### 9.3 Critical Compaction/Memory Fixes (March–April 2026)

| Bug | Impact | Fixed in |
|-----|--------|---------|
| Nested CLAUDE.md re-injected dozens of times | Massive token waste | v2.1.89 |
| Progress messages surviving compaction | Context bloat | v2.1.89 |
| Background subagents invisible after compaction | Duplicate agent spawning | v2.1.89 |
| Deferred tools losing input schemas | Unusable tools until re-discovery | v2.1.89 |
| Autocompact thrash loop | Infinite token burn | v2.1.89 (circuit breaker) |
| `--resume` truncating recent history | Lost context + cache miss | v2.1.92 |

### 9.4 Long-Running Sessions

Anthropic's scientific computing guide recommends tmux on a compute node for multi-day sessions:

```bash
tmux new-session -s claude-research
claude --model opus
# Detach: Ctrl+B, D | Reattach: tmux attach -t claude-research

# Best practices:
# 1. Commit after every meaningful unit of work
# 2. CHANGELOG.md = portable memory (including failed approaches)
# 3. Tests = continuous verification oracle
# 4. /compact with focus when context fills
# 5. /loop N for iterative tasks
```

**Auto-memory:** Stored in `~/.claude/projects/<project>/memory/MEMORY.md`. Truncated at 200 lines / 25KB at session start. Memory timestamps (March 2026) enable freshness reasoning.

---

## 10. Batch Processing & Scheduled Tasks

### 10.1 The `/batch` Skill

Orchestrates large-scale codebase changes through three phases:

**Phase 1 — Research & Plan:** Explore agents research scope → decompose into 5–30 units → present plan for approval.

**Phase 2 — Parallel Execution:** 1 background agent per unit in isolated git worktrees → implement → test → commit → push → open PR. Up to 10 parallel agents.

**Phase 3 — Tracking:** Live status table. Failed units don't affect others.

Runs **up to 10× faster** than sequential prompts. Best for migrations, convention enforcement, dependency swaps, test generation.

### 10.2 Cloud Scheduled Tasks

Created via `claude.ai/code/scheduled` or `/schedule`. Clones repo fresh each run, creates own session, operates from default branch. Minimum interval: 1 hour. CLI task expiry: 3 days. Each run = full session cost.

### 10.3 Cloud Auto-Fix

Subscribes to GitHub PR events. CI failure → investigate → fix → push → explain. Clear review comment → implement. Ambiguous → asks clarification. Each cycle = full API call.

---

## 11. Top 10 Cost Optimizations (Ranked by Impact)

| Rank | Optimization | Impact | Command | CCA-F Domain |
|------|-------------|--------|---------|-------------|
| 1 | Default to Sonnet 4.6 | 80% input cost reduction vs Opus | `/model sonnet` | D2 |
| 2 | Set MAX_THINKING_TOKENS=10000 | ~70% reduction in thinking costs | `export MAX_THINKING_TOKENS=10000` | D2 |
| 3 | `/clear` between unrelated tasks | Prevents stale context compounding | `/clear` | D5 |
| 4 | Write specific prompts naming files | 3-turn vs 12-turn = 50K+ tokens | Name exact files + outcomes | D3 |
| 5 | Use opusplan alias | Opus design + Sonnet implementation | `/model opusplan` | D2 |
| 6 | Subagent model → Haiku globally | ~93% cheaper exploration | `export CLAUDE_CODE_SUBAGENT_MODEL=haiku` | D1 |
| 7 | CLAUDE.md under 200 lines | Saves tokens every turn | Move to `.claude/commands/` | D2 |
| 8 | ToolSearch (automatic) | 85%+ reduction in tool tokens | Auto when MCP > 10K tokens | D4 |
| 9 | Effort: low for simple tasks | Skips thinking entirely | Frontmatter: `effort: low` | D2 |
| 10 | `--bare` for CI/scripts | ~14% faster, minimal overhead | `claude -p '...' --bare` | D2 |

---

## 12. CCA-F Exam Relevance

**Structure:** 60 questions in 120 minutes. 6 scenarios available, 4 randomly selected per sitting.

**Domain weights:** D1 Agentic Architecture (25%), D2 Claude Code Config (20%), D3 Prompt Engineering (20%), D4 Tool Design & MCP (20%), D5 Context Management (15%).

**Key exam principles:**

The exam rewards **programmatic enforcement over prompt-based guidance** — hooks, gates, and interceptors are deterministic while prompts are probabilistic.

**Frequently tested concepts from this guide:**

1. Subagents do NOT inherit context — all information must be explicitly passed
2. Tool descriptions are the primary routing mechanism, not function names
3. Keep tools to 4–5 per agent for optimal selection accuracy
4. ToolSearch places tool_reference blocks in conversation history (not prefix)
5. The Batch API is a latency trade with 50% savings but no SLA
6. Prompt caching is per-model — switching models invalidates the cache
7. CLAUDE.md loads into every API call — bloated files compound cost
8. The `--resume` bug connected ToolSearch, caching, and session management
9. Auto-compaction triggers at ~83.5% with a circuit breaker after 3 thrash loops
10. `opusplan` routes Plan-mode turns to Opus while keeping main session on Sonnet

---

*Sources: [Claude Code Docs](https://code.claude.com/docs/en/), [Claude API Pricing](https://platform.claude.com/docs/en/about-claude/pricing), [Claude Code Changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md), [Anthropic Scientific Computing Guide](https://www.anthropic.com/research/long-running-Claude), Claude Code Camp, community analysis.*
