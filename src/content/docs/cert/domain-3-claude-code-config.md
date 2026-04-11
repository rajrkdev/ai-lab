---
title: "Domain 3: Claude Code Config & Workflows"
description: "20% of the exam. Covers CLAUDE.md hierarchy, .claude/rules/, skills, slash commands, plan mode, and CI/CD integration."
sidebar:
  order: 3
---

# Domain 3: Claude Code Configuration & Workflows

## Weight: 20% (~12 questions)

**Appears in Scenarios:** 2 (Code Generation), 4 (Developer Productivity), 5 (CI/CD)

---

## What This Domain Tests

- Understand the 3-level CLAUDE.md precedence hierarchy
- Configure path-specific rules with glob patterns
- Build skills with correct SKILL.md frontmatter
- Choose between plan mode vs. direct execution
- Integrate Claude Code into CI/CD pipelines with the `-p` flag

---

## Task Statement 3.1: CLAUDE.md Configuration Hierarchy

### The Three Levels of Configuration

Configuration is loaded from multiple CLAUDE.md files and merged. Later (more specific) files override earlier (less specific) ones.

```
CONFIGURATION LOADING ORDER:
(Each level overrides the one above it)

┌─────────────────────────────────────────────────────────────────┐
│  LEVEL 1: User-Level  (LOWEST PRECEDENCE)                       │
│                                                                 │
│  ~/.claude/CLAUDE.md                                            │
│                                                                 │
│  • Personal preferences for YOU only                            │
│  • NOT shared via version control                               │
│  • A new team member joining WILL NOT have this file            │
│  • Examples: "Use dark mode", "Prefer verbose logging"          │
└────────────────────────────────┬────────────────────────────────┘
                                 │ overridden by ▼
┌─────────────────────────────────────────────────────────────────┐
│  LEVEL 2: Project-Level                                         │
│                                                                 │
│  .claude/CLAUDE.md  OR  ./CLAUDE.md (project root)             │
│                                                                 │
│  • Team standards shared via version control                    │
│  • Applies to ALL team members who check out the repo           │
│  • Examples: "Use TypeScript strict mode", coding conventions   │
└────────────────────────────────┬────────────────────────────────┘
                                 │ overridden by ▼
┌─────────────────────────────────────────────────────────────────┐
│  LEVEL 3: Directory-Level  (HIGHEST PRECEDENCE)                 │
│                                                                 │
│  ./subdirectory/CLAUDE.md                                       │
│                                                                 │
│  • Applied when editing files IN this directory                 │
│  • Area-specific rules (e.g., API conventions, test conventions)│
│  • Examples: "All API endpoints must validate with Zod"         │
└─────────────────────────────────────────────────────────────────┘
```

### The #1 Exam Trap: User-Level Config Not Shared

```
SCENARIO: A new team member joins. Claude Code doesn't follow 
          team coding standards. You confirm standards are defined.

WRONG DIAGNOSIS: Network issue, outdated Claude Code version

CORRECT DIAGNOSIS:
  Standards are in ~/.claude/CLAUDE.md (user-level)
  This file lives on YOUR machine ONLY
  New team members have EMPTY user-level config
  
FIX: Move standards to .claude/CLAUDE.md (project-level)
     Now it's version-controlled and shared with everyone
```

### The @import Syntax — Modular Config

Keep CLAUDE.md files modular by importing shared rule files:

```markdown
# CLAUDE.md (project root)

## Universal Standards
- Use TypeScript strict mode
- All functions must have JSDoc comments

## Package-Specific Standards
@docs/api-standards.md
@docs/testing-standards.md
```

Each package imports only what it needs:

```markdown
# packages/api/CLAUDE.md
@../../docs/api-standards.md
@../../docs/error-handling.md

# packages/frontend/CLAUDE.md
@../../docs/react-standards.md
@../../docs/accessibility.md
```

### CLAUDE.local.md — Personal Overrides

For local preferences that should NOT be committed:

```markdown
# .claude/CLAUDE.local.md  ← gitignored (never committed)

# Personal development overrides
- Use verbose logging mode during development
- Run tests with --watch flag
- Open dev server at port 4321 instead of 3000
```

### Diagnosing Config Issues with /memory

