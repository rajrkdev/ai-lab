---
title: "Study Roadmap"
---

# Claude Certified Architect – Foundations: Detailed Study Roadmap

## Your Starting Position

Based on your existing work, here's an honest assessment of where you stand against each exam domain. This drives the priority weighting in the roadmap.

**Domain 1: Agentic Architecture & Orchestration (27% of exam)**
Current strength: MODERATE. You understand agentic concepts deeply from your RAG taxonomy work, and agent framework evaluations. However, the exam tests *Claude Agent SDK specifics* — the `Agent` tool (formerly `Task`), `AgentDefinition` configuration, `allowedTools`, hooks (`PreToolUse`/`PostToolUse`), `stop_reason` handling, `fork_session`, and hub-and-spoke coordinator patterns. These are SDK-level implementation details you haven't drilled on yet.

**Domain 2: Tool Design & MCP Integration (18% of exam)**
Current strength: STRONG. Your comprehensive MCP server types guide, stdio vs Streamable HTTP transport knowledge, and `.mcp.json` configuration expertise cover most of this domain. Gaps: the `isError` flag pattern for structured error responses, tool distribution principles (4-5 tools per agent vs 18), and `tool_choice` forced selection patterns.

**Domain 3: Claude Code Configuration & Workflows (20% of exam)**
Current strength: STRONG. Your universal CLAUDE.md template, configuration hierarchy knowledge (precedence tiers, settings.json), and workflow orchestration SKILL.md put you ahead here. Gaps: `.claude/rules/` YAML frontmatter path-scoping (glob patterns for conditional loading), `context: fork` in skill frontmatter, the Explore subagent, and CI/CD integration with `-p` flag + `--output-format json` + `--json-schema`.

**Domain 4: Prompt Engineering & Structured Output (20% of exam)**
Current strength: MODERATE. You have strong prompt engineering instincts from previous applied work, but this domain tests *specific Claude API patterns*: `tool_use` with JSON schemas for guaranteed structured output, `tool_choice` options (`"auto"` vs `"any"` vs forced), few-shot examples for false positive reduction, validation-retry loops, and the Message Batches API (50% savings, 24-hour window, `custom_id` correlation, no multi-turn tool calling).

**Domain 5: Context Management & Reliability (15% of exam)**
Current strength: MODERATE-STRONG. Your context window management and prompt caching work provides foundation. Exam-specific patterns to learn: "lost in the middle" effect mitigation, progressive summarization risks, structured "case facts" extraction, scratchpad files for context boundaries, `/compact`, crash recovery via state manifests, and confidence calibration with stratified sampling.

---

## Study Architecture: 4 Phases

The roadmap is organized in 4 phases that follow a deliberate progression: conceptual foundations first, then hands-on implementation, then scenario practice, and finally exam simulation. Each phase builds on the previous one.

### Phase 1: Conceptual Foundations (Days 1–5)

The goal of this first phase is to build a complete mental model of every testable concept before writing any code. Read actively — for each topic, ask yourself "what tradeoff is being tested here?" because every exam question is a tradeoff question.

**Day 1: Agent SDK Deep Dive — The Agentic Loop (Domain 1, Task 1.1 + 1.7)**

Start here because Domain 1 is 27% of the exam and likely your biggest knowledge gap at the SDK level.

Study the agentic loop lifecycle end-to-end. The loop follows a precise sequence: your code sends a prompt to Claude → Claude responds with text and/or `tool_use` blocks → you check `stop_reason` → if `"tool_use"`, execute the tools, append results to conversation history, send again → if `"end_turn"`, the loop terminates. This is the most fundamental concept on the exam.

Key anti-patterns to memorize (these appear as wrong answers):
- Parsing Claude's natural language output to decide when to stop (e.g., checking if the response contains "I'm done") — always use `stop_reason`
- Setting an arbitrary iteration cap (like `max_iterations = 5`) as the primary stopping mechanism
- Checking for assistant text content as a completion indicator

Then study session management: `--resume <session-name>` continues a named session, `fork_session` creates independent branches from a shared baseline, and starting fresh with injected summaries is more reliable than resuming when tool results are stale.

Resources to read:
- Agent loop docs: `platform.claude.com/docs/en/agent-sdk/agent-loop`
- Agent SDK overview: `platform.claude.com/docs/en/agent-sdk/overview`
- Anthropic engineering blog: "Building agents with the Claude Agent SDK"

