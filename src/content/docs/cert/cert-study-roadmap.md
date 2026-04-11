---
title: "21-Day Study Roadmap"
description: "Phase-by-phase study plan from conceptual foundations through hands-on exercises, scenario practice, and exam simulation."
sidebar:
  order: 7
---

# Claude Certified Architect – Foundations: 21-Day Study Roadmap

## Your Study Plan at a Glance

```
PHASE 1: Conceptual Foundations    Days 1–5
PHASE 2: Hands-On Implementation   Days 6–12
PHASE 3: Scenario Practice         Days 13–17
PHASE 4: Exam Simulation           Days 18–21
```

Each phase builds on the previous one. Don't skip ahead — understanding before implementation, implementation before scenario practice.

---

## Domain Strength Assessment

Use this to calibrate how much time to spend on each domain:

| Domain | Typical Starting Strength | Key Gaps to Fill |
|---|---|---|
| **D1: Agentic Architecture (27%)** | Moderate — conceptual understanding but gaps in SDK specifics | `stop_reason` routing, `AgentDefinition`, hooks API, `fork_session`, `pause_turn` |
| **D2: Tool Design & MCP (18%)** | Strong if MCP experience exists | `isError` flag, error categories, tool distribution, `tool_choice` modes |
| **D3: Claude Code Config (20%)** | Strong if Claude Code user | `.claude/rules/` glob patterns, `context: fork`, Explore subagent, CI `-p` flag |
| **D4: Prompt Engineering (20%)** | Moderate — instincts good, API patterns need drilling | `tool_use` schemas, Batch API facts, validation-retry loops, few-shot structure |
| **D5: Context Management (15%)** | Moderate-Strong | "Lost in the middle" mitigation, case facts pattern, scratchpad files, crash recovery |

---

## Phase 1: Conceptual Foundations (Days 1–5)

**Goal:** Build a complete mental model of every testable concept before writing any code. For each topic, ask: "What tradeoff is being tested here?" — every exam question is a tradeoff question.

### Day 1: The Agentic Loop — D1, Task 1.1

Start here because D1 is 27% of the exam and contains the most SDK-level specifics.

**What to study:**

The agentic loop is a precise sequence:
1. Your code sends prompt + tool definitions + conversation history to Claude
2. Claude responds with text and/or `tool_use` blocks
3. Your code checks `stop_reason` — not Claude's text content
4. If `"tool_use"`: execute tools, append results as a user message, loop again
5. If `"end_turn"`: terminate loop, return text

**All stop_reason values to memorize:**
- `"end_turn"` → Claude finished. Terminate loop.
- `"tool_use"` → Claude wants tools. Execute and loop.
- `"max_tokens"` → Response truncated. Handle or increase max_tokens.
- `"refusal"` → Safety classifier declined. Log and surface to user.
- `"pause_turn"` → Server-side loop hit iteration limit. Send response back to continue.
- `"stop_sequence"` → Hit a custom stop sequence. Treat like end_turn.
- `"model_context_window_exceeded"` → Hit context limit. Compact and retry.

**Anti-patterns to memorize as wrong answers:**
- Parsing `"I'm done"` or similar text for termination
- Using `for i in range(10)` as the primary stop mechanism
- Checking text content to decide routing

**Session management:** `--resume <session-name>`, `--continue` (most recent), `forkSession: true` (independent branch without modifying original).

**Resources:**
- [Domain 1 Study Guide](./domain-1-agentic-architecture)
- Agent SDK overview and agent loop docs

---

### Day 2: Multi-Agent Orchestration & Hooks — D1, Tasks 1.2–1.5

Highest-value study day. Covers the most heavily weighted exam topics.

**Hub-and-spoke pattern:** Coordinator spawns specialized subagents. Subagents operate with isolated context — they do NOT inherit the coordinator's conversation history. Internal tool calls stay inside subagents. Only the final message returns to parent.