```
> /memory

Loaded CLAUDE.md files:
  ~/.claude/CLAUDE.md (user)
  .claude/CLAUDE.md (project)
  src/api/CLAUDE.md (directory)

Loaded rules:
  .claude/rules/testing.md (global)
  .claude/rules/api-conventions.md (paths: src/api/**)
  .claude/rules/terraform.md (paths: terraform/**)
```

Use `/memory` when Claude isn't following expected rules — verify which config files are actually loaded.

---

## Task Statement 3.2: The .claude/rules/ Directory

### Why Rules Files Beat Directory CLAUDE.md for Scattered Files

Test files are spread throughout the codebase:

```
src/
  components/
    Button.tsx
    Button.test.tsx       ← Needs testing rules
    Modal.tsx
    Modal.test.tsx        ← Needs testing rules
  api/
    users.ts
    users.test.ts         ← Needs testing rules
  utils/
    format.ts
    format.test.ts        ← Needs testing rules
```

**Problem with directory CLAUDE.md:** You'd need a CLAUDE.md in every single directory. Doesn't scale.

**Solution with path-specific rules:** One file, one glob pattern, applies everywhere:

```
.claude/
  rules/
    testing.md          ← paths: ["**/*.test.*"] — applies to ALL test files
    api-conventions.md  ← paths: ["src/api/**/*"] — applies to all API files
    terraform.md        ← paths: ["terraform/**/*", "**/*.tf"]
    security.md         ← No paths field → applies GLOBALLY
```

### Rules File Structure

```yaml
# .claude/rules/testing.md
---
paths:
  - "**/*.test.ts"
  - "**/*.test.tsx"
  - "**/*.spec.ts"
  - "**/*.spec.tsx"
---

# Testing Conventions

Rules applied ONLY when editing test files:
- Use `describe`/`it` blocks with descriptive names
- Each test file must have at least one integration test
- Mock external services — never call real APIs in tests
- Use factory functions for test data (not inline object literals)
- Assert both success paths AND error paths
- Minimum coverage: 80% for new code
```

```yaml
# .claude/rules/api.md
---
paths:
  - "src/api/**/*"
  - "src/routes/**/*"
---

# API Conventions

- All endpoints validate input with Zod schemas
- Return consistent error format: {error: string, code: number, details?: object}
- Use middleware for authentication (never inline auth logic)
- Rate limit all public endpoints
- Never expose internal error stack traces to clients
```

```yaml
# .claude/rules/general.md
# No paths field → applies to ALL files globally

# General Standards
- Use meaningful variable names (not x, temp, data)
- Keep functions under 30 lines
- Add comments for non-obvious logic only
- Prefer const over let; avoid var
```

### Rules Loading Flow

```
User edits: src/api/users.test.ts
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Claude Code checks all rules files:                    │
│                                                         │
│  general.md  → no paths → LOAD (global)                 │
│  testing.md  → paths: ["**/*.test.*"]                   │
│                matches src/api/users.test.ts? YES → LOAD│
│  api.md      → paths: ["src/api/**/*"]                  │
│                matches src/api/users.test.ts? YES → LOAD│
│  terraform.md→ paths: ["terraform/**/*"]                │
│                matches src/api/users.test.ts? NO → SKIP │
│                                                         │
│  Active rules: general + testing + api                  │
└─────────────────────────────────────────────────────────┘
```

---

## Task Statement 3.3: Custom Slash Commands and Skills

### Slash Commands

**Project-scoped** (`.claude/commands/`) — shared via version control:

```markdown
# .claude/commands/review.md
Review the current changes against our team's code review checklist:

1. Check for proper error handling on all async operations
2. Verify all public functions have JSDoc documentation
3. Ensure test coverage for every new code path
4. Check for SQL injection, XSS, and data leak risks
5. Verify naming conventions follow our standards

Focus on: $ARGUMENTS
```

Usage: `/review the auth module changes`

**User-scoped** (`~/.claude/commands/`) — personal, not shared:

```markdown
# ~/.claude/commands/debug.md
Enter debug mode for the file I'm currently editing.
Add verbose console.log statements at every function entry/exit.
Use --watch mode and show stack traces for any errors.
```

### Skills — The Recommended System

Skills live in `.claude/skills/` with a required `SKILL.md` file:

```
.claude/
  skills/
    analyze-codebase/
      SKILL.md          ← Required — contains frontmatter + instructions
      templates/        ← Optional supporting files
      examples/
    generate-tests/
      SKILL.md
    security-audit/
      SKILL.md
```

