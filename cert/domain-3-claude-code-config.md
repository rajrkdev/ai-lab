---
layout: default
title: "Domain 3: Claude Code Config"
---

# Domain 3: Claude Code Configuration & Workflows

## Weight: 20% of Exam

**Appears in Scenarios:** 2 (Code Generation), 4 (Developer Productivity), 5 (CI/CD)

---

## Task Statement 3.1: CLAUDE.md Configuration Hierarchy

### The Three Levels

Claude Code loads configuration from multiple CLAUDE.md files, combining them with increasing specificity:

```
LOWEST PRECEDENCE (applied first):
┌───────────────────────────────────────────┐
│ ~/.claude/CLAUDE.md                       │
│ User-level: personal preferences          │
│ NOT shared via version control             │
│ Only applies to YOU                       │
└───────────────────┬───────────────────────┘
                    │ overridden by ▼
┌───────────────────────────────────────────┐
│ .claude/CLAUDE.md  OR  ./CLAUDE.md        │
│ Project-level: team standards             │
│ Shared via version control                │
│ Applies to ALL team members               │
└───────────────────┬───────────────────────┘
                    │ overridden by ▼
┌───────────────────────────────────────────┐
│ ./subdirectory/CLAUDE.md                  │
│ Directory-level: area-specific rules      │
│ Applied when editing files in this dir    │
└───────────────────────────────────────────┘
HIGHEST PRECEDENCE (applied last)
```

### Common Exam Trap: User-Level Config Not Shared

**Scenario:** A new team member joins and reports that Claude Code isn't following your team's coding standards. You check and confirm the standards are defined. Where's the problem?

**Answer:** The standards are in `~/.claude/CLAUDE.md` (user-level), which is NOT shared via version control. The new team member doesn't have this file. **Fix:** Move the standards to `.claude/CLAUDE.md` (project-level).

### The @import Syntax

Keep CLAUDE.md modular by importing external files:

```markdown
# CLAUDE.md (project root)

## Universal Standards
- Use TypeScript strict mode
- All functions must have JSDoc comments

## Package-Specific Standards
@docs/api-standards.md
@docs/testing-standards.md
```

Each package can import only the standards relevant to it:

```markdown
# packages/api/CLAUDE.md
@../../docs/api-standards.md
@../../docs/error-handling.md

# packages/frontend/CLAUDE.md  
@../../docs/react-standards.md
@../../docs/accessibility.md
```

### The .claude/rules/ Directory

An alternative to a monolithic CLAUDE.md — organize topic-specific rule files:

```
.claude/
  rules/
    testing.md          ← Testing conventions
    api-conventions.md  ← API design rules
    deployment.md       ← Deployment procedures
    security.md         ← Security requirements
```

All `.md` files in `.claude/rules/` are discovered recursively. Rules without path restrictions apply globally.

### The /memory Command

Use `/memory` to verify which memory files are loaded and diagnose inconsistent behavior:

```
> /memory
Loaded CLAUDE.md files:
  ~/.claude/CLAUDE.md (user)
  .claude/CLAUDE.md (project)
  src/api/CLAUDE.md (directory)
  
Loaded rules:
  .claude/rules/testing.md (global)
  .claude/rules/api-conventions.md (paths: src/api/**)
```

### CLAUDE.local.md

For personal overrides that shouldn't be committed:

```
# .claude/CLAUDE.local.md (gitignored)
# Personal preferences that override project settings
- Use verbose logging during development
- Run tests with --watch flag
```

---

## Task Statement 3.2: Custom Slash Commands and Skills

### Slash Commands

**Project-scoped** (`.claude/commands/`) — shared via version control:
```markdown
# .claude/commands/review.md
Review the current changes against our team's code review checklist:

1. Check for proper error handling
2. Verify all public functions have documentation
3. Ensure test coverage for new code paths
4. Check for security vulnerabilities
5. Verify naming conventions

Focus on: $ARGUMENTS
```

