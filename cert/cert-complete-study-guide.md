---
layout: default
title: "Complete Study Guide"
---

# Claude Certified Architect – Foundations: Complete Study Guide

The Claude Certified Architect exam tests deep, applied knowledge across five domains spanning agentic architecture, tool design, Claude Code configuration, prompt engineering, and context management. This guide covers **every task statement** with exact syntax, code examples, and the precise distinctions the exam tests. The five domains are weighted: Agentic Architecture (27%), Tool Design & MCP (18%), Claude Code Configuration (20%), Prompt Engineering & Structured Output (20%), and Context Management & Reliability (15%).

---

## DOMAIN 1: Agentic Architecture & Orchestration (27%)

This is the highest-weighted domain. It tests your understanding of agentic loops, multi-agent patterns, the Agent SDK's hook system, and session management.

### Task 1.1 — The agentic loop lifecycle and stop reasons

The agentic loop is the core runtime pattern. Claude processes messages, optionally calls tools, and continues until it signals completion. The loop routes on the `stop_reason` field — never on parsed text content.

**All `stop_reason` values** (the `StopReason` type):

| Value | Meaning |
|-------|---------|
| `end_turn` | Claude finished naturally. The most common stop reason. Can occasionally produce empty responses (2–3 tokens). |
| `tool_use` | Claude is requesting tool execution. Response content includes `tool_use` blocks with `id`, `name`, and `input`. |
| `max_tokens` | Response was truncated at the `max_tokens` limit. |
| `stop_sequence` | Claude encountered a custom stop sequence from the `stop_sequences` parameter. |
| `refusal` | Safety classifiers intervened. Claude refused to generate a response. |
| `pause_turn` | Server-side sampling loop hit its iteration limit (default 10). The response can be sent back as-is to let the model continue. |

An additional value, **`model_context_window_exceeded`**, indicates Claude hit the context window limit. Available by default on Sonnet 4.5+; earlier models require the beta header `model-context-window-exceeded-2025-08-26`.

**How tool results get appended to conversation history.** After receiving a `tool_use` response, you append the assistant's full response, then send tool results back as a **user message with `tool_result` content blocks**:

```python
# Append the assistant's response (contains tool_use blocks)
messages.append({"role": "assistant", "content": response.content})

# Return tool results as a user message
messages.append({"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": "toolu_123", "content": "6912"},
    {"type": "tool_result", "tool_use_id": "toolu_456", "content": "..."}
]})
```

Multiple tool results can be combined in a single user message. The SDK can execute read-only tools in parallel and batch all results back together. **Critical anti-pattern**: never add text blocks immediately after tool results — this teaches Claude to expect user input after every tool call, causing empty `end_turn` responses.

**Model-driven vs. pre-configured decision trees.** Model-driven loops let Claude decide when to call tools and when to stop — the loop imposes no fixed number of steps. Pre-configured decision trees are fixed sequential pipelines (prompt chaining) where steps are predetermined. Anthropic's "Building Effective Agents" post calls these "workflows" rather than true agents.

**Three anti-patterns to know:**
- **Parsing natural language for termination** — checking Claude's text content to decide whether to stop, instead of using `stop_reason`
- **Arbitrary iteration caps** — using fixed loop counters rather than trusting `end_turn` or using proper `max_turns` / `max_budget_usd` limits
- **Checking text content for routing decisions** — making routing decisions by parsing natural language output rather than using structured tool calls

The correct pattern routes entirely on `stop_reason`:

```python
if response.stop_reason == "end_turn":
    return [b.text for b in response.content if b.type == "text"]
# stop_reason == "tool_use" → execute tools and loop
```

### Task 1.2 — Multi-agent coordinator-subagent patterns

The **hub-and-spoke** (orchestrator-worker) architecture places a lead agent at the center. It analyzes queries, develops strategy, and spawns specialized subagents that operate in parallel. Subagents act as intelligent filters — iteratively using tools, then returning curated, compressed results to the lead.

**Subagent context isolation** is a critical exam concept. Each subagent runs in its own **fresh conversation** — it does not inherit the coordinator's conversation history. Intermediate tool calls and results stay inside the subagent; only its final message returns to the parent as a tool result. The parent receives a concise summary, not every file the subagent read.

The **coordinator's three responsibilities** are task decomposition (breaking queries into subtasks), delegation (assigning each subtask with objective, output format, tool guidance, and scope boundaries), and result aggregation (synthesizing results and deciding if more research is needed).

**Risks of overly narrow task decomposition.** Without detailed task descriptions, agents duplicate work, leave gaps, or misinterpret tasks. An early failure mode was agents spawning 50 subagents for simple queries. The recommended scaling rules: simple fact-finding = **1 agent with 3–10 tool calls**; direct comparisons = **2–4 subagents with 10–15 calls each**; complex research = **10+ subagents**.