**Day 2: Multi-Agent Orchestration & Hooks (Domain 1, Tasks 1.2–1.5)**

This is the highest-value study day because it covers the exam's most heavily weighted topics.

Start with the hub-and-spoke pattern: a coordinator agent manages all communication, error handling, and routing between subagents. Subagents operate with isolated context — they do NOT inherit the coordinator's conversation history. The coordinator must explicitly pass findings in the subagent's prompt. The `Agent` tool (renamed from `Task` in v2.1.63) is the mechanism for spawning subagents, and `allowedTools` must include `"Agent"` for a coordinator to invoke them.

Study `AgentDefinition`: it takes `description` (when to use this agent), `prompt` (system prompt), `tools` (allowed tool names), and `model`. The `description` field is what Claude reads to decide which subagent to invoke — make it precise.

Then study hooks. `PreToolUse` hooks intercept outgoing tool calls before execution — use them to enforce compliance rules (block refunds > $500, verify customer ID before order lookup). `PostToolUse` hooks intercept tool results before the model processes them — use them to normalize data formats (Unix timestamps → ISO 8601). The critical exam concept: hooks provide *deterministic guarantees* while prompt instructions provide *probabilistic compliance*. When business rules require guaranteed compliance (identity verification before financial operations), always choose hooks.

Parallel subagent spawning: the coordinator can emit multiple `Agent` tool calls in a single response to run subagents concurrently.

Resources:
- Subagents docs: `platform.claude.com/docs/en/agent-sdk/subagents`
- Hooks docs: `platform.claude.com/docs/en/agent-sdk/hooks`
- Permissions docs: `platform.claude.com/docs/en/agent-sdk/permissions`

**Day 3: Tool Design, MCP Integration & Built-in Tools (Domain 2)**

You have strong MCP foundations. Focus on the exam-specific angles you haven't drilled.

Tool descriptions are the primary mechanism LLMs use for tool selection. Minimal descriptions lead to unreliable selection. The exam tests your ability to diagnose and fix tool misrouting by expanding descriptions to include input formats, example queries, edge cases, and boundary explanations. When two tools have overlapping descriptions (like `analyze_content` and `analyze_document`), the fix is to rename them and differentiate their descriptions, not to add few-shot examples or build routing classifiers.

The `isError` flag pattern: MCP tool results can include `isError: true` to signal failures. Return structured error metadata including `errorCategory` (transient/validation/permission), `isRetryable` boolean, and human-readable descriptions. The exam distinguishes between access failures (timeouts needing retry) and valid empty results (successful queries with no matches) — these must not be confused.

Tool distribution principle: giving an agent 18 tools degrades selection reliability vs 4-5 focused tools. Each subagent should get only tools relevant to its role. But you can provide scoped cross-role tools for high-frequency needs (e.g., a `verify_fact` tool for the synthesis agent).

`tool_choice` options:
- `"auto"` — Claude decides freely (may return text without calling a tool)
- `"any"` — must call a tool but can choose which
- `{"type": "tool", "name": "extract_metadata"}` — forced to call that specific tool
These are testable facts. `"any"` guarantees structured output when document type is unknown. Forced selection ensures a specific tool runs first (e.g., metadata extraction before enrichment).

Built-in tools: Grep searches file *contents* for patterns. Glob finds files by *name/extension* patterns. Read/Write for full file operations; Edit for targeted modifications using unique text matching. When Edit fails (non-unique match), fall back to Read + Write.

Resources:
- MCP tools spec: `modelcontextprotocol.io/specification/draft/server/tools`
- MCP resources spec: `modelcontextprotocol.io/specification/2025-06-18/server/resources`
- MCP in Claude Code: `code.claude.com/docs/en/mcp`
- Tool use docs: `docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview`

**Day 4: Claude Code Configuration & CI/CD (Domain 3)**

This is your strongest domain. Focus on exam-specific details you might get wrong.

CLAUDE.md hierarchy — the exact precedence matters:
- `~/.claude/CLAUDE.md` → user-level, NOT shared via version control
- `.claude/CLAUDE.md` or root `CLAUDE.md` → project-level, version-controlled
- Subdirectory `CLAUDE.md` → directory-level, most specific

