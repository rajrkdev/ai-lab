---
title: "The Definitive Claude Code Reference Guide"
description: "Complete reference for Claude Code architecture, configuration, slash commands, tools, hooks, MCP, agents, context management, and professional workflows."
sidebar:
  order: 2
---

# The Definitive Claude Code Reference Guide
## Architecture, Configuration & Professional Usage

> **Last Updated:** April 2026 | **Target:** Claude Certified Architect Foundations (CCA-F) + Daily Professional Use
> **Author:** Generated for Raj — Backend Tech Lead | AI-Enabled Architect Track

---

## 1. What Is Claude Code

Claude Code is Anthropic's **agentic CLI coding tool** that operates as a full autonomous coding agent — not a line-completion assistant. It reads entire codebases, edits files across projects, runs commands, handles failures, iterates, and commits results through natural language instructions.

### Key Differentiators

| Feature | Claude Code | GitHub Copilot | Cursor |
|---------|------------|----------------|--------|
| Paradigm | Autonomous agent | Line completion | AI-assisted editor |
| Scope | Entire codebase | Current file | Open files |
| Execution | Full terminal access | None | Limited |
| Multi-file edits | Architecturally coherent | N/A | Single-file focus |
| CI/CD integration | Headless mode | N/A | N/A |
| Tool extension | MCP protocol | Extensions | Plugins |
| Permission model | Granular allow/deny/ask | N/A | N/A |

### By the Numbers (April 2026)

- **113,000+ GitHub stars**
- **~195 million lines of code** processed weekly
- **~4% of all public GitHub commits** authored by Claude Code
- **$1B+ annualized revenue** (surpassed November 2025)
- **SWE-bench Verified:** Opus 4.6 = 80.8%, Sonnet 4.6 = 79.6%

---

## 2. Architecture: The Agentic Loop

Every Claude Code interaction follows a continuous **three-phase agentic loop**:

```
┌─────────────────────────────────────────────────┐
│                  AGENTIC LOOP                    │
│                                                  │
│   ┌──────────┐  ┌───────────┐  ┌────────────┐  │
│   │  GATHER  │→ │   TAKE    │→ │  VERIFY    │  │
│   │ CONTEXT  │  │  ACTION   │  │  RESULTS   │  │
│   └──────────┘  └───────────┘  └────────────┘  │
│        ↑                              │          │
│        └──────────────────────────────┘          │
│              (repeat until done)                 │
└─────────────────────────────────────────────────┘
```

**Phase 1 — Gather Context:** Search files, read code, grep patterns, navigate dependencies, build understanding.

**Phase 2 — Take Action:** Edit files, write new code, run bash commands, invoke MCP tools, spawn subagents.

**Phase 3 — Verify Results:** Run tests, check compiler output, validate changes, review diffs.

Two components power this: **Models that reason** (Opus, Sonnet, Haiku) and **Tools that act** (Read, Write, Edit, Bash, Search, WebFetch, Agent, MCP tools).

---

## 3. Three-Tier Agent Architecture

```
┌──────────────────────────────────────────────────────────┐
│ TIER 3: AGENT TEAMS (Research Preview)                    │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│ │ Team Lead│ │Teammate 1│ │Teammate 2│ │Teammate 3│    │
│ │(orchestr)│ │(worktree)│ │(worktree)│ │(worktree)│    │
│ └─────┬────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘    │
│       └────────────┴────────────┴────────────┘           │
│  Shared task lists │ Dependency tracking │ P2P messaging │
├──────────────────────────────────────────────────────────┤
│ TIER 2: SUBAGENTS (Agent/Task Tool)                      │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐               │
│ │  Explore  │ │   Plan    │ │  General  │  Up to 10     │
│ │(read-only)│ │(read-only)│ │(full tool)│  concurrent   │
│ └───────────┘ └───────────┘ └───────────┘               │
│  Each: own context window │ custom system prompt         │
├──────────────────────────────────────────────────────────┤
│ TIER 1: MAIN AGENT                                       │
│  User ←→ Terminal/IDE ←→ Claude (Opus/Sonnet/Haiku)     │
│  Access: files, terminal, git, CLAUDE.md, MCP, all tools │
└──────────────────────────────────────────────────────────┘
```

### Tier 1 — Main Agent
The primary instance the user interacts with. Has access to everything: project files, terminal, git, CLAUDE.md memory, MCP servers, and all tools.

### Tier 2 — Subagents
Spawned via the **Agent tool** for isolated tasks. Each gets its own context window (up to 200K or 1M tokens), custom system prompt, and scoped tool access. Built-in types:
- **Explore** — Fast, read-only codebase search
- **Plan** — Implementation planning in read-only mode
- **General-purpose** — Full tool access for execution
- Up to **10 concurrent** with intelligent queuing
- **Cannot spawn other subagents** (single level only)

### Tier 3 — Agent Teams
Multiple Claude Code instances in parallel with shared task lists, dependency tracking, and peer-to-peer messaging. Each in its own **git worktree**. Enable: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Cost: **~3-7× a single session**.

---

## 4. Installation & Setup

### System Requirements

| Component | Requirement |
|-----------|-------------|
| **macOS** | 13.0+ (Ventura) |
| **Windows** | 10 1809+ or Server 2019+ |
| **Linux** | Ubuntu 20.04+, Debian 10+, Alpine 3.19+ |
| **Architecture** | x64 or ARM64 |
| **RAM** | 4 GB minimum |
| **Internet** | Required (always) |
| **Windows extra** | Git for Windows |

### Installation Commands

```bash
# macOS / Linux / WSL (recommended)
curl -fsSL https://claude.ai/install.sh | bash

# Windows PowerShell
irm https://claude.ai/install.ps1 | iex

# Windows CMD
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd

# Homebrew
brew install --cask claude-code

# WinGet
winget install Anthropic.ClaudeCode

# Specific version
curl -fsSL https://claude.ai/install.sh | bash -s 2.1.89

# Stable channel
curl -fsSL https://claude.ai/install.sh | bash -s stable

# Legacy npm (deprecated)
npm install -g @anthropic-ai/claude-code
```

### First Run
```bash
cd your-project
claude          # Opens interactive session
claude --version  # Verify installation
claude doctor   # Diagnose health
```

---

## 5. Authentication Methods

| Method | Setup | Best For |
|--------|-------|----------|
| **Claude Pro/Max/Team/Enterprise** | Browser OAuth on `claude` first run | Individual/team use |
| **Anthropic Console** | `ANTHROPIC_API_KEY` env var | API access with credits |
| **Amazon Bedrock** | `CLAUDE_CODE_USE_BEDROCK=true` + AWS creds; interactive wizard: `claude --bedrock-setup` (v2.1.92) | AWS infrastructure |
| **Google Vertex AI** | `CLAUDE_CODE_USE_VERTEX=true` + GCP creds; interactive wizard: `claude --vertex-setup` (v2.1.98) | GCP infrastructure |
| **Azure AI Foundry** | `CLAUDE_CODE_USE_FOUNDRY=1` + Azure creds | Azure infrastructure |
| **Custom helper** | `apiKeyHelper` setting → shell script | Enterprise SSO |

> **Note:** Free Claude.ai plan does NOT include Claude Code access.

---

## 6. CLAUDE.md Configuration System

### File Hierarchy (Load Order — All Concatenated)

```
Priority 1 (Highest):  Managed Policy CLAUDE.md
                        macOS: /Library/Application Support/ClaudeCode/CLAUDE.md
                        Linux: /etc/claude-code/CLAUDE.md
                        Windows: C:\Program Files\ClaudeCode\CLAUDE.md

Priority 2:            Project CLAUDE.md (team-shared, version-controlled)
                        ./CLAUDE.md  OR  ./.claude/CLAUDE.md

Priority 3:            User CLAUDE.md (personal, all projects)
                        ~/.claude/CLAUDE.md

Priority 4 (Lowest):   Local CLAUDE.md (personal, project-specific, gitignored)
                        ./CLAUDE.local.md
```

