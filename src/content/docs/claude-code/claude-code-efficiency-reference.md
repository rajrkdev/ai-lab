---
title: "Claude Code: Context, Cost & Token Efficiency — Reference"
description: "Complete reference for context management, prompt caching, token budgets, model selection, effort controls, hooks, environment variables, and the advisor tool in Claude Code v2.1.101+. Covers all five CCA-F exam domains."
sidebar:
  order: 5
---

# Claude Code: Context, Cost & Token Efficiency — Complete Reference

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
- Average API cost: **~$13/developer/active day** (90th percentile under $30; $150-250/month)
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

### 2.2a When Each Cache Tier Activates

The two write tiers exist because Anthropic optimizes differently depending on how likely a cached prefix is to be reused.

| Tier | Write cost | Who gets it | When it activates |
|------|-----------|------------|------------------|
| **5-minute** | 1.25× base | API-key customers; subagents; rarely-resumed sessions | Default everywhere for direct API users |
| **1-hour** | 2.0× base | Pro/Max subscribers (logged-in CLI) for likely-reused prefixes | System prompt + tool definitions on interactive sessions |

**Why the split exists:** Writing a 1-hour cache entry costs 2.0× but a cache hit costs only 0.1×. If the prefix is reused even once within an hour the write premium is fully recovered. Anthropic rolls the 1-hour tier out selectively — interactive users reuse long prefixes (system prompt, tools) repeatedly in a session; API script runs and subagents rarely do.

**March 2026 silent regression:** Community analysis of raw JSONL session logs confirmed that Anthropic silently changed the default cache TTL from 1 hour to 5 minutes for some subscriber sessions sometime in early March 2026. Any pause longer than 5 minutes caused the full cached context to expire, forcing a complete cache-write on the next turn. The effect: users saw no change in visible behavior but quiet quota drain and cost inflation. Partially resolved by Anthropic server-side; the `--exclude-dynamic-system-prompt-sections` flag (v2.1.98) mitigates the daily-invalidation portion by stripping volatile date headers from the system prompt.

**Practical implication:** If `/cost` shows unexpectedly high `cache_write` tokens relative to `cache_read` tokens mid-session — especially after a pause — the 5-minute TTL has fired and the cache went cold. Use `/context` to verify, and consider `/compact` before long idle periods rather than after.

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
| Move the current date out of system prompt | Date string changes every day, invalidating cache (v2.1.42 tip) | Daily cold cache = full write cost every session start |
| Use `--exclude-dynamic-system-prompt-sections` | CLI flag (v2.1.98) strips volatile auto-injected sections (e.g., date headers) from system prompt for deterministic CI runs | N/A — opt-in flag |
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

### 3.3 ToolSearch Failure Modes

Claude can invoke ToolSearch using either a **regex variant** (`tool_search_tool_regex`) or a **BM25 variant** (`tool_search_tool_bm25`). Each has distinct failure modes.

**Regex variant (`tool_search_tool_regex`):**
- Claude constructs a Python `re.search()` pattern against tool names and descriptions
- **Failure:** Patterns longer than 200 characters are silently truncated, causing empty or wrong results with no error message
- **Fix:** Use short, high-entropy patterns: `(?i)finance|billing` not `(?i)financial_reporting|billing_management|invoice_processing`
- Prefer character classes and alternation over verbose literals

**BM25 variant (`tool_search_tool_bm25`):**
- Uses natural-language keyword ranking against the tool catalog
- **Failure:** When the MCP server name is long (e.g., `amazon-bedrock-agentcore-browser-mcp`), server-name tokens dominate BM25 scoring and crowd out capability keywords. A query like `amazon-bedrock-agentcore-browser-mcp navigate evaluate` returns `browser_navigate` and `browser_navigate_back` but misses `browser_evaluate` because the result limit (5) cuts off before it ranks
- **Fix:** Strip the server name prefix from your query entirely. Use just `navigate evaluate` or `browser evaluate page`

