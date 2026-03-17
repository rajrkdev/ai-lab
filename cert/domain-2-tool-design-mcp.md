---
layout: default
title: "Domain 2: Tool Design & MCP"
---

# Domain 2: Tool Design & MCP Integration

## Weight: 18% of Exam

**Appears in Scenarios:** 1 (Customer Support), 3 (Multi-Agent Research), 4 (Developer Productivity)

---

## What This Domain Tests

This domain tests your ability to design tools that Claude can reliably select, implement structured error handling in MCP tools, distribute tools appropriately across agents, configure MCP servers, and choose the right built-in tool for each task.

---

## Task Statement 2.1: Design Effective Tool Interfaces

### Tool Descriptions Are Everything

Tool descriptions are the **primary mechanism** Claude uses to decide which tool to call. When descriptions are minimal or ambiguous, Claude picks the wrong tool.

### The Problem: Minimal Descriptions

```python
# ❌ MINIMAL DESCRIPTIONS — Claude can't differentiate these
tools = [
    {
        "name": "analyze_content",
        "description": "Analyzes content",  # Too vague!
        "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}}
    },
    {
        "name": "analyze_document",
        "description": "Analyzes a document",  # Nearly identical!
        "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}}
    }
]
# Result: Claude randomly picks between them. 50% misrouting.
```

### The Fix: Detailed, Differentiated Descriptions

```python
# ✅ DETAILED DESCRIPTIONS — Claude knows exactly when to use each
tools = [
    {
        "name": "extract_web_results",
        "description": (
            "Extract and summarize key findings from web search results. "
            "Input: raw HTML or text from a web page. "
            "Output: structured findings with titles, key quotes, and relevance scores. "
            "Use this for: processing web search output, summarizing articles. "
            "Do NOT use for: analyzing uploaded PDFs, processing local files, "
            "or verifying claims against source material."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "web_content": {
                    "type": "string",
                    "description": "Raw HTML or text content from a web page"
                },
                "query": {
                    "type": "string",
                    "description": "The original search query for relevance scoring"
                }
            },
            "required": ["web_content"]
        }
    },
    {
        "name": "extract_document_data",
        "description": (
            "Extract structured data points from uploaded documents (PDFs, reports, "
            "spreadsheets). Input: document text or file path. "
            "Output: structured data with field names, values, page numbers, and "
            "confidence scores. "
            "Use this for: processing uploaded PDFs, extracting tables from reports, "
            "pulling specific data points from contracts. "
            "Do NOT use for: web search results, HTML content, or claim verification."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "document_text": {"type": "string"},
                "fields_to_extract": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific fields to extract (e.g., 'total_amount', 'date', 'parties')"
                }
            },
            "required": ["document_text"]
        }
    }
]
```

### What Good Tool Descriptions Include

Every tool description should cover:

1. **What it does** — One clear sentence
2. **Input format** — What data it expects
3. **Output format** — What it returns
4. **When to use it** — Specific scenarios
5. **When NOT to use it** — Boundaries with similar tools
6. **Example queries** — Concrete examples that trigger this tool

### Splitting Generic Tools

When a tool is too generic, split it into purpose-specific tools:

```
BEFORE (one generic tool):
  analyze_document → Does everything (extraction, summarization, verification)

AFTER (three specific tools):
  extract_data_points    → Pulls structured data from documents
  summarize_content      → Creates concise summaries
  verify_claim_against_source → Checks if a claim matches source material
```

### System Prompt Keyword Traps

Keyword-sensitive instructions in the system prompt can override well-written tool descriptions:

```python
# ❌ PROBLEM: System prompt says "always search" for certain keywords
system_prompt = """
When the user mentions 'order' or 'customer', always use the search tool first.
"""
# This causes Claude to call search_tool even when get_customer is the right choice,
# because "customer" triggers the keyword rule.

# ✅ FIX: Review system prompts for keyword-sensitive instructions
# that might create unintended tool associations
system_prompt = """
Use the most appropriate tool based on what the user needs:
- For customer identity verification: get_customer
- For order details: lookup_order  
- For general information: search_tool
"""
```

---

## Task Statement 2.2: Structured Error Responses for MCP Tools

### The isError Flag Pattern

MCP tool results can signal errors using the `isError` flag. This is critical because it tells Claude "something went wrong" rather than "here's an empty/unexpected result."