### Directory Walking Behavior
Claude Code walks **up** the directory tree from CWD, checking each directory for `CLAUDE.md` and `CLAUDE.local.md`. Files above CWD load at launch. Files in subdirectories load **on demand** when Claude reads files in those directories.

### Import System
```markdown
# In your CLAUDE.md
@README.md                    # Import project readme
@docs/architecture.md         # Import architecture docs
@docs/git-instructions.md     # Import workflow docs
@AGENTS.md                    # Cross-compatibility with AGENTS.md
```
- Recursive imports up to **5 hops deep**
- HTML comments stripped before injection

### What to Put in CLAUDE.md
- Project architecture and structure
- Build commands: `npm run build`, `dotnet build`
- Test instructions: `npm test -- --file path`
- Coding standards and style guidelines
- Naming conventions
- Common workflows
- Architectural decisions and patterns
- Preferred libraries and frameworks
- Review checklists
- Compact Instructions (preserved during compaction)

### Best Practices
- Target **under 200 lines** per file
- Use markdown headers and bullets
- Be specific: "Use 2-space indentation" not "Format code properly"
- Split large files using `@imports` or `.claude/rules/`
- Run `/init` to generate starter CLAUDE.md
- Run `/memory` to view all loaded memory files

---

## 7. Complete Slash Commands Reference

### Session Management
| Command | Aliases | Description |
|---------|---------|-------------|
| `/clear` | `/reset`, `/new` | Clears conversation history |
| `/compact [focus]` | — | Compresses context; optional focus area |
| `/exit` | `/quit` | Exits CLI |
| `/resume [session]` | `/continue` | Resume by ID, name, or picker |
| `/branch [name]` | `/fork` | Creates conversation fork / branch (renamed v2.1.80) |
| `/rename [name]` | — | Renames session |
| `/rewind` | `/checkpoint` | Restores code to previous point |
| `/export [filename]` | — | Export conversation as text |
| `/copy` | — | Copy last response to clipboard |

### Discovery & Debugging
| Command | Description |
|---------|-------------|
| `/help` | Shows all commands |
| `/context` | Token usage visualization with optimization tips |
| `/cost` | Detailed token usage and cost stats |
| `/doctor` | Diagnose installation health |
| `/feedback` / `/bug` | Submit feedback |
| `/hooks` | View hook configurations |
| `/commands` | List available commands |
| `/skills` | List available skills |
| `/debug [desc]` | Enable debug logging (bundled skill) |
| `/insights` | Session analytics and productivity stats |
| `/changelog` | View what changed in latest Claude Code update |
| `/todos` | View and manage current task list |

### Configuration
| Command | Description |
|---------|-------------|
| `/config` / `/settings` | Opens settings interface |
| `/permissions` / `/allowed-tools` | Manage tool permissions |
| `/model [model]` | Switch AI model (←/→ adjust effort) |
| `/effort [level]` | Set effort: `low` / `medium` / `high` (v2.1.72: `max` removed) |
| `/fast [on/off]` | Toggle fast mode for Opus 4.6 (v2.1.36) |
| `/output-style [style]` | Set output style |
| `/theme` | Change color theme |
| `/color` | Set Claude's response accent color (v2.1.75) |
| `/vim` | Toggle Vim editing mode |
| `/terminal-setup` | Configure keybindings |
| `/keybindings` | Interactive keybinding editor |
| `/sandbox` | Toggle sandbox mode |
| `/status` | Session status: version, model, account |
| `/reload-plugins` | Hot-reload installed plugins without restarting (v2.0.12+) |

### Project & Memory
| Command | Description |
|---------|-------------|
| `/init` | Initialize project with CLAUDE.md |
| `/memory` | Edit memory files, toggle auto-memory |
| `/add-dir <path>` | Add working directories |

### Integration
| Command | Description |
|---------|-------------|
| `/agents` | Manage subagent configurations |
| `/mcp` | Manage MCP server connections |
| `/ide` | Manage IDE integrations |
| `/chrome` | Configure Chrome settings |
| `/install-github-app` | Setup GitHub Actions |
| `/desktop` / `/app` | Continue in Desktop app |
| `/mobile` | QR code for mobile app |
| `/remote-control` / `/rc` | Make session controllable from claude.ai |
| `/team-onboarding` | Generate team onboarding guide for your codebase (v2.1.104) |

### Code & Review
| Command | Description |
|---------|-------------|
| `/diff` | Interactive diff viewer |
| `/review` | Start code review |
| `/security-review` | Security vulnerability analysis |
| `/pr-comments [PR]` | Show GitHub PR comments |
| `/plan [desc]` | Enter plan mode |

### Bundled Skills as Commands
| Command | Description |
|---------|-------------|
| `/batch <instruction>` | Parallel large-scale changes (5-30 units) |
| `/claude-api` | Load Claude API reference |
| `/loop [interval] <prompt>` | Run prompt on recurring schedule (v2.1.71) |
| `/simplify [focus]` | Three parallel review agents |
| `/btw <question>` | Side question (no context impact) |
| `/ultraplan [desc]` | Invoke extended planning mode for complex tasks |
| `/powerup` | Load all available skills into context (v2.1.90) |
| `/bashes` | List all Bash commands approved this session |

### Account
| Command | Description |
|---------|-------------|
| `/login` / `/logout` | Authentication |
| `/usage` | Plan limits and rate status |
| `/stats` | Daily usage and session history |
| `/extra-usage` | Configure overflow billing |
| `/voice` | Push-to-talk (hold spacebar, 20+ langs) |

---

## 8. Settings & Configuration

### Settings File Locations & Precedence

```
Highest Priority
  ↓  Managed settings (server → MDM/OS-level → file-based)
  ↓  Command line arguments
  ↓  Local project: .claude/settings.local.json
  ↓  Shared project: .claude/settings.json
  ↓  User settings: ~/.claude/settings.json
Lowest Priority
```

Array settings **merge** across scopes (concatenated, deduplicated). If **denied** at any level, no lower level can override.

### Key Settings Fields

```jsonc
{
  // Permission rules
  "permissions": {
    "allow": ["Read", "Grep", "Glob", "Bash(npm run *)"],
    "deny": ["Bash(rm -rf *)"],
    "ask": ["Write", "Edit"]
  },
  
  // Default permission mode
  "defaultMode": "default", // default|acceptEdits|plan|auto|dontAsk|bypassPermissions
  
  // Model override
  "model": "claude-sonnet-4-6-20260305",
  
  // Hooks (lifecycle events)
  "hooks": { /* see Hooks section */ },
  
  // Environment variables
  "env": {
    "CUSTOM_VAR": "value"
  },
  
  // Auto-update channel
  "autoUpdatesChannel": "stable", // stable|latest
  
  // Sandbox config
  "sandbox": {
    "enabled": false,
    "network": { "allowList": [], "allowMachLookup": true, "enableWeakerNetworkIsolation": false },
    "filesystem": { "allowWrite": [], "denyRead": [], "allowRead": [] },
    "failIfUnavailable": false  // v2.1.83: fail if sandbox cannot start
  },
  
  // Restrict available models
  "availableModels": ["claude-sonnet-4-6-*", "claude-opus-4-6-*"],
  
  // Response language
  "language": "en",
  
  // Auto-memory directory (v2.1.74) — defaults to ~/.claude/projects/<project>/memory/
  "autoMemoryDirectory": "/path/to/memory/dir",
  
  // Map friendly model aliases to specific model IDs (v2.1.73)
  "modelOverrides": {
    "opus": "claude-opus-4-6-20260305",
    "sonnet": "claude-sonnet-4-6-20260305"
  },
  
  // Attribution model for cost tracking (e.g. per-team billing)
  "attributionModel": "team-name",
  
  // Include git metadata in system prompt (v2.1.69)
  "includeGitInstructions": true,
  
  // Disable skill shell execution — skill scripts run in read-only mode (v2.1.91)
  "disableSkillShellExecution": false,
  
  // Prevent Claude Code from registering OS deep links (v2.1.83)
  "disableDeepLinkRegistration": false,
  
  // Restrict which plugin channels are allowed (enterprise, v2.1.84)
  "allowedChannelPlugins": ["anthropic-official"],
  
  // File suggestion in IDE integration (v2.0.65)
  "fileSuggestion": true,
  
  // Respect .gitignore for file discovery
  "respectGitignore": true,
  
  // Days before old sessions are purged from history
  "cleanupPeriodDays": 30,
  
  // Override the spinner tips shown during processing (v2.1.45)
  "spinnerTipsOverride": [],
  
  // Fraction (0–1) of sessions that are prompted for feedback survey
  "feedbackSurveyRate": 0.1,
  
  // Sparse checkout paths when using worktree isolation (v2.1.76)
  "worktree": {
    "sparsePaths": ["src/", "tests/"]
  },
  
  // MCP servers
  "mcpServers": { /* see MCP section */ }
}
```