**Shared failure mode:** When neither variant returns the needed tool, Claude either attempts to call it by guessed name (fails with unknown tool) or halts and asks the user. Mitigation: keep tool descriptions distinct and keyword-rich; avoid tool names that differ only by suffix (`get_user`, `get_users`, `get_user_by_id` → `get_user_single`, `get_users_list`, `get_user_by_id`).

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
| Extended thinking | low / med / high | low / med / high | Not supported |
| Fast mode | Yes (v2.1.36, Max/Team users) | N/A | N/A |
| Cost relative to Opus | 1× | 0.2× (80% cheaper) | 0.07× (93% cheaper) |

**Fast mode for Opus 4.6 (v2.1.36):** Available to Max and Team tier users. Activates a faster, lower-latency processing path. Good for quick lookups, formatting, and simple refactors where latency matters more than maximum reasoning depth. Toggle with `/fast on` or in session settings.

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

### `/effort` Command (v2.1.76)

The primary way to set effort in an interactive session:

```
/effort low      # Quick tasks: formatting, lookups, simple moves
/effort medium   # Default: most coding work
/effort high     # Complex debugging, architecture decisions
```

Can also be set via arrow keys in the `/model` picker. In **VS Code** (v2.1.72+), a colored indicator on the input border shows current effort level.

### `ultrathink` Keyword (v2.1.68)

Including `ultrathink` in a prompt triggers **maximum effort for that single turn only**, regardless of the session effort setting. Re-added in v2.1.68:

```
ultrathink: refactor the authentication module to use the repository pattern
```

Does not change the session effort level — subsequent turns revert to the session default. Equivalent to "think harder" in extended thinking token budget terms.

### Effort Level Reference

| Level | Approx. thinking tokens | Use cases | Token cost vs medium |
|-------|------------------------|-----------|---------------------|
| low | 0–500 (often skipped) | Formatting, linting, lookups, file moves | ~0–10% of medium |
| medium | 1K–8K (adaptive) | Most coding: features, tests, docs, refactoring | Baseline |
| high | 8K–32K | Complex debugging, architecture decisions | 2–4× medium |
| xhigh | 32K–80K (Opus 4.7 only) | Very hard problems, cross-system refactors | 5–10× medium |
| max | Up to model ceiling | Most open-ended problems; not session-persistent | Highest |

> **Note:** Token ranges are approximate and model-dependent. Adaptive thinking (see "Adaptive Thinking" subsection below) adjusts within these bands per-turn. `xhigh` is available on Opus 4.7 only. Use `ultrathink` in the prompt to request maximum reasoning depth for a single turn without changing the session level.

**Default effort by plan and model (as of v2.1.94, April 2026):**

| User tier | Opus 4.6 / Sonnet 4.6 | Opus 4.7 |
|-----------|----------------------|---------|
| Pro / Max (CLI) | medium | xhigh |
| API key / Team / Enterprise | high (raised in v2.1.94) | xhigh |
| Bedrock / Vertex / Foundry | high (raised in v2.1.94) | xhigh |

### Effort in Frontmatter

```yaml
# In skill frontmatter: .claude/skills/quick-format/SKILL.md
---
name: quick-format
description: Quick code formatting check
effort: low
---

# In agent frontmatter: .claude/agents/reviewer.md
---
name: code-reviewer
model: sonnet
effort: low
---
```

**Priority order:** `CLAUDE_CODE_EFFORT_LEVEL` env var (highest) → skill/agent frontmatter → session `/effort` command → model default. `ultrathink` in prompt text overrides for a single turn.

### 5.4 Adaptive Thinking (v2.1.74, February 9 2026)

Adaptive thinking lets Opus 4.6 and Sonnet 4.6 decide per-turn how many thinking tokens to spend, rather than using the fixed budget set by `MAX_THINKING_TOKENS`. It is the default mode since February 9, 2026.

**The February 2026 perception problem:** On the same day adaptive thinking launched, Anthropic also silently lowered the default effort from `high` to `medium` (March 3, 2026 for interactive sessions). Community analysis of 6,852 sessions measured a 67% drop in model reasoning depth compared to pre-February baselines. The culprit was the effort default change, not adaptive thinking itself.