```python
# MCP tool returning a successful result
def handle_tool_call(name, arguments):
    if name == "get_customer":
        customer = db.find_customer(arguments["email"])
        if customer:
            return {
                "content": [{"type": "text", "text": json.dumps(customer)}],
                "isError": False  # Success
            }
        else:
            # Valid empty result — no customer found (NOT an error)
            return {
                "content": [{"type": "text", "text": json.dumps({
                    "result": "no_match",
                    "message": "No customer found with that email",
                    "suggestion": "Try searching by phone number instead"
                })}],
                "isError": False  # This is NOT an error — it's a valid empty result
            }

# MCP tool returning an error
def handle_tool_call_with_error(name, arguments):
    if name == "get_customer":
        try:
            customer = db.find_customer(arguments["email"])
            return {"content": [{"type": "text", "text": json.dumps(customer)}]}
        except DatabaseTimeout:
            return {
                "content": [{"type": "text", "text": json.dumps({
                    "errorCategory": "transient",
                    "isRetryable": True,
                    "message": "Database timeout. The customer database is temporarily "
                               "unavailable. This is usually resolved within 30 seconds.",
                    "attempted_query": arguments["email"]
                })}],
                "isError": True  # This IS an error
            }
        except InvalidEmailFormat:
            return {
                "content": [{"type": "text", "text": json.dumps({
                    "errorCategory": "validation",
                    "isRetryable": False,
                    "message": "Invalid email format. Expected: user@domain.com",
                    "received_input": arguments["email"]
                })}],
                "isError": True
            }
```

### Error Categories

| Category | Examples | Retryable? | Agent Action |
|---|---|---|---|
| **Transient** | Timeout, service unavailable, rate limit | Yes | Retry after delay |
| **Validation** | Invalid input format, missing required field | No (fix input) | Fix input and retry |
| **Business** | Policy violation, refund exceeds limit | No | Explain to user or escalate |
| **Permission** | Unauthorized access, insufficient privileges | No | Escalate or use alternative |

### Structured Error Response Format

```json
{
  "errorCategory": "transient",
  "isRetryable": true,
  "message": "Human-readable description of what went wrong",
  "attempted_query": "What was tried",
  "partial_results": "Any data retrieved before failure",
  "alternative_approaches": "What the agent could try instead"
}
```

### Critical Distinction: Access Failures vs Valid Empty Results

```python
# ❌ WRONG — These two situations are handled identically
# (Both return empty result as "success")

# Access failure (database timeout) — THIS IS AN ERROR
return {"content": [{"type": "text", "text": "[]"}], "isError": False}  # ❌

# Valid empty result (no matching customer) — THIS IS SUCCESS
return {"content": [{"type": "text", "text": "[]"}], "isError": False}  # Correct here

# ✅ CORRECT — Distinguish between them
# Access failure:
return {
    "content": [{"type": "text", "text": json.dumps({
        "errorCategory": "transient",
        "isRetryable": True,
        "message": "Database timeout — could not complete search"
    })}],
    "isError": True  # Tells Claude: "This failed, you may want to retry"
}

# Valid empty result:
return {
    "content": [{"type": "text", "text": json.dumps({
        "result": "no_match",
        "message": "Search completed successfully. No customers match that criteria.",
        "records_searched": 15000
    })}],
    "isError": False  # Tells Claude: "Search worked, just no matches"
}
```

### Anti-Patterns in Error Handling

**Anti-pattern 1: Generic "Operation failed" errors**
```python
# ❌ Hides what happened — agent can't make recovery decisions
return {"content": [{"type": "text", "text": "Operation failed"}], "isError": True}
```

**Anti-pattern 2: Silently suppressing errors (returning empty as success)**
```python
# ❌ Pretends the search succeeded when it didn't
except DatabaseTimeout:
    return {"content": [{"type": "text", "text": "[]"}], "isError": False}
```

**Anti-pattern 3: Terminating entire workflow on single failure**
```python
# ❌ One subagent failure shouldn't kill the whole pipeline
if search_agent_failed:
    raise SystemError("Search failed — aborting research")
```

### Local Recovery Before Propagation

Subagents should handle transient errors locally, only propagating what they can't resolve:

```python
# Inside the web search subagent:
async def search(query):
    for attempt in range(3):  # Local retry for transient errors
        try:
            results = await web_search(query)
            return results
        except Timeout:
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            # After 3 attempts, propagate to coordinator with context
            return {
                "error": True,
                "errorCategory": "transient",
                "message": "Web search timed out after 3 attempts",
                "attempted_query": query,
                "partial_results": [],  # Nothing retrieved
                "alternative": "Try a more specific query or different source"
            }
```

---

## Task Statement 2.3: Tool Distribution and tool_choice