Usage: `/review the auth module changes`

**User-scoped** (`~/.claude/commands/`) — personal:
```markdown
# ~/.claude/commands/quick-test.md
Run the test suite for the file I'm currently editing.
Use --watch mode and show only failing tests.
```

### Skills (The Newer, Recommended System)

Skills live in `.claude/skills/` with a required `SKILL.md`:

```
.claude/
  skills/
    analyze-codebase/
      SKILL.md          ← Required. Contains frontmatter + instructions.
      templates/        ← Optional supporting files
      examples/
    generate-tests/
      SKILL.md
    security-audit/
      SKILL.md
```

### SKILL.md Frontmatter Options

```yaml
---
name: analyze-codebase
description: "Performs deep analysis of the codebase structure, dependencies, and patterns"
context: fork          # Run in isolated subagent context
allowed-tools:         # Restrict tools during execution
  - Read
  - Grep
  - Glob
argument-hint: "module or directory to analyze"
agent: Explore         # Use the Explore subagent type
---

# Codebase Analysis Skill

When invoked, analyze the specified area of the codebase:

1. Map the directory structure
2. Identify key entry points and exports
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
| `context: fork` | Run in isolated subagent context | Skills that produce verbose output or exploratory context |
| `allowed-tools` | Restrict available tools | Prevent destructive actions (limit to read-only) |
| `argument-hint` | Prompt for required parameters | When skill needs specific input |
| `agent` | Subagent type (Explore, Plan) | For codebase exploration or planning |
| `name` | Slash command name | Becomes `/name` |
| `description` | When to auto-invoke | Claude reads this to decide |

### context: fork — Why It Matters

Without `context: fork`, a skill's verbose output pollutes the main conversation:

```
❌ WITHOUT fork:
  Main session: "Analyze the auth module"
  → Skill runs, outputs 5000 tokens of analysis
  → All 5000 tokens remain in main conversation context
  → Context window fills faster
  → Subsequent work suffers from attention dilution

✅ WITH context: fork:
  Main session: "Analyze the auth module"
  → Skill runs in ISOLATED subagent
  → Subagent outputs 5000 tokens (in its own context)
  → Only the SUMMARY returns to main session
  → Main context stays clean
```

### Skills vs CLAUDE.md

| | Skills | CLAUDE.md |
|---|---|---|
| **Loading** | On-demand (invoked by user or Claude) | Always loaded |
| **Best for** | Task-specific workflows | Universal standards |
| **Context** | Can be isolated with `context: fork` | Always in context |
| **Examples** | "Analyze codebase", "Generate tests" | "Use TypeScript strict", "Follow PEP 8" |

### Personal Skill Customization

Create personal variants in `~/.claude/skills/` with different names to avoid affecting teammates:

```yaml
# ~/.claude/skills/my-review/SKILL.md (personal)
---
name: my-review
description: "My personalized code review with extra security focus"
---
# ... personal review checklist with extra security checks
```

---

## Task Statement 3.3: Path-Specific Rules

### YAML Frontmatter with Glob Patterns

```yaml
# .claude/rules/testing.md
---
paths:
  - "**/*.test.ts"
  - "**/*.test.tsx"
  - "**/*.spec.ts"
---

# Testing Conventions

- Use `describe`/`it` blocks with clear names
- Each test file must have at least one integration test
- Mock external services, never real API calls
- Use factory functions for test data, not inline objects
- Assert both success and error paths
```

```yaml
# .claude/rules/terraform.md
---
paths:
  - "terraform/**/*"
  - "**/*.tf"
---

# Terraform Conventions

- All resources must have tags: Name, Environment, Team
- Use modules for reusable infrastructure
- State must be stored in S3 with DynamoDB locking
- Always run `terraform plan` before `apply`
```

```yaml
# .claude/rules/api.md
---
paths:
  - "src/api/**/*"
  - "src/routes/**/*"