**How adaptive thinking actually works:** Rather than always burning a fixed 32K thinking budget, the model scales thinking tokens to task complexity. A lookup uses ~500 tokens; a multi-file refactor might use 20K. At `high` effort, the ceiling is ~32K. At `xhigh` (Opus 4.7), ~80K.

**Key environment variables:**

```bash
# Revert to fixed thinking budget (Opus 4.6 / Sonnet 4.6 only — NOT Opus 4.7)
export CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1

# Set the fixed budget when adaptive is disabled
export MAX_THINKING_TOKENS=10000   # Default was ~32K before adaptive

# Restore effort to previous default for API users
export CLAUDE_CODE_EFFORT_LEVEL=high
```

> **Opus 4.7 note:** Opus 4.7 always uses adaptive reasoning. `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING` has no effect on it. `MAX_THINKING_TOKENS` does not apply.

**Decision guide:**

| Symptom | Fix |
|---------|-----|
| Responses feel shallow / low reasoning depth | Raise effort: `/effort high` or `export CLAUDE_CODE_EFFORT_LEVEL=high` |
| Costs spiked after Feb 2026 update | Likely effort default raised for your tier; set `export CLAUDE_CODE_EFFORT_LEVEL=medium` |
| Need deterministic token budgets for CI billing | `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1` + `MAX_THINKING_TOKENS=10000` |
| One-off deep reasoning on a specific turn | Add `ultrathink` to that prompt; leave session effort unchanged |

---

## 6. `--bare` Mode for CI and Scripted Calls

The `--bare` flag (v2.1.81, March 2026) creates a minimal, deterministic execution environment by skipping:

| Skipped | Why it matters |
|---------|---------------|
| All lifecycle hooks (see §12) | No hook execution overhead — PreToolUse, PostToolUse, PreCompact, SessionStart, etc. all skipped |
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
| `@import` for modularity | `@path/to/file.md` — resolved relative to the importing file, not the working directory; max depth: 5 hops; depth 6 is silently ignored | Keep root CLAUDE.md lean |
| HTML comments `<!-- -->` | Stripped before injection into API calls | Zero token cost — free human notes |
| `claudeMdExcludes` setting | Skip irrelevant CLAUDE.md in monorepos | Avoid unrelated project instructions |
| `.claudeignore` | Like `.gitignore` — block build artifacts, lock files | Prevent accidental large file reads |

### 7.3 Recommended Structure (Anthropic's Scientific Computing Guide)

```markdown
# Project: MyProject

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

### What "Explicitly Pass All Info" Means in Practice

A poorly-formed subagent prompt assumes the agent already knows context from the parent:

```
# BAD — agent has no idea what "the auth refactor" means or where files are
Task: Continue the auth refactor we discussed. Make sure tests still pass.
```

A well-formed subagent prompt is self-contained — a stranger could execute it:

```
# GOOD — every fact the agent needs is spelled out
Task: Refactor the JWT validation logic in src/auth/validator.ts.
Context: We are migrating from HS256 to RS256. The current implementation
is in validateToken() at line 47. The public key path is config/keys/rs256.pub.
Do NOT modify the token generation code in src/auth/generator.ts.
Tests are in tests/auth/validator.test.ts — run with `npm test auth` before finishing.
Success: All 14 existing tests pass and the function signature is unchanged.
```

Key fields to always include: file paths, function names, what NOT to change, how to run tests, and a concrete definition of "done".

### Cost-Efficient Agent Architecture

```
TIER 1 — Main session (opusplan or Sonnet)
  └── Coordination, architecture, task decomposition

TIER 2 — Subagents (Haiku or Sonnet per frontmatter)
  └── CLAUDE_CODE_SUBAGENT_MODEL=haiku (global default)
  └── ~1× cost (same process, scoped context)

