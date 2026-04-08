---
title: "Domain 1: Agentic Architecture"
---

# Domain 1: Agentic Architecture & Orchestration

## Weight: 27% of Exam (Highest Priority Domain)

**Appears in Scenarios:** 1 (Customer Support), 3 (Multi-Agent Research), 4 (Developer Productivity)

---

## What This Domain Tests

This domain tests your ability to design and implement autonomous AI agents that can reason, act, and coordinate with other agents. You must understand:

- How the agentic loop works at the API level
- How to orchestrate multiple agents in a hub-and-spoke pattern
- How to pass context between agents correctly
- When to use programmatic enforcement vs prompt-based guidance
- How to use hooks for deterministic compliance
- How to decompose complex tasks into manageable subtasks
- How to manage sessions across long-running workflows

---

## Task Statement 1.1: Design and Implement Agentic Loops

### What is an Agentic Loop?

An agentic loop is a while loop where Claude keeps running until it decides it's done. Unlike a simple chat (one question → one answer), an agent can call tools, observe results, reason about them, call more tools, and keep going until the task is complete.

**The key insight: Claude controls when the loop ends, not your code.** Your code just checks a signal called `stop_reason` to know whether to continue or stop.

### The Loop Lifecycle (Step by Step)

```
┌─────────────────────────────────────────────────────────┐
│                    AGENTIC LOOP                         │
│                                                         │
│  1. Your Code ──── sends prompt ────► Claude API        │
│                                         │               │
│                                         ▼               │
│                              ┌─────────────────┐        │
│                              │ Claude Evaluates │        │
│                              │ and Responds     │        │
│                              └────────┬────────┘        │
│                                       │                 │
│                                       ▼                 │
│                              ┌─────────────────┐        │
│                              │ Check stop_reason│        │
│                              └──┬───────────┬──┘        │
│                                 │           │           │
│                    "end_turn"   │           │ "tool_use"│
│                                 │           │           │
│                                 ▼           ▼           │
│                           ┌────────┐  ┌──────────┐     │
│                           │  DONE  │  │ Execute  │     │
│                           │ Return │  │ Tool(s)  │     │
│                           │ Result │  └────┬─────┘     │
│                           └────────┘       │           │
│                                            ▼           │
│                                    ┌──────────────┐    │
│                                    │ Append tool  │    │
│                                    │ results to   │    │
│                                    │ conversation │    │
│                                    └──────┬───────┘    │
│                                           │            │
│                                           └──► LOOP    │
│                                              BACK TO 1 │
└─────────────────────────────────────────────────────────┘
```

### The Five Steps Explained

**Step 1: Send the prompt.** Your code sends the user's message plus tool definitions to Claude. On subsequent iterations, you also include the full conversation history (all prior messages + tool results).

**Step 2: Claude evaluates.** Claude reads everything — the system prompt, conversation history, tool definitions — and decides what to do. It can produce text, call one or more tools, or both.

**Step 3: Check stop_reason.** The API response includes a `stop_reason` field:
- `"tool_use"` → Claude wants to call tools. Continue the loop.
- `"end_turn"` → Claude is finished. Stop the loop and return the text.
- `"max_tokens"` → Claude hit the output limit. Response was truncated.
- `"refusal"` → Claude declined due to safety concerns.
- `"pause_turn"` → Server-side tool loop hit its iteration limit. Continue.
- `"stop_sequence"` → Claude hit a custom stop sequence you defined.

**Step 4: Execute tools.** For each `tool_use` block in Claude's response, run the corresponding tool function and collect the result.

**Step 5: Append to history.** Add Claude's response as an `assistant` message, then add tool results as a `user` message with `tool_result` blocks. Each tool result must reference the `tool_use_id` from Step 4.

### Complete Code Example — Raw API Loop

**Python:**
```python
import anthropic

client = anthropic.Anthropic()

# Define tools with detailed descriptions
tools = [
    {
        "name": "get_customer",
        "description": "Look up a customer by email or phone. Returns customer ID, "
                       "name, account status, and loyalty tier. Use this BEFORE any "
                       "order lookups or refund processing to verify customer identity. "
                       "Input: email (string) or phone (string). At least one required.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Customer email address"},
                "phone": {"type": "string", "description": "Customer phone number"}
            }
        }
    },
    {
        "name": "lookup_order",
        "description": "Retrieve order details by order ID. Returns items, amounts, "
                       "status, and shipping info. Requires a verified customer_id from "
                       "get_customer — do NOT call with only a customer name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "customer_id": {"type": "string", "description": "Verified customer ID from get_customer"}
            },
            "required": ["order_id", "customer_id"]
        }
    }
]

def execute_tool(name: str, tool_input: dict) -> str:
    """Execute a tool and return the result as a string."""
    if name == "get_customer":
        # In production, this calls your backend API
        return '{"customer_id": "C-12345", "name": "Jane Smith", "status": "active"}'
    elif name == "lookup_order":
        return '{"order_id": "ORD-789", "total": 99.99, "status": "delivered"}'
    return '{"error": "Unknown tool"}'

def agent_loop(user_message: str) -> str:
    """
    The core agentic loop. Continues until Claude signals end_turn.
    """
    messages = [{"role": "user", "content": user_message}]
    
    while True:
        # Step 1: Call Claude with tools
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            tools=tools,
            messages=messages,
        )
        
        # Step 2: Append Claude's FULL response to conversation history
        # (includes both text blocks and tool_use blocks)
        messages.append({"role": "assistant", "content": response.content})
        
        # Step 3: Check stop_reason
        if response.stop_reason == "end_turn":
            # Extract and return text from Claude's response
            text_parts = [block.text for block in response.content 
                         if block.type == "text"]
            return "\n".join(text_parts)
        
        # Step 4: Execute each tool Claude requested
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,   # MUST match the tool_use block's id
                    "content": result,
                })
        
        # Step 5: Append tool results as a USER message
        # (This is how Claude "sees" tool outputs — they're user messages)
        messages.append({"role": "user", "content": tool_results})
    
    # Loop continues until stop_reason == "end_turn"
```