**Iterative refinement loops** allow the lead researcher to synthesize results, determine if more research is needed, and spawn additional subagents or refine strategy. The system dynamically adapts, following leads that emerge during investigation. When context exceeds 200K tokens, a memory tool persists the research plan.

### Task 1.3 — Subagent invocation and context passing

**The Agent tool was renamed from "Task" in version 2.1.63.** Existing `Task(...)` references in settings and agent definitions still work as aliases.

**`allowedTools` must include "Agent"** for the coordinator — without it, subagents never get spawned. Conversely, never include Agent in a subagent's own tools, because subagents cannot spawn their own subagents (prevents infinite nesting).

**AgentDefinition configuration** accepts four key fields:

```typescript
agents: {
  'code-reviewer': {
    description: 'Expert code review specialist. Use for quality, security, and maintainability reviews.',
    prompt: 'You are a code review specialist with expertise in security, performance...',
    tools: ['Read', 'Grep', 'Glob'],   // Scoped tool set
    model: 'sonnet'                      // Can route to different models
  }
}
```

The `description` field is what Claude uses to decide when to delegate. The `prompt` is the subagent's custom system prompt. The `tools` array restricts which tools the subagent can access. The `model` field can route to cheaper/faster models (e.g., Haiku for simple tasks).

**Fork-based session management** enables parallel exploration. `forkSession: true` creates a new session ID when resuming, branching from the original without modifying it:

```typescript
const forkedResponse = query({
  prompt: "Try a GraphQL API approach instead",
  options: { resume: sessionId, forkSession: true }
});
```

The original session remains unchanged and can still be resumed independently.

**Parallel subagent spawning**: Claude can request multiple Agent tool calls in a single response, and the SDK executes them in parallel. This is how the lead agent spins up 3–5 subagents simultaneously, cutting research time by up to **90%** for complex queries.

### Task 1.4 — Programmatic enforcement vs. prompt-based guidance

Hooks provide **deterministic control** over agent behavior. Prompt instructions provide **probabilistic compliance** — they have a non-zero failure rate. For compliance-critical paths (identity verification before financial operations, blocking dangerous commands), always use programmatic enforcement.

The **permission flow order** is: PreToolUse Hook → Deny Rules → Allow Rules → Ask Rules → Permission Mode Check → canUseTool Callback → PostToolUse Hook.

**Structured handoff protocols** require compiling handoff summaries when escalating: customer ID, root cause, refund amount, recommended action. These summaries serve human agents who lack access to the conversation transcript.

### Task 1.5 — Agent SDK hooks in detail

**PreToolUse hooks** fire before a tool executes. They can **block** (`permissionDecision: 'deny'`), **allow** (`'allow'`), **ask** (`'ask'`), or **modify** tool inputs via `updatedInput`. Use cases: blocking dangerous bash commands, redirecting file writes to a sandbox.

**PostToolUse hooks** fire after a tool returns. They can add `additionalContext` to the conversation or modify MCP tool output via `updatedMCPToolOutput`. They **cannot undo actions** — the tool has already executed.

**Hook callback API** — every callback receives three arguments:

1. **`input_data`** (dict): Event details including `hook_event_name`, `session_id`, `transcript_path`, `cwd`, `permission_mode`. PreToolUse adds: `tool_name`, `tool_input`, `tool_use_id`. PostToolUse adds: `tool_response`.
2. **`tool_use_id`** (str | None): Correlates Pre and Post events for the same call.
3. **`context`** (HookContext): TypeScript provides `signal` (AbortSignal) for cancellation; Python reserved for future use.

The **return object** supports: `continue`, `stopReason`, `suppressOutput`, `systemMessage` at the top level. Inside `hookSpecificOutput`: `hookEventName` (required), `permissionDecision` ('allow'|'deny'|'ask'), `permissionDecisionReason`, `updatedInput` (PreToolUse only, requires `permissionDecision: 'allow'`), and `additionalContext` (PostToolUse).

**Hooks run in the application process, consuming zero context window tokens.** This is a key distinction — they operate outside the model's context entirely.

**Deterministic vs. probabilistic**: hooks = deterministic guarantees; prompt instructions = probabilistic compliance. The exam tests this distinction directly.

### Task 1.6 — Task decomposition strategies

**Fixed sequential pipelines** (prompt chaining) follow predefined step sequences — "workflows." **Dynamic adaptive decomposition** lets agents decide what to do next, appropriate for open-ended problems where required steps can't be predicted in advance.

