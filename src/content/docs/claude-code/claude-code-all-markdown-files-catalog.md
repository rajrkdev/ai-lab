---
title: Every Markdown File Claude Code Recognizes — Complete Catalog
sidebar:
  order: 4
---

# Every Markdown File Claude Code Recognizes — Complete Catalog

## Quick Reference Map

```
YOUR SYSTEM
├── /Library/Application Support/ClaudeCode/    (macOS Enterprise)
│   └── CLAUDE.md                               ← 1. Enterprise Policy Memory
│
├── /etc/claude-code/                           (Linux Enterprise)
│   └── CLAUDE.md                               ← 1. Enterprise Policy Memory
│
├── ~/.claude/
│   ├── CLAUDE.md                               ← 2. User Memory (all projects)
│   ├── commands/
│   │   └── *.md                                ← 3. Personal Slash Commands
│   ├── agents/
│   │   └── *.md                                ← 4. Personal Subagents
│   ├── skills/
│   │   └── <skill-name>/
│   │       ├── SKILL.md                        ← 5. Personal Skills
│   │       └── *.md (supporting files)
│   ├── output-styles/
│   │   └── *.md                                ← 6. Personal Output Styles
│   └── projects/<project>/<session>/
│       └── session_memory                      ← (auto-generated, not user-editable)
│
YOUR PROJECT (cwd)
├── CLAUDE.md                                   ← 7. Project Memory (team-shared)
├── CLAUDE.local.md                             ← 8. Project Local Memory (personal, gitignored)
├── .claude/
│   ├── CLAUDE.md                               ← 7. (alternate location for Project Memory)
│   ├── rules/
│   │   └── *.md                                ← 9. Rules (global + path-scoped)
│   ├── commands/
│   │   └── *.md                                ← 10. Project Slash Commands
│   ├── agents/
│   │   └── *.md                                ← 11. Project Subagents
│   ├── skills/
│   │   └── <skill-name>/
│   │       ├── SKILL.md                        ← 12. Project Skills
│   │       └── *.md (supporting files)
│   ├── output-styles/
│   │   └── *.md                                ← 13. Project Output Styles
│   └── settings.local.json                     (JSON, not MD — but relevant)
│
├── src/
│   └── Domain/
│       └── CLAUDE.md                           ← 14. Subtree Memory (on-demand)
│
SUBAGENT AUTO MEMORY
├── ~/.claude/agent-memory/<agent>/              (user scope)
│   └── MEMORY.md                               ← 15. Subagent Memory
├── .claude/agent-memory/<agent>/                (project scope)
│   └── MEMORY.md                               ← 15. Subagent Memory
│
PLUGINS
└── <plugin>/
    ├── commands/*.md                           ← 16. Plugin Commands
    ├── agents/*.md                             ← 17. Plugin Agents
    ├── skills/*/SKILL.md                       ← 18. Plugin Skills
    └── output-styles/*.md                      ← 19. Plugin Output Styles
│
IMPORTED FILES (via @path syntax in any CLAUDE.md)
└── any *.md referenced with @                  ← 20. Imported Files
```

---

## Detailed Breakdown of Each File

---

### 1. CLAUDE.md — Enterprise Policy Memory

| Attribute | Detail |
|-----------|--------|
| **File** | `CLAUDE.md` |
| **Locations** | macOS: `/Library/Application Support/ClaudeCode/CLAUDE.md` · Linux: `/etc/claude-code/CLAUDE.md` · Windows: `C:\Program Files\ClaudeCode\CLAUDE.md` |
| **When loaded** | Always — first thing at session start (highest priority) |
| **Priority** | Highest — overrides all other CLAUDE.md files |
| **Who creates it** | IT/DevOps teams via MDM, Ansible, Group Policy, etc. |
| **Shared with** | All users in the organization |
| **Git tracked** | No — deployed via config management |
| **Token impact** | Permanent overhead every session |
| **Frontmatter** | None required |