`.claude/rules/` with YAML frontmatter is a key testable pattern. Rules files use `paths` fields with glob patterns (e.g., `paths: ["terraform/**/*"]`) for conditional activation. These load only when editing matching files, reducing irrelevant context. The advantage over subdirectory CLAUDE.md files: glob patterns can target files spread across the codebase (like `**/*.test.tsx` for all test files regardless of directory).

Skills frontmatter: `context: fork` runs the skill in an isolated subagent context (prevents polluting main conversation). `allowed-tools` restricts tool access during skill execution. `argument-hint` prompts for required parameters.

CI/CD integration facts:
- `-p` (or `--print`) flag runs Claude Code in non-interactive mode — this is the correct answer for CI pipeline hangs
- `--output-format json` with `--json-schema` produces machine-parseable structured output
- CLAUDE.md provides project context (testing standards, review criteria) to CI-invoked Claude Code
- Session context isolation: the same session that generated code is less effective at reviewing it — use independent review instances

Plan mode vs direct execution:
- Plan mode: complex tasks, large-scale changes, multiple valid approaches, architectural decisions
- Direct execution: simple, well-scoped changes (single-file bug fix, adding one validation check)
- Explore subagent: isolates verbose discovery output, returns summaries to preserve main context

Resources:
- Claude Code settings: `code.claude.com/docs/en/settings`
- Headless/CI mode: `code.claude.com/docs/en/headless`
- Subagents: `code.claude.com/docs/en/sub-agents`

**Day 5: Prompt Engineering, Structured Output & Batch Processing (Domain 4)**

Start with structured output via `tool_use`. This is the exam's recommended approach for guaranteed schema-compliant output — it eliminates JSON syntax errors entirely. You define an extraction tool with a JSON schema as its input parameters, force Claude to call it, and extract structured data from the `tool_use` response.