**The coordinator's three jobs:**
1. Task decomposition (breaking queries into well-scoped subtasks)
2. Delegation (assigning subtasks with clear objectives, output formats, scope limits)
3. Result aggregation (synthesizing, evaluating coverage, spawning follow-ups)

**AgentDefinition fields:**
- `description` → What Claude reads to decide WHEN to delegate to this agent
- `prompt` → Agent's system prompt (its persona and instructions)
- `tools` → Restricted tool access (omit = inherit all tools)
- `model` → Route to cheaper/faster models (Haiku for simple tasks)

**Hooks — this is high-frequency exam content:**
- `PreToolUse` → Fires BEFORE execution. Can `deny`, `allow`, `ask`, or modify input via `updatedInput`
- `PostToolUse` → Fires AFTER execution. Cannot undo. Can add `additionalContext`.
- Permission decision flow: PreToolUse → Deny Rules → Allow Rules → Ask Rules → PermMode → canUseTool → PostToolUse
- Key fact: Hooks run in the application process — consume **zero context window tokens**

**Parallel spawning:** Emit multiple Agent tool calls in one response → SDK runs them concurrently → up to 90% faster.

---

### Day 3: Tool Design, MCP, Built-in Tools — D2

You have MCP foundations. Focus on exam-specific angles.

**Tool descriptions:**
- Primary mechanism for selection — not few-shot, not routing layers
- Fix misrouting by expanding descriptions (at least 3–4 sentences)
- Include: what it does, input format, output format, when to use, when NOT to use
- Consolidation guidance: prefer fewer tools with `action` parameters over many single-action tools

**isError flag — critical distinction:**
- `isError: true` = tool execution FAILED (need retry or alternative)
- `isError: false` with empty content = search SUCCEEDED with zero results
- Protocol errors (JSON-RPC) are discarded; tool execution errors reach Claude's context

**tool_choice:**
- `"auto"` → Claude decides (may skip tools)
- `"any"` → Must call a tool, Claude picks which → use when document type is unknown
- `{"type": "tool", "name": "X"}` → Must call tool X → use for required first steps

**MCP configuration:**
- `.mcp.json` in repo root = project scope (shared via git)
- `~/.claude.json` = user scope (personal, not committed)
- `${VAR}` = env var expansion (fails if unset)
- `${VAR:-default}` = env var with fallback

**Built-in tools:**
- Grep → searches file CONTENTS
- Glob → searches file NAMES/PATHS
- Edit → targeted modification via unique text match (fallback: Read + Write)

---

### Day 4: Claude Code Configuration & CI/CD — D3

**CLAUDE.md hierarchy:**
- `~/.claude/CLAUDE.md` → user-level, NOT shared via version control
- `.claude/CLAUDE.md` or root `CLAUDE.md` → project-level, version-controlled
- Subdirectory `CLAUDE.md` → highest precedence

**`.claude/rules/` with glob patterns:**
```yaml
---
paths:
  - "**/*.test.*"
---
# Applies to ALL test files regardless of directory
```
Better than directory CLAUDE.md for files scattered across the codebase.

**Skills frontmatter:** `context: fork` isolates verbose output from main conversation. `allowed-tools` restricts access. `argument-hint` prompts for parameters. `agent: Explore` for read-only codebase exploration.

**CI/CD facts:**
- `-p` flag = non-interactive mode (the correct answer — always)
- `CLAUDE_HEADLESS=true` = does not exist (wrong answer)
- `--batch` = does not exist (wrong answer)
- `--output-format json` + `--json-schema` = structured CI output
- Independent sessions: generate in Session 1, review in Session 2 (no shared context)

**Plan mode:** Complex multi-file tasks, architectural decisions. Direct execution: single-file, clear scope.

---

### Day 5: Prompt Engineering, Structured Output & Batch — D4

**Structured output via tool_use:**
- Most reliable approach: eliminates JSON syntax errors
- Define extraction tool with JSON schema → force with `tool_choice`
- Nullable fields (`"type": ["string", "null"]`) prevent fabrication
- Add `"unclear"` enum value for genuinely ambiguous cases
- Schemas eliminate SYNTAX errors. Cannot catch SEMANTIC errors (line items not summing to total).