**Purpose**: Organization-wide coding standards, security policies, compliance requirements, approved tools/libraries. This is the "law of the land" that individual developers cannot override.

**Example**:
```markdown
# Enterprise Policy — Acme Corp

## Security
- Never commit secrets, API keys, or credentials
- All new endpoints require authentication middleware
- Use parameterized queries only — no string concatenation for SQL

## Compliance
- GDPR: All PII must be encrypted at rest
- SOC2: Audit logging required for data access operations
- Do not use unapproved third-party packages

## Standards
- Code must pass SonarQube quality gate before merge
- All PRs require minimum 2 approvals
```

---

### 2. CLAUDE.md — User Memory (Personal, All Projects)

| Attribute | Detail |
|-----------|--------|
| **File** | `CLAUDE.md` |
| **Location** | `~/.claude/CLAUDE.md` |
| **When loaded** | Always at session start |
| **Priority** | High — loaded after Enterprise, before Project |
| **Shared with** | Just you, across all projects |
| **Git tracked** | No |
| **Token impact** | Permanent overhead every session |

**Purpose**: Your personal coding preferences that travel with you regardless of project — editor preferences, personal shortcuts, formatting preferences.

**Example**:
```markdown
# Personal Preferences

## Coding Style
- Prefer functional patterns over imperative
- Use descriptive variable names, never abbreviations
- Always add XML doc comments on public methods

## Interaction
- Before making changes, propose a plan first and wait for "OK"
- Keep solutions minimal — avoid over-engineering
- When unsure, ask rather than assume
```

---

### 3. Slash Commands — Personal (`~/.claude/commands/*.md`)

| Attribute | Detail |
|-----------|--------|
| **File** | Any `*.md` file |
| **Location** | `~/.claude/commands/` (supports subdirectories) |
| **Filename** | Becomes the command name: `review.md` → `/review` |
| **Invocation** | User-invoked — you type `/command-name` explicitly |
| **When loaded** | Only when you invoke the command |
| **Shared with** | Just you, across all projects |
| **Git tracked** | No |

**Frontmatter fields**:
```yaml
---
description: What this command does (shown in autocomplete)
allowed-tools: Read, Grep, Glob, Bash(git diff:*)
model: claude-sonnet-4-5-20250929          # optional model override
---
```

**Special variables**:
- `$ARGUMENTS` — everything the user types after the command
- `$1`, `$2` — individual positional arguments
- `@file.txt` — file content injection (replaced with file contents)
- `!command` — shell command execution (replaced with output)

**Example** (`~/.claude/commands/review.md`):
```markdown
---
description: Comprehensive code review of recent changes
allowed-tools: Read, Grep, Glob, Bash(git diff:*)
---

## Changed Files
!`git diff --name-only HEAD~1`

## Detailed Changes
!`git diff HEAD~1`

## Review Checklist
Review the above changes for:
1. Logic errors and bugs
2. Security vulnerabilities
3. Performance issues
4. Style consistency
5. Test coverage
```

**Subdirectory organization**:
```
~/.claude/commands/
├── frontend/
│   ├── component.md        # /component
│   └── style-check.md      # /style-check
├── backend/
│   ├── api-test.md          # /api-test
│   └── db-migrate.md        # /db-migrate
└── review.md                # /review
```
Subdirectories appear in the command description but do NOT affect the command name.

---

### 4. Subagents — Personal (`~/.claude/agents/*.md`)

| Attribute | Detail |
|-----------|--------|
| **File** | Any `*.md` file |
| **Location** | `~/.claude/agents/` |
| **Filename** | Becomes the agent name |
| **Invocation** | You ask Claude to use it, or Claude auto-delegates based on description |
| **When loaded** | Agent definitions loaded at session start; agent runs in separate context when invoked |
| **Shared with** | Just you, across all projects |
| **Creation** | Manual file or via `/agents` interactive command |