### The Too-Many-Tools Problem

Giving an agent access to 18 tools degrades selection reliability compared to 4-5 focused tools. More tools = more decision complexity = more errors.

```
❌ ONE AGENT WITH 18 TOOLS:
  Coordinator agent: [web_search, fetch_url, read_doc, extract_data,
    summarize, verify_claim, translate, format_report, send_email,
    create_chart, query_database, update_record, schedule_meeting,
    generate_image, compress_file, validate_json, convert_format, notify]
  
  Result: Agent frequently picks wrong tool. 
  "summarize" vs "extract_data" confusion is constant.

✅ DISTRIBUTED ACROSS SPECIALIZED AGENTS:
  Search agent:    [web_search, fetch_url]           (2 tools)
  Analysis agent:  [read_doc, extract_data]          (2 tools)
  Synthesis agent: [summarize, verify_claim, format_report]  (3 tools)
  Coordinator:     [Agent]                           (1 tool)
  
  Result: Each agent has focused, non-overlapping tools.
```

### Scoped Cross-Role Tools

Sometimes a subagent needs occasional access to a tool outside its specialization. Rather than giving it the full tool, provide a scoped version:

```python
# ❌ WRONG — Giving synthesis agent full web_search access
synthesis_agent = AgentDefinition(
    tools=["summarize", "verify_claim", "web_search"],  # ❌ Web search is not its role
)

# ✅ CORRECT — Scoped verify_fact tool for quick lookups
synthesis_agent = AgentDefinition(
    tools=["summarize", "verify_claim", "verify_fact"],  # ✅ Scoped tool
    # verify_fact does simple fact-checking (dates, names, statistics)
    # Complex verifications still go through coordinator → search agent
)
```

### tool_choice Options

`tool_choice` controls whether and how Claude uses tools:

```python
# "auto" (default) — Claude decides freely
# May return text without calling any tool
response = client.messages.create(
    tools=tools,
    tool_choice={"type": "auto"},   # Claude might or might not use tools
    messages=messages,
)

# "any" — Claude MUST call a tool, but can choose which one
# Guarantees structured output when document type is unknown
response = client.messages.create(
    tools=[extract_invoice, extract_receipt, extract_contract],
    tool_choice={"type": "any"},    # Must call one of these tools
    messages=messages,
)

# Forced — Claude MUST call this specific tool
# Use to ensure a specific step happens first
response = client.messages.create(
    tools=[extract_metadata, enrich_data, validate],
    tool_choice={"type": "tool", "name": "extract_metadata"},  # Must call this one
    messages=messages,
)
# Then in the NEXT turn, use "auto" for subsequent steps
```

### When to Use Each

| tool_choice | When to Use | Exam Scenario |
|---|---|---|
| `"auto"` | General agentic loop — Claude decides freely | Default for most agents |
| `"any"` | Must get structured output, document type unknown | Structured data extraction with multiple schemas |
| `{"type": "tool", "name": "..."}` | Must run a specific tool first | Extract metadata before enrichment |

### TypeScript Examples

```typescript
// Force a specific tool first
const metadataResponse = await client.messages.create({
  model: "claude-sonnet-4-20250514",
  tools: [extractMetadata, enrichData, validate],
  tool_choice: { type: "tool", name: "extract_metadata" },
  messages,
});

// Then allow free choice for subsequent steps
const enrichResponse = await client.messages.create({
  model: "claude-sonnet-4-20250514",
  tools: [enrichData, validate],
  tool_choice: { type: "auto" },
  messages: updatedMessages,
});
```

---

## Task Statement 2.4: MCP Server Integration

### Configuration Scopes

