---
layout: default
title: "Gap-Fill Study Reference"
---

# Claude Certified Architect — Complete Gap-Fill Study Reference

**This reference covers all 28 knowledge gaps across the five exam domains**, providing exact code definitions, JSON structures, API flows, and configuration syntax sourced from official Anthropic documentation, the Agent SDK repos, and the MCP specification. Every section is organized by domain and gap number for fast lookup during study.

---

## Domain 1 — Agentic architecture (27% of exam)

### Gap 1: AgentDefinition — exact type definitions in both SDKs

The `AgentDefinition` describes a named subagent that can be spawned by the orchestrator via the `Task` or `Agent` tool. The TypeScript SDK exposes more fields than Python.

**TypeScript:**
```typescript
type AgentDefinition = {
  description: string;                          // When to use this agent (required)
  prompt: string;                               // Agent's system prompt (required)
  tools?: string[];                             // Allowed tool names; omit to inherit all
  disallowedTools?: string[];                   // Tools to block
  model?: "sonnet" | "opus" | "haiku" | "inherit"; // Default: inherit
  mcpServers?: AgentMcpServerSpec[];            // MCP servers for this agent
  skills?: string[];                            // Skills to preload
  maxTurns?: number;                            // Tool-use turn limit
  criticalSystemReminder_EXPERIMENTAL?: string; // Experimental reminder
};
```

**Python:**
```python
@dataclass
class AgentDefinition:
    description: str          # Required
    prompt: str               # Required
    tools: list[str] | None = None     # Default: None (inherit all)
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
```

The Python dataclass currently has **four fields**; the TypeScript version adds `disallowedTools`, `mcpServers`, `skills`, `maxTurns`, and an experimental field. Agents are passed to `query()` through the `agents` dict inside the options object. Here is the canonical pattern in both languages:

**TypeScript — passing agents:**
```typescript
for await (const message of query({
  prompt: "Review this codebase",
  options: {
    allowedTools: ["Read", "Glob", "Grep", "Task"],
    agents: {
      "code-reviewer": {
        description: "Expert code reviewer",
        prompt: "Analyze code quality and suggest improvements.",
        tools: ["Read", "Glob", "Grep"],
        model: "sonnet"
      }
    }
  }
})) { /* handle messages */ }
```

**Python — passing agents:**
```python
async for message in query(
    prompt="Use the code-reviewer agent to review this codebase",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep", "Agent"],
        agents={
            "code-reviewer": AgentDefinition(
                description="Expert code reviewer",
                prompt="Analyze code quality and suggest improvements.",
                tools=["Read", "Glob", "Grep"]
            )
        }
    )
): ...
```

The `Task` (or `Agent`) tool name must appear in `allowedTools` for the orchestrator to spawn subagents. The `description` field is what Claude reads to decide which agent to invoke.

---

### Gap 2: allowedTools vs disallowedTools — the permission pipeline

These two parameters serve fundamentally different purposes. **`allowedTools` is a permission allowlist** — it auto-approves the listed tools so no human confirmation is required, but **does not remove unlisted tools** from Claude's toolbox. **`disallowedTools` is a hard block** — it removes tools from the model entirely, and overrides even `bypassPermissions` mode.

The SDK evaluates permissions in this exact order:

1. **Deny rules** (`disallowedTools` + `settings.json` deny list) — checked first; if matched, tool is **blocked unconditionally**
2. **Permission mode** — `bypassPermissions` approves everything not denied; `acceptEdits` approves file ops; others fall through
3. **Allow rules** (`allowedTools` + `settings.json` allow list) — if matched, tool is **auto-approved**
4. **Hooks** — custom code can allow, deny, or modify tool requests
5. **`canUseTool` callback** — prompts the user at runtime

**Critical interaction rules:**
- Setting `allowed_tools=["Read"]` alongside `permission_mode="bypassPermissions"` still approves **every** tool — `allowedTools` does not constrain bypass mode
- `disallowedTools` **can** block tools even in `bypassPermissions`
- For a locked-down agent in TypeScript, pair `allowedTools` with `permissionMode: "dontAsk"` — listed tools are approved, everything else is denied outright without prompting

**Syntax across surfaces:**

| Surface | Allow syntax | Deny syntax |
|---------|-------------|-------------|
| Python SDK | `allowed_tools=["Read","Grep"]` | `disallowed_tools=["Bash(rm*)","Write"]` |
| TypeScript SDK | `allowedTools: ["Read","Grep"]` | `disallowedTools: ["Bash(rm*)","Write"]` |
| CLI flags | `--allowedTools "Read,Grep"` | `--disallowedTools "Write,Edit"` |
| AgentDefinition (TS) | `tools: ["Read","Grep"]` | `disallowedTools: ["Write"]` |

---

### Gap 3: MCP tool format strings in allowedTools

MCP tools follow a **triple-underscore namespace convention**: `"mcp__<server-name>__<tool-name>"`. The server name maps directly to the key in your `mcpServers` configuration dictionary. A wildcard allows all tools from a server: `"mcp__<server-name>__*"`.

```typescript
options: {
  mcpServers: {
    "github": { /* config */ },
    "db": { /* config */ }
  },
  allowedTools: [
    "mcp__github__*",              // All tools from the github server
    "mcp__db__query",              // Only the query tool from db server
    "mcp__slack__send_message"     // Specific tool from slack server
  ]
}
```

```python
options = ClaudeAgentOptions(
    mcp_servers={"calc": calculator_server},
    allowed_tools=["mcp__calc__add", "mcp__calc__multiply"],
)
```

On the CLI: `--allowedTools "mcp__gitlab"` allows all tools from the `gitlab` server. MCP prompts are referenced as `/mcp__servername__promptname`.

---

### Gap 4: ResultMessage / SDKResultMessage — complete type definitions

The result message is a **discriminated union** keyed on `subtype`. The success variant carries `result` (text) and optional `structured_output`; error variants carry an `errors` array instead.