---

## 9. Permission System

### Permission Modes

```
┌─────────────────────────────────────────────────────────┐
│              PERMISSION MODES (Shift+Tab to cycle)       │
├──────────────┬──────────────────────────────────────────┤
│ Default      │ Prompts for file edits + all tool use    │
│ Accept Edits │ Auto-approves edits + common FS commands │
│ Plan         │ READ-ONLY — proposes but can't execute   │
│ Auto         │ Classifier decides safety                │
│ Don't Ask    │ Denies anything not pre-approved         │
│ Bypass       │ Auto-approves EVERYTHING (danger!)       │
└──────────────┴──────────────────────────────────────────┘
```

### Permission Rule Syntax
```
Tool(pattern)     → Bash(npm run *)
Read(./.env)      → Specific file
mcp__github__*    → MCP server tools
```

### Hierarchy: Deny ALWAYS Wins
```
Enterprise Managed → deny: [...] 
      ↓ (cannot override)
User Settings → allow: [...], deny: [...], ask: [...]
      ↓
Project Settings → allow: [...], deny: [...], ask: [...]
      ↓
Local Settings → allow: [...], deny: [...], ask: [...]
```

---

## 10. Environment Variables

### API & Authentication
| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | API key for Console auth |
| `ANTHROPIC_AUTH_TOKEN` | Auth token override |
| `ANTHROPIC_BASE_URL` | Custom API endpoint |
| `ANTHROPIC_MODEL` | Override default model |

### Provider Selection
| Variable | Description |
|----------|-------------|
| `CLAUDE_CODE_USE_BEDROCK=1` | Use Amazon Bedrock |
| `CLAUDE_CODE_USE_MANTLE=1` | Use Amazon Bedrock powered by Mantle (v2.1.94) |
| `CLAUDE_CODE_USE_VERTEX=1` | Use Google Vertex AI |
| `CLAUDE_CODE_USE_FOUNDRY=1` | Use Azure AI Foundry |

### Behavior Control
| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` | — | Max output tokens per response |
| `CLAUDE_CODE_MAX_RETRIES` | 10 | Max API retries |
| `CLAUDE_CODE_EFFORT_LEVEL` | — | Effort level: `low` / `medium` / `high` (`max` removed in v2.1.72) |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | 83.5 | Auto-compact trigger (1-100) |
| `BASH_DEFAULT_TIMEOUT_MS` | — | Bash command timeout |
| `API_TIMEOUT_MS` | 600000 | API request timeout |
| `CLAUDE_CODE_NO_FLICKER=1` | — | Flicker-free alt-screen rendering (v2.1.89) |
| `CLAUDE_CODE_PERFORCE_MODE=1` | — | Enable Perforce VCS integration (v2.1.98) |
| `CLAUDE_STREAM_IDLE_TIMEOUT_MS` | — | Timeout for idle streaming connections |
| `CLAUDE_CODE_MAX_CONTEXT_TOKENS` | — | Cap context window token count |
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` | — | Max output tokens per response |
| `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` | — | Limit tokens returned from file read operations |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` | — | Strip credentials from Bash, hook, and MCP stdio subprocess environments (v2.1.83) |
| `CLAUDE_CODE_SCRIPT_CAPS` | — | Limit per-session script invocations (v2.1.98) |
| `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` | — | Force 200K context even when 1M is available |
| `DISABLE_COMPACT` | — | Disable auto-compaction entirely |
| `CLAUDE_CODE_DISABLE_CRON=1` | — | Disable CronCreate scheduling tool |
| `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` | — | Override SessionEnd hook timeout (default: 10 minutes) |
| `CLAUDE_CODE_EXIT_AFTER_STOP_DELAY` | — | Delay (ms) before exiting after Stop event |
| `CLAUDE_CODE_SHELL` | — | Override shell used for Bash tool (e.g. `/bin/zsh`) |
| `CLAUDE_CODE_TMPDIR` | — | Custom temp directory for Claude Code operations |
| `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1` | — | Keep Bash tool cwd anchored to project root |

### Model Pinning
| Variable | Description |
|----------|-------------|
| `ANTHROPIC_MODEL` | Override default primary model |
| `ANTHROPIC_SMALL_FAST_MODEL` | Override the small/fast model (Haiku-equivalent) |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Pin Sonnet version |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | Pin Opus version |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Pin Haiku version |
| `ANTHROPIC_CUSTOM_MODEL_OPTION` | Override the custom model dropdown option (v2.1.78) |
| `CLAUDE_CODE_SUBAGENT_MODEL` | Override subagent model |

### MCP & Plugins
| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TIMEOUT` | — | MCP server connection timeout |
| `MCP_TOOL_TIMEOUT` | — | Per-tool execution timeout (separate from connection) |
| `MAX_MCP_OUTPUT_TOKENS` | 25000 | Max MCP tool output |
| `ENABLE_TOOL_SEARCH` | true | Deferred tool loading |
| `CLAUDE_CODE_PLUGIN_SEED_DIR` | — | Pre-installed plugin directories for offline/headless installs (multiple paths: `:` on Unix, `;` on Windows) |
| `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS` | — | Timeout for git operations during plugin installation |
| `MCP_CONNECTION_NONBLOCKING=true` | — | Non-blocking MCP connections in `-p`/headless mode (v2.1.89) |

### Feature Flags
| Variable | Description |
|----------|-------------|
| `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` | Skip all CLAUDE.md loading |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` | Disable auto memory |
| `DISABLE_PROMPT_CACHING=1` | Disable prompt caching |
| `DISABLE_AUTOUPDATER=1` | Disable auto-updates |
| `CLAUDE_CODE_SIMPLE=1` | Minimal prompt (Bash/Read/Edit only) |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | Enable agent teams (still flag-gated) |
| `CLAUDE_CODE_ENABLE_POWERSHELL=1` | Enable opt-in PowerShell tool (Windows, v2.1.84) |
| `ENABLE_CLAUDEAI_MCP_SERVERS=false` | Opt out of claude.ai MCP connectors (v2.1.63) |
| `IS_DEMO=1` | Hide email/org info from UI (v2.1.0) |
| `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` | Disable background task scheduling |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` | Block non-essential network requests (telemetry, updates) |
| `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1` | Suppress auto-injected git workflow instructions |
| `CLAUDE_CODE_CERT_STORE=bundled` | Use only bundled CA certificates, not OS CA store (v2.1.104 changed default to trust OS CA) |

### OpenTelemetry (OTEL)
| Variable | Description |
|----------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP endpoint URL for traces/metrics/logs |
| `OTEL_LOG_USER_PROMPTS=1` | Include user prompt text in OTEL spans |
| `OTEL_LOG_TOOL_DETAILS=1` | Include tool parameters in OTEL events |
| `OTEL_LOG_TOOL_CONTENT=1` | Include tool result content in OTEL events |
| **`TRACEPARENT`** (auto-set) | W3C trace context propagated to Bash tool subprocesses when OTEL is enabled (v2.1.97) — enables child-process spans to parent correctly in distributed traces |

---

## 11. Complete Tools Inventory

### File Operations