**TypeScript:**
```typescript
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

const tools: Anthropic.Tool[] = [
  {
    name: "get_customer",
    description: "Look up a customer by email or phone. Returns customer ID, " +
                 "name, account status, and loyalty tier. Use this BEFORE any " +
                 "order lookups or refund processing to verify customer identity.",
    input_schema: {
      type: "object",
      properties: {
        email: { type: "string", description: "Customer email address" },
        phone: { type: "string", description: "Customer phone number" },
      },
    },
  },
  {
    name: "lookup_order",
    description: "Retrieve order details by order ID. Requires a verified " +
                 "customer_id from get_customer.",
    input_schema: {
      type: "object",
      properties: {
        order_id: { type: "string" },
        customer_id: { type: "string", description: "Verified customer ID" },
      },
      required: ["order_id", "customer_id"],
    },
  },
];

function executeTool(name: string, input: Record<string, unknown>): string {
  if (name === "get_customer") {
    return JSON.stringify({ customer_id: "C-12345", name: "Jane Smith" });
  }
  if (name === "lookup_order") {
    return JSON.stringify({ order_id: "ORD-789", total: 99.99 });
  }
  return JSON.stringify({ error: "Unknown tool" });
}

async function agentLoop(userMessage: string): Promise<string> {
  const messages: Anthropic.MessageParam[] = [
    { role: "user", content: userMessage },
  ];

  while (true) {
    // Step 1: Call Claude
    const response = await client.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 4096,
      tools,
      messages,
    });

    // Step 2: Append assistant response
    messages.push({ role: "assistant", content: response.content });

    // Step 3: Check stop_reason
    if (response.stop_reason === "end_turn") {
      const textBlocks = response.content.filter(
        (b): b is Anthropic.TextBlock => b.type === "text"
      );
      return textBlocks.map((b) => b.text).join("\n");
    }

    // Step 4 + 5: Execute tools, append results
    const toolResults: Anthropic.ToolResultBlockParam[] = response.content
      .filter((b): b is Anthropic.ToolUseBlock => b.type === "tool_use")
      .map((toolUse) => ({
        type: "tool_result" as const,
        tool_use_id: toolUse.id,
        content: executeTool(toolUse.name, toolUse.input as Record<string, unknown>),
      }));

    messages.push({ role: "user", content: toolResults });
  }
}
```

### Agent SDK Version (Simplified)

The Claude Agent SDK abstracts the loop away. You consume a stream of messages:

**Python (Agent SDK):**
```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

async def main():
    async for message in query(
        prompt="Check order #12345 for customer jane@example.com",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Glob"],
            permission_mode="acceptEdits",
            max_turns=10,            # Safety limit (not primary stopping mechanism)
            max_budget_usd=0.50,     # Cost safety limit
        ),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)          # Claude's reasoning
                elif hasattr(block, "name"):
                    print(f"Tool: {block.name}")  # Tool being called
        elif isinstance(message, ResultMessage):
            # Check HOW the loop ended
            print(f"Subtype: {message.subtype}")    # "success", "error_max_turns", etc.
            print(f"Stop reason: {message.stop_reason}")  # "end_turn", "refusal", etc.
            print(f"Cost: ${message.total_cost_usd}")
            print(f"Turns: {message.num_turns}")
            if message.subtype == "success":
                print(f"Result: {message.result}")

asyncio.run(main())
```

**TypeScript (Agent SDK):**
```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Check order #12345 for customer jane@example.com",
  options: {
    allowedTools: ["Read", "Edit", "Glob"],
    permissionMode: "acceptEdits",
    maxTurns: 10,
    maxBudgetUsd: 0.50,
  },
})) {
  if (message.type === "assistant") {
    for (const block of message.content) {
      if ("text" in block) console.log(block.text);
      if ("name" in block) console.log(`Tool: ${block.name}`);
    }
  }
  if (message.type === "result") {
    console.log(`Subtype: ${message.subtype}`);
    console.log(`Stop reason: ${message.stop_reason}`);
    if (message.subtype === "success") {
      console.log(`Result: ${message.result}`);
    }
  }
}
```

### SDK Message Types

The Agent SDK yields five message types during the loop:

| Message Type | When It Appears | What It Contains |
|---|---|---|
| `SystemMessage` | Start and lifecycle events | Subtype: `init`, `compact_boundary` |
| `AssistantMessage` | Each time Claude responds | Text blocks and/or tool_use blocks |
| `UserMessage` | After tool execution | Tool results fed back to Claude |
| `StreamEvent` | During streaming | Raw API events (message_delta, etc.) |
| `ResultMessage` | Always the LAST message | Result text, cost, usage, session_id |