---

# API Conventions

- All endpoints must validate input with Zod schemas
- Return consistent error format: {error: string, code: number}
- Use middleware for authentication
- Rate limit all public endpoints
```

### Why Path-Specific Rules Beat Directory CLAUDE.md

**The test file problem:** Test files are spread throughout the codebase (`Button.test.tsx` next to `Button.tsx`). A directory-level CLAUDE.md can't apply testing rules to files in many different directories.

```
src/
  components/
    Button.tsx
    Button.test.tsx      ← Needs testing rules
    Modal.tsx
    Modal.test.tsx       ← Needs testing rules
  api/
    users.ts
    users.test.ts        ← Needs testing rules
  utils/
    format.ts
    format.test.ts       ← Needs testing rules
```

**Directory CLAUDE.md approach (limited):**
You'd need a CLAUDE.md in every directory. Doesn't scale.

**Path-specific rules approach (scalable):**
One file: `.claude/rules/testing.md` with `paths: ["**/*.test.*"]`
Applies to ALL test files regardless of where they live.

### Rules Without Path Restrictions

Rules files without a `paths` field apply globally (like project-level CLAUDE.md):

```yaml
# .claude/rules/general.md
# No paths field → applies everywhere

# General Standards
- Use meaningful variable names
- Keep functions under 30 lines
- Add comments for non-obvious logic
```

---

## Task Statement 3.4: Plan Mode vs Direct Execution

### When to Use Plan Mode

Plan mode restricts Claude to read-only codebase analysis. It produces implementation plans without making changes.

**Use plan mode for:**
- Microservice restructuring
- Library migrations affecting 45+ files
- Choosing between integration approaches with different infrastructure requirements
- Any task with architectural implications
- Multiple valid approaches where you need to evaluate tradeoffs

**Activate plan mode:**
- `Shift+Tab` to toggle
- `/plan` command
- `--permission-mode plan` CLI flag

### When to Use Direct Execution

**Use direct execution for:**
- Single-file bug fix with a clear stack trace
- Adding a date validation conditional
- Renaming a variable across a file
- Well-understood changes with clear scope

### The Explore Subagent

A built-in, read-only agent optimized for codebase exploration:

```yaml
# Skill using Explore subagent
---
name: explore-module
agent: Explore
context: fork
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash  # read-only bash
---
```

**Why use it:** Isolates verbose discovery output (file listings, grep results, dependency maps) from the main conversation context. Returns only a concise summary.

### Combining Plan + Direct Execution

```
Phase 1 (Plan Mode):
  "Analyze our auth module and propose a migration from JWT to OAuth2"
  → Claude explores codebase, identifies all JWT usage
  → Produces migration plan with 3 approaches
  → You review and choose Approach B

Phase 2 (Direct Execution):
  "Implement Approach B from the migration plan"
  → Claude executes the planned changes
  → Modifies files according to the agreed plan
```

---

## Task Statement 3.5: Iterative Refinement Techniques

### Input/Output Examples (Most Effective for Clarity)

When prose descriptions produce inconsistent results, provide concrete examples:

```
❌ VAGUE INSTRUCTION:
  "Convert the date formats to be consistent"

✅ CONCRETE EXAMPLES:
  Input: "Jan 5, 2025" → Output: "2025-01-05"
  Input: "5/1/25" → Output: "2025-01-05"
  Input: "2025-01-05" → Output: "2025-01-05" (already correct)
  Input: "January 5th, 2025" → Output: "2025-01-05"
```

### Test-Driven Iteration

Write tests first, then iterate by sharing failures:

```
Step 1: Write test suite
  test_parse_date("Jan 5, 2025") → "2025-01-05"
  test_parse_date("invalid") → raises ValueError
  test_parse_date("") → raises ValueError
  test_parse_date("2025-13-40") → raises ValueError

Step 2: Ask Claude to implement
  "Implement parse_date to pass these tests"