TIER 3 — Agent Teams (only when lateral comms needed)
  └── 2–4 teammates max, ~3–7× cost
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
| `--resume` full prompt-cache miss for users with deferred tools, MCP servers, or custom agents | ~20× cost increase per resumed turn | v2.1.93 |
| Edit/Write failing with "File content has changed" when a PostToolUse format-on-save hook rewrites file between consecutive edits | Broken hook + edit chain | v2.1.93 |
| PreCompact hook added | Hooks can now block or guide compaction behavior | v2.1.95 |
| Context token ceiling (`CLAUDE_CODE_MAX_CONTEXT_TOKENS`) | Hard cap prevents runaway context growth in CI | v2.1.96 |
| Auto mode not respecting explicit user boundaries ("don't push", "wait for X") | Unauthorized actions in auto mode | v2.1.93 |

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

## 11. Top 12 Cost Optimizations (Ranked by Impact)

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
| 11 | PostToolUse hooks for data filtering | Pre-filter large outputs before Claude sees them; community reports 40–70% cost reduction | `.claude/settings.json` hooks | D4 |
| 12 | Advisor before architecture decisions | Prevents costly rework from wrong approaches; call once before design, once before done | `advisor()` in session | D1 |

---

## 12. Hooks Reference

Hooks are user-defined shell commands (or scripts) that fire at specific points in Claude Code's lifecycle. They turn best-practice guidelines into deterministic enforcement — hooks always run; prompts sometimes work.

### 12.1 All Hook Events (April 2026)

Hooks fire at three cadences: **once per session**, **once per turn**, and **on every tool call** in the agentic loop.

| Event | Cadence | Blocking? | Key use cases |
|-------|---------|-----------|--------------|
| `SessionStart` | Per session | No | Load env vars, warm caches, re-inject context after compaction |
| `SessionEnd` | Per session | No | Cleanup, final reporting, summary logs |
| `UserPromptSubmit` | Per turn | Yes (exit 2) | Sanitize input, classify task type, route to skill |
| `PreToolUse` | Per tool call | **Yes (exit 2 or `{"decision":"block"}`)** | Security gates, file protection, mandatory review |
| `PostToolUse` | Per tool call | No | Format-on-save, lint, test runner trigger |
| `PostToolUseFailure` | Per tool call (on failure) | No | Add diagnostic context for Claude's next step |
| `Stop` | Per turn | Yes (return to keep going) | Enforce completion criteria before Claude stops |
| `SubagentStop` | Per subagent | No | Validate subagent output before returning to parent |
| `PermissionRequest` | Per auto-mode check | Yes | Auto-approve/deny permission dialogs |
| `PermissionDenied` | Per auto-mode denial | Partial (`{retry: true}`) | Tell Claude it can retry after adjusting approach |
| `PreCompact` | Before compaction | Yes (exit 2) | Block compaction; inject critical context that compaction would lose |
| `PostCompact` | After compaction | No | Re-inject state; reload environment |
| `Notification` | On alert | No | Slack/webhook routing; desktop notifications |
| `FileChanged` | On watched file change | No | Hot-reload, re-read config on disk changes |
| `CwdChanged` | On directory change | No | Reload env vars (direnv-style), switch project context |

### 12.2 Hook Configuration

```json
// .claude/settings.json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "bash /scripts/block-rm-rf.sh"
      }]
    }],
    "PostToolUse": [{
      "matcher": "Edit",
      "hooks": [{
        "type": "command",
        "command": "npx prettier --write $CLAUDE_TOOL_ARG_FILE_PATH"
      }]
    }],
    "PreCompact": [{
      "matcher": "compact",
      "hooks": [{
        "type": "command",
        "command": "cat .claude/compact-context.md"
      }]
    }]
  }
}
```

**Blocking a tool call (PreToolUse):**
- Exit with code `2`, or
- Return JSON `{"decision": "block", "reason": "explanation"}` — Claude sees the reason

**PermissionDenied retry:**
- Return `{"retry": true}` — tells Claude it may try again with an adjusted approach

### 12.3 Token Cost Impact of Hooks

| Hook pattern | Token effect |
|-------------|-------------|
| PostToolUse grep/filter before injecting output | **Reduces** tokens — hook distills 10K-line log to 50 matching lines |
| PostToolUse that re-reads the edited file | **Adds** tokens — avoid unless the read is necessary |
| PreToolUse that always calls an LLM | **Adds** tokens per tool call — use shell scripts, not LLM calls, in hooks |
| `--bare` mode | **Skips all hooks** — use for CI where hooks add overhead without benefit |