| Tool | Permission | Description |
|------|-----------|-------------|
| **Read** | None | Read text, images, PDFs (≤100 pages), notebooks; offset/limit for large files |
| **Write** | Required | Create/overwrite files; auto-creates parent dirs |
| **Edit** | Required | Exact string search-and-replace; optional `replace_all` |
| **MultiEdit** | Required | Multiple edits in single operation |

### Search Tools

| Tool | Permission | Description |
|------|-----------|-------------|
| **Grep** | None | Regex search via ripgrep; case-insensitive, context lines, file type filter, multiline |
| **Glob** | None | File pattern matching; `**` recursive, `{}` alternatives; sorted by modification time |

### Execution & Web

| Tool | Permission | Description |
|------|-----------|-------------|
| **Bash** | Required | Persistent shell; configurable timeout; background execution |
| **PowerShell** | Required | Windows-native PowerShell tool; opt-in preview (v2.1.84, enable via `CLAUDE_CODE_ENABLE_POWERSHELL=1`) |
| **WebSearch** | Required | Web search for current information |
| **WebFetch** | Required | Fetch and analyze web pages; domain-controllable |

### Agent & Task Management

| Tool | Permission | Description |
|------|-----------|-------------|
| **Agent** (prev. Task) | None | Spawn subagents: description, prompt, type, model, background, max_turns |
| **ExitWorktree** | None | Exit current worktree and return to parent session (v2.1.72) |
| **CronCreate** | None | Schedule recurring task: cron expression + prompt; runs within session (v2.1.71) |
| **SendMessage** | None | Send message to another agent in the same team; P2P communication (Agent Teams) |
| **TodoWrite** | None | Task lists: id, content, status, priority |
| **NotebookEdit** | Required | Edit Jupyter notebook cells |
| **LSP** | None | Code intelligence: go-to-def, find refs, hover, symbols, call hierarchy |

### Monitoring & Observability

| Tool | Permission | Description |
|------|-----------|-------------|
| **Monitor** | None | Stream and filter events from background scripts/agents in real-time (v2.1.98) |

### Extension Tools

| Tool | Permission | Description |
|------|-----------|-------------|
| **Skill** | Required | Invoke custom skills; controllable via `Skill(name)` |
| **MCP tools** | Per-server | `mcp__<server>__<tool>` naming convention |

---

## 12. Hooks System

### Overview
Hooks are **deterministic guarantees** — unlike CLAUDE.md instructions which are advisory. User-defined shell commands, HTTP endpoints, or LLM prompts that execute at specific lifecycle points.

### Hook Events (25+)

```
SESSION LIFECYCLE          TOOL LIFECYCLE           AGENT LIFECYCLE
├── SessionStart           ├── PreToolUse *         ├── SubagentStart
├── SessionEnd             ├── PostToolUse          ├── SubagentStop
├── UserPromptSubmit *     ├── PostToolUseFailure   ├── TaskCreated
├── Stop *                 ├── PermissionDenied *   ├── TaskCompleted
├── StopFailure            │   (v2.1.89)            ├── TeammateIdle
├── Notification           CONTEXT & CONFIG
│                          ├── InstructionsLoaded   COMPACTION
WORKSPACE                  │   (v2.1.69)            ├── PreCompact
├── CwdChanged (v2.1.83)   ├── ConfigChange         ├── PostCompact (v2.1.76)
├── WorktreeCreate (v2.1.50)│  (v2.1.49)
├── WorktreeRemove (v2.1.50)├── FileChanged (v2.1.83)
                           INTERACTION              SETUP
                           ├── Elicitation (v2.1.76)├── Setup (v2.1.10)
                           ├── ElicitationResult         (--maintenance flag)
                               (v2.1.76)

* = Can block/modify behavior
```

### Configuration Structure

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",   // Regex for tool name
        "if": "Bash(rm *)",                   // Optional permission rule filter (v2.1.85)
        "once": true,                          // Run once per session then remove (v2.1.0)
        "hooks": [
          {
            "type": "command",                // command | http | prompt | agent
            "command": "python3 /scripts/validate.py",
            "timeout": 30000                  // ms; global hook timeout = 10 min (v2.1.3)
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "npm test || exit 2"   // Exit 2 = block, force continue
          }
        ]
      }
    ],
    "Setup": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "scripts/setup-env.sh" // Runs on --maintenance flag or Setup event (v2.1.10)
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "scripts/inject-session-title.sh"
            // hookSpecificOutput: { "sessionTitle": "string" } renames the session (v2.1.x)
          }
        ]
      }
    ]
  }
}
```

> **`disableAllHooks` setting:** Set `"disableAllHooks": true` in settings to completely disable all hook execution. `"disableSkillShellExecution": true` (v2.1.91) prevents skills from running shell commands.
>
> **`CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`**: Override the SessionEnd hook timeout (separate env var; default inherits the 10-minute global hook timeout).

### hookSpecificOutput

Some hooks support special output fields:

| Hook event | `hookSpecificOutput` field | Effect |
|-----------|---------------------------|--------|
| `UserPromptSubmit` | `sessionTitle` (string) | Renames the current session |
| `WorktreeCreate` | `worktreePath` (string) | Overrides the worktree directory path (v2.1.50) |

### Hook Types

| Type | Description | Added |
|------|-------------|-------|
| `command` | Run a shell command; stdin receives JSON context | Original |
| `http` | POST JSON to a URL endpoint (v2.1.63); response controls flow | v2.1.63 |
| `prompt` | Pass hook context to Claude as an LLM prompt | Original |
| `agent` | Spawn a full subagent to handle the event | Original |

**HTTP Hook Configuration (v2.1.63):**
```jsonc
{
  "PostToolUse": [{
    "matcher": "Write|Edit",
    "hooks": [{
      "type": "http",
      "url": "https://your-webhook.example.com/claude-hook",
      "timeout_ms": 5000          // Optional; default is 30000
    }]
  }]
}
```
The HTTP endpoint receives the same JSON body as the `stdin` of a `command` hook. Returning `{"permissionDecision": "deny"}` from a `PreToolUse` HTTP hook blocks execution.

### Hook Input (JSON on stdin)
```json
{
  "session_id": "abc-123",
  "transcript_path": "/path/to/transcript",
  "cwd": "/project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": { "file_path": "src/auth.ts", "content": "..." }
}
```

### Environment Variables in Hooks
| Variable | Description |
|----------|-------------|
| `$CLAUDE_PROJECT_DIR` | Project root |
| `$CLAUDE_SESSION_ID` | Current session |
| `$CLAUDE_TOOL_INPUT` | JSON tool input |
| `$CLAUDE_TOOL_INPUT_FILE_PATH` | File path from tool input |

### Exit Codes
| Code | Meaning |
|------|---------|
| 0 | Success — stdout parsed as JSON |
| 2 | Block — stops tool execution with error |
| Other | Warning — logged but doesn't block |

### PreToolUse Return Values
```json
{ "permissionDecision": "allow" }  // Auto-approve
{ "permissionDecision": "deny" }   // Block
{ "permissionDecision": "ask" }    // Prompt user
{ "permissionDecision": "defer" }  // Use normal flow
```

### Practical Examples

**Auto-format after edits:**
```jsonc
{
  "PostToolUse": [{
    "matcher": "Write|Edit|MultiEdit",
    "hooks": [{
      "type": "command",
      "command": "npx prettier --write \"$CLAUDE_TOOL_INPUT_FILE_PATH\""
    }]
  }]
}
```

**Block sensitive files:**
```jsonc
{
  "PreToolUse": [{
    "matcher": "Edit|Write",
    "hooks": [{
      "type": "command",
      "command": "python3 -c \"import sys,json; d=json.load(sys.stdin); p=d.get('tool_input',{}).get('file_path',''); sys.exit(2) if any(x in p for x in ['.env','package-lock.json','.git/']) else sys.exit(0)\""
    }]
  }]
}
```

**Desktop notification on pause:**
```jsonc
{
  "Notification": [{
    "hooks": [{
      "type": "command",
      "command": "notify-send 'Claude Code' 'Awaiting your input'"
    }]
  }]
}
```

---

## 13. MCP Integration

### Transport Types

| Transport | Use Case | Example |
|-----------|----------|---------|
| **HTTP (Streamable HTTP)** | Remote servers (recommended) | `claude mcp add --transport http notion https://mcp.notion.com/mcp` |
| **stdio** | Local processes | `claude mcp add --transport stdio db -- npx -y @bytebase/dbhub --dsn "postgres://..."` |
| **SSE** | Legacy (deprecated) | Use HTTP instead |