The **per-file analysis + cross-file integration pass** pattern runs subagents in parallel to analyze individual files, then the coordinator performs a cross-file integration pass to synthesize findings. The built-in Explore subagent is optimized for read-only codebase analysis.

**Adaptive investigation plans** use extended thinking as a controllable scratchpad. The lead agent assesses tools, determines query complexity and subagent count, and defines each subagent's role. The strategy is "start wide, then narrow down" — explore the landscape before drilling into specifics. The system continuously updates its approach based on discoveries.

### Task 1.7 — Session state, resumption, and forking

**`--resume` with session names**: Pass `resume=sessionId` (captured from `ResultMessage.session_id`) to restore full context. Every `query()` call without a resume parameter starts a fresh session with no memory. In the CLI: `--resume` flag or `--continue` for the most recent session.

**`fork_session`** creates a new session ID when resuming, branching without modifying the original. Used for parallel exploration branches and checkpointing.

**When to resume vs. start fresh**: Resume when you need full context continuity (follow-up questions, continuing incomplete work). Start fresh with summaries when context has accumulated too much or you want a clean window. Subagents inherently use the "start fresh" pattern.

**`/compact`** summarizes and compresses conversation context. **Automatic compaction** triggers when the context window approaches its limit, emitting a `SystemMessage` with subtype `"compact_boundary"`. The **PreCompact hook** runs before compaction (receives `trigger: 'manual'|'auto'`). After compaction, specific instructions from early conversation may not be preserved — persistent rules belong in CLAUDE.md, not the initial prompt.

---

## DOMAIN 2: Tool Design & MCP Integration (18%)

This domain covers how tools are defined, how errors are handled, how tool counts affect performance, and MCP server configuration.

### Task 2.1 — Tool descriptions drive tool selection

**Tool descriptions are the primary mechanism** for LLM tool selection. Anthropic's guidance: "Provide extremely detailed descriptions. This is by far the most important factor in tool performance." Aim for **at least 3–4 sentences** per tool description, more for complex tools. Descriptions should explain what the tool does, when it should (and shouldn't) be used, what each parameter means, and important limitations.

The API constructs a special system prompt from tool definitions that gets injected before user prompts. Even small refinements to tool descriptions can yield dramatic improvements — Claude Sonnet 3.5 achieved **state-of-the-art SWE-bench performance** after precise description refinements.

**Minimal/ambiguous descriptions** leave Claude with open questions about behavior and usage, leading to incorrect tool selection. Use unambiguous parameter names: `user_id` instead of `user`. Avoid generic names like `query_db_orders` with descriptions like "Execute order query."

**System prompt instructions** can steer tool usage. Example: "Only search the web for queries you cannot confidently answer" prevents over-eager tool calling. These keyword-sensitive instructions can override or supplement tool descriptions.

**Consolidation vs. splitting**: Current official guidance actually recommends **consolidating related operations** into fewer tools with an `action` parameter (e.g., one `github_pr` tool with actions `create`/`review`/`merge`), rather than creating separate tools for each action. Use meaningful namespacing: `github_list_prs`, `slack_send_message`.

### Task 2.2 — Structured error responses and the MCP isError flag