**TypeScript (`SDKResultMessage`):**
```typescript
type SDKResultMessage =
  | {
      type: "result";
      subtype: "success";
      uuid: UUID;
      session_id: string;
      duration_ms: number;
      duration_api_ms: number;
      is_error: boolean;
      num_turns: number;
      result: string;                         // Final text output
      stop_reason: string | null;             // "end_turn", "max_tokens", "refusal"
      total_cost_usd: number;
      usage: NonNullableUsage;                // { input_tokens, output_tokens, ... }
      modelUsage: { [model: string]: ModelUsage };
      permission_denials: SDKPermissionDenial[];
      structured_output?: unknown;
    }
  | {
      type: "result";
      subtype: "error_max_turns" | "error_during_execution"
             | "error_max_budget_usd" | "error_max_structured_output_retries";
      uuid: UUID;
      session_id: string;
      duration_ms: number;
      duration_api_ms: number;
      is_error: boolean;
      num_turns: number;
      stop_reason: string | null;
      total_cost_usd: number;
      usage: NonNullableUsage;
      modelUsage: { [model: string]: ModelUsage };
      permission_denials: SDKPermissionDenial[];
      errors: string[];                       // Error descriptions
    };
```

**Python (`ResultMessage`):**
```python
@dataclass
class ResultMessage:
    subtype: str                                 # "success" or "error_*"
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None          # {input_tokens, output_tokens, ...}
    result: str | None = None                     # Only on success
    stop_reason: str | None = None
    structured_output: Any = None
```

**Five subtype values:** `"success"`, `"error_max_turns"`, `"error_max_budget_usd"`, `"error_during_execution"`, `"error_max_structured_output_retries"`. All error subtypes still carry `total_cost_usd`, `usage`, `num_turns`, and `session_id` for post-mortem analysis and session resumption.

---

### Gap 5: fork_session — exact syntax in both SDKs

Forking creates a **new session** starting with a copy of the original's history, then diverging. The original session is untouched and can be resumed independently.

**Python — `fork_session=True`:**
```python
# Step 1: Run initial query, capture session_id
session_id = None
async for message in query(
    prompt="Analyze the auth module",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Grep"]),
):
    if isinstance(message, ResultMessage):
        session_id = message.session_id

# Step 2: Fork (resume + fork_session together)
async for message in query(
    prompt="Try OAuth2 instead of JWT",
    options=ClaudeAgentOptions(
        resume=session_id,          # Point to original session
        fork_session=True,          # Branch into new session
    ),
):
    if isinstance(message, ResultMessage):
        forked_id = message.session_id   # New ID, different from session_id

# Step 3: Original session continues independently
async for message in query(
    prompt="Continue JWT approach",
    options=ClaudeAgentOptions(resume=session_id),
): ...
```

**TypeScript — `forkSession: true`:**
```typescript
for await (const message of query({
  prompt: "Try OAuth2 instead",
  options: {
    resume: sessionId,        // Original session
    forkSession: true,        // Fork into new session
  }
})) {
  if (message.type === "result") {
    console.log(`Forked: ${message.session_id}`);  // New session ID
  }
}
```

**Key behavior:** Forking branches the **conversation history**, not the filesystem. If a forked agent edits files, those changes are real and visible to any session in the same directory.

| SDK | Resume param | Fork param |
|-----|-------------|------------|
| Python | `resume=session_id` | `fork_session=True` |
| TypeScript | `resume: sessionId` | `forkSession: true` |

---

### Gap 6: max_turns and max_budget_usd

**`max_turns` counts only tool-use turns, not text-only turns.** The official docs define a "turn" as one round trip: Claude produces output containing tool calls → SDK executes tools → results feed back. The final text-only response is not counted.

| SDK | Turn limit | Budget limit |
|-----|-----------|-------------|
| Python | `max_turns: int \| None = None` | `max_budget_usd: float \| None = None` |
| TypeScript | `maxTurns?: number` | `maxBudgetUsd?: number` |

When limits are hit, the SDK returns a `ResultMessage` with the corresponding error subtype (`"error_max_turns"` or `"error_max_budget_usd"`), **not** an exception. The message still contains `total_cost_usd`, `num_turns`, and `session_id` for diagnostics.

```python
if isinstance(message, ResultMessage):
    if message.subtype == "error_max_turns":
        print(f"Hit turn limit after {message.num_turns} turns")
    elif message.subtype == "error_max_budget_usd":
        print(f"Hit budget at ${message.total_cost_usd}")
```

---

### Gap 7: The Explore subagent

Claude Code ships three built-in subagent types:

| Subagent | Model | Tools | Purpose |
|----------|-------|-------|---------|
| **Explore** | **Haiku** (fast, cheap) | Glob, Grep, Read, safe Bash (ls, git status/log/diff, find, cat, head, tail) | Codebase exploration — strictly read-only |
| **Plan** | **Sonnet** (or Opus with `opusplan`) | Read, Glob, Grep, Bash | Research for planning mode |
| **general-purpose** | **Sonnet** (inherits) | All tools (full read/write) | Complex multi-step tasks |

The Explore subagent's system prompt includes `"=== CRITICAL: READ-ONLY MODE — NO FILE MODIFICATIONS ==="`. It supports **three thoroughness levels**: `quick` (targeted lookups), `medium` (balanced), `very thorough` (comprehensive). In **plan mode**, Claude delegates research to the **Plan** subagent, not Explore. Explore keeps exploration results **out of the main conversation context** via context isolation, saving tokens in the parent session.

---

### Gap 8: The /compact command and auto-compaction

**Auto-compaction triggers** when the context window approaches approximately **95% capacity**. Claude Code then summarizes the conversation history automatically.

**What is preserved:** Current task state, key decisions, important code snippets, next steps, and learnings. **What may be lost:** Detailed early instructions, verbose tool outputs (cleared first), and granular conversation details. Persistent instructions should live in `CLAUDE.md`.