### Installation Scopes

| Scope | Stored In | Shared? | Loaded In |
|-------|-----------|---------|-----------|
| **Local** (default) | `~/.claude.json` | No | Current project only |
| **Project** | `.mcp.json` (repo root) | Yes (VCS) | Current project |
| **User** | `~/.claude.json` | No | All projects |

Precedence: Local > Project > User

### Tool Naming Convention
```
mcp__<server_name>__<tool_name>

Example: mcp__github__list_issues
         mcp__sentry__get_error
         mcp__db__query
```

### .mcp.json Format
```jsonc
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "db": {
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub", "--dsn", "${DB_CONNECTION_STRING}"],
      "env": {
        "DB_CONNECTION_STRING": "${DB_DSN:-postgresql://localhost:5432/dev}"
      }
    }
  }
}
```

### MCP Management Commands
```bash
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
claude mcp add --transport stdio db -- npx -y @bytebase/dbhub --dsn "..."
claude mcp list
claude mcp get <name>
claude mcp remove <name>
/mcp                          # In-session status check
```

### Popular MCP Servers
| Server | Transport | URL/Command |
|--------|-----------|-------------|
| **GitHub** | HTTP | `https://api.githubcopilot.com/mcp/` |
| **Sentry** | HTTP | `https://mcp.sentry.dev/mcp` |
| **Notion** | HTTP | `https://mcp.notion.com/mcp` |
| **PostgreSQL** | stdio | `npx -y @bytebase/dbhub --dsn "..."` |
| **Figma** | HTTP | `https://mcp.figma.com/mcp` |

> **Output limit:** 25,000 tokens default (configurable via `MAX_MCP_OUTPUT_TOKENS`)

### MCP Elicitation (v2.1.76)

MCP servers can now request structured input from the user mid-task via the **Elicitation** protocol. When a server sends an elicitation request (e.g., asking for credentials, a confirmation, or a form value), Claude Code pauses and presents the request to the user. Hooks `Elicitation` (pre) and `ElicitationResult` (post) fire around each request.

### MCP Tool Result Size Override (v2.1.91)

MCP tools can opt-in to returning up to **500K tokens** per result by including `_meta["anthropic/maxResultSizeChars"]` in their response. This is critical for tools that return large files, database dumps, or long logs:

```json
{
  "content": [{ "type": "text", "text": "...large content..." }],
  "_meta": { "anthropic/maxResultSizeChars": 500000 }
}
```

The default cap is still 25,000 tokens unless overridden.

---

## 14. Subagents Deep Dive

### Agent Tool Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `description` | string | 3-5 word task summary |
| `prompt` | string | Detailed instructions |
| `subagent_type` | string | `"general-purpose"`, `"Explore"`, `"Plan"`, or custom |
| `model` | string | `"sonnet"`, `"opus"`, `"haiku"` |
| `run_in_background` | boolean | For tasks >30 seconds |
| `max_turns` | number | Iteration limit |

### Built-in Subagent Types

| Type | Mode | Tools | Best For |
|------|------|-------|----------|
| **Explore** | Read-only | Read, Grep, Glob, LSP | Codebase investigation |
| **Plan** | Read-only | Read, Grep, Glob | Implementation planning |
| **General-purpose** | Full | All tools | Execution tasks |

### Custom Subagent Definition
File: `.claude/agents/code-reviewer.md`
```yaml
---
description: "Thorough code review with security focus"
tools:
  - Read
  - Grep
  - Glob
  - LSP
disallowedTools:
  - Write
  - Bash
model: sonnet
permissionMode: plan
maxTurns: 20
effort: high
background: false
color: "#FF6B35"
---

# Code Reviewer Agent

Review code changes for:
1. Security vulnerabilities (OWASP Top 10)
2. Performance anti-patterns
3. Coding standard violations per CLAUDE.md
4. Test coverage gaps
```

### Key Constraints
- Subagents **cannot spawn other subagents** (single level)
- Up to **10 concurrent** with intelligent queuing
- Each gets **own context window** (up to 200K or 1M)
- Main agent receives **summarized results** only

---

## 15. Agent Teams

### Architecture
```
┌─────────────────────────────────────────────┐
│               TEAM LEAD                      │
│  Creates team, spawns teammates, coordinates │
│  Assigns tasks, merges results               │
├─────────────────────────────────────────────┤
│ TEAMMATE 1    │ TEAMMATE 2    │ TEAMMATE 3  │
│ ┌───────────┐ │ ┌───────────┐ │ ┌─────────┐│
│ │ Worktree  │ │ │ Worktree  │ │ │Worktree ││
│ │ (branch)  │ │ │ (branch)  │ │ │(branch) ││
│ │ Own CTX   │ │ │ Own CTX   │ │ │Own CTX  ││
│ └───────────┘ │ └───────────┘ │ └─────────┘│
└─────────────────────────────────────────────┘
Communication: Shared task lists + dependency tracking + P2P messaging
```

### Enable & Display
```bash
# Enable (research preview)
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# Display modes
# In-process: all in main terminal, Shift+Down to cycle
# Split panes: tmux or iTerm2 for parallel viewing
```

### Best Practices
- **3-5 teammates** optimal
- **5-6 tasks per teammate**
- Start with **research before parallel implementation**
- **Avoid same-file edits** across teammates
- Cost: **~3-7× single session**

### SendMessage Tool (Agent P2P)

Teammates can communicate directly via `SendMessage` without routing through the lead. This is useful for progress updates and dependency notifications:

```
// Teammate 1 notifies Teammate 2 that shared library is ready
SendMessage(to="teammate-2", message="auth module complete at src/auth/index.ts")
```

### ExitWorktree (v2.1.72)

When a teammate finishes its work in an isolated worktree, it calls **ExitWorktree** to release the branch lock and signal completion back to the lead. The lead receives the result and can proceed with merging.

---

## 16. Prompt Caching & Cost Optimization

### How Caching Works
```
REQUEST STRUCTURE (prefix-based caching):

┌──────────────────────────────────┐
│ System prompt                     │  ← Cached (stable)
├──────────────────────────────────┤
│ CLAUDE.md content                │  ← Cached (stable)
├──────────────────────────────────┤
│ Tool schemas                     │  ← Cached (stable)
├──────────────────────────────────┤
│ Conversation history (growing)   │  ← Partially cached
├──────────────────────────────────┤
│ New message                      │  ← Never cached
└──────────────────────────────────┘

Only the newest content at the end differs between turns →
Everything before it = cache HIT
```

### Cache Pricing

| Token Type | Cost vs Base Input | TTL |
|------------|-------------------|-----|
| Cache Write | 1.25× (5-min) or 2× (1-hour) | 5 min / 1 hour |
| Cache Read (HIT) | **0.1×** (90% discount) | — |
| Non-cached Input | 1.0× | — |

### Economics
- **Break-even:** After single cache read (5-min TTL)
- **Typical hit rate:** 70-95% in active sessions
- **Example:** 400K input tokens, 95% hit rate → costs ~15% of non-cached pricing
- **Average cost:** ~$6/developer/day, <$12 for 90% of users
- **Monthly team average:** $100-200/developer with Sonnet 4.6

### What Breaks Cache
| Action | Impact |
|--------|--------|
| `/clear` | Resets conversation → all cache lost |
| Switching models | New prefix → all cache lost |
| Editing CLAUDE.md | Prefix changes → cache invalidated |
| TTL expiry | 5 minutes inactivity → cache drops |