Step 3: Run tests, share failures
  "Tests pass except test_parse_date('2025-13-40') — 
   it returns '2025-13-40' instead of raising ValueError"

Step 4: Claude fixes the edge case
```

### The Interview Pattern

Have Claude ask questions before implementing:

```
You: "Build a caching layer for our API"

Claude (interview): "Before I implement, let me ask:
1. What's the expected cache hit ratio? (affects eviction strategy)
2. Should the cache survive service restarts? (in-memory vs Redis)
3. How do you want to handle cache invalidation for writes?
4. What's the maximum acceptable staleness for cached data?"

You: "1. ~80%, 2. Must survive restarts, 3. Write-through, 4. 30 seconds"

Claude: "Got it. I'll implement a Redis-backed write-through cache with 30s TTL..."
```

### When to Batch vs Sequence Issues

**Batch (single message)** when fixes interact:
```
"Three interacting issues:
1. The error handler catches too broadly (catches all exceptions)
2. The retry logic doesn't respect the error handler's categories
3. The logging doesn't include the error category

These are related — fixing #1 changes what #2 and #3 need to handle."
```

**Sequential** when fixes are independent:
```
Message 1: "Fix the date parsing in utils.py"
(Claude fixes, you verify)
Message 2: "Add rate limiting to the API endpoints"
(Independent fix)
```

---

## Task Statement 3.6: CI/CD Integration

### The -p Flag (Non-Interactive Mode)

```bash
# ❌ HANGS — Claude Code waits for interactive input
claude "Review this PR for security issues"

# ✅ CORRECT — -p flag runs non-interactively
claude -p "Review this PR for security issues"

# Full CI command with structured output
claude -p "Review the changes in this PR" \
  --output-format json \
  --json-schema '{
    "type": "object",
    "properties": {
      "findings": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "file": {"type": "string"},
            "line": {"type": "integer"},
            "severity": {"type": "string", "enum": ["critical", "warning", "info"]},
            "issue": {"type": "string"},
            "suggestion": {"type": "string"}
          },
          "required": ["file", "severity", "issue"]
        }
      }
    }
  }'
```

### Structured Output for CI

`--output-format json` returns:
```json
{
  "session_id": "abc123",
  "total_cost_usd": 0.05,
  "structured_output": {
    "findings": [
      {
        "file": "src/auth.ts",
        "line": 42,
        "severity": "critical",
        "issue": "SQL injection vulnerability in user lookup",
        "suggestion": "Use parameterized queries instead of string concatenation"
      }
    ]
  }
}
```

### Session Context Isolation

The same Claude session that generated code is less effective at reviewing its own changes (retains reasoning context, less likely to question its own decisions).

```bash
# ❌ SAME SESSION generates and reviews
claude -p "Write auth middleware" > middleware.ts
claude -p "Review the middleware you just wrote"  # Same context = biased review

# ✅ INDEPENDENT SESSIONS for generation and review
# Session 1: Generate
claude -p "Write auth middleware" > middleware.ts

# Session 2: Review (fresh context, no prior reasoning)
claude -p "Review middleware.ts for security issues"
```

### Avoiding Duplicate PR Comments

When re-running reviews after new commits:

```bash
# Include prior findings so Claude only reports NEW issues
claude -p "Review this PR. 
Previous review found these issues (already addressed or tracked):
$(cat previous_findings.json)

Report ONLY new issues or issues that remain unaddressed." \
  --output-format json
```

### CLAUDE.md for CI Context

Document testing standards and fixtures in CLAUDE.md so CI-invoked Claude Code generates better tests:

```markdown
# CLAUDE.md

## Testing Standards
- Use Jest with React Testing Library
- Available fixtures: `testUser`, `testOrder`, `testProduct` in `tests/fixtures/`
- Prefer integration tests over unit tests for API routes
- Mock external services with `nock`
- Minimum coverage: 80% for new code