MCP defines two error mechanisms. **Protocol errors** are standard JSON-RPC errors (unknown tools, invalid arguments). **Tool execution errors** use the `isError: true` flag in the result object:

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [{"type": "text", "text": "API rate limit exceeded. Retry after 30 seconds."}],
    "isError": true
  }
}
```

The **critical distinction**: protocol-level errors are captured by the MCP client and discarded. Tool call errors with `isError: true` are **injected back into the LLM context window** — the model can leverage smart error messages to recover. In the SDK, when a tool throws an exception, the tool runner catches it and returns the error as a tool result with `is_error: true`.

**Error categories** in practice: **transient** (rate limits, timeouts — retryable), **validation** (invalid inputs, bad parameters), **business logic** (date in past, constraint violations), **permission** (unauthorized, forbidden). Structured metadata should include `errorCategory`, `isRetryable` boolean, and human-readable descriptions with corrective guidance.

**Access failures vs. valid empty results** is a critical exam distinction. An access failure (`isError: true`) means the query didn't complete — needs retry decisions. A valid empty result (`isError: false`, empty content) means the search worked but found nothing. Conflating them is an anti-pattern.

**Local recovery within subagents**: Subagents should implement local recovery for transient failures, propagating to the coordinator only errors they cannot resolve locally, along with partial results and what was attempted.

### Task 2.3 — Tool count affects selection accuracy

**Too many tools degrades performance.** Prior to Tool Search, agents experienced reliability issues after approximately **20 tools**. The GitHub toolkit alone contains 18 tools; Gmail has 10–13. With too many options, tool selection degrades, parameter hallucination increases, and latency grows. A 5-server setup consumed ~55K tokens before conversation begins.

Anthropic's **Tool Search** tool mitigates this: Opus 4 jumped from **49% → 74%** accuracy; **85% reduction** in token overhead (from ~77K to ~8.7K tokens). When MCP definitions exceed 10K tokens, Claude Code auto-defers loading with `defer_loading: true`.

**Scoped tool access per agent role**: restrict tools based on the agent's purpose. Read-only agents: `["Read", "Glob", "Grep", "LS"]`. Dev agents: `["Read", "Write", "Edit", "Bash(git:*)"]`.

**`tool_choice` parameter options:**

| Option | Behavior | When to use |
|--------|----------|-------------|
| `"auto"` | Claude decides whether to call tools. **Default.** | Most use cases; conversational + tool use |
| `"any"` | Must use one tool, model chooses which. | Guaranteed invocation, tool doesn't matter |
| `{"type": "tool", "name": "..."}` | Forces a specific tool. | Structured JSON extraction, workflow gates |
| `"none"` | No tools allowed. | When tools are defined but shouldn't be used |

When `tool_choice` is `any` or `tool`, the API **prefills the assistant message** — no natural language precedes the `tool_use` block. With extended thinking, only `auto` and `none` are supported. Setting `disable_parallel_tool_use=true` limits to exactly one tool call.

### Task 2.4 — MCP server configuration

**Project-level**: `.mcp.json` in project root — shared via version control. Added with `claude mcp add <name> --scope project`.

**User-level**: `~/.claude.json` — personal config across all projects. Added with `--scope user`.

**Local (default)**: Available only to you in the current project. Added with `--scope local` (or no scope flag).

**Enterprise managed**: `managed-mcp.json` — users cannot add servers through CLI or config files.

Standard configuration format:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..." }
    },
    "remote-server": {
      "url": "https://endpoint.to.connect.to",
      "headers": { "Authorization": "Bearer token" }
    }
  }
}
```

**Environment variable expansion** (`${VAR}` syntax) support varies by client. VS Code and Kiro support it; Claude Desktop uses literal values. In Claude Code, pass via `--env` flags: `claude mcp add github --env GITHUB_TOKEN=value`.

**MCP Resources** provide read-only, application-controlled data. Unlike tools (model-controlled), resources are selected by the application/user. They're identified by URI (`file:///logs/app.log`, `config://app`), support text and binary content, and enable real-time updates via subscriptions.

### Task 2.5 — Built-in tools in Claude Code

**Glob** finds files by name patterns. Returns matching paths sorted by modification time. Use for file discovery: `"**/*.ts"`, `"src/**/*.config.*"`.

**Grep** searches file contents with regex (built on ripgrep). Supports output modes: `content`, `files_with_matches`, `count`. Use for finding code patterns across the codebase.

**Read** reads file contents with line numbers. Supports text files (any size, with pagination), images, PDFs (with page selection), and Jupyter notebooks. **Claude must Read a file before using Edit** to ensure accurate content.

**Write** creates new files or completely overwrites existing ones. Use for new files or full rewrites.

**Edit** performs targeted modifications — surgical changes to specific parts. Fails if the target string isn't found (safety against wrong-file edits). For a one-line fix in a 500-line file, Edit sends ~2 lines vs. Write sending all 500.

**Edit failure fallback**: If Edit fails (target not found), fall back to Read → Write — read the full file, apply modifications, write the entire file back.

The **incremental codebase understanding pattern** is Glob → Grep → Read. Glob discovers file structure, Grep narrows to relevant content, Read provides full context for identified files. Claude Code's system prompt mandates using these built-in tools instead of shell equivalents (`find`, `cat`, `head`).

---

## DOMAIN 3: Claude Code Configuration & Workflows (20%)

This domain covers CLAUDE.md hierarchy, custom commands and skills, path-specific rules, plan mode, iterative refinement, and CI/CD integration.

### Task 3.1 — CLAUDE.md configuration hierarchy

CLAUDE.md files form a layered configuration system, loaded in order of increasing specificity:

1. **Managed policy** (organization-wide, cannot be excluded): macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`; Linux `/etc/claude-code/CLAUDE.md`
2. **User global**: `~/.claude/CLAUDE.md` — personal preferences across all projects
3. **Project root**: `./CLAUDE.md` or `./.claude/CLAUDE.md` — version-controlled, shared with team
4. **Local project**: `./CLAUDE.local.md` — personal project-specific, auto-added to .gitignore
5. **Parent directories**: Claude walks up the tree, loading CLAUDE.md files from each parent. In a monorepo, both `root/CLAUDE.md` and `root/packages/web/CLAUDE.md` load when CWD is `packages/web/`
6. **Subdirectory CLAUDE.md files** load **on demand** when Claude reads files in those directories (not at launch)

**`@import` syntax** expands referenced files inline at load time:

```markdown
See @README.md for project overview and @package.json for available commands.
- Git workflow: @docs/git-workflow.md
- Personal overrides: @~/.claude/my-project-instructions.md
```

Paths resolve relative to the containing CLAUDE.md file. Maximum **5 hops** of recursion.

**`.claude/rules/` directory** provides modular, topic-specific rule files. Rules without `paths` frontmatter load at launch (same priority as `.claude/CLAUDE.md`). Rules with `paths` load on demand when matching files are read. CLAUDE.md survives compaction — it's re-read from disk after `/compact`. Recommended maximum: **200 lines** per file; effective instruction budget is ~100–150 items.

### Task 3.2 — Custom slash commands and skills

**Slash commands** live in `.claude/commands/` (project-scoped, invoked via `/project:name`) or `~/.claude/commands/` (user-scoped). Subdirectories create namespaces: `.claude/commands/frontend/component.md` → `/project:frontend:component`.

Command files use Markdown with YAML frontmatter:

```markdown
---
argument-hint: [issue-number] [priority]
description: Fix a GitHub issue
allowed-tools: Read, Grep, Bash(git diff *)
---
Fix issue #$1 with priority $2. Check the issue description and implement changes.
```

**`$ARGUMENTS`** captures all arguments; **`$1`, `$2`** are positional. `!command` embeds shell output. `@file` references files.

**Skills** (the recommended newer approach) live in `.claude/skills/<name>/SKILL.md` (project) or `~/.claude/skills/<name>/SKILL.md` (user). SKILL.md frontmatter fields:

| Field | Purpose |
|-------|---------|
| `name` | Display name and /slash-command |
| `description` | When to invoke — primary mechanism Claude uses to load skill |
| `argument-hint` | Autocomplete hint, available as `$ARGUMENTS` |
| `context` | `fork` runs in isolated subagent context; `inherit` (default) runs in main conversation |
| `agent` | Subagent type for `context: fork` (e.g., `Explore`, `Plan`, `general-purpose`) |
| `allowed-tools` | Space-separated list: `Read Grep Glob Bash(git *)` |
| `model` | Override: `haiku`, `sonnet`, `opus`, or `inherit` |
| `hooks` | Lifecycle hooks scoped to this skill |

Skill description budget scales at **2% of context window** with a **16,000 character** fallback.

### Task 3.3 — Path-specific rules

The `.claude/rules/` directory supports YAML frontmatter with a `paths` field for glob-based scoping:

```yaml
---
paths:
  - "src/api/**/*.ts"
  - "src/handlers/**/*.ts"