### Maximizing Cache Hits
1. Keep sessions focused on one task
2. Use `/compact` instead of `/clear`
3. Don't change models or CLAUDE.md mid-session
4. Work in bursts within 5-minute window
5. Track with `/cost` (API) or `/stats` (subscription)

---

## 17. Context Window Management

### Context Structure (200K or 1M tokens)

```
┌─────────────────────────────────────────────┐
│ System prompt              ~2,700 tokens    │
├─────────────────────────────────────────────┤
│ System tools (schemas)    ~16,800 tokens    │
├─────────────────────────────────────────────┤
│ Custom agent descriptions  ~1,300 tokens    │
├─────────────────────────────────────────────┤
│ Memory files (CLAUDE.md)   ~7,400 tokens    │
├─────────────────────────────────────────────┤
│ Skill descriptions         ~1,000 tokens    │
├─────────────────────────────────────────────┤
│                                             │
│     MESSAGES + TOOL RESULTS                 │
│     (grows with conversation)               │
│                                             │
├─────────────────────────────────────────────┤
│ Autocompact buffer        ~33,000 tokens    │
└─────────────────────────────────────────────┘

Overhead BEFORE you type: ~30,000-40,000 tokens
```

### Compaction Mechanics
- **Auto-compaction triggers** at ~83.5% capacity (~167K for 200K window)
- Configurable via `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`
- Process: clears older tool outputs → summarizes conversation
- **CLAUDE.md survives** — re-read from disk and re-injected fresh
- `/compact [focus]` produces higher-quality summaries than auto-compact
- Since v2.0.64, compaction is **effectively instant**

### Quality Degradation
Performance degrades around **147K-152K tokens** due to "lost-in-the-middle" attention — not at the 200K limit. Token quality > quantity.

### Strategies
| Strategy | When | Why |
|----------|------|-----|
| `/clear` | Between unrelated tasks | Clean context, no carryover |
| `/compact [focus]` | At logical breakpoints | Higher quality than auto |
| Subagent delegation | Verbose operations | Each gets own context |
| Keep CLAUDE.md concise | Always | <200 lines target |
| Use `sonnet[1m]` / `opus[1m]` | Large codebases | 1M context avoids 200K limits |
| Session handoff | Long sessions | Write notes, start fresh |

---

## 18. Skills System

### Skill Structure
```
.claude/skills/my-skill/
├── SKILL.md          # Required: YAML frontmatter + instructions
├── templates/        # Optional: template files
├── examples/         # Optional: example code
└── scripts/          # Optional: helper scripts
```

### SKILL.md Format
```yaml
---
name: deploy
description: "Deploy application to staging or production"
argument-hint: "[staging|production]"
disable-model-invocation: false
user-invocable: true
allowed-tools:
  - Bash(npm run deploy:*)
  - Bash(az *)
model: sonnet
effort: high
context: fork          # Run in subagent
paths:
  - "deploy/**"
  - "infra/**"
hooks:
  PostToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo 'Deploy step completed'"
---

# Deploy Skill

Follow these steps to deploy:

1. Run `npm run build` to build the application
2. Run tests: `npm test`
3. Deploy to $ARGUMENTS environment
4. Verify health check at the target URL

## Arguments
- `staging` — Deploy to staging environment
- `production` — Deploy to production (requires approval)
```

### Key Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Slash command name |
| `description` | string | Used for auto-invocation matching |
| `argument-hint` | string | Autocomplete hint |
| `disable-model-invocation` | boolean | User-only invoke |
| `user-invocable` | boolean | Hide from menu if false |
| `allowed-tools` | array | Auto-approved tools |
| `model` | string | Override model |
| `effort` | string | Override effort level |
| `context` | string | `fork` = run in subagent |
| `paths` | array | Glob patterns for conditional activation |
| `hooks` | object | Lifecycle hooks scoped to skill |

### Skill Discovery Locations
1. Enterprise managed settings (highest priority)
2. Personal: `~/.claude/skills/<name>/SKILL.md`
3. Project: `.claude/skills/<name>/SKILL.md`
4. Plugin skills

### Loading Behavior
- **Descriptions** always in context (budget: 1% of context window)
- **Full content** loads only when invoked (user or auto)
- Invoked content **stays for session** and **survives auto-compaction**

### String Substitutions
| Placeholder | Description |
|-------------|-------------|
| `$ARGUMENTS` | All arguments after command |
| `$ARGUMENTS[N]` | Nth argument (0-indexed) |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_SKILL_DIR}` | Skill directory path |

### Dynamic Context Injection
````markdown
# In SKILL.md content:
Current PR diff:
!`gh pr diff`

Current git status:
!`git status --short`
````
Shell commands run before content reaches Claude.

---

## 19. Rules System

### Location
```
.claude/rules/           # Project-level
~/.claude/rules/         # User-level
```
Each `.md` file covers one topic. Discovered recursively, supports symlinks.

### Unconditional Rules
Rules without YAML frontmatter load at launch (same priority as `.claude/CLAUDE.md`):
```markdown
# Code Style Rules

Always use 2-space indentation in TypeScript files.
Prefer `const` over `let` unless reassignment is required.
```

### Conditional (Path-Scoped) Rules
```yaml
---
paths:
  - "src/api/**/*.ts"
  - "src/controllers/**/*.ts"
---

# API Development Rules

All API endpoints must include input validation using Zod schemas.
Every controller method must have JSDoc documentation.
Error responses must follow RFC 7807 Problem Details format.
```
Triggered **only when Claude reads matching files**.

### Rules vs CLAUDE.md vs Skills

| Feature | CLAUDE.md | Rules | Skills |
|---------|-----------|-------|--------|
| Location | Root / subdirectory | `.claude/rules/` | `.claude/skills/` |
| Loading | Session start | Session start (unconditional) or on-demand (conditional) | On invoke only |
| Organization | Single file + imports | Multiple focused files | Full packages |
| Path scoping | Via subdirectory placement | YAML `paths` field | YAML `paths` field |
| Best for | Core project instructions | Modular per-topic rules | Reusable workflows |

---

## 20. Custom Commands (Legacy)

```
.claude/commands/          # Project-level
~/.claude/commands/        # User-level
```

A file at `.claude/commands/deploy.md` creates `/deploy`. Contents become the prompt.

```markdown
<!-- .claude/commands/fix-tests.md -->
Run the test suite and fix all failing tests.
Focus on: $ARGUMENTS
Commit the fixes with descriptive messages.
```

> **Note:** Skills system is the recommended replacement. If a skill and command share the same name, the **skill takes precedence**.

---

## 21. IDE Integration

### VS Code Extension
- Requires VS Code **1.98.0+**
- Also supports **Cursor**, **Windsurf**, **VSCodium**
- Install via Extensions marketplace → "Claude Code"
- Open: ✱ Spark icon, `Cmd+Shift+P` → "Claude Code", or Activity Bar

#### Key Features
- **Inline diffs** with accept/reject
- **@-mentions** for fuzzy file references
- **Plan review** as markdown with inline comments
- **Checkpoints** with three rewind options
- **Multiple conversations** with colored status dots

#### Key Shortcuts
| Shortcut | Action |
|----------|--------|
| `Cmd+Esc` | Toggle focus editor ↔ Claude |
| `Option+K` | Insert @-mention from editor |
| `Cmd+Shift+Esc` | New conversation tab |

### JetBrains Plugin
- IntelliJ, PyCharm, WebStorm, all JetBrains IDEs
- `Cmd+Esc` quick launch
- IDE-native diff viewing
- `Cmd+Option+K` file reference shortcut

### Terminal Integration
- `claude` in VS Code terminal auto-detects IDE
- `/ide` connects external terminal to VS Code/JetBrains
- Extension and CLI share conversation history

---

## 22. Headless Mode & CI/CD

### Non-Interactive Usage
```bash
# Basic headless
claude -p "refactor the auth module"

# With output format
claude -p "review code" --output-format json