### SKILL.md Frontmatter — Complete Reference

```yaml
---
name: analyze-codebase         # Becomes the slash command: /analyze-codebase
description: "Performs deep analysis of codebase structure, dependencies, and patterns.
              Use when asked to understand how a module works or trace a data flow."
context: fork                  # Run in isolated subagent context (see below)
allowed-tools:                 # Restrict tools during skill execution
  - Read
  - Grep
  - Glob
argument-hint: "module or directory to analyze"   # Prompted at invocation
agent: Explore                 # Use the Explore subagent (read-only, optimized)
---

# Codebase Analysis Skill

When invoked, analyze the specified area:

1. Map the directory structure with Glob
2. Identify key entry points and exports with Grep
3. Trace dependency chains
4. Report patterns and potential issues

## Output Format
Return a structured report with:
- Architecture overview
- Dependency graph
- Identified patterns (good and bad)
- Recommended improvements
```

### Frontmatter Options Explained

| Option | Purpose | When to Use |
|---|---|---|
| `name` | Slash command name (`/name`) | Always required |
| `description` | When Claude auto-invokes this skill | Make it specific — Claude reads this |
| `context: fork` | Run in isolated subagent context | Skills with verbose output (prevents polluting main context) |
| `allowed-tools` | Restrict available tools | Read-only analysis skills, security constraints |
| `argument-hint` | Prompt for required parameters | When skill needs specific input |
| `agent: Explore` | Use the Explore subagent | Read-only codebase exploration |
| `agent: Plan` | Use the Plan subagent | Architectural planning tasks |

### context: fork — Why It Matters

```
WITHOUT context: fork:
  Main session asks: "Analyze the auth module"
  ┌─────────────────────────────────────────────────────┐
  │ Skill runs inside main session context              │
  │ Outputs: 5,000 tokens of analysis, file listings,  │
  │ grep results, dependency maps...                    │
  │ ALL 5,000 tokens remain in main conversation        │
  │ Context window fills → subsequent work degrades     │
  └─────────────────────────────────────────────────────┘

WITH context: fork:
  Main session asks: "Analyze the auth module"
  ┌─────────────────────────────────────────────────────┐
  │ Skill runs in ISOLATED SUBAGENT                     │
  │ Subagent generates 5,000 tokens of analysis         │
  │ (all inside its own context, invisible to main)     │
  │                                                     │
  │ Only the SUMMARY returns to main session (~200 tok) │
  │ Main context stays clean → no degradation           │
  └─────────────────────────────────────────────────────┘
```

### Skills vs. CLAUDE.md — When to Use Each

| | Skills | CLAUDE.md |
|---|---|---|
| **Loading** | On-demand (user invokes or Claude decides) | Always loaded automatically |
| **Best for** | Task-specific workflows, complex operations | Universal standards, always-apply rules |
| **Context** | Isolated with `context: fork` | Always in main context |
| **Examples** | "Analyze codebase", "Generate tests", "Security audit" | "Use TypeScript strict", "Follow PEP 8" |
| **Team sharing** | `.claude/skills/` via version control | `.claude/CLAUDE.md` via version control |
| **Personal variants** | `~/.claude/skills/` | `~/.claude/CLAUDE.md` |

---

## Task Statement 3.4: Plan Mode vs. Direct Execution

### Decision Flow — Which Mode?

```
New task arrives
       │
       ▼
Is the scope clear and contained to 1–2 files?
       │
  YES  │  NO
       │
       ▼  ▼
  Use direct    Are there multiple valid approaches
  execution     with different architectural tradeoffs?
                       │
                  YES  │  NO
                       │
                       ▼  ▼
                  Use Plan    Is it a multi-file change
                  Mode        affecting 10+ files?
                                    │
                               YES  │  NO
                                    │
                                    ▼  ▼
                               Use Plan   Judgment call:
                               Mode       consider Plan Mode
```

### Plan Mode — Use For

```
✅ USE PLAN MODE WHEN:
  • Microservice restructuring
  • Library migrations affecting 10+ files
  • Choosing between integration approaches with different infrastructure requirements
  • Any task with significant architectural implications
  • Multiple valid approaches where you need to evaluate tradeoffs
  • Before making changes that would be hard to undo

HOW TO ACTIVATE:
  Shift+Tab (keyboard toggle in interactive mode)
  /plan command
  --permission-mode plan (CLI flag for scripting)
```