Schema design considerations tested on the exam:
- Make fields optional (nullable) when source documents may not contain the info — this prevents fabrication
- Use `enum` with `"other"` + detail string patterns for extensible categories
- Add `"unclear"` as an enum value for ambiguous cases
- Strict JSON schemas eliminate *syntax* errors but NOT *semantic* errors (line items that don't sum to total)

Few-shot prompting: the exam treats this as the most effective technique for consistency when detailed instructions alone produce inconsistent results. Create 2-4 targeted examples for ambiguous scenarios showing reasoning for why one action was chosen. Few-shot examples enable generalization to novel patterns — this is a key distinction from rule-based approaches.

Explicit criteria > vague instructions: "flag comments only when claimed behavior contradicts actual code behavior" beats "check that comments are accurate." General instructions like "be conservative" or "only report high-confidence findings" fail to improve precision.

Validation-retry loops: append specific validation errors to the prompt on retry. But recognize when retries are ineffective — when information is absent from the source document (vs format or structural errors).

Message Batches API facts (these are testable):
- 50% cost savings
- Up to 24-hour processing window, no guaranteed latency SLA
- Appropriate for: overnight reports, weekly audits, nightly test generation
- NOT appropriate for: blocking pre-merge checks
- Does NOT support multi-turn tool calling within a single request
- `custom_id` fields correlate request/response pairs
- Handle failures by resubmitting only failed documents identified by `custom_id`

Multi-instance review: a second independent Claude instance (without prior reasoning context) catches more issues than self-review instructions or extended thinking in the same session.

Resources:
- Structured outputs: `platform.claude.com/docs/en/build-with-claude/structured-outputs`
- Tool use implementation: `docs.anthropic.com/en/docs/build-with-claude/tool-use/implement-tool-use`
- Batch processing: `docs.anthropic.com/en/docs/build-with-claude/message-batches`

---

### Phase 2: Hands-On Implementation (Days 6–12)

Now build the four exercises from the exam guide. These reinforce concepts through muscle memory and reveal gaps your reading missed.

**Days 6–7: Exercise 1 — Multi-Tool Agent with Escalation Logic**

Build a customer support agent using the Claude Agent SDK (Python). This single exercise covers Domain 1 + Domain 2 + Domain 5.

Step 1: Define 3-4 tools (`get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`) with detailed descriptions that clearly differentiate each tool's purpose.

Step 2: Implement the agentic loop checking `stop_reason` — continue on `"tool_use"`, terminate on `"end_turn"`.

Step 3: Add structured error responses to tools with `errorCategory`, `isRetryable`, and human-readable descriptions.

Step 4: Implement a `PreToolUse` hook that blocks `process_refund` when amount exceeds $500, redirecting to escalation.

Step 5: Implement a `PostToolUse` hook that normalizes timestamps from tool results before the model processes them.

Step 6: Test with a multi-concern message (e.g., "I want to return order #123 AND dispute the charge on order #456") and verify the agent decomposes, handles each, and synthesizes.

What to observe and note: How does the agent behave when you remove the hook and rely only on prompt instructions? This demonstrates the deterministic vs probabilistic compliance distinction.

**Days 8–9: Exercise 2 — Claude Code Team Configuration**

Set up a real project with the full configuration stack. This covers Domain 3 + Domain 2.

Step 1: Create a project-level CLAUDE.md with universal standards.

Step 2: Create `.claude/rules/testing.md` with `paths: ["**/*.test.*"]` and `.claude/rules/api.md` with `paths: ["src/api/**/*"]`.

Step 3: Create a skill in `.claude/skills/analyze-codebase/SKILL.md` with `context: fork` and `allowed-tools` restrictions.

Step 4: Configure an MCP server in `.mcp.json` with `${GITHUB_TOKEN}` environment variable expansion.

Step 5: Test plan mode on a multi-file refactoring task vs direct execution on a single-file bug fix. Note the behavioral differences.

Step 6: Run Claude Code in CI mode with `-p "review this PR" --output-format json --json-schema '{"type":"object","properties":{"findings":{"type":"array"}}}'`

**Days 10–11: Exercise 3 — Structured Data Extraction Pipeline**

Build an extraction system processing insurance documents. This covers Domain 4 + Domain 5 and directly maps to your applied work.

Step 1: Define an extraction tool with a JSON schema: required fields, optional/nullable fields, enum with `"other"` + detail, `"unclear"` for ambiguous cases.

Step 2: Use `tool_choice: {"type": "tool", "name": "extract_claim"}` to force extraction.

Step 3: Process a document with missing fields — verify null returns instead of fabrication.

Step 4: Implement a validation-retry loop: when validation fails, send follow-up with original document + failed extraction + specific error.

Step 5: Add 3 few-shot examples showing extraction from documents with varied formats.

Step 6: Design a batch processing strategy with `custom_id` correlation and failure handling.

**Day 12: Exercise 4 — Multi-Agent Research Pipeline**

Build a coordinator with web search + document analysis + synthesis subagents. This covers Domain 1 + Domain 2 + Domain 5.

Step 1: Build coordinator with `allowedTools` including `"Agent"`. Define subagents via `AgentDefinition`.

Step 2: Emit multiple `Agent` tool calls in a single coordinator response for parallel execution.

Step 3: Design structured output separating content from metadata (claim, evidence, source URL, publication date).

Step 4: Simulate a subagent timeout — return structured error context and verify coordinator proceeds with partial results.

Step 5: Test with conflicting source data — verify synthesis preserves both values with attribution rather than arbitrarily selecting one.

---

### Phase 3: Scenario Practice (Days 13–17)

Now shift to exam-format practice. For each scenario, work through questions focusing on tradeoff reasoning.

**Day 13: Scenario 1 — Customer Support Resolution Agent**

This scenario tests the intersection of Domains 1, 2, and 5. The key tradeoffs:
- Programmatic enforcement (hooks) vs prompt-based guidance for workflow ordering
- When to escalate (policy gaps, customer requests, inability to progress) vs resolve autonomously
- Structured handoff summaries for human agents
- Tool description quality for reliable selection
- Context management across multi-issue sessions

Practice questions to work through:
1. Agent skips `get_customer` 12% of the time — what's the fix? (Programmatic prerequisite, not prompt enhancement)
2. Agent calls wrong tool due to minimal descriptions — what's the first step? (Expand tool descriptions, not few-shot examples)
3. Agent has 55% first-contact resolution — how to improve escalation? (Explicit criteria + few-shot examples, not confidence scores or sentiment analysis)
4. Customer asks for human agent — what should the agent do? (Honor immediately without attempting investigation first)
5. Multiple customer matches from `get_customer` — what should the agent do? (Ask for additional identifiers, not heuristic selection)

**Day 14: Scenarios 2 + 3 — Code Generation & Multi-Agent Research**

Scenario 2 tradeoffs:
- Plan mode vs direct execution (complexity assessment)
- `.claude/rules/` with glob patterns vs subdirectory CLAUDE.md (test files spread across codebase)
- Skills with `context: fork` vs CLAUDE.md (on-demand vs always-loaded)
- Iterative refinement: input/output examples, test-driven iteration, interview pattern

Scenario 3 tradeoffs:
- Narrow task decomposition by coordinator → incomplete coverage
- Subagent context isolation — must explicitly pass findings
- Iterative refinement loops — coordinator evaluates synthesis for gaps
- Parallel subagent spawning via multiple `Agent` calls in one turn
- Scoped cross-role tools (verify_fact for synthesis) vs full tool access

**Day 15: Scenarios 4 + 5 — Developer Productivity & CI/CD**

Scenario 4 tradeoffs:
- Grep (content search) vs Glob (file pattern matching)
- Incremental codebase understanding: Grep → Read → trace flows (not read all files upfront)
- Edit tool failure → Read + Write fallback
- MCP tool descriptions must be detailed enough to prevent agent preferring built-in tools

Scenario 5 tradeoffs:
- `-p` flag for non-interactive CI mode (not `CLAUDE_HEADLESS` or `--batch`)
- Batch API for overnight reports, synchronous API for pre-merge checks
- Session context isolation: independent review instance > same-session self-review
- Include prior review findings to avoid duplicate comments
- Multi-pass review: per-file local analysis + cross-file integration pass

**Day 16: Scenario 6 — Structured Data Extraction**

This scenario tests Domains 4 + 5. Focus on:
- `tool_use` with JSON schemas eliminates syntax errors but not semantic errors
- Optional/nullable fields prevent fabrication when info is absent
- `tool_choice: "any"` guarantees structured output with unknown document types
- Retry-with-error-feedback for format mismatches; retries are ineffective for absent information
- Batch API: `custom_id` correlation, resubmit only failed docs, no multi-turn tool calling
- Human review routing: field-level confidence scores calibrated with labeled validation sets
- Aggregate accuracy metrics (97% overall) can mask poor performance on specific document types

**Day 17: Cross-Domain Pattern Recognition**

The exam's hardest questions require recognizing which principle applies across domains. Study these cross-cutting patterns:

Pattern 1 — Deterministic vs Probabilistic: Hooks for guaranteed compliance, prompt instructions for guidance. This applies to tool ordering (D1), data normalization (D1), and review criteria (D4).

Pattern 2 — Isolation: Subagent context isolation (D1), `context: fork` for skills (D3), independent review instances (D4), session context isolation in CI (D3).

Pattern 3 — Structured Metadata: Claim-source mappings (D5), structured error responses with `errorCategory` (D2), `detected_pattern` fields for feedback loops (D4), `custom_id` for batch correlation (D4).

Pattern 4 — Proportionate Response: Expand tool descriptions before building routing classifiers (D2), add explicit criteria before deploying ML classifiers (D5), test prompts on samples before batch processing (D4).

Pattern 5 — Anti-patterns as Distractors: Same-session self-review, sentiment-based escalation, generic "be conservative" instructions, arbitrary iteration caps, silently suppressing errors, parsing natural language for loop termination.

---

### Phase 4: Exam Simulation & Final Review (Days 18–21)

**Day 18: Practice Exam**

Take the official practice exam (link provided by Anthropic through Skilljar). The practice exam uses the same scenarios, format, and difficulty level. After each answer, read the explanation thoroughly — the explanations reveal the exam's reasoning framework.

**Day 19: Gap Analysis & Targeted Review**

Based on practice exam results, identify which domains and task statements you missed. Go back to the specific documentation for those areas. Focus on the tradeoff reasoning — if you got a question wrong, understand *why* the correct answer is better, not just *what* it is.

**Day 20: Rapid-Fire Concept Review**

Review these high-frequency exam facts one final time:

Agent SDK: `stop_reason` values (`"tool_use"` → continue, `"end_turn"` → stop). `Agent` tool for subagent spawning. `allowedTools` must include `"Agent"`. `AgentDefinition` with description, prompt, tools. Hooks: `PreToolUse` for blocking, `PostToolUse` for normalization. Subagents don't inherit parent context.

MCP: `isError` flag. `.mcp.json` project scope vs `~/.claude.json` user scope. `${VAR}` expansion. MCP resources for content catalogs. Tools from all configured servers available simultaneously.

Claude Code: CLAUDE.md hierarchy (user < project < directory). `.claude/rules/` with `paths` glob patterns. `.claude/commands/` (project) vs `~/.claude/commands/` (personal). Skills with `context: fork`, `allowed-tools`, `argument-hint`. `-p` flag for CI. `--output-format json` + `--json-schema`. Plan mode for complex tasks. `/compact` for context reduction. `/memory` for checking loaded files.

API: `tool_use` with JSON schemas for guaranteed structured output. `tool_choice`: `"auto"` (optional), `"any"` (must use a tool), forced (must use specific tool). Message Batches API: 50% savings, 24hr window, `custom_id`, no multi-turn tool calling.

Context: "Lost in the middle" effect. Progressive summarization loses numerical details. Trim verbose tool outputs. Place key findings at beginning. Scratchpad files for long sessions. `/compact` for context reduction.

**Day 21: Final Exam Simulation**

Do one more pass through the 12 sample questions from the exam guide. For each, before looking at the answer, write down your reasoning for eliminating each distractor. If you can confidently eliminate 2 distractors on every question, your pass probability is extremely high.

---

## Official Resources Checklist

These are the documentation pages to read (in priority order matching the roadmap):

1. Agent SDK overview — `platform.claude.com/docs/en/agent-sdk/overview`
2. Agent loop — `platform.claude.com/docs/en/agent-sdk/agent-loop`
3. Subagents — `platform.claude.com/docs/en/agent-sdk/subagents`
4. Hooks — `platform.claude.com/docs/en/agent-sdk/hooks`
5. Permissions — `platform.claude.com/docs/en/agent-sdk/permissions`
6. Agent Skills — `platform.claude.com/docs/en/agent-sdk/skills`
7. Tool use — `docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview`
8. Implement tool use — `docs.anthropic.com/en/docs/build-with-claude/tool-use/implement-tool-use`
9. Structured outputs — `platform.claude.com/docs/en/build-with-claude/structured-outputs`
10. Batch processing — `docs.anthropic.com/en/docs/build-with-claude/message-batches`
11. MCP tools spec — `modelcontextprotocol.io/specification/draft/server/tools`
12. MCP resources spec — `modelcontextprotocol.io/specification/2025-06-18/server/resources`
13. MCP in Claude Code — `code.claude.com/docs/en/mcp`
14. Claude Code settings — `code.claude.com/docs/en/settings`
15. Claude Code headless — `code.claude.com/docs/en/headless`
16. Claude Code subagents — `code.claude.com/docs/en/sub-agents`
17. Anthropic engineering blog: "Building agents with the Claude Agent SDK"

Anthropic Academy courses on Skilljar (free):
- Claude Code in Action
- Building with the Claude API
- Introduction to MCP
- Advanced MCP Patterns
- Introduction to Agent Skills

Community resources:
- GitHub: `SGridworks/claude-certified-architect-training` (110 practice questions)
- Exam guide PDF (you already have this)

---

## Exam Day Strategy

The exam presents 4 random scenarios from a pool of 6, with approximately 15 questions each. Here is how to approach it:

First, read each scenario description carefully before answering any questions. The scenario context often contains details that eliminate wrong answers.

Second, for each question, eliminate distractors before selecting. The exam guide reveals that distractors target candidates with "incomplete knowledge or experience." Common distractor patterns include: over-engineered solutions when a simple fix exists (routing classifiers when tool descriptions are the problem), probabilistic approaches when deterministic guarantees are needed (prompt instructions when hooks are required), and wrong-level fixes (blaming downstream agents when the coordinator's task decomposition is the issue).

Third, watch for "most effective first step" phrasing. This always points toward the lowest-effort, highest-leverage fix — not the most comprehensive solution.

Fourth, there is no penalty for guessing. Never leave a question blank.

Fifth, pace yourself. With 60 questions and scenario reading time, you have roughly 1-1.5 minutes per question. If you're stuck, eliminate what you can, pick the best remaining option, and move on.