# With structured output
claude -p "list all API endpoints" --json-schema '{"type":"array","items":{"type":"object","properties":{"path":{"type":"string"},"method":{"type":"string"}}}}'

# With scoped permissions
claude -p "fix tests" --allowedTools "Read,Write,Edit,Bash(npm test *)" --permission-mode dontAsk

# With max turns
claude -p "implement feature X" --max-turns 20

# Bare mode (reproducible CI)
claude -p "check code quality" --bare

# Piped input
git diff main | claude -p "review for security issues" --allowedTools "Read,Grep"
cat error.log | claude -p "find root cause"
```

### Key Headless Flags
| Flag | Description |
|------|-------------|
| `-p` / `--print` | Non-interactive mode |
| `--output-format` | `text`, `json`, `stream-json` |
| `--json-schema` | Structured output schema |
| `--allowedTools` | Scoped tool permissions |
| `--permission-mode` | `default`, `acceptEdits`, `plan`, `dontAsk`, `bypassPermissions` |
| `--max-turns` | Iteration limit |
| `--bare` | Skip auto-discovery of CLAUDE.md + memory (reproducible CI; v2.1.81) |
| `--channels` | Subscribe to named event channels for pub/sub messaging (v2.1.80) |
| `--exclude-dynamic-system-prompt-sections` | Strip volatile auto-injected system prompt sections (e.g., date headers) for cross-user prompt caching in CI (v2.1.98) |
| `-w` / `--worktree <path>` | Start session in specified Git worktree (v2.1.49) |
| `--append-system-prompt` | Inject instructions |
| `--system-prompt` | Full system prompt override |

### GitHub Actions
```yaml
name: Claude Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: "Review this PR for security issues and code quality"
          trigger_phrase: "@claude"
```

Quick setup: `/install-github-app`

---

## 23. Security & Sandboxing

### Defense in Depth
- Default posture: **read-only** (explicit permission required for writes/commands)
- Permission hierarchy: **deny always wins** → ask → allow
- Enterprise managed settings **cannot be overridden**

### Sandbox Mode
Enable: `/sandbox`
- **macOS:** Seatbelt framework
- **Linux:** bubblewrap (`sudo apt install bubblewrap socat`)
- Reduces permission prompts by **~84%**
- Filesystem writes restricted to CWD
- Network isolation via proxy server

### Built-in Protections
- `curl` and `wget` blocked by default
- Input sanitization prevents command injection
- Command injection detection: suspicious commands require manual approval even if allowlisted
- Web fetch uses separate context (anti-prompt-injection)
- First-time codebase runs require verification
- New MCP servers require verification
- OS CA certificate store trusted by default (v2.1.104) — no need to configure custom CA bundles

> ⚠️ **`--dangerously-skip-permissions`** should ONLY be used in Docker containers without internet. A documented incident resulted in total file loss via `rm -rf`.

---

## 23b. Plugin System (v2.0.12+)

> Introduced October 2025. Plugins extend Claude Code with new slash commands, tools, hooks, and CLAUDE.md content — without modifying core files.

### Plugin Installation
```bash
# Install from the marketplace
claude plugin install anthropic/git-utils
claude plugin install anthropic/test-runner

# List installed plugins
claude plugin list

# Enable / disable without uninstalling
claude plugin enable git-utils
claude plugin disable git-utils

# Validate plugin integrity
claude plugin validate git-utils

# Update all plugins
claude plugin update

# Hot-reload without restarting session
/reload-plugins
```

### Plugin Structure
A plugin is a directory with a `plugin.json` manifest:

```jsonc
// .claude/plugins/my-plugin/plugin.json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Adds project-specific commands",
  "skills": ["./skills/"],       // auto-load all SKILL.md files in directory
  "claude_md": "./CLAUDE.md",    // appended to root CLAUDE.md
  "hooks": {                      // merged into session hooks
    "PostToolUse": [...]
  }
}
```

### Enterprise Plugin Distribution

Enterprise admins can pre-install plugins via **managed-settings.d/** (v2.1.83) — a drop-in directory of JSON fragments that are merged at startup without overwriting user settings:

```
/etc/claude/managed-settings.d/
├── 01-org-policy.json      # allow/deny rules
├── 02-approved-plugins.json # auto-install list
└── 03-mcp-servers.json     # shared MCP servers
```

Each `.json` file follows the same schema as `settings.json`. Files are processed in lexicographic order. Managed settings take highest precedence and cannot be overridden by user or project settings.

**Enterprise MDM delivery:**
- **macOS:** `com.anthropic.claudecode` preference domain via `defaults write` or profiles
- **Windows:** `HKLM\SOFTWARE\Anthropic\ClaudeCode` registry keys (v2.1.51)
- **`forceRemoteSettingsRefresh`** policy (v2.1.92): forces pull of latest managed settings on every session start

---

## 24. Development Workflows

### Core Workflow: Explore → Plan → Code → Commit

```
1. EXPLORE     "How does authentication work in this codebase?"
      ↓
2. PLAN        Shift+Tab ×2 → Plan mode → reviewable markdown
      ↓
3. CODE        Shift+Tab → Accept Edits or Default mode
      ↓
4. COMMIT      "commit my changes with a descriptive message"
      ↓