### Direct Execution — Use For

```
✅ USE DIRECT EXECUTION WHEN:
  • Single-file bug fix with a clear stack trace
  • Adding one validation conditional
  • Renaming a variable across a single file
  • Well-understood changes with clear, limited scope
  • Quick, low-risk changes where planning overhead isn't worth it
```

### The Explore Subagent — Read-Only Discovery

```
BUILT-IN EXPLORE SUBAGENT:
  • Read-only: can only read files, search content, list directories
  • Optimized for codebase exploration
  • Returns concise summaries (not raw file contents)
  • Perfect for: "What does this module do?" before making changes

USE IN SKILLS:
  agent: Explore
  context: fork
  allowed-tools:
    - Read
    - Grep
    - Glob

WHY USE IT:
  Isolates verbose discovery output from main conversation
  Main session only sees the summary
  Keeps context clean for the actual implementation work
```

### Combining Plan Mode + Direct Execution

```
PHASE 1 — Plan Mode (understanding and design):
  "Analyze our auth module and propose a migration from JWT to OAuth2"
  ↓
  Claude explores codebase (read-only)
  Identifies all JWT usage across files
  Produces migration plan with 3 approaches
  You review and choose Approach B (requires only 5 files changed)

PHASE 2 — Direct Execution (implementation):
  "Implement Approach B from the migration plan"
  ↓
  Claude modifies the agreed 5 files
  Follows the approved plan exactly
  No exploratory reads wasting context
```

---

## Task Statement 3.5: Iterative Refinement Techniques

### Input/Output Examples — Most Effective for Transformation Tasks

When prose instructions produce inconsistent results, provide concrete before/after examples:

```
❌ VAGUE:
  "Convert the dates to be consistent across the codebase"

✅ CONCRETE EXAMPLES:
  Transform input dates to ISO 8601 (YYYY-MM-DD):
  
  Input: "Jan 5, 2025"       → Output: "2025-01-05"
  Input: "5/1/25"            → Output: "2025-01-05"
  Input: "2025-01-05"        → Output: "2025-01-05"  (already correct, unchanged)
  Input: "January 5th, 2025" → Output: "2025-01-05"
  Input: "invalid"           → Raise ValueError("Cannot parse date: 'invalid'")
  Input: ""                  → Raise ValueError("Empty date string")
```

### Test-Driven Iteration

```
STEP 1: Write test suite first
  test_parse_date("Jan 5, 2025")   → "2025-01-05"
  test_parse_date("invalid")       → raises ValueError
  test_parse_date("")              → raises ValueError
  test_parse_date("2025-13-40")    → raises ValueError  ← tricky edge case

STEP 2: Ask Claude to implement
  "Implement parse_date() to pass all these tests"

STEP 3: Run tests, share failures precisely
  "Tests pass except test_parse_date('2025-13-40') —
   it returns '2025-13-40' instead of raising ValueError"

STEP 4: Claude fixes the edge case with full context
```

### The Interview Pattern

Have Claude clarify requirements before implementing — avoids wasted work:

```
You: "Build a caching layer for our API"

Claude (interviews): "Before I implement, I have a few questions:
  1. Expected cache hit ratio? (~80% affects eviction strategy choice)
  2. Must cache survive service restarts? (in-memory vs Redis/Memcached)
  3. How handle cache invalidation for write operations? (write-through vs TTL)
  4. Maximum acceptable staleness for cached data? (affects TTL value)"

You: "80%, must survive restarts, write-through, 30-second max staleness"

Claude: "Got it. I'll implement a Redis-backed write-through cache with 30s TTL..."
```

### Batch vs. Sequential Issue Reporting

```
BATCH (send together) when issues INTERACT:
  "Three interacting issues — fix as a unit:
   1. Error handler catches all exceptions (too broad)
   2. Retry logic doesn't respect error handler's categories
   3. Logging doesn't include error category
   These are coupled — fixing #1 changes what #2 and #3 handle."

SEQUENTIAL (send one at a time) when issues are INDEPENDENT:
  Message 1: "Fix the date parsing in utils.py"
  (Review and verify the fix)
  Message 2: "Add rate limiting to the API endpoints"
  (These are independent — no risk of interaction)
```

---

## Task Statement 3.6: CI/CD Integration