## Review Criteria
- Report: bugs, security issues, data leaks, race conditions
- Skip: minor style issues, local naming patterns, import ordering
- Use severity levels: critical (blocks merge), warning (should fix), info (nice to have)
```

---

## Practice Questions — Domain 3

### Question 1
A new team member reports Claude Code doesn't follow your team's coding conventions. You confirm the conventions are properly defined. Where should you look first?

**A)** Check if conventions are in `~/.claude/CLAUDE.md` instead of `.claude/CLAUDE.md`
**B)** Check if the new team member's Claude Code version is outdated
**C)** Check if `.claude/rules/` files have incorrect glob patterns
**D)** Check if the conventions use `@import` syntax that the new member's OS doesn't support

**Correct Answer: A**
User-level `~/.claude/CLAUDE.md` is NOT shared via version control. If conventions are there, the new team member doesn't have them. Moving to `.claude/CLAUDE.md` makes them project-scoped and available to everyone.

### Question 2
Your CI pipeline script runs `claude "Analyze this PR"` but hangs indefinitely. What's the fix?

**A)** `claude -p "Analyze this PR"`
**B)** `CLAUDE_HEADLESS=true claude "Analyze this PR"`
**C)** `claude "Analyze this PR" < /dev/null`
**D)** `claude --batch "Analyze this PR"`

**Correct Answer: A**
The `-p` (or `--print`) flag runs Claude Code in non-interactive mode. B, C, and D reference non-existent features or Unix workarounds that don't address Claude Code's command syntax.

### Question 3
Your codebase has test files spread throughout (`Button.test.tsx` next to `Button.tsx`). You want all tests to follow the same conventions regardless of location. What's the most maintainable approach?

**A)** Create `.claude/rules/testing.md` with `paths: ["**/*.test.*"]`
**B)** Put all conventions in root CLAUDE.md and let Claude infer which apply
**C)** Create skills for each code type
**D)** Place CLAUDE.md in each subdirectory

**Correct Answer: A**
Glob patterns in `.claude/rules/` automatically apply to matching files regardless of directory. B relies on inference. C requires manual invocation. D doesn't scale for files spread across many directories.

---

## Quick Reference — Domain 3 Cheat Sheet

| Concept | Key Fact |
|---|---|
| **User-level config** | `~/.claude/CLAUDE.md` — NOT shared via version control |
| **Project-level config** | `.claude/CLAUDE.md` or root `CLAUDE.md` — shared via VC |
| **Directory-level** | Subdirectory `CLAUDE.md` — highest precedence |
| **@import** | Reference external files for modularity |
| **.claude/rules/** | Topic-specific rule files with optional path-scoping |
| **Path-scoping** | YAML frontmatter: `paths: ["**/*.test.*"]` |
| **Glob patterns** | Better than directory CLAUDE.md for cross-codebase conventions |
| **/memory** | Verify which config files are loaded |
| **Project commands** | `.claude/commands/` — shared via VC |
| **Personal commands** | `~/.claude/commands/` — not shared |
| **Skills** | `.claude/skills/` with `SKILL.md` frontmatter |
| **context: fork** | Isolate skill output from main conversation |
| **allowed-tools** | Restrict tools during skill execution |
| **argument-hint** | Prompt for required parameters |
| **Plan mode** | Complex tasks, architectural decisions, multi-file |
| **Direct execution** | Simple, well-scoped, single-file changes |
| **Explore subagent** | Read-only codebase exploration, isolated context |
| **-p flag** | Non-interactive mode for CI/CD |
| **--output-format json** | Machine-parseable structured output |
| **--json-schema** | Enforce output schema in CI |
| **Session isolation** | Independent review instance > same-session self-review |
| **Prior findings** | Include in context to avoid duplicate PR comments |
| **Interview pattern** | Claude asks questions before implementing |
| **Input/output examples** | Most effective for transformation clarity |