**Manual compaction** accepts optional focus instructions:
```
/compact                                      # Basic compact
/compact Focus on code samples and API usage  # Custom preservation
```

**The `compact_boundary` message** marks where compaction occurred in the SDK event stream:
```typescript
type SDKCompactBoundaryMessage = {
  type: "system";
  subtype: "compact_boundary";
  uuid: UUID;
  session_id: string;
  compact_metadata: {
    trigger: "manual" | "auto";     // How compaction was triggered
    pre_tokens: number;              // Token count before compaction
  };
};
```

A **`PreCompact` hook** fires before compaction, allowing custom code to run. After compaction, a `SessionStart` event fires with `source: "compact"`.

---

## Domain 2 — Tool design and MCP (18% of exam)

### Gap 9: MCP error handling — two distinct error types

**Protocol-level errors** use the standard JSON-RPC 2.0 `error` field and are **NOT visible to the LLM**:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "error": {
    "code": -32602,
    "message": "Unknown tool: invalid_tool_name"
  }
}
```

Standard error codes: `-32700` (parse), `-32600` (invalid request), `-32601` (method not found), `-32602` (invalid params), `-32603` (internal error), `-32002` (resource not found, MCP-specific).

**Tool execution errors** are returned as a successful JSON-RPC response with `isError: true` in the `CallToolResult`. These **ARE visible to the LLM** so it can self-correct:
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [
      { "type": "text", "text": "API rate limit exceeded" }
    ],
    "isError": true
  }
}
```

The spec states: *"Any errors that originate from the tool SHOULD be reported inside the result object with isError set to true, NOT as an MCP protocol-level error response."*

---

### Gap 10: MCP tool definition schema and CallToolResult

**Complete Tool interface (spec version 2025-06-18):**
```typescript
interface Tool {
  name: string;
  title?: string;                    // Human-readable display name
  description?: string;
  inputSchema: {
    type: "object";
    properties?: { [key: string]: object };
    required?: string[];
  };
  outputSchema?: {                   // New in draft spec
    type: "object";
    properties?: { [key: string]: object };
    required?: string[];
  };
  annotations?: ToolAnnotations;
  _meta?: { [key: string]: unknown };
}

interface ToolAnnotations {
  title?: string;
  readOnlyHint?: boolean;            // Tool does not modify environment
  destructiveHint?: boolean;         // May perform destructive updates
  idempotentHint?: boolean;          // Repeated calls have no additional effect
  openWorldHint?: boolean;           // Interacts with external entities
}
```

**CallToolResult type:**
```typescript
interface CallToolResult {
  content: ContentBlock[];           // TextContent | ImageContent | AudioContent
                                     // | ResourceLink | EmbeddedResource
  structuredContent?: any;           // JSON object (when outputSchema is used)
  isError?: boolean;                 // Default: false
  _meta?: { [key: string]: unknown };
}
```

Content types include `{ type: "text", text: "..." }`, `{ type: "image", data: "base64...", mimeType: "image/png" }`, `{ type: "audio", data: "base64...", mimeType: "audio/wav" }`, and `{ type: "resource_link", uri: "...", name: "..." }`.

When `outputSchema` is provided, the server returns both `content` (text representation) and `structuredContent` (parsed JSON matching the schema). Annotations are **hints only** — clients must not trust them from untrusted servers.

---

### Gap 11: MCP Resources

Resources are **application-driven** (unlike tools which are model-driven). They provide direct data access without tool calls, reducing exploratory roundtrips.

**Key operations:**
- `resources/list` — enumerate available resources (supports pagination with `cursor` / `nextCursor`)
- `resources/read` — fetch content by URI, returns `contents` array with `uri`, `mimeType`, and `text` or `blob`
- `resources/templates/list` — discover URI templates (RFC 6570) like `file:///{path}`
- `resources/subscribe` / `resources/unsubscribe` — register for change notifications
- `notifications/resources/updated` — server-to-client push when a subscribed resource changes
- `notifications/resources/list_changed` — server-to-client push when the available resource list changes

**Common URI schemes:** `https://` (web), `file:///path/to/file` (filesystem-like), `git://` (version control), and custom schemes like `calendar://events/2024` or `weather://forecast/{city}/{date}`.

**Resource interface:**
```typescript
interface Resource {
  uri: string;
  name: string;
  title?: string;
  description?: string;
  mimeType?: string;
  size?: number;              // Bytes
  annotations?: {
    audience?: ("user" | "assistant")[];
    priority?: number;        // 0.0 to 1.0
    lastModified?: string;    // ISO 8601
  };
}
```

Resources reduce exploratory tool calls because a `db://schema` resource eliminates the need for a `describe_tables` tool call. URI templates with parameters (e.g., `weather://forecast/{city}/{date}`) enable parameterized access without custom tool definitions.

---

### Gap 12: Environment variable expansion in .mcp.json

**Syntax:** `${VAR}` expands to the variable's value. `${VAR:-default}` uses the default when the variable is unset. **If a variable is unset and has no default, Claude Code errors out** — it does not silently use an empty string.

**Supported fields:** `command`, `args`, `env`, `url`, `headers`.

```json
{
  "mcpServers": {
    "api-server": {
      "type": "http",
      "url": "${API_BASE_URL:-https://api.example.com}/mcp",
      "headers": {
        "Authorization": "Bearer ${API_KEY}"
      }
    },
    "db-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@some/mcp-server"],
      "env": {
        "SECRET_KEY": "${SECRET_KEY}",
        "DB_URL": "${DATABASE_URL:-postgresql://localhost:5432/mydb}"
      }
    }
  }
}
```

---

### Gap 13: Tool Search and deferred tool loading

Tool Search lets Claude work with **hundreds or thousands** of tools by loading definitions on demand. In the API, mark tools with `"defer_loading": true`. Claude sees a lightweight `tool_search_tool` instead of full definitions, then searches when needed.