### ResultMessage Subtypes (How the Loop Ends)

| Subtype | Meaning |
|---|---|
| `success` | Claude finished the task normally |
| `error_max_turns` | Hit the max_turns limit |
| `error_max_budget_usd` | Hit the budget limit |
| `error_during_execution` | API failure or cancellation |
| `error_max_structured_output_retries` | Failed structured output validation too many times |

### Model-Driven vs Pre-Configured Decision-Making

This is a critical exam distinction:

**Model-Driven (Correct Agentic Pattern):**
Claude decides which tools to call and in what order based on the conversation context. You provide all available tools, and Claude reasons about which ones are needed.

```
User: "Check my order #12345"
Claude thinks: "I need to verify the customer first..."
→ Calls get_customer
→ Gets customer ID
Claude thinks: "Now I can look up the order..."
→ Calls lookup_order with verified customer_id
→ Gets order details
Claude thinks: "I have all the info. Let me respond."
→ Returns final answer (stop_reason: "end_turn")
```

**Pre-Configured Pipeline (Not Truly Agentic):**
Your code dictates the sequence. Claude has no autonomy.

```python
# ❌ NOT agentic — this is a fixed pipeline
def process_request(user_message):
    step1 = call_claude("Extract customer email from: " + user_message)
    step2 = get_customer(step1.email)
    step3 = call_claude("What order does the customer want? " + user_message)
    step4 = lookup_order(step3.order_id, step2.customer_id)
    step5 = call_claude("Summarize: " + json.dumps(step4))
    return step5
```

The exam tests this distinction because pre-configured pipelines can't adapt to unexpected situations (e.g., customer asks about something that doesn't require an order lookup).

### ⚠️ Three Anti-Patterns (These ARE Wrong Answers)

**Anti-Pattern 1: Parsing Natural Language for Loop Termination**
```python
# ❌ WRONG — Never do this
while True:
    response = call_claude(messages)
    if "I have completed the task" in response.text:  # ❌ BAD
        break
    if "task is done" in response.text.lower():       # ❌ BAD
        break
```
**Why wrong:** Claude's text is non-deterministic. It might phrase completion differently each time, or include "I'm done" while still needing to call more tools. `stop_reason` is the ONLY reliable signal.

**Anti-Pattern 2: Arbitrary Iteration Caps as Primary Mechanism**
```python
# ❌ WRONG — Iteration cap as primary control
for i in range(5):  # ❌ BAD as primary mechanism
    response = call_claude(messages)
    process_response(response)
```
**Why wrong:** Either cuts off Claude too early (task incomplete) or runs too long (wasting tokens). `max_turns` as a SAFETY NET is fine; as the primary mechanism, it's wrong.

```python
# ✅ CORRECT — max_turns as safety net, stop_reason as primary
options = ClaudeAgentOptions(
    max_turns=20,  # Safety limit, not primary mechanism
)
# The loop still terminates naturally via stop_reason == "end_turn"
```

**Anti-Pattern 3: Checking for Text Content as Completion**
```python
# ❌ WRONG — Text presence doesn't mean completion
while True:
    response = call_claude(messages)
    if any(block.type == "text" for block in response.content):  # ❌ BAD
        return extract_text(response)
```
**Why wrong:** Claude often emits text ALONGSIDE tool calls, explaining what it's about to do. The presence of text doesn't mean Claude is done. Only `stop_reason == "end_turn"` means done.

### How Tool Results Build Context

Each loop iteration grows the conversation history:

```
Turn 1:
  messages = [
    {role: "user", content: "Check order #12345 for jane@example.com"}
  ]
  → Claude responds with tool_use: get_customer({email: "jane@example.com"})

Turn 2:
  messages = [
    {role: "user", content: "Check order #12345 for jane@example.com"},
    {role: "assistant", content: [text: "Let me look up...", tool_use: get_customer]},
    {role: "user", content: [tool_result: {customer_id: "C-12345", ...}]}
  ]
  → Claude responds with tool_use: lookup_order({order_id: "12345", customer_id: "C-12345"})

Turn 3:
  messages = [
    ... all previous messages ...,
    {role: "assistant", content: [text: "Found the customer...", tool_use: lookup_order]},
    {role: "user", content: [tool_result: {order_id: "ORD-789", total: 99.99, ...}]}
  ]
  → Claude responds with text only (stop_reason: "end_turn")
```

**Key insight:** Claude can reference ANY prior tool result because the full history is in the messages array. This is how it connects `customer_id` from `get_customer` to the `lookup_order` call.

**Context consumption warning:** Verbose tool results accumulate and consume tokens. If `lookup_order` returns 40 fields but only 5 are relevant, that's wasted context. This connects to Domain 5 (trimming tool outputs).

---

## Task Statement 1.2: Orchestrate Multi-Agent Systems

### Hub-and-Spoke Architecture

In a multi-agent system, a **coordinator agent** manages all inter-agent communication. Subagents never talk to each other directly — everything flows through the coordinator.

```
                    ┌──────────────┐
                    │  Coordinator │
                    │    Agent     │
                    └──┬───┬───┬──┘
                       │   │   │
            ┌──────────┘   │   └──────────┐
            │              │              │
            ▼              ▼              ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │ Web Search │ │  Document  │ │  Synthesis │
     │  Subagent  │ │  Analysis  │ │  Subagent  │
     │            │ │  Subagent  │ │            │
     └────────────┘ └────────────┘ └────────────┘
     Tools:         Tools:         Tools:
     - web_search   - read_doc     - verify_fact
     - fetch_url    - extract_data   (scoped)
```