5. PR          "create a PR for this feature"
```

### TDD Pattern
```
"Write tests for the auth module first, then implement to make them pass"
```
- Give verification targets: test cases, screenshots, expected output
- Test incrementally: one file at a time
- Use `/debug` for structured debugging

### Git Integration
- Auto-staging, commit messages, branch creation, PR opening
- `git diff main --name-only | claude -p "review changed files for security"`
- `/install-github-app` for automated GitHub Actions
- `claude --worktree feature-auth` for isolated parallel work

### Large Codebase Strategies
- Install code intelligence plugins (LSP)
- Use Explore subagents for investigation
- Run `/init` to generate CLAUDE.md
- Use `.claudeignore` to exclude irrelevant files
- `/batch <instruction>` for 5-30 independent parallel units

---

## 25. Troubleshooting

### /doctor Checks
- Installation type and version
- Search functionality (ripgrep)
- Keybinding configuration
- System status
- Performance metrics

### Common Issues

| Problem | Solution |
|---------|----------|
| `command not found: claude` | Add `~/.local/bin` to PATH |
| `syntax error near '<'` | Install script returned HTML; use Homebrew |
| `Killed` during install (Linux) | Add 2GB swap (needs 4GB RAM) |
| TLS/SSL errors | Update CA certs; `NODE_EXTRA_CA_CERTS` for corporate proxies |
| "organization disabled" with active sub | Check for `ANTHROPIC_API_KEY` env var overriding subscription |
| Auto-compaction thrashing | Context ping-ponging; use `/clear` and start fresh |

### Log Locations
| Item | Path |
|------|------|
| User settings | `~/.claude/settings.json` |
| Project settings | `.claude/settings.json` |
| Debug logs | `~/.claude/debug/` |
| Session data | `~/.claude/projects/` |
| Binary (macOS/Linux) | `~/.local/bin/claude` |
| Binary (Windows) | `%USERPROFILE%\.local\bin\claude.exe` |

---

## 26. Complete Glossary

| Term | Definition |
|------|-----------|
| **Agentic loop** | Core cycle: gather context → take action → verify results, repeated autonomously |
| **Tool use** | Claude invoking system capabilities (Read, Write, Bash, etc.) |
| **Subagent** | Specialized Claude instance via Agent tool with isolated context |
| **Headless mode** | Non-interactive CLI via `-p` flag for automation/CI |
| **Compact/Compaction** | Summarizing history to free context space |
| **CLAUDE.md** | Markdown config files teaching Claude project conventions |
| **Hooks** | Deterministic shell/HTTP/LLM commands at lifecycle points |
| **MCP** | Model Context Protocol — open standard for external tool integration |
| **Skills** | Modular SKILL.md packages with specialized knowledge |
| **Rules** | Modular `.claude/rules/*.md` instruction files |
| **Custom commands** | Legacy `.claude/commands/*.md` slash commands |
| **Agent teams** | Multiple Claude instances with shared tasks and messaging |
| **Plan mode** | Read-only mode — proposes without executing |
| **Context window** | Total token budget (200K or 1M) |
| **Worktree** | Isolated git worktree for parallel work |
| **Cache hit** | Input matches cached prefix → 90% cost reduction |
| **Permission mode** | One of six autonomy levels |
| **Auto memory** | Automatic recording/recall across sessions |
| **Checkpoint** | Auto-saved code state; rewind via `Esc+Esc` |
| **Remote control** | Bridge connecting terminal to web/mobile |
| **Sandbox** | OS-level filesystem/network isolation |
| **Bare mode** | `--bare` flag for reproducible environments |
| **Fast mode** | Quick responses on Opus 4.6 |
| **Effort level** | Controls reasoning depth: low/medium/high/max/auto |
| **Tool search** | Deferred MCP tool loading — names only at start |

---

## 27. Power User Tips & Shortcuts

### Essential Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Escape` | Cancel operation or clear input |
| `Esc+Esc` (double) | Open rewind menu |
| `Ctrl+C` | Stop response; double-tap = hard exit |
| `Shift+Enter` | New line in input |
| `Shift+Tab` | Cycle permission modes |
| `Ctrl+R` | Search prompt history |
| `Ctrl+G` | Open prompt in `$EDITOR` |
| `Ctrl+B` | Move bash command to background |
| `Alt+T` | Toggle extended thinking |
| `Alt+P` | Open model picker |

> **macOS Tip:** Configure Option as Meta key in terminal for Alt shortcuts.

### High-Impact Techniques
1. **`/btw` for side questions** — no context impact
2. **Pipe data:** `cat error.log | claude -p "find root cause"`
3. **Git worktrees:** `claude --worktree feature-name`
4. **Let Claude interview you:** "I want to build X. Ask me clarifying questions."
5. **Interrupt early** with `Escape` if heading wrong direction
6. **Use `/compact` at logical breakpoints** instead of waiting for auto-compact

### Cost Optimization Hierarchy
1. Choose model strategically: Sonnet (most tasks), Opus (complex), Haiku (simple subagents)
2. `/clear` between unrelated tasks; `/compact` at logical breakpoints
3. Move specialized instructions from CLAUDE.md to skills (on-demand loading)
4. `/effort low` for simple tasks
5. Delegate verbose operations to subagents
6. Be specific in prompts: "add input validation to auth.ts" > "improve this codebase"
7. Disable unused MCP servers
8. Install code intelligence plugins to reduce file reads

---

## 28. Update Timeline

### 2025
| Date | Milestone |
|------|-----------|
| Feb 2025 | Launch as limited research preview |
| May 22, 2025 | GA (v1.0.0): Opus 4, Sonnet 4, GH Actions, VS Code + JetBrains |
| Sep 29, 2025 | Sonnet 4.5 (SWE 77.2%): checkpoints, subagents, hooks, Agent SDK |
| Oct 2025 | Web version + iOS app; Agent Skills system (v2.0.12) + plugin marketplace |
| Nov 1, 2025 | Opus 4.5 (SWE 80.9%); surpassed $1B ARR |
| Dec 2025 | `.claude/rules/`, named sessions, agentskills.io |

### 2026
| Date | Milestone |
|------|-----------|
| Jan 2026 | SKILL.md hot-reload (v2.1.0), session forking, Claude Cowork |
| Feb 5, 2026 | Opus 4.6 (SWE 80.8%, 1M beta), agent teams, auto memories, remote control |
| Feb 28, 2026 | Task tool renamed to Agent tool (v2.1.63); HTTP hooks; `--worktree` flag |
| Mar 2026 | Sonnet 4.6 (SWE 79.6%, 1M native), /loop (v2.1.71), effort simplified to low/medium/high (v2.1.72) |
| Mar 2026 | 1M context for Opus 4.6 on Max/Team/Enterprise (v2.1.75); MCP elicitation (v2.1.76) |
| Mar 2026 | `--channels` pub/sub flag (v2.1.80); `--bare` CI flag (v2.1.81); `managed-settings.d/` (v2.1.83) |
| Mar 2026 | PowerShell tool opt-in preview for Windows (v2.1.84); `CLAUDE_CODE_NO_FLICKER` (v2.1.89); `/powerup` (v2.1.90) |
| Apr 2026 | Bedrock setup wizard (v2.1.92); `forceRemoteSettingsRefresh` policy; default effort → high for professional tiers (v2.1.94) |
| Apr 2026 | `CLAUDE_CODE_USE_MANTLE=1` for Bedrock-Mantle (v2.1.94); `refreshInterval` status line setting + W3C `TRACEPARENT` propagation to Bash subprocesses (v2.1.97) |
| Apr 2026 | Monitor tool (v2.1.98); Vertex AI setup wizard; `CLAUDE_CODE_PERFORCE_MODE` |
| Apr 12, 2026 | OS CA certificate store trusted by default (v2.1.104); `/team-onboarding` command |

### Current Version: v2.1.104 (April 12, 2026)

### Current Models

| Model | SWE-bench | Context | Input / Output | Notes |
|-------|-----------|---------|---------------|-------|
| Opus 4.6 | 80.8% | 1M tokens (Max/Team/Enterprise) | $5 / $25 per MTok | Default for API/Bedrock/Vertex/Team/Enterprise (v2.1.94) |
| Sonnet 4.6 | 79.6% | 1M tokens native | $3 / $15 per MTok | Default for Pro plan |
| Haiku 4.5 | — | 200K tokens | Lowest tier | Fast mode subagents |

---

## 29. Directory Map

```
YOUR PROJECT/
├── CLAUDE.md                  # Project instructions (team-shared, VCS)
├── CLAUDE.local.md            # Local override (gitignored)
├── .claudeignore              # Files to exclude
├── .mcp.json                  # MCP server config (project scope)
└── .claude/
    ├── CLAUDE.md              # Alt location for project instructions
    ├── settings.json          # Project settings (team-shared)
    ├── settings.local.json    # Local settings (gitignored)
    ├── rules/                 # Modular instruction files
    │   ├── code-style.md
    │   ├── testing.md
    │   └── api-standards.md
    ├── skills/                # Custom skills
    │   ├── deploy/
    │   │   ├── SKILL.md
    │   │   └── scripts/
    │   └── db-migration/
    │       └── SKILL.md
    ├── agents/                # Custom subagents
    │   ├── code-reviewer.md
    │   └── security-auditor.md
    └── commands/              # Legacy custom commands
        └── fix-tests.md

~/.claude/                     # User-level (all projects)
├── CLAUDE.md                  # User instructions
├── settings.json              # User settings
├── rules/                     # User-level rules
├── skills/                    # Personal skills
├── agents/                    # Personal subagents
├── debug/                     # Debug logs
└── projects/<hash>/
    └── memory/
        ├── MEMORY.md          # Auto memory index
        └── *.md               # Topic memory files
```

---

## CCA-F Exam Focus Areas

For the Claude Certified Architect Foundations exam, prioritize understanding:

1. **Agentic Architecture & Orchestration:** The three-tier architecture (main → subagent → teams), agentic loop mechanics, how/when subagents spawn, agent team coordination
2. **Claude Code Configuration & Workflows:** CLAUDE.md hierarchy and precedence, settings cascade, /init workflow, explore→plan→code→commit pattern
3. **Prompt Engineering & Structured Output:** How CLAUDE.md instructions affect behavior, headless mode with --json-schema, effort levels
4. **Tool Design & MCP Integration:** All built-in tools and permissions, MCP transport types, tool naming convention, .mcp.json configuration
5. **Context Management & Reliability:** Context window structure, compaction triggers, cache economics, hooks for deterministic control, permission model (deny always wins)

---

*This guide is comprehensive as of April 2026. Claude Code evolves rapidly — always cross-reference with official docs at [code.claude.com/docs](https://code.claude.com/docs) and [docs.anthropic.com/en/docs/claude-code](https://docs.anthropic.com/en/docs/claude-code).*