**Claude Code auto-enables Tool Search** when MCP tool descriptions exceed **~10% of the context window**. You can control this with `ENABLE_TOOL_SEARCH=true|false|auto:5` (custom threshold percentage).

**Two search tool variants:**
- `tool_search_tool_regex` — Claude constructs regex patterns (max 200 chars)
- `tool_search_tool_bm25` — Claude uses natural language queries

**API-level configuration:**
```json
{
  "name": "get_weather",
  "description": "Get current weather for a location",
  "input_schema": { "type": "object", "properties": { "location": {"type": "string"} } },
  "defer_loading": true
}
```

**MCP integration** uses `mcp_toolset` with per-tool overrides:
```json
{
  "type": "mcp_toolset",
  "mcp_server_name": "database-server",
  "default_config": { "defer_loading": true },
  "configs": { "search_events": { "defer_loading": false } }
}
```

**Key limits:** Maximum **10,000 tools** in catalog, **3–5 results** per search, regex max **200 chars**, supported on **Sonnet 4.0+ and Opus 4.0+ only** (no Haiku). Tool Search delivers up to **85% reduction** in tool token usage and improved tool selection accuracy (Opus 4.5: 79.5% → 88.1%).

---

### Gap 14: All built-in tools in Claude Code

| Tool | Parameters | Purpose | Selection criteria |
|------|-----------|---------|-------------------|
| **Read** | `file_path`, `offset?`, `limit?` | Read files (text, images, PDFs, notebooks). Returns cat -n format, 2000 line default | Start of task; user references a file; before Edit/Write |
| **Write** | `file_path`, `content` | Create new files or overwrite entirely | New files only. Existing files should use Edit |
| **Edit** | `file_path`, `old_string`, `new_string`, `replace_all?` | Surgical find-and-replace in files | Modifying existing files (preferred over Write) |
| **MultiEdit** | `file_path`, `edits[]` (each: `old_string`, `new_string`, `replace_all?`) | Atomic multi-edit on a single file | Multiple changes to same file |
| **Bash** | `command`, `description?`, `timeout?` (default 120s, max 600s), `run_in_background?` | Execute shell commands | Terminal ops only — NOT for reading/editing/searching |
| **Grep** | `pattern`, `path?`, `include?`, `type?`, `output_mode?`, context flags | Content search via ripgrep | Finding text patterns across codebase |
| **Glob** | `pattern`, `path?` | File name pattern matching | Finding files by name, sorted by modification time |
| **LS** | `path`, `ignore?` | Directory listing | When you need a directory listing |
| **Task** | `description`, `prompt` | Spawn subagent (Explore/Plan/general-purpose) | Complex multi-step or open-ended research |
| **WebSearch** | `query`, `allowed_domains?`, `blocked_domains?` | Web search for current information | Up-to-date info beyond knowledge cutoff |
| **WebFetch** | `url`, `prompt` | Fetch and analyze URL content (15-min cache) | Retrieving web content; auto-upgrades HTTP→HTTPS |
| **TodoWrite** | `todos[]` (each: `content`, `activeForm`, `status`, `priority?`, `id?`) | Task tracking | Complex multi-step tasks (3+ steps) |
| **TodoRead** | *(none)* | Read current session todo list | Check progress |
| **NotebookRead** | `notebook_path` | Read Jupyter notebooks | Reviewing .ipynb files |
| **NotebookEdit** | `notebook_path`, `cell_number`, `new_source`, `cell_type?`, `edit_mode?` | Edit notebook cells | Modifying Jupyter notebooks |
| **BashOutput** | `bash_id`, `filter?` | Get output from background shells | Monitoring background processes |
| **KillShell** | `shell_id` | Terminate background shell | Cleaning up background processes |

---

## Domain 3 — Claude Code configuration (20% of exam)

### Gap 15: .claude/rules/ YAML frontmatter

Rule files are `.md` files in `.claude/rules/` (project level) or `~/.claude/rules/` (user level), discovered recursively. Only two frontmatter fields are supported:

```yaml
---
paths:
  - "src/api/**/*.ts"
  - "**/*.{ts,tsx}"
description: "API development rules"
---
# Rule content here in Markdown
```

**`paths`** (array of glob patterns): Scopes the rule to files matching these patterns. Omit for global rules loaded unconditionally. **`description`** (string): Optional description.

**Glob syntax:** `*` matches any characters except `/`, `**` matches recursively through directories, `?` matches a single character, `[abc]` matches character classes, `{a,b}` expands to alternatives.

**YAML quoting is mandatory** for patterns starting with `*` or `{`:
```yaml
# ✅ Correct — quoted
paths:
  - "**/*.ts"
  - "{src,lib}/**/*.ts"

# ❌ Incorrect — unquoted (invalid YAML)
paths:
  - **/*.ts
```

**Loading strategy:** Global rules (no `paths`) are injected at startup. Path-scoped rules are indexed at startup but only activated when Claude accesses a matching file.

---

### Gap 16: SKILL.md frontmatter — all fields

Skills live in `.claude/skills/<name>/SKILL.md` (project) or `~/.claude/skills/<name>/SKILL.md` (personal).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | Directory name | Lowercase letters, numbers, hyphens (max 64 chars) |
| `description` | string | First paragraph | What the skill does; Claude uses this to decide auto-invocation |
| `argument-hint` | string | — | Autocomplete hint shown in command picker |
| `allowed-tools` | string or YAML list | Standard permissions | Tools auto-approved when skill is active |
| `disable-model-invocation` | boolean | `false` | If true, only user can invoke via /name |
| `user-invocable` | boolean | `true` | If false, hidden from / menu; only Claude can invoke |
| `context` | `"inherit"` or `"fork"` | `"inherit"` | `inherit` = runs in main context; `fork` = isolated subagent |
| `agent` | string | `"general-purpose"` | Subagent type when `context: fork` — `Explore`, `Plan`, `general-purpose`, or custom |
| `model` | string | `"inherit"` | `haiku`, `sonnet`, `opus`, `inherit`, or full model ID |
| `hooks` | object | — | Lifecycle hooks (`PreToolUse`, `PostToolUse`) scoped to this skill |
| `version` | string | — | Metadata for version tracking |
| `mode` | boolean | — | If true, categorized as a "mode command" in menus |