**Project-level** (`.mcp.json` in repository root) — shared with team via version control:
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "jira": {
      "command": "npx",
      "args": ["-y", "mcp-server-jira"],
      "env": {
        "JIRA_API_TOKEN": "${JIRA_API_TOKEN}",
        "JIRA_BASE_URL": "${JIRA_BASE_URL:-https://mycompany.atlassian.net}"
      }
    }
  }
}
```

**User-level** (`~/.claude.json` or `~/.claude/settings.local.json`) — personal/experimental:
```json
{
  "mcpServers": {
    "my-experimental-server": {
      "command": "python",
      "args": ["/home/user/experiments/my-mcp-server.py"],
      "env": {
        "DEBUG": "true"
      }
    }
  }
}
```

### Environment Variable Expansion

The `${VAR}` syntax keeps secrets out of version control:

```json
{
  "mcpServers": {
    "database": {
      "command": "npx",
      "args": ["mcp-server-postgres"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}",
        "DB_PASSWORD": "${DB_PASSWORD:-default_dev_password}"
      }
    }
  }
}
```

- `${VAR}` — Uses environment variable `VAR`. Fails if unset.
- `${VAR:-default}` — Uses `VAR` if set, otherwise uses `default`.

### MCP Resources vs Tools

| | MCP Tools | MCP Resources |
|---|---|---|
| **Purpose** | Execute actions | Expose read-only data |
| **Control** | Model-controlled (Claude decides when to call) | Application-controlled |
| **Examples** | `create_ticket`, `send_email`, `query_db` | Issue summaries, documentation hierarchies, database schemas |
| **Use case** | Performing operations | Giving agents visibility into available data without exploratory tool calls |

**MCP Resources reduce exploratory calls:**
```
WITHOUT resources:
  Agent: "What tables exist?" → calls list_tables()
  Agent: "What columns in users?" → calls describe_table("users")
  Agent: "What columns in orders?" → calls describe_table("orders")
  (3 tool calls just to understand the schema)

WITH resources:
  Resource "database://schema" automatically loaded into context
  Agent already knows all tables and columns
  (0 exploratory calls)
```

### Community vs Custom MCP Servers

**Use community servers** for standard integrations (GitHub, Jira, Slack, Postgres):
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

**Build custom servers** only for team-specific workflows:
```json
{
  "mcpServers": {
    "insurance-claims": {
      "command": "python",
      "args": ["./tools/claims-mcp-server.py"]
    }
  }
}
```

### Enhancing MCP Tool Descriptions

If Claude prefers built-in tools (like Grep) over more capable MCP tools, enhance the MCP tool descriptions:

```python
# ❌ MINIMAL — Claude ignores this and uses Grep instead
@mcp.tool()
def search_codebase(query: str):
    """Search the codebase."""  # Too vague!
    
# ✅ DETAILED — Claude understands this is superior to Grep
@mcp.tool()
def search_codebase(query: str):
    """Search the codebase using semantic code search with AST-aware indexing.
    
    Unlike basic grep, this tool:
    - Understands code structure (finds implementations, not just string matches)
    - Ranks results by relevance to the query
    - Returns surrounding context (function signatures, class hierarchy)
    - Supports natural language queries ("find all error handlers")
    
    Input: Natural language query or code pattern
    Output: Ranked list of code locations with context
    
    Use INSTEAD OF Grep when you need to understand code semantics,
    not just find text patterns."""
```

---

## Task Statement 2.5: Built-in Tools (Read, Write, Edit, Bash, Grep, Glob)

### Tool Selection Guide

```
"I need to find where function X is called across the codebase"
  → Grep (searches file CONTENTS for patterns)

"I need to find all test files in the project"
  → Glob (finds files by NAME/EXTENSION patterns)

"I need to read the entire contents of config.py"
  → Read (loads full file contents)

"I need to change line 42 of config.py from X to Y"
  → Edit (targeted modification using unique text matching)

"I need to rewrite config.py entirely"
  → Write (full file replacement)

"I need to run the test suite"
  → Bash (execute shell commands)
```

### Grep vs Glob — Know the Difference

```bash
# GREP — Search file CONTENTS for patterns
# "Find all files that CONTAIN the text 'processRefund'"
Grep("processRefund")
# Returns: matching lines with file paths and line numbers

# GLOB — Find files by NAME patterns
# "Find all files NAMED *.test.tsx"
Glob("**/*.test.tsx")
# Returns: file paths matching the pattern
```

### Edit Tool Failure → Read + Write Fallback

The Edit tool works by matching a unique text string in the file and replacing it. If the text isn't unique (appears multiple times), Edit fails.

```python
# Edit tool: targeted modification
Edit(
    file="config.py",
    old_str="MAX_RETRIES = 3",    # Must be unique in the file
    new_str="MAX_RETRIES = 5"
)

# If "MAX_RETRIES = 3" appears in multiple places, Edit fails.
# Fallback: Read the full file, modify in memory, Write the result.
content = Read("config.py")
content = content.replace("MAX_RETRIES = 3", "MAX_RETRIES = 5", 1)  # Replace first occurrence
Write("config.py", content)
```

### Incremental Codebase Understanding

Don't read all files upfront. Build understanding step by step:

```
Step 1: Grep to find entry points
  Grep("def main") → finds src/app.py, src/cli.py

Step 2: Read entry points to understand structure
  Read("src/app.py") → sees imports from auth, database, api

Step 3: Grep to trace specific flows
  Grep("from auth import") → finds all files using auth module