Poorly written hooks (e.g., a PostToolUse that `cat`s a large file unconditionally) can compound cost worse than the tool itself. The `--bare` flag skips all hooks and is the correct choice for automated pipelines.

### 12.4 Hooks vs. Instructions

| Use hooks when | Use CLAUDE.md instructions when |
|---------------|--------------------------------|
| You need the behavior enforced every time, unconditionally | The guidance is probabilistic ("try to...") |
| The action is dangerous or irreversible | The guidance is stylistic or contextual |
| You want deterministic CI pipeline gates | The instruction rarely applies |
| Speed matters (hooks are faster than another Claude turn) | Flexibility and judgment are needed |

---

## 13. Environment Variables Reference

Consolidated reference for all token-cost-relevant environment variables. Variables marked ★ have the highest practical impact.

### Core Cost Controls

| Variable | Default | Effect |
|----------|---------|--------|
| ★ `CLAUDE_CODE_SUBAGENT_MODEL` | inherit | Override model for all subagents. Set to `haiku` globally for ~93% cost reduction on exploration tasks |
| ★ `MAX_THINKING_TOKENS` | ~32K | Fixed thinking budget when adaptive thinking is disabled. Lower to `10000` for ~70% thinking cost reduction |
| ★ `CLAUDE_CODE_EFFORT_LEVEL` | model/plan default | Highest-priority effort override. Values: `low`, `medium`, `high`, `xhigh`, `max`. Set `high` to restore pre-March 2026 reasoning depth |
| `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING` | unset | Set to `1` to revert Opus 4.6/Sonnet 4.6 to fixed `MAX_THINKING_TOKENS` budget. No effect on Opus 4.7 |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | 83.5 | Context fill % that triggers auto-compaction. Range: 1–100. Lower = more aggressive compaction |
| `CLAUDE_CODE_MAX_CONTEXT_TOKENS` (v2.1.96) | unset | Hard ceiling on context size. When combined with `DISABLE_COMPACT`, prevents context growth beyond the cap |

### Session and Execution Controls

| Variable | Default | Effect |
|----------|---------|--------|
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` | model max | Cap output token budget per turn. Note: has no effect on Opus 4.6 in some versions (tracked bug) |
| `CLAUDE_CODE_SCRIPT_CAPS` (v2.1.96) | unset | Restricts script capabilities in Bash tool. Paired with PID namespace isolation on Linux |
| `CLAUDE_CODE_PERFORCE_MODE` (v2.1.96) | unset | Enables Perforce VCS mode instead of Git |
| `CLAUDE_CODE_USE_MANTLE` (v2.1.94) | unset | Set to `1` for Amazon Bedrock powered by Mantle |
| `AWS_BEARER_TOKEN_BEDROCK` | unset | Bearer token for Bedrock auth (replaces SigV4 in CLAUDE_CODE_SKIP_BEDROCK_AUTH mode) |

### Observability and Telemetry

| Variable | Default | Effect |
|----------|---------|--------|
| `DISABLE_TELEMETRY` | unset | Set to `1` to opt out of usage telemetry |
| `DISABLE_ERROR_REPORTING` | unset | Set to `1` to suppress crash report uploads |
| `CLAUDE_CODE_ENABLE_TELEMETRY` | unset | Enable structured telemetry output (OpenTelemetry) |
| `OTEL_*` | — | Standard OpenTelemetry transport/logging env vars; used for forwarding metrics to external observability stacks |
| `MAX_STRUCTURED_OUTPUT_RETRIES` | 3 | Retry limit for structured output format recovery |

### Quick-Start `.env` for Cost-Optimized Interactive Sessions

```bash
# Restore high-reasoning default (pre-March 2026 behavior)
export CLAUDE_CODE_EFFORT_LEVEL=high

# Set thinking budget ceiling (applies when adaptive thinking is off)
export MAX_THINKING_TOKENS=10000

# Route all subagents to Haiku (~93% cheaper for exploration)
export CLAUDE_CODE_SUBAGENT_MODEL=haiku