### Critical Rule: Subagents Have Isolated Context

**Subagents do NOT automatically inherit the coordinator's conversation history.** They start fresh with only what you explicitly provide in their prompt.

```python
# ❌ WRONG assumption — subagent does NOT see coordinator's history
coordinator_response = call_coordinator("Research AI in healthcare")
# The search subagent does NOT know what the coordinator discussed

# ✅ CORRECT — explicitly pass context in the subagent's prompt
search_subagent_prompt = f"""
Research the following topic: AI in healthcare.

Focus areas identified by the coordinator:
1. Drug discovery applications
2. Diagnostic imaging
3. Clinical trial optimization

Return structured findings with source URLs.
"""
```

### Coordinator Responsibilities

The coordinator agent has four jobs:

1. **Task Decomposition** — Break the user's request into subtasks
2. **Delegation** — Decide which subagents to invoke (and which to skip)
3. **Result Aggregation** — Combine subagent outputs
4. **Quality Control** — Check if the combined output is complete

### The Narrow Decomposition Trap

This is directly tested in the exam (see Sample Question 7 in the exam guide).

```
User: "Research the impact of AI on creative industries"

❌ NARROW DECOMPOSITION (coordinator decomposes too narrowly):
  → Subtask 1: "AI in digital art creation"
  → Subtask 2: "AI in graphic design"
  → Subtask 3: "AI in photography"
  Result: Report covers only visual arts. Music, writing, film are missing.

✅ BROAD DECOMPOSITION:
  → Subtask 1: "AI in visual arts (digital art, graphic design, photography)"
  → Subtask 2: "AI in music (composition, production, performance)"
  → Subtask 3: "AI in writing (novels, journalism, screenwriting)"
  → Subtask 4: "AI in film/video (editing, VFX, animation)"
  Result: Comprehensive coverage.
```

**Root cause:** The coordinator's task decomposition was too narrow. The subagents executed correctly within their assigned scope — the problem is what they were assigned.

### Dynamic Subagent Selection

Good coordinators don't always invoke the full pipeline. They analyze the query and select only the needed subagents:

```
Simple query: "What is the capital of France?"
  → Skip all subagents, answer directly.

Medium query: "Summarize this PDF about climate change"
  → Invoke document_analysis subagent only.

Complex query: "Compare renewable energy policies across G7 nations"
  → Invoke web_search + document_analysis + synthesis subagents.
```

### Iterative Refinement Loops

The coordinator evaluates synthesis output for gaps and re-delegates:

```
Coordinator → search_agent("AI in healthcare")
Coordinator → analysis_agent(search_results)
Coordinator → synthesis_agent(analysis_output)

Coordinator evaluates: "The synthesis is missing clinical trial data."

Coordinator → search_agent("AI clinical trial optimization studies 2024-2025")
Coordinator → analysis_agent(new_search_results)
Coordinator → synthesis_agent(original_output + new_analysis, "Fill gap in clinical trials")

Coordinator evaluates: "Coverage is now sufficient."
→ Return final output.
```

---

## Task Statement 1.3: Configure Subagent Invocation and Context Passing

### The Agent Tool (Formerly "Task")

The `Agent` tool is how a coordinator spawns subagents. Prior to Claude Code v2.1.63, this was called the `Task` tool. The exam guide still references `Task` in some places.

**Critical requirement:** `allowedTools` must include `"Agent"` (or `"Task"`) for the coordinator to invoke subagents.

### AgentDefinition Configuration

```python
# Python Agent SDK
from claude_agent_sdk import AgentDefinition

search_agent = AgentDefinition(
    description="Searches the web for information on specified topics. "
                "Use for finding current data, news, and online sources. "
                "Returns structured findings with source URLs.",
    prompt="""You are a web research specialist. For each topic:
1. Search for recent, authoritative sources
2. Extract key findings with direct quotes
3. Return structured output:
   - claim: The finding
   - source_url: Where you found it
   - publication_date: When it was published
   - relevance_score: 1-5 rating of relevance""",
    tools=["web_search", "fetch_url"],  # Only tools this agent needs
    model="sonnet",                      # Can override model per agent
)

analysis_agent = AgentDefinition(
    description="Analyzes documents and extracts structured data. "
                "Use for processing PDFs, reports, and long-form text.",
    prompt="You are a document analysis specialist...",
    tools=["read_document", "extract_data"],
    model="sonnet",
)

# Coordinator setup — must include "Agent" in allowed tools
coordinator = ClaudeAgentOptions(
    allowed_tools=["Agent"],  # This allows the coordinator to spawn subagents
    agents=[search_agent, analysis_agent],  # Available subagents
    system_prompt="""You are a research coordinator. Analyze the user's query,
    decompose it into subtasks, and delegate to the appropriate subagents.
    Specify research goals and quality criteria, not step-by-step procedures.""",
)
```