**Invocation control matrix:**

| `disable-model-invocation` | `user-invocable` | User invoke? | Claude auto-invoke? |
|---|---|---|---|
| false | true | ✅ | ✅ |
| true | true | ✅ | ❌ |
| false | false | ❌ | ✅ |
| true | false | ❌ | ❌ |

**Complete example with all fields:**
```yaml
---
name: code-review
description: Reviews code for quality and best practices
argument-hint: [file-path]
allowed-tools: Read, Grep, Glob, Bash(git diff:*)
disable-model-invocation: false
user-invocable: true
context: inherit
model: sonnet
version: 1.0.0
hooks:
  PreToolUse:
    - matcher: "Bash"
      once: true
      hooks:
        - type: command
          command: "./scripts/validate.sh"
---
# Code Review Skill
Review $ARGUMENTS for quality, security, and best practices.
```

**Dynamic content variables:** `$ARGUMENTS` (full argument string), `$1`, `$2` (positional arguments), `!`command`` (shell output injected before loading), `@file` (file contents included inline).

---

### Gap 17: Slash command frontmatter and syntax

Custom commands in `.claude/commands/` are now unified with skills — both create `/name` invocations with identical frontmatter. Project commands at `.claude/commands/deploy.md` become `/project:deploy`. Personal commands at `~/.claude/commands/deploy.md` become `/user:deploy`. Subdirectories create namespaced commands.

**Frontmatter fields** are the same as SKILL.md: `allowed-tools`, `description`, `argument-hint`, `model`, `context`, `agent`, `hooks`.

**Dynamic context features:**

`$ARGUMENTS` captures the full argument string after the command name. `$1`, `$2` extract positional arguments. These are text-substituted before Claude sees the prompt.

`!`command`` executes a shell command and injects its output:
```markdown
---
description: Create a git commit with a conventional message
allowed-tools: Bash(git add:*), Bash(git commit:*)
---
## Changes
!`git diff --cached`

Create a commit message following Conventional Commits for $ARGUMENTS.
```

`@file` includes file contents inline:
```markdown
Review the following files:
- @package.json
- @tsconfig.json
Check for security issues and misconfigurations.
```

---

### Gap 18: The -p flag and all headless CLI flags

**Core headless flags:**

| Flag | Short | Values | Description |
|------|-------|--------|-------------|
| `--print` | `-p` | *(boolean)* | Non-interactive mode; send query, print result, exit |
| `--output-format` | — | `text`, `json`, `stream-json` | `text` = plain output; `json` = structured with metadata + `structured_output` field; `stream-json` = NDJSON for real-time streaming |
| `--input-format` | — | `text`, `stream-json` | `stream-json` enables multi-turn JSONL input |
| `--json-schema` | — | JSON schema string | Validates structured output (with `--output-format json`) |
| `--verbose` | — | *(boolean)* | Full turn-by-turn output in stream-json |

**Session management:**

| Flag | Short | Description |
|------|-------|-------------|
| `--continue` | `-c` | Continue most recent conversation |
| `--resume` | `-r` | Resume specific session by ID or name |
| `--fork-session` | — | Branch into new session from resumed session |
| `--session-id` | — | Use specific UUID as session ID |

**Model and agent:**

| Flag | Description |
|------|-------------|
| `--model` | Model name/alias (`sonnet`, `opus`, `haiku`, or full name) |
| `--fallback-model` | Fallback when default is overloaded |
| `--agent` | Specify custom agent name |
| `--agents` | Define subagents via JSON string |

**System prompt control (4 flags):**

| Flag | Description |
|------|-------------|
| `--system-prompt` | **Replaces** entire default system prompt |
| `--system-prompt-file` | Replace with file contents (mutually exclusive with above) |
| `--append-system-prompt` | **Appends** to default system prompt (recommended) |
| `--append-system-prompt-file` | Append file contents |

**Permission and tool flags:**

| Flag | Description |
|------|-------------|
| `--allowedTools` | Auto-approve listed tools (comma-separated) |
| `--disallowedTools` | Block listed tools entirely |
| `--permission-mode` | `default`, `acceptEdits`, `plan`, `bypassPermissions`, `dontAsk` |
| `--dangerously-skip-permissions` | Skip ALL permission checks ⚠️ |
| `--tools` | Restrict available tools (empty string disables all) |

**Execution limits:** `--max-turns` (integer), `--max-budget-usd` (decimal).

**Other notable flags:** `--add-dir` (additional working directories), `--mcp-config` (MCP server JSON file), `--worktree` / `-w` (git worktree isolation), `--debug` (debug logging with optional category filter), `--betas` (beta feature headers), `--effort` (`low`/`medium`/`high`).

---

### Gap 19: Plan mode

Plan mode restricts Claude to **read-only operations** for analysis and planning without making changes.

**Allowed operations:** Read, Grep, Glob, LS, WebSearch, WebFetch, TodoWrite, AskUserQuestion, and writing plan files to `~/.claude/plans/`.

**Blocked operations (by system prompt instruction):** Write, Edit, MultiEdit, Bash (write commands), NotebookEdit, and any destructive filesystem operations.

**Three activation methods:**
1. **Shift+Tab** — cycles through modes: Normal → `⏵⏵ accept edits on` → `⏸ plan mode on`
2. **`/plan [description]`** — enter plan mode, optionally with an immediate planning goal
3. **`--permission-mode plan`** — start a session directly in plan mode

**Important caveat:** Plan mode is enforced via **system prompt instructions**, not hard tool-level blocks. If you have `"allow": ["Write"]` in settings.json, Claude may still perform writes. Use `PreToolUse` hooks for deterministic enforcement.