Step 4: Read specific files to follow the flow
  Read("src/auth/middleware.py") → understands auth flow

This is BETTER than: Read all 50 files → overwhelm context window
```

### Tracing Function Usage Across Wrapper Modules

```
Step 1: Identify all exported names from the module
  Grep("export function" OR "def.*:" in utils/index.ts)
  → finds: processOrder, validateInput, formatResponse

Step 2: Search for each name across the codebase
  Grep("processOrder") → found in: api/orders.ts, tests/orders.test.ts
  Grep("validateInput") → found in: api/middleware.ts, api/users.ts
  Grep("formatResponse") → found in: api/responses.ts
```

---

## Practice Questions — Domain 2

### Question 1 (Difficulty: Medium)
Your agent has tools `get_customer` ("Retrieves customer information") and `lookup_order` ("Retrieves order details"). Production logs show the agent frequently calls `get_customer` when users ask "check my order #12345." Both tools accept similar identifier formats. What's the most effective first step?

**A)** Add few-shot examples showing correct tool selection.
**B)** Expand each tool's description to include input formats, example queries, edge cases, and boundaries explaining when to use it versus the other tool.
**C)** Implement a routing layer that parses input and pre-selects the appropriate tool.
**D)** Consolidate both tools into a single `lookup_entity` tool.

**Correct Answer: B**
Tool descriptions are the primary mechanism for tool selection. Expanding them is the lowest-effort, highest-leverage fix. A adds token overhead without fixing the root cause. C is over-engineered. D requires more effort than a "first step" warrants.

### Question 2 (Difficulty: Hard)
Your web search subagent times out. You need to design how this failure flows back to the coordinator. Which approach enables the best recovery?

**A)** Return structured error context including failure type, attempted query, partial results, and alternative approaches.
**B)** Retry with exponential backoff, returning generic "search unavailable" after all retries fail.
**C)** Return an empty result set marked as successful.
**D)** Propagate the timeout exception to terminate the entire workflow.

**Correct Answer: A**
Structured error context gives the coordinator the information it needs for intelligent recovery — retry with a modified query, try alternatives, or proceed with partial results. B hides context. C suppresses the error. D kills the whole workflow unnecessarily.

### Question 3 (Difficulty: Medium)
You need Claude to extract data from an unknown document type (could be invoice, receipt, or contract). Each type has a different extraction schema. How should you configure tool_choice?

**A)** `tool_choice: "auto"` — let Claude decide which extraction schema to use.
**B)** `tool_choice: "any"` — guarantee Claude calls an extraction tool rather than returning text.
**C)** `tool_choice: {"type": "tool", "name": "extract_invoice"}` — always extract as invoice first.
**D)** Don't set tool_choice and add instructions in the system prompt.

**Correct Answer: B**
`"any"` guarantees Claude calls a tool (structured output) but lets it choose which extraction schema matches the document. `"auto"` might return text instead. Forced selection assumes invoice format. D is probabilistic.

---

## Quick Reference — Domain 2 Cheat Sheet

| Concept | Key Fact |
|---|---|
| **Tool descriptions** | Primary mechanism for tool selection. Minimal = unreliable. |
| **Good descriptions include** | Purpose, input format, output format, when to use, when NOT to use |
| **Tool misrouting fix** | Expand descriptions first (not few-shot, not routing layer) |
| **isError flag** | MCP pattern for signaling tool failures to the agent |
| **Error categories** | transient, validation, business, permission |
| **Structured error fields** | errorCategory, isRetryable, message, partial_results |
| **Access failure vs empty result** | Timeout = isError:true. No matches = isError:false. |
| **Too many tools** | 18 tools degrades selection vs 4-5 focused tools |
| **tool_choice "auto"** | Claude decides freely (may skip tools) |
| **tool_choice "any"** | Must call a tool, choose which |
| **tool_choice forced** | Must call specific named tool |
| **MCP project scope** | `.mcp.json` — shared via version control |
| **MCP user scope** | `~/.claude.json` — personal/experimental |
| **${VAR} expansion** | Environment variables in .mcp.json |
| **MCP resources** | Content catalogs to reduce exploratory tool calls |
| **Community vs custom** | Community for standard (GitHub, Jira). Custom for team-specific. |
| **Grep** | Search file CONTENTS for patterns |
| **Glob** | Find files by NAME/EXTENSION patterns |
| **Edit failure** | Fallback to Read + Write when text match isn't unique |
| **Codebase exploration** | Incremental: Grep → Read → trace. Not read-all-upfront. |