# Compact at 75% instead of 83.5% for faster headroom recovery
export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=75
```

### Quick-Start for CI / `--bare` Pipelines

```bash
# Deterministic fixed budget — no adaptive thinking
export CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1
export MAX_THINKING_TOKENS=5000

# Hard context ceiling — prevents runaway cost in long CI runs
export CLAUDE_CODE_MAX_CONTEXT_TOKENS=80000

# Use --bare to skip hooks, MCP, CLAUDE.md, memory
claude -p "Review this diff for security issues" --bare \
  --allowedTools "Read,Bash(git diff:*)" \
  --output-format json
```

---

## 14. The Advisor Tool

### 14.1 Two Distinct "Advisor" Concepts

**Important:** Two separate things share the "advisor" name in the Claude ecosystem. They are architecturally different and serve different audiences.

| | Built-in `advisor()` harness tool | Anthropic Advisor API (beta) |
|-|----------------------------------|------------------------------|
| **What it is** | A tool built into the Claude Code session harness | An API-level feature for developers building their own apps |
| **Who uses it** | Claude, mid-task, to consult a stronger reviewer | Developers building executor+advisor app patterns |
| **How invoked** | Claude calls `advisor()` with no parameters | Via API with `advisor-tool-2026-03-01` beta header |
| **What it sees** | Your entire conversation history, automatically | The context you pass in the API call |
| **Since** | Available in Claude Code harness sessions | Beta rollout April 9, 2026 |
| **Benchmarks** | N/A (internal harness tool) | Sonnet + Opus advisor: 74.8% SWE-bench Multilingual (vs 72.1% Sonnet alone, at 11.9% less cost than Opus solo) |

### 14.2 The Built-in `advisor()` Tool — For Day-to-Day Development

This is the advisor you interact with in Claude Code sessions. When Claude (or a skill) calls `advisor()`, it forwards the **entire conversation transcript** to a stronger reviewer model. The reviewer sees everything: the task, every tool call made, every result received, every reasoning step. It then returns a single message with guidance.

**Purpose:** Catch reasoning errors, surface overlooked constraints, and give a second opinion before Claude commits to an approach — especially on decisions that are hard to reverse or expensive to redo.

#### When Claude (or You) Should Trigger the Advisor

| Situation | Why advisor adds value |
|-----------|----------------------|
| **Before substantive work** — before writing code, before committing to an architecture, before deleting anything | The advisor sees what Claude is about to do and can catch flawed assumptions before they're encoded in code |
| **After orientation, before implementation** — you've explored the codebase, now you're about to act | Orientation (reading files, grepping) is cheap to redo; implementation is not. Advisor after orienting, before writing |
| **When stuck** — same error recurring, approach not converging, unexpected results | The advisor has the full picture and can identify the wrong-turn Claude took several steps back |
| **Change of approach** — Claude is about to switch strategies | Validates whether the new approach is actually better or just differently wrong |
| **Before declaring done** — task appears complete | The strongest use: the advisor catches gaps between what was asked and what was done |
| **Risky / irreversible actions** — deleting branches, force pushes, schema changes | Adds a high-quality gate before the irreversible step |
| **Ambiguous requirements** — the task description is underspecified | Advisor can identify which interpretation is most defensible and flag what to clarify |

#### When NOT to Trigger the Advisor

| Situation | Reason to skip |
|-----------|---------------|
| Short reactive tasks where the next action is dictated by tool output you just read | Advisor adds most value before approach crystallizes, not during mechanical execution |
| After every single tool call | Over-calling drains tokens; the advisor is expensive on large contexts |
| When you have primary-source evidence that already resolves the question | Trust the file, the test result, the stack trace — don't ask for a second opinion on facts |
| When the task is already complete and the deliverable is durable | Call advisor BEFORE declaring done; if the session ends during the advisor call, a written/committed result persists |

#### Cost Model

The advisor call forwards the entire conversation. On a large session (50+ turns with tool results), this is a significant token spend — roughly equivalent to a full API call with the entire context as input. The expense is justified when the alternative is redoing hours of work.

**Practical guidance:**
- On tasks longer than a few steps: call advisor **at least once** before committing to an approach and **once** before declaring done
- On short tasks: call advisor when the next action is non-obvious or high-risk
- Never call advisor redundantly — if you already have evidence pointing one way and the advisor points another, make one more reconciliation call rather than silently switching

#### Acting on Advisor Feedback

```
Rule: Give advice serious weight.