**Plan subagent vs Explore subagent:** In plan mode, Claude delegates research to the **Plan** subagent (Sonnet model, full read tools). The **Explore** subagent (Haiku model, read-only) can also be used for fast codebase exploration. The Plan subagent prevents infinite nesting — subagents cannot spawn other subagents.

When **exiting plan mode**, Claude asks for **additional confirmation** about the task before executing, ensuring safety during the transition.

---

## Domain 4 — Prompt engineering and structured output (20% of exam)

### Gap 20: Structured outputs (GA January 2026)

Structured outputs provide **guaranteed JSON schema conformance** through constrained decoding — the model literally cannot produce tokens that violate the schema. This is fundamentally different from the old tool_use workaround that relied on best-effort fine-tuning.

**Two complementary features:**
1. **JSON outputs** via `output_config.format` — controls Claude's response format
2. **Strict tool use** via `strict: true` on tool schemas — guarantees tool input validation

**Raw API example:**
```json
{
  "model": "claude-opus-4-6",
  "max_tokens": 1024,
  "messages": [{"role": "user", "content": "Extract info from: John Smith (john@example.com)..."}],
  "output_config": {
    "format": {
      "type": "json_schema",
      "schema": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "email": {"type": "string"}
        },
        "required": ["name", "email"],
        "additionalProperties": false
      }
    }
  }
}
```

**Python SDK with Pydantic:**
```python
from pydantic import BaseModel
from anthropic import Anthropic

class ContactInfo(BaseModel):
    name: str
    email: str

client = Anthropic()
response = client.messages.parse(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "..."}],
    output_format=ContactInfo,
)
print(response.parsed_output)  # ContactInfo object
```

**Strict tool use:**
```json
{
  "name": "get_weather",
  "strict": true,
  "input_schema": {
    "type": "object",
    "properties": { "location": {"type": "string"} },
    "required": ["location"],
    "additionalProperties": false
  }
}
```

**Three complexity limits (combined across all strict schemas in a request):**

| Limit | Value |
|-------|-------|
| Strict tools per request | **20** |
| Total optional parameters | **24** (across all strict schemas) |
| Parameters with union types (`anyOf`) | **16** |

Compilation timeout is **180 seconds**. Compiled grammars are **cached 24 hours** from last use. Cache invalidates when schema structure changes but NOT when only `name`/`description` changes.

**Edge cases:** `stop_reason: "refusal"` means safety override (output may not match schema). `stop_reason: "max_tokens"` means incomplete output. Not compatible with citations or message prefilling.

**Migration note:** `output_format` (beta) → `output_config.format` (GA). The beta header `structured-outputs-2025-11-13` still works during the transition period.

---

### Gap 21: Complete tool_use API flow

The five-step cycle:

**Step 1 — Define tools and send request:**
```json
{
  "model": "claude-sonnet-4-5",
  "max_tokens": 1024,
  "tools": [{
    "name": "get_weather",
    "description": "Get current weather in a given location",
    "input_schema": {
      "type": "object",
      "properties": {
        "location": { "type": "string", "description": "City and state" }
      },
      "required": ["location"]
    }
  }],
  "messages": [{"role": "user", "content": "What's the weather in SF?"}]
}
```

**Step 2 — Response has `stop_reason: "tool_use"`:**
```json
{
  "role": "assistant",
  "stop_reason": "tool_use",
  "content": [
    { "type": "text", "text": "I'll check the weather for you." },
    {
      "type": "tool_use",
      "id": "toolu_01A09q90qw90lq917835lqs136",
      "name": "get_weather",
      "input": { "location": "San Francisco, CA" }
    }
  ]
}
```

**Step 3 — Execute tool on your system** (client-side).

**Step 4 — Send tool_result referencing `tool_use_id`:**
```json
{
  "role": "user",
  "content": [{
    "type": "tool_result",
    "tool_use_id": "toolu_01A09q90qw90lq917835lqs136",
    "content": "65°F, partly cloudy"
  }]
}
```

**Step 5 — Claude responds with final answer:**
```json
{
  "role": "assistant",
  "stop_reason": "end_turn",
  "content": [{ "type": "text", "text": "The weather in SF is 65°F and partly cloudy." }]
}
```

**`tool_choice` parameter options:** `"auto"` (default — Claude decides), `"any"` (must use a tool), `{"type": "tool", "name": "..."}` (force specific tool), `"none"` (disable tools). When tools are present, an automatic system prompt addition costs **346 tokens** for `auto`/`none`, **313 tokens** for `any`/`tool`.

**Python SDK agentic loop:**
```python
response = client.messages.create(model="claude-sonnet-4-5", max_tokens=1024,
    tools=[...], messages=[{"role": "user", "content": "What's the weather in SF?"}])

if response.stop_reason == "tool_use":
    for block in response.content:
        if block.type == "tool_use":
            result = execute_tool(block.name, block.input)
            follow_up = client.messages.create(model="claude-sonnet-4-5", max_tokens=1024,
                tools=[...],
                messages=[
                    {"role": "user", "content": "What's the weather in SF?"},
                    {"role": "assistant", "content": response.content},
                    {"role": "user", "content": [
                        {"type": "tool_result", "tool_use_id": block.id, "content": result}
                    ]}
                ])
```

---

### Gap 22: Message Batches API

**50% cost discount**, up to **100,000 requests** per batch or **256 MB**, with **29-day result retention**. Most batches complete within 1 hour; the 24-hour expiration is the hard deadline.

