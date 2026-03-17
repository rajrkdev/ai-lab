# Claude Certified Architect – Foundations: Master Study Guide

## Exam Quick Facts
- **Format:** 60 multiple-choice questions (4 random scenarios from pool of 6)
- **Passing Score:** 720/1000
- **Question Type:** One correct answer, three distractors (plausible wrong answers)
- **No penalty for guessing** — never leave a question blank

## Domain Weights
| Domain | Weight | Your Focus Level |
|---|---|---|
| D1: Agentic Architecture & Orchestration | **27%** | ~16 questions — HIGHEST PRIORITY |
| D2: Tool Design & MCP Integration | 18% | ~11 questions |
| D3: Claude Code Configuration & Workflows | 20% | ~12 questions |
| D4: Prompt Engineering & Structured Output | 20% | ~12 questions |
| D5: Context Management & Reliability | 15% | ~9 questions |

---

## THE 20 RULES THAT COVER 80% OF THE EXAM

### Rule 1: stop_reason Controls the Loop
The agentic loop continues when `stop_reason == "tool_use"` and terminates when `stop_reason == "end_turn"`. Never parse natural language, use iteration caps as primary mechanism, or check for text content.

### Rule 2: Hooks = Deterministic. Prompts = Probabilistic.
When financial/compliance consequences exist, ALWAYS choose programmatic hooks over prompt instructions. PreToolUse blocks bad calls. PostToolUse normalizes results.

### Rule 3: Subagents Don't Inherit Context
Subagents start fresh. You MUST explicitly pass all needed information in their prompt. This is the root cause of many exam scenario failures.

### Rule 4: Tool Descriptions Are the #1 Selection Mechanism
Minimal descriptions → misrouting. The first fix is always to expand descriptions, not add few-shot examples or build routing layers.

### Rule 5: 4-5 Tools Per Agent, Not 18
Too many tools degrades selection. Distribute tools across specialized subagents.

### Rule 6: isError Distinguishes Failures from Empty Results
Timeout = `isError: true`. No matches found = `isError: false`. Never suppress errors as success.

### Rule 7: tool_choice Controls Structured Output
`"auto"` = optional. `"any"` = must use a tool (guarantees structured output). `forced` = must use specific tool.

### Rule 8: tool_use Eliminates Syntax Errors, Not Semantic Errors
JSON schemas prevent malformed JSON. They can't catch "line items don't sum to total."

### Rule 9: CLAUDE.md Hierarchy: User < Project < Directory
User-level (`~/.claude/CLAUDE.md`) is NOT shared via version control. This is the #1 misconfiguration.

### Rule 10: .claude/rules/ with Glob Patterns for Cross-Codebase Conventions
`paths: ["**/*.test.*"]` applies to all test files regardless of directory. Better than directory CLAUDE.md for scattered files.

### Rule 11: -p Flag for CI/CD
`claude -p "prompt"` runs non-interactively. `--output-format json` + `--json-schema` for structured CI output.

### Rule 12: Independent Review Instance > Same-Session Self-Review
The same session that generated code is biased when reviewing it. Use a fresh session.

### Rule 13: Explicit Criteria > Vague Instructions
"Flag only when claimed behavior contradicts actual code" beats "check comments are accurate." "Be conservative" doesn't improve precision.

### Rule 14: Few-Shot Examples Enable Generalization
2-4 targeted examples for ambiguous cases. The model generalizes to novel patterns, not just matching shown cases.

### Rule 15: Nullable Fields Prevent Fabrication
Make fields optional when source documents may not contain the info. Claude will return null instead of inventing values.

### Rule 16: Batch API = 50% Savings, 24hr Window, No Multi-Turn
Use for overnight reports. NOT for blocking pre-merge checks. custom_id correlates results.

### Rule 17: Extract "Case Facts" to Prevent Summarization Loss
Amounts, dates, order numbers go in a persistent block OUTSIDE summarized history.

### Rule 18: Escalate When Customer Requests Human — Immediately
Don't attempt investigation first. Honor the explicit request.

### Rule 19: Narrow Coordinator Decomposition → Coverage Gaps
If the final report misses topics, check the coordinator's task decomposition first.

### Rule 20: Per-File + Cross-File Review for Large PRs
Split into local analysis passes + integration pass to avoid attention dilution.

---

## DISTRACTOR PATTERNS (Wrong Answer Signals)

When you see these in answer options, they're likely wrong:

| Pattern | Why It's Wrong |
|---|---|
| "Add to system prompt that X is mandatory" | Probabilistic, not deterministic |
| "Deploy a classifier model" | Over-engineered when prompt fixes haven't been tried |
| "Sentiment-based escalation" | Sentiment ≠ complexity |
| "Self-reported confidence threshold" | LLM confidence is poorly calibrated |
| "Consolidate tools into one" | Hides the real problem (poor descriptions) |
| "Larger context window" | Doesn't fix attention quality issues |
| "Run 3 passes and require consensus" | Suppresses intermittent but real findings |
| "Routing layer that parses input" | Bypasses Claude's natural language understanding |
| `CLAUDE_HEADLESS=true` | Doesn't exist. Use `-p` flag. |
| `--batch` flag | Doesn't exist. Use `-p` flag. |

---

## EXAM STRATEGY

### Reading Scenarios
Read the scenario description carefully before any questions. Key details (tool names, target metrics, architecture choices) eliminate wrong answers.

### "Most Effective First Step" Questions
These always point to the lowest-effort, highest-leverage fix. Not the most comprehensive solution.

### Elimination Strategy
1. Eliminate over-engineered options (ML classifiers, separate models)
2. Eliminate prompt-only fixes for compliance/financial scenarios
3. Eliminate options that blame downstream agents when coordinator is the issue
4. Pick the remaining option that addresses the root cause

### Time Management
~60 questions in the exam period. If stuck, eliminate what you can, pick best remaining, move on. No penalty for guessing.

---

## KEY TECHNOLOGIES REFERENCE

| Technology | Key Commands/Concepts |
|---|---|
| **Agent SDK** | `query()`, `AgentDefinition`, `allowedTools`, `ResultMessage.subtype` |
| **Hooks** | `PreToolUse` (block/modify), `PostToolUse` (normalize), `permissionDecision` |
| **MCP** | `isError`, `.mcp.json`, `${VAR}`, resources, tools |
| **Claude Code** | `CLAUDE.md`, `.claude/rules/`, `.claude/skills/`, `/memory`, `/compact` |
| **Claude Code CLI** | `-p`, `--output-format json`, `--json-schema`, `--resume`, `fork_session` |
| **Claude API** | `tool_use`, `tool_choice`, `stop_reason`, `system`, `max_tokens` |
| **Batch API** | 50% savings, 24hr window, `custom_id`, no multi-turn tools |
| **Built-in Tools** | Grep (content search), Glob (file patterns), Read/Write/Edit, Bash |