**Few-shot prompting:**
- Use for: inconsistent results, ambiguous cases, consistent output format
- 2–4 targeted examples for ambiguous scenarios
- Include reasoning — enables generalization to novel patterns

**Explicit criteria:**
- "Flag only when X contradicts Y" beats "check accuracy"
- "Be conservative" / "high-confidence only" = vague, doesn't improve precision
- False positive category with 60%+ FP rate → disable temporarily, improve separately

**Validation-retry loops:**
- Send original document + failed extraction + specific errors on retry
- Retries fix format errors. Don't fix absent information — make field nullable.

**Batch API:**
- 50% cost savings
- Up to 24-hour window, no latency SLA
- Multi-turn tool calling: NOT supported
- `custom_id` correlates requests to results
- Use for: overnight reports, weekly audits, nightly generation
- NOT for: blocking pre-merge checks, real-time responses

---

## Phase 2: Hands-On Implementation (Days 6–12)

**Goal:** Build the four exercises from the exam guide. Implementation reveals gaps that reading misses.

### Days 6–7: Exercise 1 — Multi-Tool Agent with Escalation Logic

Build a customer support agent (Python, raw API). Covers D1 + D2 + D5.

```
Step 1: Define 3–4 tools with detailed, differentiated descriptions
  • get_customer: verify identity (REQUIRED before refunds)
  • lookup_order: requires verified customer_id
  • process_refund: requires order verification
  • escalate_to_human: structured handoff summary

Step 2: Implement agentic loop on stop_reason
  while True:
    response = client.messages.create(...)
    messages.append({"role": "assistant", "content": response.content})
    if response.stop_reason == "end_turn": return text
    # Execute tools, append as user message, loop

Step 3: Structured error responses
  • transient errors: isError:true, isRetryable:true
  • validation errors: isError:true, isRetryable:false, specific guidance
  • valid empty results: isError:false

Step 4: PreToolUse hook blocking process_refund > $500

Step 5: PostToolUse hook normalizing Unix timestamps → ISO 8601

Step 6: Test with multi-issue message ("return order AND dispute charge")
```

**Observe:** Remove the hook → rely on prompt instructions. Notice how often it fails.

---

### Days 8–9: Exercise 2 — Claude Code Team Configuration

Configure a complete project configuration stack. Covers D3 + D2.

```
Step 1: Project-level CLAUDE.md with universal standards

Step 2: .claude/rules/testing.md with paths: ["**/*.test.*"]
        .claude/rules/api.md with paths: ["src/api/**/*"]

Step 3: .claude/skills/analyze-codebase/SKILL.md
        with context: fork, allowed-tools: [Read, Grep, Glob]

Step 4: .mcp.json with GitHub MCP server
        env: {GITHUB_TOKEN: "${GITHUB_TOKEN}"}

Step 5: Test plan mode on multi-file refactoring
        vs. direct execution on single-file bug fix

Step 6: Run CI mode:
  claude -p "review this PR" --output-format json \
    --json-schema '{"type":"object","properties":{"findings":{"type":"array"}}}'
```

---

### Days 10–11: Exercise 3 — Structured Data Extraction Pipeline

Build an extraction system for insurance/invoice documents. Covers D4 + D5.

```
Step 1: Define extraction tool with JSON schema
  • Required fields: vendor_name, total_amount, payment_status
  • Nullable fields: tax_id, invoice_number, discount
  • Enum + "other": currency, document_type
  • "unclear" enum value: payment_status

Step 2: Force with tool_choice: {"type": "tool", "name": "extract_claim"}

Step 3: Process a document with missing fields → verify null (not fabricated)

Step 4: Validation-retry loop
  • First attempt fails validation
  • Retry with: original doc + failed extraction + specific errors

Step 5: 3 few-shot examples showing varied document formats

Step 6: Batch processing design
  • custom_id per document
  • Poll for completion
  • Resubmit failed docs only
```

---