If the advisor says X and your tool results say Y:
  → Surface the conflict in one more advisor call: "I found Y, you suggest X — which constraint breaks the tie?"
  → Do NOT silently switch to X without verifying
  → Do NOT dismiss X without engaging with it

A passing self-test is not evidence the advice is wrong.
It is evidence your test doesn't check what the advice is checking.
```

#### Advisor in Your Own Workflow (Non-Claude Triggering)

You can prompt Claude to call the advisor by including trigger phrases in your message:
- `"check with advisor before proceeding"`
- `"get a second opinion on this approach"`
- `"advisor review before you write"`

This is especially useful for:
- Architecture decisions where getting it wrong means a large rework
- Security-sensitive code (auth, permissions, data access)
- Database migrations or schema changes
- Any step that touches shared infrastructure

### 14.3 The Anthropic Advisor API — For App Builders

For developers building Claude-powered applications (not using the Claude Code harness), the Advisor API lets you pair a fast executor model with Opus as an on-demand advisor.

**Pattern:**

```python
# Executor: Sonnet or Haiku handles routine work
# Advisor: Opus consulted only on uncertain decisions

# API call with beta header
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    tools=[advisor_tool],   # Makes advisor() callable
    messages=messages,
    betas=["advisor-tool-2026-03-01"]
)
```

**Benchmark results (Anthropic internal, April 2026):**

| Executor | Advisor | Score | vs baseline | vs full Opus | Cost vs full Opus |
|----------|---------|-------|------------|-------------|------------------|
| Sonnet 4.6 | None | 72.1% SWE-bench Multilingual | — | -8.7pp | -80% |
| Sonnet 4.6 | Opus 4.6 | 74.8% | +2.7pp | -6pp | **-11.9%** |
| Haiku 4.5 | None | 19.7% BrowseComp | — | — | -93% |
| Haiku 4.5 | Opus 4.6 | 41.2% BrowseComp | **+109%** | — | **-85%** |

The Haiku + Opus advisor pairing is the most dramatic: more than double the performance for 85% less cost than using Sonnet.

**When to use the Advisor API vs. always using Opus:** Use it when most requests are routine (Sonnet/Haiku handles them) but a subset require deep reasoning. The executor decides when to escalate. If >40% of requests need escalation, switching the main model to Opus may be cheaper.

---

## 15. CCA-F Exam Relevance

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
11. PreToolUse is the ONLY hook that can block an action; all others are observational
12. `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1` does NOT apply to Opus 4.7
13. ToolSearch regex patterns >200 chars are silently truncated — use short high-entropy patterns
14. 1-hour cache write tier (2.0×) is for Pro/Max subscribers on likely-reused prefixes; API customers get 5-minute (1.25×) by default
15. The advisor() tool forwards the entire conversation — most valuable before approach crystallization and before declaring done

---

*Sources: [Claude Code Docs](https://code.claude.com/docs/en/), [Claude Code Hooks](https://code.claude.com/docs/en/hooks), [Claude API Pricing](https://platform.claude.com/docs/en/about-claude/pricing), [Adaptive Thinking Docs](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking), [Advisor Tool Docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool), [Claude Code Changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md), [Anthropic Scientific Computing Guide](https://www.anthropic.com/research/long-running-Claude), [Apiyi April 2026 Changelog Analysis](https://help.apiyi.com/en/claude-code-changelog-2026-april-updates-en.html), [Cache TTL Community Analysis](https://github.com/anthropics/claude-code/issues/46829), [ToolSearch Failure Issue](https://github.com/anthropics/claude-code/issues/30466), Claude Code Camp, community analysis. Updated April 18, 2026 (v2.1.101).*