### The -p Flag — Critical Exam Fact

```
❌ WRONG (hangs in CI — waits for interactive input):
  claude "Review this PR for security issues"

✅ CORRECT (runs non-interactively):
  claude -p "Review this PR for security issues"

❌ THESE DO NOT EXIST:
  CLAUDE_HEADLESS=true   ← Not a real env var
  --batch                ← Not a real flag
  claude --headless      ← Not a real flag
```

### Full CI Command with Structured Output

```bash
# CI pipeline script
claude -p "Review the changes in this PR for security and correctness" \
  --output-format json \
  --json-schema '{
    "type": "object",
    "properties": {
      "findings": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "file":       {"type": "string"},
            "line":       {"type": "integer"},
            "severity":   {"type": "string", "enum": ["critical", "warning", "info"]},
            "issue":      {"type": "string"},
            "suggestion": {"type": "string"}
          },
          "required": ["file", "severity", "issue"]
        }
      },
      "summary": {"type": "string"},
      "approved": {"type": "boolean"}
    }
  }'
```

### CI/CD Pipeline Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    CI/CD CLAUDE CODE PIPELINE                    │
│                                                                  │
│  PR opened/updated                                               │
│        │                                                         │
│        ▼                                                         │
│  ┌─────────────────────────────────┐                            │
│  │ Session 1: Code Generation      │ ← Generates implementation  │
│  │ claude -p "Implement feature X" │                            │
│  └─────────────────────────────────┘                            │
│        │                                                         │
│        │ Output: code files                                      │
│        ▼                                                         │
│  ┌─────────────────────────────────┐                            │
│  │ Session 2: PR Review            │ ← INDEPENDENT session       │
│  │ claude -p "Review these changes │   No prior reasoning context│
│  │   for security issues"          │   (fresh perspective)       │
│  │ --output-format json            │                            │
│  └─────────────────────────────────┘                            │
│        │                                                         │
│        │ Output: JSON findings                                   │
│        ▼                                                         │
│  ┌─────────────────────────────────┐                            │
│  │ Parse JSON                      │                            │
│  │ Post findings as PR comments     │                            │
│  │ Fail build if severity=critical  │                            │
│  └─────────────────────────────────┘                            │
└──────────────────────────────────────────────────────────────────┘
```

### Session Context Isolation for Review

```python
# ❌ SAME SESSION generates and reviews
# Claude retains reasoning context — less likely to question own decisions

# Session 1: Generate
subprocess.run(["claude", "-p", "Write auth middleware"], capture_output=True)

# Session 2: Review (SAME session — biased)
subprocess.run(["claude", "-p", "Review the middleware you just wrote"], capture_output=True)
# ↑ Claude remembers WHY it made each decision → confirmation bias

# ✅ INDEPENDENT SESSIONS for generation and review

# Session 1: Generate
result = subprocess.run(
    ["claude", "-p", "Write auth middleware"],
    capture_output=True
)
with open("middleware.ts", "w") as f:
    f.write(result.stdout)

# Session 2: Review (completely fresh — no prior reasoning)
review = subprocess.run(
    ["claude", "-p", f"Review middleware.ts for security issues:\n{open('middleware.ts').read()}"],
    capture_output=True
)
```

### Avoiding Duplicate PR Comments

When re-running reviews after new commits:

```bash
# Include prior findings so Claude only reports NEW or still-unaddressed issues
claude -p "Review this PR.

Previous review findings (already addressed or tracked):
$(cat previous_findings.json)

Report ONLY:
1. New issues introduced since the previous review
2. Previously reported issues that remain unaddressed

Do NOT re-report issues that have been fixed." \
  --output-format json
```

### CLAUDE.md for CI Context

Provide Claude with CI-specific context via CLAUDE.md:

```markdown
# CLAUDE.md

## CI/CD Review Standards

### Testing
- Use Jest with React Testing Library
- Available fixtures: testUser, testOrder, testProduct in tests/fixtures/
- Prefer integration tests over unit tests for API routes
- Mock external services with nock
- Minimum coverage: 80% for new code

### Review Criteria
Report these (and ONLY these):
- Bugs: Logic errors, race conditions, memory leaks
- Security: SQL injection, XSS, exposed credentials, data leaks
- Correctness: Wrong return types, missing error handling

Do NOT report:
- Minor style preferences
- Local naming patterns
- Import ordering