### Day 12: Exercise 4 — Multi-Agent Research Pipeline

Coordinator with web search + document analysis + synthesis subagents. Covers D1 + D2 + D5.

```
Step 1: Coordinator with allowedTools: ["Agent"]
        Define agents via AgentDefinition with description, prompt, tools

Step 2: Coordinator emits multiple Agent tool calls (parallel execution)

Step 3: Structured subagent output
  {"claim": "...", "source_url": "...", "date": "...", "relevance": 5}

Step 4: Simulate subagent timeout
  → Return structured error: failure_type, attempted_query, partial_results
  → Coordinator proceeds with partial results + coverage annotation

Step 5: Conflicting source data
  → Verify synthesis presents BOTH values with context (not picking one)
```

---

## Phase 3: Scenario Practice (Days 13–17)

**Goal:** Exam-format practice. For each question, write down your reasoning before looking at the answer.

### Day 13: Scenario 1 — Customer Support Resolution Agent

Tests intersection of D1, D2, D5. Key tradeoffs:

| Issue | Wrong Answer | Correct Answer |
|---|---|---|
| Agent skips get_customer 12% of time | Add mandatory prompt instruction | PreToolUse hook enforcing ordering |
| Calls wrong tool due to vague description | Add few-shot examples first | Expand tool descriptions first |
| Customer asks for human agent | "Let me try to help first" | Escalate IMMEDIATELY |
| Multiple customer matches | Pick most recent account | Ask for additional identifier |
| 55% first-contact resolution | Sentiment-based escalation | Explicit criteria + few-shot examples |

---

### Day 14: Scenarios 2 + 3 — Code Generation & Multi-Agent Research

**Scenario 2 tradeoffs:**
- Plan mode vs direct execution (scope of change)
- `.claude/rules/` glob patterns vs subdirectory CLAUDE.md (test files everywhere)
- Skills `context: fork` vs CLAUDE.md (on-demand vs always-loaded)
- Iterative refinement: input/output examples, test-driven, interview pattern

**Scenario 3 tradeoffs:**
- Narrow task decomposition → coverage gaps (check coordinator first)
- Subagent context isolation → must pass findings explicitly
- Iterative refinement loops → coordinator evaluates and spawns follow-ups
- Parallel spawning → multiple Agent calls in one coordinator response

---

### Day 15: Scenarios 4 + 5 — Developer Productivity & CI/CD

**Scenario 4 tradeoffs:**
- Grep (content) vs Glob (file names) — most common confusion
- Incremental exploration: Grep → Read → trace (not read-all-upfront)
- Edit tool failure → Read + Write fallback
- MCP tool descriptions must explain why they're better than built-in tools