```typescript
// TypeScript Agent SDK
import { AgentDefinition, query } from "@anthropic-ai/claude-agent-sdk";

const searchAgent: AgentDefinition = {
  description: "Searches the web for information on specified topics.",
  prompt: "You are a web research specialist...",
  tools: ["web_search", "fetch_url"],
  model: "sonnet",
};

const analysisAgent: AgentDefinition = {
  description: "Analyzes documents and extracts structured data.",
  prompt: "You are a document analysis specialist...",
  tools: ["read_document", "extract_data"],
  model: "sonnet",
};

for await (const message of query({
  prompt: "Research AI impact on healthcare",
  options: {
    allowedTools: ["Agent"],
    agents: [searchAgent, analysisAgent],
  },
})) {
  // Process messages...
}
```

### Explicit Context Passing

Since subagents don't inherit coordinator context, you must pass all necessary information in the subagent's prompt:

```python
# ✅ CORRECT — Pass complete findings from prior agents
synthesis_prompt = f"""
Synthesize these research findings into a comprehensive report.

## Web Search Findings:
{json.dumps(search_results, indent=2)}

## Document Analysis Findings:
{json.dumps(analysis_results, indent=2)}

## Requirements:
- Preserve source attribution for every claim
- Note conflicting data with both sources
- Highlight gaps in coverage
"""
```

### Structured Data for Context Passing

Separate content from metadata to preserve attribution:

```json
{
  "findings": [
    {
      "claim": "AI reduces drug discovery time by 40%",
      "evidence": "Study of 50 pharmaceutical companies...",
      "source_url": "https://nature.com/articles/...",
      "document_name": "Nature Medicine Vol 32",
      "page_number": 15,
      "publication_date": "2025-03-15"
    }
  ]
}
```

### Parallel Subagent Spawning

The coordinator can emit multiple `Agent` tool calls in a single response to run subagents concurrently:

```
Coordinator response (single turn):
  tool_use: Agent("Search for AI in drug discovery")
  tool_use: Agent("Search for AI in diagnostics")
  tool_use: Agent("Search for AI in clinical trials")

  → All three run in parallel, results return together
```

This is more efficient than sequential spawning across separate turns.

### Coordinator Prompt Design

Specify goals and quality criteria, NOT step-by-step procedures:

```python
# ❌ WRONG — Step-by-step instructions reduce adaptability
coordinator_prompt = """
Step 1: Always search for the topic first.
Step 2: Then analyze the top 5 results.
Step 3: Then synthesize into a report.
"""

# ✅ CORRECT — Goals and quality criteria enable adaptation
coordinator_prompt = """
Research the given topic comprehensively. Aim for:
- At least 5 distinct authoritative sources
- Coverage of all major subtopics (identify what these are based on the query)
- Conflicting viewpoints represented with attribution
- Recency: prioritize sources from the last 2 years

Decide which subagents to invoke based on query complexity.
Simple factual queries may not need all agents.
"""
```

### Fork-Based Session Management

`fork_session` creates independent branches from a shared analysis baseline:

```
Session: "Analyze auth module"
    │
    ├── (analysis complete — shared baseline)
    │
    ├── fork_session → Branch A: "Refactor using middleware pattern"
    │
    └── fork_session → Branch B: "Refactor using decorator pattern"

Both branches have the shared analysis but explore different approaches.
```

---

## Task Statement 1.4: Multi-Step Workflows with Enforcement

### Programmatic Enforcement vs Prompt-Based Guidance

This is THE most tested concept in Domain 1. Know it cold.

**Prompt-Based Guidance (Probabilistic):**
```python
system_prompt = """
IMPORTANT: Always verify the customer with get_customer 
before calling lookup_order or process_refund.
"""
# Problem: Claude follows this ~88% of the time. 
# 12% failure rate on critical business logic is unacceptable.
```

**Programmatic Enforcement (Deterministic):**
```python
# Using a PreToolUse hook to block unauthorized calls
verified_customer_id = None

def pre_tool_hook(tool_name, tool_input, context):
    global verified_customer_id
    
    if tool_name == "get_customer":
        return {"permissionDecision": "allow"}
    
    if tool_name in ["lookup_order", "process_refund"]:
        if verified_customer_id is None:
            return {
                "permissionDecision": "deny",
                "additionalContext": "Customer must be verified with get_customer first. "
                                     "Please call get_customer before proceeding."
            }
        return {"permissionDecision": "allow"}
    
    return {"permissionDecision": "allow"}

def post_tool_hook(tool_name, tool_result, context):
    global verified_customer_id
    if tool_name == "get_customer":
        result = json.loads(tool_result)
        verified_customer_id = result.get("customer_id")
```

### When to Use Which

| Scenario | Approach | Why |
|---|---|---|
| Identity verification before financial operations | **Programmatic (hooks)** | Errors have financial consequences |
| Preferring certain code style | Prompt-based | Style preference, not compliance |
| Blocking refunds > $500 | **Programmatic (hooks)** | Business rule requires 100% enforcement |
| Suggesting best practices | Prompt-based | Guidance, not requirement |
| PII handling before data access | **Programmatic (hooks)** | Regulatory requirement |

**Exam Rule of Thumb:** If the question mentions financial consequences, regulatory requirements, or compliance — the answer is ALWAYS programmatic enforcement (hooks), never prompt-based.

### Structured Handoff Protocols

When escalating to a human agent, compile a structured summary because the human may not have access to the conversation:

```json
{
  "handoff_summary": {
    "customer_id": "C-12345",
    "customer_name": "Jane Smith",
    "issue_type": "billing_dispute",
    "root_cause": "Double charge on order ORD-789 ($99.99 x2)",
    "actions_taken": [
      "Verified customer identity",
      "Confirmed duplicate charge in order system",
      "Attempted automated refund — blocked (exceeds $500 threshold)"
    ],
    "recommended_action": "Process manual refund of $99.99",
    "refund_amount": 99.99,
    "urgency": "high",
    "customer_sentiment": "frustrated but cooperative"
  }
}
```

### Multi-Concern Request Decomposition

When a customer has multiple issues, decompose into distinct items:

```
Customer: "I want to return order #123, and also I was charged twice for order #456"

Decomposition:
  Issue 1: Return request for order #123
    → lookup_order(#123) → process_return()
  
  Issue 2: Duplicate charge on order #456
    → lookup_order(#456) → identify duplicate → process_refund()
  
Synthesis: "I've processed your return for order #123 and initiated a refund 
of $49.99 for the duplicate charge on order #456."
```

---

## Task Statement 1.5: Agent SDK Hooks

### Hook Types and When They Fire

```
                  ┌──────────────────┐
                  │  Claude decides  │
                  │  to call a tool  │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │  PreToolUse Hook │ ◄── Intercept BEFORE execution
                  │                  │     Can: block, modify input, add context
                  └────────┬─────────┘
                           │
               ┌───────────┼───────────┐
               │ allow     │ deny      │
               ▼           ▼           │
        ┌────────────┐  ┌───────────┐  │
        │  Tool Runs │  │ Rejection │  │
        │            │  │ sent to   │  │
        └──────┬─────┘  │ Claude    │  │
               │        └───────────┘  │
               ▼                       │
        ┌──────────────────┐           │
        │ PostToolUse Hook │ ◄── Intercept AFTER execution
        │                  │     Can: transform results, add context
        └──────────────────┘
```

### PreToolUse Hook — Block Policy-Violating Actions

```python
# Python: Block refunds exceeding $500
def pre_tool_use_hook(tool_name, tool_input, tool_use_id, context):
    if tool_name == "process_refund":
        amount = tool_input.get("amount", 0)
        if amount > 500:
            return {
                "permissionDecision": "deny",
                "additionalContext": (
                    f"Refund of ${amount} exceeds the $500 automated limit. "
                    "Please escalate to a human agent using escalate_to_human "
                    "with the refund details."
                )
            }
    return {"permissionDecision": "allow"}
```

```typescript
// TypeScript: Block refunds exceeding $500
function preToolUseHook(
  toolName: string,
  toolInput: Record<string, unknown>,
  toolUseId: string,
  context: HookContext
): HookResult {
  if (toolName === "process_refund") {
    const amount = (toolInput.amount as number) ?? 0;
    if (amount > 500) {
      return {
        permissionDecision: "deny",
        additionalContext:
          `Refund of $${amount} exceeds the $500 automated limit. ` +
          "Please escalate to a human agent.",
      };
    }
  }
  return { permissionDecision: "allow" };
}
```

### PostToolUse Hook — Normalize Data Formats

```python
# Python: Normalize heterogeneous data from different MCP tools
from datetime import datetime

def post_tool_use_hook(tool_name, tool_result, tool_use_id, context):
    result = json.loads(tool_result)
    
    # Normalize Unix timestamps to ISO 8601
    if "created_at" in result and isinstance(result["created_at"], (int, float)):
        result["created_at"] = datetime.fromtimestamp(
            result["created_at"]
        ).isoformat()
    
    # Normalize numeric status codes to human-readable strings
    status_map = {1: "active", 2: "inactive", 3: "suspended"}
    if "status" in result and isinstance(result["status"], int):
        result["status"] = status_map.get(result["status"], f"unknown({result['status']})")
    
    return {"result": json.dumps(result)}
```

### Key Facts About Hooks

- **Hooks run in YOUR application process**, not inside Claude's context window
- **Hooks consume ZERO context window tokens** — they're invisible to Claude
- **PreToolUse can return:** `permissionDecision` ("allow"/"deny"/"ask"), `additionalContext`, `updatedInput`
- **PostToolUse can return:** transformed result, `additionalContext`
- A denied tool call sends a rejection message to Claude, which can then try a different approach

---

## Task Statement 1.6: Task Decomposition Strategies

### When to Use Each Pattern

**Prompt Chaining (Fixed Sequential Pipeline):**
Best for predictable, multi-aspect reviews where the steps are known in advance.

```
Code Review Pipeline:
  Step 1: Analyze each file individually (per-file local analysis)
  Step 2: Run cross-file integration pass (check data flow between files)
  Step 3: Compile findings into structured report
```

**Dynamic Adaptive Decomposition:**
Best for open-ended investigation tasks where subtasks depend on what's discovered.

```
"Add comprehensive tests to a legacy codebase"
  Step 1: Map project structure (discover what exists)
  Step 2: Identify high-impact areas (based on what Step 1 found)
  Step 3: Create prioritized test plan (adapts as dependencies emerge)
  Step 4: Implement tests for highest-priority area
  Step 5: Discover new dependencies → update plan → continue
```

### Per-File + Cross-File Pattern

For large code reviews, split into focused passes to avoid attention dilution:

```
14-file PR review:

Pass 1 (Local): Analyze each file individually
  file1.py → [finding1, finding2]
  file2.py → [finding3]
  ...
  file14.py → [finding20]

Pass 2 (Integration): Cross-file data flow analysis
  "Does file3.py correctly handle the error types defined in file1.py?"
  "Are the API contracts in file7.py consistent with file12.py's expectations?"

Result: Consistent depth per file + cross-file issue detection
```

---

## Task Statement 1.7: Session State, Resumption, and Forking

### Three Session Patterns

**1. Named Session Resumption:**
```bash
# Start a named session
claude --session-name "auth-refactor"

# Resume it later
claude --resume "auth-refactor"

# Or resume the most recent session
claude --resume
```
**Use when:** Prior context is mostly valid. Files haven't changed much.

**2. Fork Session:**
```bash
# After analysis is complete, fork to explore two approaches
# Branch A: Try middleware approach
claude --fork-session

# Branch B: Try decorator approach  
claude --fork-session
```
**Use when:** You want to explore divergent approaches from a shared baseline.

**3. Fresh Session with Injected Summaries:**
```python
# When prior tool results are stale (code changed significantly)
summary = """
Previous analysis found:
- 15 modules with circular dependency issues
- Authentication module has 3 critical vulnerabilities
- Database layer uses deprecated connection pooling

Note: modules auth.py, db.py, and utils.py were refactored overnight.
Please re-analyze these three modules specifically.
"""
# Start a new session with this summary as context
```
**Use when:** Prior tool results are stale (files modified, significant time passed).

### The /compact Command

`/compact` summarizes the conversation to reduce context usage during extended exploration sessions. The SDK auto-triggers this at ~95% context capacity.

**Use when:** Context fills with verbose discovery output during long sessions.

### Decision Framework

| Situation | Action |
|---|---|
| Resuming after minor changes | `--resume` + inform about changes |
| Exploring 2 alternative approaches | `fork_session` from shared baseline |
| Resuming after major refactoring | Fresh session + injected summary |
| Extended session filling context | `/compact` to reduce tokens |

---

## Practice Questions — Domain 1

### Question 1 (Difficulty: Medium)
Your agent implementation uses the following loop structure:
```python
while True:
    response = client.messages.create(...)
    for block in response.content:
        if block.type == "text":
            return block.text  # Return as soon as we see text
```
Users report that the agent frequently returns incomplete results, missing tool calls that should have been made. What's the root cause?

**A)** The agent needs a higher `max_tokens` to complete its response.
**B)** The loop terminates whenever Claude includes text alongside tool calls, instead of checking `stop_reason` for `"end_turn"`.
**C)** The tool definitions are too vague, causing Claude to skip them.
**D)** The conversation history isn't being passed between iterations.

**Correct Answer: B**
Claude often emits text alongside tool_use blocks (e.g., "Let me look up your order..."). This code returns as soon as it sees any text, never executing the tool calls Claude requested. The correct approach is to check `stop_reason == "end_turn"` as the termination condition.

---

### Question 2 (Difficulty: Hard)
Your multi-agent research system has a coordinator, web search subagent, document analysis subagent, and synthesis subagent. The synthesis subagent consistently produces reports missing citations from the web search results, even though the web search subagent returns them correctly. What's the most likely cause?

**A)** The synthesis subagent's model is too small to handle citation formatting.
**B)** The coordinator is not passing the web search findings to the synthesis subagent's prompt, and subagents don't inherit coordinator context automatically.
**C)** The web search subagent is returning citations in a format the synthesis subagent can't parse.
**D)** The synthesis subagent needs few-shot examples of citations to produce them.

**Correct Answer: B**
Subagents operate with isolated context — they don't automatically inherit the coordinator's conversation history. If the coordinator doesn't explicitly include the web search findings in the synthesis subagent's prompt, the synthesis agent simply doesn't have them.

---

### Question 3 (Difficulty: Hard)
Production monitoring shows that your customer support agent processes refunds without verifying customer identity in 8% of cases, despite clear system prompt instructions. The refunds occasionally go to wrong accounts. What change provides the strongest guarantee this won't happen?

**A)** Add few-shot examples showing the correct tool call sequence.
**B)** Add a PostToolUse hook that validates refund recipients after processing.
**C)** Implement a PreToolUse hook that blocks `process_refund` and `lookup_order` until `get_customer` has returned a verified customer ID.
**D)** Strengthen the system prompt with uppercase emphasis: "YOU MUST ALWAYS call get_customer FIRST."

**Correct Answer: C**
When business logic requires guaranteed compliance (identity verification before financial operations), programmatic enforcement via hooks provides deterministic guarantees. Options A and D are prompt-based approaches with non-zero failure rates — unacceptable for financial operations. Option B catches the problem after the refund is already processed, which is too late.

---

### Question 4 (Difficulty: Medium)
You're debugging a coordinator agent that always invokes all four subagents (search, analyze, synthesize, format) for every query, even simple factual questions like "What year was Python created?" What's the best improvement?

**A)** Add a query classifier that pre-determines which subagents are needed.
**B)** Design the coordinator prompt to analyze query complexity and dynamically select which subagents to invoke.
**C)** Create a fast-path that bypasses all subagents for queries under 10 words.
**D)** Reduce the number of subagents to 2 to simplify the routing decision.

**Correct Answer: B**
The coordinator should analyze query requirements and dynamically select which subagents to invoke rather than always routing through the full pipeline. This is model-driven decision-making. Options A and C are pre-configured approaches that bypass Claude's reasoning. Option D reduces capability unnecessarily.