**Frontmatter fields**:
```yaml
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Glob, Grep
disallowedTools: Write, Edit, Bash
model: sonnet                    # sonnet | opus | haiku
permissionMode: default          # default | plan | bypassPermissions
maxTurns: 50                     # max agentic loop iterations
skills:                          # skills this agent can use
  - code-review
  - security-scan
memory:
  scope: user                    # user | project | local
hooks:
  PreToolUse:
    - matcher: Write
      hooks:
        - type: command
          command: echo "Write detected"
mcpServers:
  - name: github
---
```

The markdown body below the frontmatter becomes the **system prompt** for the subagent.

**Example** (`~/.claude/agents/code-reviewer.md`):
```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices. Use for PR reviews, security audits, and code quality checks.
tools: Read, Glob, Grep
model: sonnet
memory:
  scope: user
---

You are a code reviewer. Focus on:

## Review Priorities (in order)
1. Logic errors and bugs
2. Security vulnerabilities
3. Performance problems
4. Maintainability and tech debt
5. Code style consistency

## Instructions
- Read the target files thoroughly
- Cross-reference with related files for consistency
- Provide actionable feedback with specific line references
- Categorize issues by severity (Critical/High/Medium/Low)

## Memory
Update your agent memory as you discover codepaths, patterns, and key architectural decisions.
```

---

### 5. Skills — Personal (`~/.claude/skills/*/SKILL.md`)

| Attribute | Detail |
|-----------|--------|
| **File** | Must be named `SKILL.md` (case-sensitive) |
| **Location** | `~/.claude/skills/<skill-name>/SKILL.md` (also auto-discovered from nested `.claude/skills/` subdirectories) |
| **Folder name** | The skill's identity (lowercase, hyphens, numbers only) |
| **Invocation** | Model-invoked (Claude auto-decides) OR user via `/skill-name` — **unified since v2.1.3** |
| **When loaded** | Frontmatter only at session start; full body on invocation |
| **Shared with** | Just you, across all projects |
| **Can include** | Supporting `.md` files, scripts, templates, data files |

**Frontmatter fields**:
```yaml
---
name: deploy-staging              # max 64 chars, lowercase+hyphens+numbers
description: >                    # max 1024 chars — CRITICAL for discovery
  Deploy to staging environment with safety checks.
  Use when user says "deploy", "staging", or "ship it".
allowed-tools: Read, Bash(npm run *), Bash(git *)
disable-model-invocation: true    # only manual /deploy-staging invocation
context: fork                     # run in separate subagent context
agent: Explore                    # which subagent type (Explore, Plan, custom)
---
```

**Special variables in skill body**:
- `$ARGUMENTS` — user input after `/skill-name`
- `${CLAUDE_SESSION_ID}` — current session identifier

**Folder structure example**:
```
~/.claude/skills/
└── deploy-staging/
    ├── SKILL.md                  # Required — entry point
    ├── FORMS.md                  # Optional — reference, loaded on demand
    ├── REFERENCE.md              # Optional — detailed docs
    ├── scripts/
    │   ├── deploy.sh             # Optional — executable scripts
    │   └── rollback.sh
    └── templates/
        └── deploy-checklist.md   # Optional — templates
```

See previous guide for complete skill details.

---

### 6. Output Styles — Personal (`~/.claude/output-styles/*.md`)

| Attribute | Detail |
|-----------|--------|
| **File** | Any `*.md` file |
| **Location** | `~/.claude/output-styles/` |
| **Invocation** | Via `/output-style` command or settings |
| **Effect** | Directly modifies Claude Code's system prompt |
| **Shared with** | Just you |

**Key behavior**: Output styles are fundamentally different from CLAUDE.md and rules. They **directly replace** parts of Claude Code's default system prompt related to software engineering. This is more invasive than CLAUDE.md (which adds a user message) or `--append-system-prompt` (which appends).