**Endpoints:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/v1/messages/batches` | Create batch |
| `GET` | `/v1/messages/batches/{batch_id}` | Check status |
| `GET` | `/v1/messages/batches/{batch_id}/results` | Download JSONL results |
| `POST` | `/v1/messages/batches/{batch_id}/cancel` | Cancel batch |
| `GET` | `/v1/messages/batches` | List batches |
| `DELETE` | `/v1/messages/batches/{batch_id}` | Delete batch |

**Create request:**
```json
{
  "requests": [
    {
      "custom_id": "req-001",
      "params": {
        "model": "claude-sonnet-4-5",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": "Hello, world"}]
      }
    }
  ]
}
```

**Processing statuses:** `in_progress`, `canceling`, `ended`.

**Per-request result types:** `succeeded` (includes message), `errored` (not billed), `canceled` (not billed), `expired` (not billed).

**JSONL results format** (results may arrive in any order — use `custom_id` to match):
```jsonl
{"custom_id":"req-002","result":{"type":"succeeded","message":{"id":"msg_...","role":"assistant","content":[{"type":"text","text":"Hello!"}],"stop_reason":"end_turn","usage":{"input_tokens":11,"output_tokens":36}}}}
{"custom_id":"req-001","result":{"type":"succeeded","message":{"id":"msg_...","role":"assistant","content":[{"type":"text","text":"Hi!"}],"stop_reason":"end_turn","usage":{"input_tokens":10,"output_tokens":34}}}}
```

The response object contains `id`, `type` ("message_batch"), `processing_status`, `request_counts` (with `processing`, `succeeded`, `errored`, `canceled`, `expired` counters), `created_at`, `ended_at`, `expires_at`, `cancel_initiated_at`, and `results_url`.

---

### Gap 23: Few-shot prompting best practices

Anthropic recommends **3–5 diverse, relevant examples** for most tasks, and **20+ examples** with prompt caching for complex tasks. Three criteria for effective examples: **relevant** (mirror actual use case), **diverse** (cover edge cases, vary enough to avoid unintended pattern matching), **clear** (wrapped in XML tags).

**Canonical XML structure:**
```xml
<examples>
  <example>
    <input>Customer feedback text here</input>
    <output>
      <reasoning>Analysis of the feedback...</reasoning>
      <classification>Category</classification>
    </output>
  </example>
  <example>
    <input>Different type of feedback</input>
    <output>
      <reasoning>Different analysis...</reasoning>
      <classification>Different Category</classification>
    </output>
  </example>