**Scenario 5 tradeoffs:**
- `-p` flag (correct) vs `CLAUDE_HEADLESS=true` / `--batch` (don't exist)
- Batch API for overnight reports vs synchronous API for pre-merge checks
- Independent review sessions vs same-session self-review
- Include prior findings to avoid duplicate PR comments
- Multi-pass review: per-file parallel + cross-file integration

---

### Day 16: Scenario 6 — Structured Data Extraction

Tests D4 + D5. Focus areas:

| Question Type | Key Distinction |
|---|---|
| Structured output method | tool_use (most reliable) vs asking for JSON in text |
| Syntax vs semantic errors | tool_use fixes syntax; cannot catch calculation errors |
| Unknown document type | tool_choice: "any" (not "auto" — auto might return text) |
| Missing field in source | Make nullable; retries won't create absent information |
| Batch API | custom_id correlation; no multi-turn tool calling |
| Accuracy validation | Segment by type AND field (not just aggregate 97%) |

---

### Day 17: Cross-Domain Pattern Recognition

The hardest questions require recognizing which principle applies across domains. Practice these:

```
"When do you need deterministic guarantees?" → Hooks (D1, D2)
"What's the first fix for tool misrouting?" → Descriptions (D2)
"What's wrong with 97% aggregate accuracy?" → Masking segment failures (D5)
"What's wrong with self-review?" → Reasoning context bias (D4)
"Why did the coordinator miss topics?" → Task decomposition gap (D1)
"Why is 'be conservative' not enough?" → Not measurable criteria (D4)
"What's wrong with sentiment-based escalation?" → Frustration ≠ complexity (D5)
"When to batch vs synchronous API?" → Blocking vs non-blocking (D4)
```

---

## Phase 4: Exam Simulation & Final Review (Days 18–21)

### Day 18: Full Practice Exam
Take the official practice exam (Anthropic Skilljar). After each incorrect answer, understand WHY that option is wrong — not just what the right answer is.

### Day 19: Gap Analysis
Based on practice exam: identify which domains and task statements you missed. Return to those specific sections in the domain guides. Focus on the tradeoff reasoning.

### Day 20: Rapid-Fire Concept Review

```
AGENT SDK:
  stop_reasons: end_turn → stop, tool_use → continue, pause_turn → send back
  AgentDefinition: description (when), prompt (who), tools (what), model (how)
  Hooks: PreToolUse (block/modify), PostToolUse (normalize)
  allowedTools must include "Agent" for coordinator

MCP:
  isError: true = failure (needs retry decisions)
  isError: false = success (even if empty result)
  .mcp.json = project scope | ~/.claude.json = user scope
  ${VAR} = required | ${VAR:-default} = optional with fallback

CLAUDE CODE:
  User < Project < Directory (precedence)
  ~/.claude/CLAUDE.md NOT shared via git
  .claude/rules/ with paths: glob for scattered files
  Skills: context: fork, allowed-tools, argument-hint
  -p flag for CI | --output-format json | --json-schema

API:
  tool_use = guaranteed structured output (eliminates syntax errors only)
  tool_choice: auto (optional) | any (must use tool) | forced (specific tool)
  Batch: 50% savings, 24hr max, no multi-turn tools, custom_id

CONTEXT:
  Case facts block → prevents summarization loss of exact values
  Lost in the middle → key findings at beginning
  Scratchpad files → persist across context window boundaries
  /compact → compresses, loses early-prompt instructions
  Stratified sampling → validate by segment, not just aggregate
```

### Day 21: Final Distractor Drill

For each question in the 12 sample questions, before looking at the answer: write down which two options you can **eliminate** and why. If you can confidently eliminate two on every question, your pass probability is very high.

---

## Official Resources (In Priority Order)

1. Agent SDK overview — `platform.claude.com/docs/en/agent-sdk/overview`
2. Agent loop — `platform.claude.com/docs/en/agent-sdk/agent-loop`
3. Subagents — `platform.claude.com/docs/en/agent-sdk/subagents`
4. Hooks — `platform.claude.com/docs/en/agent-sdk/hooks`
5. Permissions — `platform.claude.com/docs/en/agent-sdk/permissions`
6. Agent Skills — `platform.claude.com/docs/en/agent-sdk/skills`
7. Tool use overview — `docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview`
8. Implement tool use — `docs.anthropic.com/en/docs/build-with-claude/tool-use/implement-tool-use`
9. Structured outputs — `platform.claude.com/docs/en/build-with-claude/structured-outputs`
10. Batch processing — `docs.anthropic.com/en/docs/build-with-claude/message-batches`
11. MCP tools spec — `modelcontextprotocol.io/specification/draft/server/tools`
12. MCP resources spec — `modelcontextprotocol.io/specification/2025-06-18/server/resources`
13. Claude Code settings — `code.claude.com/docs/en/settings`
14. Claude Code headless — `code.claude.com/docs/en/headless`
15. Claude Code sub-agents — `code.claude.com/docs/en/sub-agents`

**Anthropic Academy (Skilljar — free):**
- Claude Code in Action
- Building with the Claude API
- Introduction to MCP
- Advanced MCP Patterns
- Introduction to Agent Skills

**Community:**
- GitHub: `SGridworks/claude-certified-architect-training` (110 practice questions)
- Official exam guide PDF (from Anthropic)