**Frontmatter fields**:
```yaml
---
name: My Teaching Style
description: Explains reasoning and teaches as it codes
keep-coding-instructions: true     # false by default — keeps SE instructions
---
```

When `keep-coding-instructions` is `false` (default for custom styles), Claude loses its default coding behavior (like running tests to verify). Set to `true` if you want coding + custom style.

**Built-in styles** (no file needed):
- **Default** — Standard software engineering system prompt
- **Explanatory** — Adds educational "Insights" between coding steps
- **Learning** — Collaborative mode, adds `TODO(human)` markers for you to implement

**Example** (`~/.claude/output-styles/architect.md`):
```markdown
---
name: architect
description: Responds with architectural thinking, trade-off analysis, and system design focus
keep-coding-instructions: true
---

# Architect Mode

When responding:
1. Always consider system-level implications before writing code
2. Discuss trade-offs explicitly (performance vs. maintainability, etc.)
3. Reference relevant design patterns by name
4. Consider scalability, observability, and failure modes
5. Suggest architectural decision records (ADRs) for significant decisions
```

---

### 7. CLAUDE.md — Project Memory (Team-Shared)

| Attribute | Detail |
|-----------|--------|
| **File** | `CLAUDE.md` |
| **Location** | `./CLAUDE.md` OR `./.claude/CLAUDE.md` (either works) |
| **When loaded** | Always at session start |
| **Priority** | High — after Enterprise and User, before Local |
| **Shared with** | Team members via git |
| **Git tracked** | Yes — committed to repository |
| **Token impact** | Permanent overhead every session |

This is the most commonly used file. See previous guide for complete details. Bootstrap with `/init`.

---

### 8. CLAUDE.local.md — Project Local Memory (Personal)

| Attribute | Detail |
|-----------|--------|
| **File** | `CLAUDE.local.md` |
| **Location** | `./CLAUDE.local.md` |
| **When loaded** | Always at session start |
| **Priority** | High — most specific project memory |
| **Shared with** | Just you, this project only |
| **Git tracked** | No — automatically added to `.gitignore` |

**Purpose**: Personal project overrides — your sandbox URLs, test credentials (non-sensitive), debugging preferences, personal workflow shortcuts for this specific project.

**Example**:
```markdown
# My Local Settings

## Dev Environment
- My sandbox API: https://raj-sandbox.azurewebsites.net
- Test database: localdb\MSSQLLocalDB
- Use port 5001 for local API

## Personal Workflow
- I prefer seeing full stack traces in error output
- When running tests, always use --verbosity detailed
```

**Important caveat**: `CLAUDE.local.md` only exists in one worktree. If you use multiple git worktrees, use `@~/.claude/my-project-instructions.md` import in your project CLAUDE.md instead.

---

### 9. Rules (`.claude/rules/*.md`)

| Attribute | Detail |
|-----------|--------|
| **Files** | Any `*.md` files |
| **Location** | `.claude/rules/` (supports nested subdirectories) |
| **When loaded** | Global rules: always at start. Path-scoped rules: when matching files are touched |
| **Priority** | Same high priority as CLAUDE.md |
| **Shared with** | Team via git |
| **Git tracked** | Yes |

**Frontmatter** (optional):
```yaml
---
paths:
  - "src/api/**/*.ts"         # Multiple globs supported (v2.1.84)
  - "src/controllers/**/*.cs"
---
```

Rules without `paths:` → loaded unconditionally (global).
Rules with `paths:` → loaded only when Claude works with matching file patterns. Supports single string or YAML list of globs (YAML list added v2.1.84).

See previous guide for complete details.

---

### 10. Slash Commands — Project (`.claude/commands/*.md`)

| Attribute | Detail |
|-----------|--------|
| **File** | Any `*.md` file |
| **Location** | `.claude/commands/` (supports subdirectories) |
| **Filename** | Becomes the command name |
| **Shared with** | Team via git |
| **Git tracked** | Yes |