</examples>
```

**Interaction with extended thinking:** *"Use `<thinking>` tags inside your few-shot examples to show Claude the reasoning pattern. It will generalize that style to its own extended thinking blocks."* When thinking is off, manual chain-of-thought with `<thinking>` and `<answer>` tags can substitute.

**Claude 4.x-specific warning:** *"Claude 4.x models pay close attention to details and examples. Ensure that your examples align with the behaviors you want to encourage and minimize behaviors you want to avoid."* In the API, examples are included at the start of the first user message.

---

## Domain 5 — Context management and reliability (15% of exam)

### Gap 24: Conversation history management

The Messages API is **stateless** — you must pass the **complete** conversation history with every request. Each turn builds on the full prior context:

```json
{
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"},
    {"role": "user", "content": "Follow-up question"}
  ]
}
```

You can inject **synthetic assistant messages** that didn't originate from Claude. The Token Count API (`POST /v1/messages/count-tokens`) is free and lets you measure context size before sending.

**Prompt caching** drastically reduces cost for conversation history. Place `cache_control` on the final block of the conversation to enable incremental caching. Cache read tokens cost **0.1× base input price** (90% savings). Cache write tokens cost 1.25× (5-minute TTL) or 2× (1-hour TTL), refreshed on each use.

**Progressive summarization:** Extract key facts and decisions first, then compress older messages. Risks include losing important early instructions. Anthropic recommends saving critical state to `CLAUDE.md` or disk files rather than relying solely on in-context memory. Context quality degrades well before hitting 100% capacity — around **20–40% usage** is where output quality starts to degrade for some tasks.

---

### Gap 25: Scratchpad files

Claude Code uses a designated scratchpad directory at the OS temporary path: `$TEMP/claude/{project-hash}/{session-id}/scratchpad/`. It also creates `tmpclaude-*-cwd` files in the working directory.

**Common patterns for persistent state:**
- `claude-progress.txt` — Anthropic's recommended progress tracking file
- `feature_list.json` — structured task status tracking
- `plan.md` or `SCRATCHPAD.md` — plans and working notes
- `~/.claude/projects/<project>/memory/MEMORY.md` — auto-memory concise index

**Interaction with /compact:** Scratchpad files **persist on disk** even after compaction. Anthropic's best practice: *"Because the plan is stored on disk, users can run /clear or /compact to free up tokens without losing the project roadmap."* The recommended pattern is to save progress to files before context resets.

The **Memory Tool** (API feature) formalizes this pattern with a `/memories` directory and a protocol: *"ASSUME INTERRUPTION: Your context window might be reset at any moment, so record progress in your memory directory."*

---

### Gap 26: Structured state persistence and crash recovery

Anthropic's official long-running agent pattern (from their engineering blog) uses two phases:

**Initializer Agent** (first context window) creates:
- `init.sh` — bootstraps environment (dev server, test suites)
- `claude-progress.txt` — progress log across sessions
- `feature_list.json` — comprehensive feature tracking with status
- Initial git commit as checkpoint baseline

**Feature list structure:**
```json
{
  "category": "functional",
  "description": "New chat button creates a fresh conversation",
  "steps": ["Navigate to interface", "Click New Chat", "Verify creation"],
  "passes": false
}
```

**Coding Agent** (subsequent context windows) follows a recovery protocol:
1. `pwd` → locate working directory
2. Read git logs and progress files to understand current state
3. Read feature list, pick highest-priority incomplete feature
4. Work incrementally on ONE feature
5. Test with browser automation/E2E tools
6. Commit with descriptive message + update progress file

**Multi-agent manifest pattern:**
```json
{
  "task_id": "api-endpoint",
  "agent_role": "backend-developer",
  "model": "claude-sonnet-4-6",
  "context_files": ["src/routes/", "src/models/"],
  "constraints": ["modify only specified directories"],
  "output_artifacts": ["src/routes/feature.ts", "tests/feature.test.ts"],
  "status": "pending",
  "token_budget": 50000
}
```

Claude Code's Teams system stores task state in `~/.claude/tasks/{team}/*.json` and team configuration in `~/.claude/teams/{team}/config.json`. Crashed teammates have a **5-minute heartbeat timeout** and are auto-marked inactive; recovery is manual — the human re-engages them, and they read progress files to resume.

**Key principle:** Git serves as the state backbone. Descriptive commits, progress files, and feature lists together provide enough context for any new agent session to pick up exactly where work stopped.

---

### Gap 27: Field-level confidence scoring

The most effective prompting pattern for per-field confidence asks for value, score, and reasoning together:

```
For each extracted field, provide:
1. The extracted value
2. A confidence score from 0.0 to 1.0
3. Brief reasoning for the confidence level

Output as JSON:
{
  "fields": {
    "company_name": {"value": "Acme Corp", "confidence": 0.95,
                     "reasoning": "Clearly stated in header"},
    "revenue":      {"value": "$4.2M", "confidence": 0.72,
                     "reasoning": "Found in footnote, ambiguous fiscal year"},
    "employee_count": {"value": null, "confidence": 0.0,
                       "reasoning": "Not found in document"}
  }
}
```

**Calibration with labeled validation sets:** Collect extraction results with confidence scores → stratify by confidence bands (0–0.3, 0.3–0.6, 0.6–0.8, 0.8–1.0) → sample proportionally from each band → human-label samples for ground truth → compare predicted confidence vs actual accuracy per band → adjust thresholds: auto-accept high-confidence, human-review low-confidence.

Research shows verbalized confidence (asking the model to state a number) often outperforms raw token probabilities for calibration. However, production systems should consider **ensemble methods** (multiple runs, vote on answers), **temperature scaling**, or **verifier models** for higher reliability. The AUROC for naive "just ask for a number" approaches can be as low as **0.58** with high variance — explicit reasoning steps improve calibration significantly.

---

### Gap 28: Information provenance patterns

**Claim-source mapping structure:**
```json
{
  "claim": "Global EV sales grew 35% in 2024",
  "sources": [
    {
      "source_id": "doc_1",
      "source_name": "IEA Global EV Report 2025",
      "relevant_quote": "Electric car sales grew by 35% year-on-year...",
      "confidence": 0.95,
      "date": "2025-03-15"
    },
    {
      "source_id": "doc_3",
      "source_name": "Bloomberg NEF",
      "relevant_quote": "EV sales increased approximately 33-37%...",
      "confidence": 0.82,
      "date": "2025-01-20"
    }
  ],
  "conflict_resolution": "Minor discrepancy; IEA figure used as primary (more recent, official source)"
}
```

**Handling conflicting statistics:** Include temporal context (date of measurement), methodological differences (e.g., "29% including hydro" vs "18% excluding hydro"), and resolution reasoning. Always surface the conflict rather than silently picking one number.

**Anthropic's Citations API** provides built-in provenance when `citations.enabled=true` on document sources. Response interleaves `cited_text` blocks (which do **not count** toward output tokens) with text. Citations are *"guaranteed to contain valid pointers to the provided documents"* and are *"significantly more likely to cite the most relevant quotes compared to purely prompt-based approaches."*

**Rendering by content type:** Use **tables** for comparative data with source attribution columns. Use **prose** for narrative synthesis with inline citations. Use **lists** for discrete claims each with explicit source references. For multi-source RAG, wrap documents in `<documents><document index="1"><source>URL</source><document_content>...</document_content></document></documents>` XML structure and instruct Claude to *"quote relevant parts of the documents first before carrying out its task."*

---

## Quick reference: permission mode cheat sheet

| Mode | Behavior | Activation |
|------|----------|------------|
| `default` | Asks before modifying | Default behavior |
| `acceptEdits` | Auto-accepts file edits; Bash still prompts | `Shift+Tab` once, or `--permission-mode acceptEdits` |
| `plan` | Read-only analysis, no execution | `Shift+Tab` twice, `/plan`, or `--permission-mode plan` |
| `bypassPermissions` | Approves everything (except `disallowedTools`) | `--permission-mode bypassPermissions` ⚠️ |
| `dontAsk` | Denies anything not pre-approved (TS SDK only) | `permissionMode: "dontAsk"` |

## Quick reference: SDK parameter name mapping

| Concept | Python (`snake_case`) | TypeScript (`camelCase`) | CLI flag |
|---------|----------------------|-------------------------|----------|
| Turn limit | `max_turns` | `maxTurns` | `--max-turns` |
| Budget limit | `max_budget_usd` | `maxBudgetUsd` | `--max-budget-usd` |
| Tool allowlist | `allowed_tools` | `allowedTools` | `--allowedTools` |
| Tool blocklist | `disallowed_tools` | `disallowedTools` | `--disallowedTools` |
| Resume session | `resume` | `resume` | `--resume` / `-r` |
| Fork session | `fork_session` | `forkSession` | `--fork-session` |
| Permission mode | `permission_mode` | `permissionMode` | `--permission-mode` |

---

## Conclusion: the five highest-yield study areas

The exam weights **agentic architecture at 27%**, making the Agent SDK's `query()` loop, permission pipeline (`disallowedTools` → `allowedTools` → hooks → `canUseTool` → `permissionMode`), and session management the single most important study area. The **tool_use five-step flow** and **structured outputs** (GA with `output_config.format` and `strict: true`) together dominate Domain 4's 20% weight — memorize the exact JSON structures and the three complexity limits (20 strict tools, 24 optional params, 16 union-typed params). For Domain 3's configuration questions, the SKILL.md frontmatter fields and their interaction with `context: fork`/`inherit` and the invocation control matrix are the most likely testable specifics. In Domain 2, the MCP error duality (protocol-level in `error` field vs tool-level with `isError: true`) is a classic exam distinction. Finally, Domain 5's crash recovery pattern — progress files, feature lists, git checkpoints, and the initializer/coder agent split — represents Anthropic's official recommended architecture for production agents.