---
# API Design Rules
- All handlers return { data, error } shape
- Use zod for request body validation
```

Glob patterns starting with `{` or `*` must be **quoted** for valid YAML. Path-scoped rules load on demand only when Claude reads files matching the pattern — API guidelines stay out of context when editing React components.

**Comparison**: `.claude/rules/` with paths uses file-pattern-based scoping (concern-based organization — testing.md, security.md). Subdirectory CLAUDE.md uses directory-based scoping (location-based). Rules files avoid merge conflicts since they're separate files; directory CLAUDE.md files risk multiple-editor conflicts.

### Task 3.4 — Plan mode vs. direct execution

**Plan mode** (activate with `Shift+Tab` twice or `/plan`) locks Claude into **read-only operations** — can read files, search, ask questions, but cannot write, edit, or execute commands.

**When to use plan mode**: complex multi-file changes, architectural decisions, unfamiliar codebases, tasks touching **7+ files**. **When to use direct execution**: simple single-file changes, well-understood tasks.

The recommended **4-phase workflow**: Enter plan mode → Research → Create detailed plan → Exit plan mode → Execute.

The **Explore subagent** is a built-in read-only agent (uses Haiku by default) optimized for codebase search and analysis. It isolates verbose discovery output, returning summaries to preserve the main conversation's context. Claude automatically delegates to Explore when in Plan Mode. Tools limited to Read, Grep, Glob.

### Task 3.5 — Iterative refinement patterns

**Input/output examples**: Provide 3–5 diverse, structured examples wrapped in XML tags. Include edge cases. Examples are more effective than step-by-step formatting instructions.

**Test-driven iteration (TDD)** is the strongest pattern for agentic coding: write tests first → confirm they fail → commit failing tests → implement code to pass tests (without modifying tests) → Claude enters autonomous loop (write → test → analyze failures → fix → retest). TDD gives Claude unambiguous feedback, creates an external oracle that stays accurate regardless of context fill, and naturally breaks complex problems into verifiable units.

**Interview pattern**: Claude uses `AskUserQuestion` to surface ambiguities before acting — asking about ambiguous requirements, architectural preferences, and implementation choices.

**Single vs. sequential messages**: Use a **single message** when problems are interconnected (solving one affects others). Use **sequential messages** when problems are independent, giving each focused attention.

### Task 3.6 — CI/CD integration

**`-p` / `--print`** enables headless non-interactive mode:

```bash
claude -p "Review for security vulnerabilities" < app.py > security_report.txt
cat error.log | claude -p "Summarize key errors"
```

**`--output-format json`** returns structured results with `result`, `cost_usd`, `duration_ms`, `num_turns`, `session_id` fields. **`--output-format stream-json`** provides real-time NDJSON processing.

**`--json-schema`** enforces structured output:

```bash
claude -p "Extract function names from auth.py" \
  --output-format json \
  --json-schema '{"type":"object","properties":{"functions":{"type":"array","items":{"type":"string"}}},"required":["functions"]}'
```

**Session context isolation**: Each `-p` call without `--continue` or `--resume` starts a **fresh context**, improving review quality (no bias toward previously written code). Chain reviews with `--resume "$session_id"`. Pass prior findings by continuing the same session to avoid duplicate reports.

Key flags for CI: `--allowedTools` for permission scoping, `--max-turns` for cost control, `--append-system-prompt` for role customization, and `--dangerously-skip-permissions` (only in isolated CI containers).

---

## DOMAIN 4: Prompt Engineering & Structured Output (20%)

This domain tests explicit criteria, few-shot prompting, structured output mechanics, validation loops, batch processing, and multi-pass review.

### Task 4.1 — Why explicit criteria beat vague instructions

Vague instructions like **"be conservative"** fail because they lack concrete decision boundaries. Claude cannot consistently interpret what "conservative" means across contexts. The result: inconsistent flagging that erodes developer trust through false positives.

The fix is **specific categorical criteria** with measurable thresholds. Instead of "be concise," specify "3 sentences, each under 20 words." Instead of "be conservative about flagging," define exact categories: "Flag only if the code contains SQL string concatenation, unsanitized user input in queries, or missing parameterized queries."

Provide **context for constraints** — explain WHY a behavior matters: "Never use ellipses because this will be read by text-to-speech." Structure prompts with explicit sections: Role (1 line), Success criteria (bullets), Constraints (bullets), Uncertainty handling, Output format.

### Task 4.2 — Few-shot prompting reduces ambiguity and hallucination

Include **3–5 diverse, relevant examples** to show Claude exactly what you want. Wrap in `<example>` tags to distinguish from instructions. Examples must be relevant (mirror actual use case), diverse (cover edge cases without creating unintended patterns), and clearly structured.

Examples demonstrate **format AND ambiguous case handling** simultaneously. For email classification, an example showing "Can I use my Mixmaster 4000 to mix paint?" classified as "Pre-sale question" (not "Other") resolves a judgment call that instructions alone can't capture.

**Generalization**: Claude 4.x models pay very close attention to example details. Few-shot examples work with extended thinking — use `<thinking>` tags inside examples to show reasoning patterns that Claude generalizes to its own thinking blocks. Few-shot combined with XML tags and structured output reduced hallucination in extraction tasks by **20%** in Anthropic case studies. Start with one example; add more only if output doesn't match.

### Task 4.3 — Structured output guarantees syntax, not semantics

Two complementary features: **JSON outputs** (`output_config.format`) for structured responses, and **strict tool use** (`strict: true`) for guaranteed schema validation. Both use **constrained decoding** — compiling JSON schemas into grammars that restrict token generation during inference.

The **key exam distinction**: structured outputs guarantee **syntactic compliance** (valid JSON, correct types, required fields) but **NOT semantic correctness**. Anthropic explicitly states: "You might get perfectly formatted incorrect answers."

**Schema design best practices**: Mark parameters `required` where possible — each optional parameter roughly doubles grammar state space. Set `additionalProperties: false` on all objects. Use enums with an "other" option paired with a detail field. For nullable fields: `"type": ["string", "null"]`. Limits: max **20 strict tools** per request, max **24 optional parameters** across all strict schemas, max **16 union-type parameters**.

```json
{
  "tools": [{
    "name": "extract_entity",
    "strict": true,
    "input_schema": {
      "type": "object",
      "properties": {
        "category": {"type": "string", "enum": ["person", "org", "location", "other"]},
        "category_detail": {"type": ["string", "null"]},
        "confidence": {"type": "number"}
      },
      "required": ["category", "confidence"],
      "additionalProperties": false
    }
  }],
  "tool_choice": {"type": "any"}
}
```

Combine `tool_choice: {"type": "any"}` with `strict: true` to guarantee both that a tool will be called AND that inputs follow the schema.

### Task 4.4 — Retry loops work for format errors, not missing information

The **retry-with-error-feedback pattern** sends validation errors back to the model: Generate draft → Review against criteria → Refine based on feedback. Each step is a separate API call for logging and branching.

**Limits of retry**: Retries work for format errors (malformed JSON, missing fields, wrong types) — structured outputs now eliminate these entirely. Retries **do NOT work** when information is absent from context. No amount of retrying will hallucinate accurate data that isn't in the source document.

**`detected_pattern` fields** in extraction schemas capture what pattern the model recognized, enabling downstream analysis and systematic error identification.

**Self-correction**: Include both `calculated_total` and `stated_total` fields. The model can flag when a document states one number but the math produces another — internal consistency checking. **Caveat**: when Claude reviews its own work in-context, it may change correct answers to incorrect ones (sycophancy bias). Mitigation: give Claude an explicit out — "If all values are correct, return the original values unchanged."

### Task 4.5 — Message Batches API details

The Batch API offers **50% cost savings** on both input and output tokens, with a **24-hour processing window** (most batches finish in under 1 hour). Up to **100,000 requests** per batch or 256 MB. Results available for 29 days.

Each request requires a unique **`custom_id`** for tracking — results may not match input order. Always use `custom_id` to match results with requests.

**No multi-turn tool calling in batch mode.** Tool use is supported but only single-turn. The batch API cannot execute the tool call loop (send `tool_use` → execute → return `tool_result` → get final response). Each request is standalone.

**Appropriate workloads**: large-scale evaluations, content moderation, bulk classification, data extraction. **Inappropriate**: multi-step reasoning requiring tool loops, interactive applications, complex agentic workflows.

**Failure handling** — four result types per request: `succeeded`, `errored` (not billed — check `error_type`), `canceled` (not billed), `expired` (not billed). Failure of one request does not affect others. Validation is asynchronous — test request shapes with the Messages API first. Prompt caching discounts **stack** with batch discounts.

### Task 4.6 — Self-review fails; independent instances succeed

**Self-review limitations**: When Claude reviews its own work in the same conversation, it retains the reasoning context that produced the original output, creating **confirmation bias**. Claude sometimes changes correct answers just because it was asked to review (sycophancy).

**Independent review instances** use separate API calls with no shared conversation history. The reviewer has no access to the original reasoning chain. **Best-of-N verification** runs the same prompt multiple times — inconsistencies across outputs indicate unreliable results.

The **per-file local + cross-file integration** pattern runs parallel agents examining different files/perspectives independently (Phase 1: local analysis), then a final agent aggregates, deduplicates, and ranks findings (Phase 2: cross-file integration). Anthropic's Code Review product uses this exact architecture.

Structure multi-pass pipelines as: **Generate → Review → Refine → Re-review**, with each step as a separate API call. For independent subtasks, run parallel prompts. Only chain sequentially when outputs depend on previous steps.

---

## DOMAIN 5: Context Management & Reliability (15%)

This domain covers context preservation, escalation design, error propagation, large codebase strategies, human review calibration, and information provenance.

### Task 5.1 — Context preservation techniques

**Progressive summarization risks**: Condensing numerical values, percentages, dates, and customer-stated expectations into vague summaries loses critical transactional facts. Overly aggressive compaction discards subtle but critical context whose importance only becomes apparent later.

**"Lost in the middle" effect**: Models follow a **U-shaped attention pattern** — they process information at the beginning and end of context reliably but may miss findings from middle sections. Mitigation: place key findings summaries at the **beginning** of aggregated inputs and use explicit section headers.

**Tool result accumulation**: Tool results consume tokens disproportionately to their relevance (e.g., 40+ fields per order lookup when only 5 matter). Trim verbose outputs to relevant fields before they accumulate. The safest form of compaction is **tool result clearing**.

**Persistent "case facts" blocks**: Extract transactional facts (amounts, dates, order numbers, statuses) into a structured block included in each prompt **outside** summarized history. For multi-issue sessions, maintain a separate context layer of structured issue data. Modify upstream agents to return structured data (key facts, citations, relevance scores) instead of verbose content.

### Task 5.2 — Escalation triggers must be explicit, not sentiment-based

**Three primary escalation triggers**: (1) customer explicitly requests a human — honor immediately, (2) policy exceptions or gaps — when policy is ambiguous or silent on the specific request, (3) inability to make meaningful progress after retries.

**Sentiment-based escalation is unreliable** because sentiment doesn't correlate with case complexity. A customer may be calm about a complex policy exception or frustrated about a simple issue.

**Self-reported confidence scores are unreliable** because LLM self-reported confidence is poorly calibrated — the agent that's making bad escalation decisions will also produce poorly calibrated confidence scores. The correct approach: **explicit escalation criteria with few-shot examples** demonstrating when to escalate vs. resolve autonomously.

**Multiple customer matches**: When results return multiple matches, ask for **additional identifiers** rather than selecting based on heuristics. This prevents misidentified accounts.

### Task 5.3 — Error propagation requires structured context

The correct pattern: return **structured error context** to the coordinator including failure type, attempted query, partial results, and potential alternative approaches. This enables intelligent recovery — whether to retry, try alternatives, or proceed with partial results.

**Access failures vs. valid empty results**: An access failure (timeout) means the query didn't complete. A valid empty result means the search succeeded but found nothing. These must be distinguished in error reporting. Returning empty results as success when there was a timeout is an anti-pattern.

**Three anti-patterns** the exam tests directly:
- **Silently suppressing errors** (returning empty results as success) — prevents recovery, risks incomplete outputs
- **Terminating entire workflow on single failure** — unnecessarily destructive when recovery strategies could succeed
- **Generic error statuses** ("search unavailable") — hides valuable context from the coordinator

### Task 5.4 — Large codebase exploration strategies

**Context degradation symptoms**: Models start giving inconsistent answers and referencing "typical patterns" rather than specific classes discovered earlier. Running out of context mid-implementation leaves the next session guessing at what happened.

**Scratchpad files** (e.g., `SCRATCHPAD.md`, `claude-progress.txt`) persist key findings across context boundaries. Agents record findings in scratchpad files and reference them for subsequent questions. These files survive context resets and compaction.

**Subagent delegation**: Spawn subagents (particularly the Explore subagent) for verbose discovery tasks. Each subagent gets a dedicated context window; the main agent receives summarized findings without exploration bloat. Summarize findings from one phase before spawning subagents for the next.

**Crash recovery via structured state manifests**: Each agent exports state to a known location. The coordinator loads a manifest on resume and injects state into agent prompts. Subagents write to the filesystem to minimize "game of telephone" effects, passing lightweight references back.

**`/compact`** summarizes older messages to free context space. Preserves architectural decisions, unresolved bugs, and implementation details while discarding redundant tool outputs. Auto-compact triggers when context approaches the limit.

### Task 5.5 — Aggregate accuracy masks document-type issues

A **97% overall accuracy** rate could mean 99.5% on invoices but 85% on handwritten forms. The exam tests understanding that aggregate metrics mask poor performance on specific document types or fields.

**Stratified random sampling** of high-confidence extractions measures ongoing error rates and detects novel patterns — specifically for extractions the model was confident about.

**Field-level confidence scores** (per extraction field, not per document) calibrated against labeled validation sets enable routing low-confidence extractions to human review, prioritizing limited reviewer capacity. Validate accuracy **by document type and field** before reducing human review coverage.

### Task 5.6 — Source attribution gets lost in summarization

When findings are compressed without preserving **claim-source mappings**, source attribution is lost. Require subagents to output structured claim-source mappings including source URLs, document names, relevant excerpts, and publication dates. Downstream agents must preserve these through synthesis.

**Conflicting statistics** from credible sources should be **annotated with source attribution**, not averaged or arbitrarily selected. Present both values with their sources and let the synthesis layer reconcile.

**Temporal data** must include publication or collection dates. A statistic from 2020 vs. 2024 isn't a contradiction — it's temporal change. Without dates, temporal differences get misinterpreted as conflicting information.

Structure synthesis output to distinguish well-established findings from contested ones, preserving original source characterizations and methodological context. Render appropriately by content type: financial data as tables, news as prose, technical findings as structured lists.

---

## Conclusion: What the exam actually tests

This certification does not test rote memorization of API parameters. It tests **applied architectural judgment** — knowing when to use hooks vs. prompts for enforcement, why `isError: true` goes in the result object (not the protocol error), why self-review fails due to retained reasoning context, and why "be conservative" is an anti-pattern replaced by explicit categorical criteria. The six highest-leverage concepts across all domains are: route on `stop_reason` never on parsed text, subagents get fresh context windows with no inherited history, hooks are deterministic while prompts are probabilistic, structured output guarantees syntax but not semantics, access failures and empty results must be distinguished, and aggregate accuracy masks document-type-specific problems. Master these distinctions and the specific code patterns documented above, and the exam's scenario-based questions become straightforward applications of these principles.