Same format as personal slash commands (item #3). Team members get these commands automatically when they clone/pull the repository.

---

### 11. Subagents — Project (`.claude/agents/*.md`)

| Attribute | Detail |
|-----------|--------|
| **File** | Any `*.md` file |
| **Location** | `.claude/agents/` |
| **Shared with** | Team via git |
| **Git tracked** | Yes |

Same format as personal subagents (item #4). Useful for team-standard agents like a shared code reviewer or deployment agent.

---

### 12. Skills — Project (`.claude/skills/*/SKILL.md`)

| Attribute | Detail |
|-----------|--------|
| **File** | `SKILL.md` inside a named folder |
| **Location** | `.claude/skills/<skill-name>/SKILL.md` (auto-discovered from nested subdirectories too) |
| **Shared with** | Team via git |
| **Git tracked** | Yes |
| **Note** | Since v2.1.3, skills and slash commands are unified—a SKILL.md in `.claude/skills/<name>/` automatically creates the `/name` slash command |

Same format as personal skills (item #5). Team members get these skills automatically.

---

### 13. Output Styles — Project (`.claude/output-styles/*.md`)

| Attribute | Detail |
|-----------|--------|
| **File** | Any `*.md` file |
| **Location** | `.claude/output-styles/` |
| **Shared with** | Team via git |
| **Git tracked** | Yes |

Same format as personal output styles (item #6). Useful for team-standard response formats.

---

### 14. Subtree CLAUDE.md — On-Demand Child Directory Memory

| Attribute | Detail |
|-----------|--------|
| **File** | `CLAUDE.md` |
| **Location** | Any subdirectory below your cwd (e.g., `src/Domain/CLAUDE.md`) |
| **When loaded** | On demand — only when Claude reads/edits files in that subdirectory |
| **Priority** | High (same as other CLAUDE.md files) |
| **Token impact** | None until Claude touches files in that directory |

**Purpose**: Domain-specific instructions for a subsystem. If your `src/Domain/` directory has complex DDD rules, put them in `src/Domain/CLAUDE.md` — they only consume tokens when Claude is actually working in that area.

**Example** (`src/Domain/CLAUDE.md`):
```markdown
# Domain Layer Rules

- This layer has ZERO dependencies on Infrastructure or WebApi
- All entities must inherit from BaseEntity
- Use Value Objects for money, dates, policy numbers
- Aggregate roots are the only public entry points
- Never expose IQueryable from repositories
```

---

### 15. MEMORY.md — Subagent Auto Memory

| Attribute | Detail |
|-----------|--------|
| **File** | `MEMORY.md` |
| **Locations** | User scope: `~/.claude/agent-memory/<agent-name>/MEMORY.md` · Project scope: `.claude/agent-memory/<agent-name>/MEMORY.md` · Local scope: `.claude/agent-memory/local/<agent-name>/MEMORY.md` |
| **When loaded** | First 200 lines loaded into subagent's system prompt at invocation |
| **Who writes it** | The subagent itself (auto-generated and maintained) |
| **Purpose** | Persistent learning for subagents across sessions |

**How it works**: When a subagent has `memory` configured in its frontmatter, it gets Read/Write/Edit tools for its memory directory. The subagent can save patterns, discoveries, and learnings to `MEMORY.md`. Next time it's invoked, the first 200 lines are automatically included in its system prompt.

**Memory scope options**:
- `user` — shared across all projects (recommended default)
- `project` — specific to this codebase
- `local` — personal + project-specific (gitignored)

**You can ask the subagent to use its memory**:
- "Review this PR, and check your memory for patterns you've seen before."
- "Now that you're done, save what you learned to your memory."

---

### 16–19. Plugin Components

Plugins bundle the same file types as personal/project configurations:

| Component | Location in Plugin | File Format |
|-----------|--------------------|-------------|
| Commands | `<plugin>/commands/*.md` | Same as slash commands |
| Agents | `<plugin>/agents/*.md` | Same as subagents |
| Skills | `<plugin>/skills/*/SKILL.md` | Same as skills |
| Output Styles | `<plugin>/output-styles/*.md` | Same as output styles |
| Hooks | `<plugin>/hooks.json` | JSON (not markdown) |
| MCP Servers | `<plugin>/.mcp.json` | JSON (not markdown) |
| LSP Servers | `<plugin>/.lsp.json` | JSON (not markdown) |
| Manifest | `<plugin>/.claude-plugin/plugin.json` | JSON (required) |

Plugin commands are namespaced: `hello.md` in plugin `my-plugin` → `/my-plugin:hello`.

---

### 20. Imported Files (via `@path` Syntax)

| Attribute | Detail |
|-----------|--------|
| **File** | Any file referenced with `@path/to/file` in a CLAUDE.md |
| **Syntax** | `@relative/path.md` or `@~/absolute/path.md` |
| **Resolution** | Relative to the file containing the import |
| **Max depth** | 5 recursive hops |
| **Ignored in** | Code spans (\`@not-imported\`) and code blocks |

These are not a separate file type — they're any markdown (or other) file pulled into CLAUDE.md context via the import mechanism.

---

## Non-Markdown Configuration Files (For Completeness)

These are NOT markdown but are part of the Claude Code configuration ecosystem:

| File | Location | Format | Purpose |
|------|----------|--------|---------|
| `settings.json` | `.claude/settings.json` (project) or `~/.claude/settings.json` (user) | JSON | Permissions, model, env vars, allowed tools |
| `settings.local.json` | `.claude/settings.local.json` | JSON | Local project settings (gitignored) |
| `managed-settings.json` | `~/.claude/managed-settings.json` (v2.1.51+) or `C:\Program Files\ClaudeCode\managed-settings.json` (Windows) | JSON | Enterprise policy (highest precedence; also via macOS plist or Windows Registry) |
| `managed-settings.d/*.json` | `~/.claude/managed-settings.d/` (v2.1.83) | JSON | Drop-in policy fragments—merged alphabetically, independent team fragments |
| `hooks.json` | `.claude/hooks.json` | JSON | Lifecycle hooks (PreToolUse, PostToolUse, Setup, etc.) |
| `.mcp.json` | `.claude/.mcp.json` or `~/.claude/.mcp.json` | JSON | MCP server configurations |
| `.lsp.json` | `.claude/.lsp.json` | JSON | Language Server Protocol configurations |
| `plugin.json` | `.claude-plugin/plugin.json` | JSON | Plugin manifest |
| `keybindings.json` | `~/.claude/keybindings.json` (v2.1.18+) | JSON | Custom key bindings—create/edit via `/keybindings` command |

---

## Master Comparison Table

| # | File | Location | Loaded When | Priority | Invocation | Git? | Token Cost |
|---|------|----------|-------------|----------|------------|------|------------|
| 1 | Enterprise CLAUDE.md | System-level path | Always, first | Highest | Automatic | No | Permanent |
| 2 | User CLAUDE.md | `~/.claude/` | Always | High | Automatic | No | Permanent |
| 3 | Personal Commands | `~/.claude/commands/*.md` | On `/command` | Normal | User types `/cmd` | No | On-use only |
| 4 | Personal Agents | `~/.claude/agents/*.md` | Definition at start; runs on invoke | Normal | User or Claude | No | On-use only |
| 5 | Personal Skills | `~/.claude/skills/*/SKILL.md` | Frontmatter at start; body on invoke | Normal | Claude auto or `/skill` | No | Minimal + on-use |
| 6 | Personal Output Styles | `~/.claude/output-styles/*.md` | When activated | System prompt level | `/output-style` | No | Replaces default prompt |
| 7 | Project CLAUDE.md | `./CLAUDE.md` or `.claude/CLAUDE.md` | Always | High | Automatic | Yes | Permanent |
| 8 | CLAUDE.local.md | `./CLAUDE.local.md` | Always | High (most specific) | Automatic | No (gitignored) | Permanent |
| 9 | Rules | `.claude/rules/*.md` | Global: always. Path-scoped: on demand | High (same as CLAUDE.md) | Automatic | Yes | Global=permanent. Scoped=conditional |
| 10 | Project Commands | `.claude/commands/*.md` | On `/command` | Normal | User types `/cmd` | Yes | On-use only |
| 11 | Project Agents | `.claude/agents/*.md` | Definition at start; runs on invoke | Normal | User or Claude | Yes | On-use only |
| 12 | Project Skills | `.claude/skills/*/SKILL.md` | Frontmatter at start; body on invoke | Normal | Claude auto or `/skill` | Yes | Minimal + on-use |
| 13 | Project Output Styles | `.claude/output-styles/*.md` | When activated | System prompt level | `/output-style` | Yes | Replaces default prompt |
| 14 | Subtree CLAUDE.md | `<subdir>/CLAUDE.md` | When Claude accesses that directory | High | Automatic | Yes | On-demand only |
| 15 | Subagent MEMORY.md | `agent-memory/<agent>/MEMORY.md` | First 200 lines at agent invocation | Normal (in subagent context) | Automatic | Depends on scope | On-use only |
| 16-19 | Plugin components | `<plugin>/commands,agents,skills,styles/` | Same as their non-plugin equivalents | Normal | Same as equivalents | Via plugin install | Same as equivalents |
| 20 | @Imported files | Anywhere (referenced via @path) | When parent CLAUDE.md loads | Same as parent | Automatic | Varies | Adds to parent's cost |

---

## Token Budget Summary

```
ALWAYS LOADED (permanent overhead):
├── Enterprise CLAUDE.md           → variable
├── User CLAUDE.md                 → variable  
├── Project CLAUDE.md              → variable
├── CLAUDE.local.md                → variable
├── Global rules (no paths:)       → variable
├── Agent/Skill frontmatter        → ~100-150 tokens each
├── MCP tool schemas               → ~500-2000 each
└── System prompt                  → ~5-15K tokens
    ─────────────────────────────
    TOTAL FIXED OVERHEAD           → ~7-32K tokens

LOADED ON DEMAND (conditional):
├── Path-scoped rules              → when matching files touched
├── Subtree CLAUDE.md files        → when Claude enters that directory
├── Skill full bodies              → when Claude invokes the skill
├── Skill supporting files         → when Claude reads them
├── Subagent MEMORY.md             → when subagent is invoked
└── Slash command content          → when user types /command
    ─────────────────────────────
    VARIES PER SESSION

SEPARATE CONTEXT (doesn't consume main window):
├── Subagent conversations         → runs in forked context
└── Skills with context: fork      → runs in subagent context

RESPONSE BUFFER (reserved):
└── ~40-45K tokens for Claude's thinking + response

USABLE CONVERSATION SPACE:
└── ~140-150K tokens (out of 200K total)
```

---

## The `/memory` Command — See What's Loaded

At any point during a session, run `/memory` to:
- See all loaded CLAUDE.md files and their sources
- See loaded rules files  
- Open any memory file in your system editor
- Verify path-scoped rules are activating correctly

---

## Sources

All information sourced from official Anthropic documentation:
- Memory management: https://code.claude.com/docs/en/memory
- Skills: https://code.claude.com/docs/en/skills
- Subagents: https://code.claude.com/docs/en/sub-agents
- Output styles: https://code.claude.com/docs/en/output-styles
- Settings: https://code.claude.com/docs/en/settings
- Plugins: https://code.claude.com/docs/en/plugins
- Plugins reference: https://code.claude.com/docs/en/plugins-reference
- Best practices: https://code.claude.com/docs/en/best-practices
- How Claude Code works: https://code.claude.com/docs/en/how-claude-code-works