---

### Question 5 (Difficulty: Medium)
You analyzed a large codebase yesterday using Claude Code, identifying test coverage gaps across 20 modules. Overnight, your team refactored 5 of those modules significantly and merged the changes. You need to continue the analysis this morning. What's the most reliable approach?

**A)** Resume the session with `--resume` and ask Claude to re-analyze the 5 changed modules.
**B)** Start a new session and inject a structured summary of yesterday's findings, noting which 5 modules changed.
**C)** Resume the session with `--resume` without mentioning the changes, since Claude will detect them.
**D)** Fork the session to create a branch that focuses on the 5 changed modules.

**Correct Answer: B**
Starting fresh with injected summaries is more reliable than resuming with stale tool results. The prior session's tool results (file contents, function signatures) for those 5 modules are now outdated. Option A risks Claude reasoning based on stale data. Option C is dangerous — Claude won't automatically detect external changes. Option D forks from a stale baseline.

---

## Hands-On Exercise: Build a Complete Customer Support Agent

**Objective:** Implement the full agentic loop with tools, hooks, and escalation.

### Step 1: Define 4 MCP Tools

Create tools with detailed descriptions:
- `get_customer` — Verify customer identity
- `lookup_order` — Retrieve order details (requires verified customer_id)
- `process_refund` — Issue refund (requires verified customer_id + order_id)
- `escalate_to_human` — Hand off to human with structured summary

### Step 2: Implement the Agentic Loop

Use the raw API pattern (not the SDK) to understand the mechanics:
```python
def agent_loop(user_message):
    messages = [{"role": "user", "content": user_message}]
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason == "end_turn":
            return extract_text(response)
        tool_results = execute_all_tools(response)
        messages.append({"role": "user", "content": tool_results})
```

### Step 3: Add PreToolUse Hook

Block `lookup_order` and `process_refund` until `get_customer` has been called:
```python
verified_customer = None

def pre_tool_hook(tool_name, tool_input):
    if tool_name in ["lookup_order", "process_refund"] and verified_customer is None:
        return {"permissionDecision": "deny", 
                "additionalContext": "Must verify customer first with get_customer."}
    return {"permissionDecision": "allow"}
```

### Step 4: Add PostToolUse Hook

Normalize timestamps and status codes:
```python
def post_tool_hook(tool_name, tool_result):
    result = json.loads(tool_result)
    # Normalize Unix timestamps
    for key in ["created_at", "updated_at"]:
        if key in result and isinstance(result[key], (int, float)):
            result[key] = datetime.fromtimestamp(result[key]).isoformat()
    return json.dumps(result)
```

### Step 5: Add Refund Threshold Hook

Block refunds > $500 and redirect to escalation:
```python
def pre_tool_hook(tool_name, tool_input):
    if tool_name == "process_refund":
        if tool_input.get("amount", 0) > 500:
            return {"permissionDecision": "deny",
                    "additionalContext": "Refund exceeds $500 limit. Use escalate_to_human."}
    # ... other checks
```

### Step 6: Test with Multi-Concern Message

Send: "I need to return order #123 because it arrived damaged, and I was also charged twice for order #456"

Verify the agent:
1. Calls `get_customer` first (enforced by hook)
2. Handles both issues (decomposition)
3. Calls `lookup_order` for each order
4. Processes return for #123 and refund for #456
5. Synthesizes a unified response

### Step 7: Test Without Hooks

Remove the hooks and use only prompt instructions. Run the same test 20 times and count how many times the agent skips `get_customer`. This demonstrates the difference between deterministic and probabilistic compliance.

---

## Quick Reference — Domain 1 Cheat Sheet

| Concept | Key Fact |
|---|---|
| **Agentic loop control** | Check `stop_reason`: `"tool_use"` → continue, `"end_turn"` → stop |
| **Tool results** | Appended as `user` messages with `tool_result` blocks |
| **Anti-pattern 1** | Never parse natural language for loop termination |
| **Anti-pattern 2** | Never use iteration caps as primary mechanism |
| **Anti-pattern 3** | Never check for text content as completion signal |
| **Subagent context** | Subagents do NOT inherit coordinator history |
| **Spawning subagents** | `allowedTools` must include `"Agent"` |
| **AgentDefinition** | description + prompt + tools + model |
| **Parallel subagents** | Multiple Agent tool calls in single coordinator response |
| **Hooks vs prompts** | Hooks = deterministic. Prompts = probabilistic. |
| **PreToolUse** | Block/modify BEFORE execution |
| **PostToolUse** | Transform/normalize AFTER execution |
| **Hooks and tokens** | Hooks consume ZERO context window tokens |
| **Financial/compliance** | ALWAYS use hooks, never prompt-only |
| **Narrow decomposition** | Coordinator splits topic too narrowly → gaps in coverage |
| **Prompt chaining** | Fixed sequential steps (code review passes) |
| **Dynamic decomposition** | Adaptive steps based on discoveries |
| **--resume** | Continue named session (when context mostly valid) |
| **fork_session** | Parallel branches from shared baseline |
| **Fresh + summary** | More reliable when prior tool results are stale |
| **max_turns** | Safety net, not primary stopping mechanism |
| **/compact** | Reduce context during long sessions |