### Severity Levels
- critical: Blocks merge. Security issues, data corruption, crashes.
- warning: Should fix before merge.
- info: Nice to have.
```

---

## Practice Questions — Domain 3

### Question 1
A new team member reports Claude Code doesn't follow team coding conventions. You verify the conventions are defined. Where should you look first?

**A)** Check if conventions are in `~/.claude/CLAUDE.md` instead of `.claude/CLAUDE.md`  
**B)** Check if the new member's Claude Code version is outdated  
**C)** Check if `.claude/rules/` glob patterns are incorrect  
**D)** Check if `@import` syntax isn't supported on the new member's OS  

**Correct Answer: A**  
`~/.claude/CLAUDE.md` (user-level) is NOT version-controlled. It lives on YOUR machine only — new team members don't have it. Moving to `.claude/CLAUDE.md` makes it project-scoped and shared with everyone.

---

### Question 2
Your CI pipeline runs `claude "Analyze this PR"` but hangs indefinitely. What's the fix?

**A)** `claude -p "Analyze this PR"`  
**B)** `CLAUDE_HEADLESS=true claude "Analyze this PR"`  
**C)** `claude "Analyze this PR" < /dev/null`  
**D)** `claude --batch "Analyze this PR"`  

**Correct Answer: A**  
The `-p` (or `--print`) flag runs Claude Code in non-interactive mode. B, C, and D all reference either non-existent flags/env vars or Unix workarounds that don't fix the root cause. `-p` is the correct and only answer.

---

### Question 3
Your codebase has test files spread throughout (`Button.test.tsx` next to `Button.tsx`). You want uniform testing conventions regardless of directory location. Most maintainable approach?

**A)** Create `.claude/rules/testing.md` with `paths: ["**/*.test.*"]`  
**B)** Put all conventions in root CLAUDE.md and let Claude infer which apply  
**C)** Create a skill that enforces conventions when invoked  
**D)** Place CLAUDE.md in every subdirectory  

**Correct Answer: A**  
Glob patterns in `.claude/rules/` apply to matching files anywhere in the codebase. B relies on Claude's inference (unreliable). C requires manual invocation — conventions won't apply automatically. D doesn't scale for files scattered across many directories.

---

## Quick Reference — Domain 3 Cheat Sheet

| Concept | Key Fact |
|---|---|
| **User-level config** | `~/.claude/CLAUDE.md` — NOT version-controlled, not shared |
| **Project-level config** | `.claude/CLAUDE.md` or root `CLAUDE.md` — shared via git |
| **Directory-level** | Subdirectory CLAUDE.md — highest precedence |
| **Precedence order** | user < project < directory |
| **@import** | References external files for modular config |
| **CLAUDE.local.md** | Personal overrides — gitignored, never committed |
| **/memory** | Verify which config files are loaded |
| **.claude/rules/** | Topic-specific rules with optional path-scoping |
| **paths: frontmatter** | YAML field for glob pattern activation |
| **Global rules** | Rules file without `paths` field → applies everywhere |
| **Glob patterns** | Better than directory CLAUDE.md for scattered files (e.g., test files) |
| **Project commands** | `.claude/commands/` — shared via version control |
| **Personal commands** | `~/.claude/commands/` — not shared |
| **Skills** | `.claude/skills/SKILL-NAME/SKILL.md` |
| **Skills: name** | Becomes the slash command name |
| **Skills: description** | What Claude reads to auto-invoke |
| **context: fork** | Isolates skill output from main conversation |
| **allowed-tools** | Restrict tools during skill execution |
| **argument-hint** | Prompts for required parameters at invocation |
| **agent: Explore** | Read-only subagent for codebase exploration |
| **Plan mode** | Complex multi-file tasks, architectural decisions |
| **Direct execution** | Simple, well-scoped, single-file changes |
| **-p flag** | Non-interactive mode for CI/CD — the correct answer |
| **CLAUDE_HEADLESS** | Does NOT exist — wrong answer |
| **--batch** | Does NOT exist — wrong answer |
| **--output-format json** | Machine-parseable output for CI |
| **--json-schema** | Enforce output schema structure |
| **Session isolation** | Independent review session > same-session self-review |
| **Prior findings** | Include in context to avoid duplicate PR comments |
| **Interview pattern** | Claude asks questions before implementing |
| **Input/output examples** | Most effective for transformation tasks |
