"use strict";
const { useState } = React;
const COLORS = {
  enterprise: { bg: "#DC2626", light: "#FEE2E2", border: "#EF4444", text: "#991B1B" },
  project: { bg: "#2563EB", light: "#DBEAFE", border: "#3B82F6", text: "#1E40AF" },
  user: { bg: "#7C3AED", light: "#EDE9FE", border: "#8B5CF6", text: "#5B21B6" },
  local: { bg: "#059669", light: "#D1FAE5", border: "#10B981", text: "#065F46" },
  skill: { bg: "#B45309", light: "#FEF3C7", border: "#F59E0B", text: "#78350F" },
  hook: { bg: "#0369A1", light: "#E0F2FE", border: "#0284C7", text: "#0C4A6E" },
  style: { bg: "#BE185D", light: "#FCE7F3", border: "#F472B6", text: "#831843" },
  rule: { bg: "#0D9488", light: "#CCFBF1", border: "#14B8A6", text: "#115E59" },
  perm: { bg: "#0F172A", light: "#E2E8F0", border: "#334155", text: "#0F172A" }
};
const scenarios = [
  // ──────── TEST 1 ────────
  {
    id: 1,
    title: "CLAUDE.md: User vs Project (Indent Style)",
    category: "CLAUDE.md Override",
    color: COLORS.project,
    difficulty: "\u2B50 Easy",
    whatWeTest: "When User CLAUDE.md says '2-space indent' but Project CLAUDE.md says '4-space indent', which instruction does Claude follow?",
    expectedWinner: "PROJECT wins \u2192 4-space indentation",
    whyItWins: "Project (Priority 4) overrides User (Priority 5). More specific scope wins.",
    files: [
      {
        path: "~/.claude/CLAUDE.md",
        label: "User CLAUDE.md",
        tier: "User (Priority 5)",
        content: `# My Global Preferences
- ALWAYS use 2-space indentation in all code
- Use single quotes for strings
- Prefer arrow functions over regular functions`
      },
      {
        path: "./CLAUDE.md",
        label: "Project CLAUDE.md",
        tier: "Project (Priority 4)",
        content: `# Project Standards
- ALWAYS use 4-space indentation in all code
- Use double quotes for strings
- Use named function declarations, never arrow functions`
      }
    ],
    testPrompt: "Create a JavaScript function called calculateTotal that takes an array of prices and a tax rate, applies the tax, and returns the total. Include proper formatting.",
    verification: [
      "Check: Does the code use 4-space indent? \u2192 Project won \u2705",
      "Check: Does it use double quotes? \u2192 Project won \u2705",
      "Check: Is it a named function (not arrow)? \u2192 Project won \u2705",
      "If 2-space/single-quotes/arrow \u2192 User won (unexpected) \u274C"
    ],
    cleanupNote: "Restore your original ~/.claude/CLAUDE.md after testing!"
  },
  // ──────── TEST 2 ────────
  {
    id: 2,
    title: "CLAUDE.local.md Overrides Project CLAUDE.md",
    category: "CLAUDE.md Override",
    color: COLORS.local,
    difficulty: "\u2B50 Easy",
    whatWeTest: "Project CLAUDE.md says 'use REST API', but your CLAUDE.local.md says 'use GraphQL'. Which does Claude follow for YOU?",
    expectedWinner: "LOCAL wins \u2192 GraphQL pattern",
    whyItWins: "CLAUDE.local.md (Priority 3) overrides Project CLAUDE.md (Priority 4). Your personal project override beats the team standard.",
    files: [
      {
        path: "./CLAUDE.md",
        label: "Project CLAUDE.md",
        tier: "Project (Priority 4)",
        content: `# API Standards
- ALWAYS create REST APIs with Express.js
- Use route handlers: GET /resource, POST /resource
- Return JSON with { data, error, status } wrapper
- Use camelCase for all field names`
      },
      {
        path: "./CLAUDE.local.md",
        label: "CLAUDE.local.md",
        tier: "Local (Priority 3)",
        content: `# My Local Override
- ALWAYS create GraphQL APIs with Apollo Server
- Use resolvers and type definitions pattern
- Return data through GraphQL schema types
- Use PascalCase for type names, camelCase for fields`
      }
    ],
    testPrompt: "Create an API endpoint for managing a list of books (CRUD operations). Show the full implementation.",
    verification: [
      "Check: Does it use GraphQL/Apollo? \u2192 Local won \u2705",
      "Check: Does it use resolvers/typeDefs? \u2192 Local won \u2705",
      "If it uses Express/REST routes \u2192 Project won (unexpected) \u274C",
      "Note: Your teammates WITHOUT CLAUDE.local.md will get REST"
    ],
    cleanupNote: "Delete CLAUDE.local.md after testing \u2014 it's auto-gitignored anyway."
  },
  // ──────── TEST 3 ────────
  {
    id: 3,
    title: "Child/Subtree CLAUDE.md Override (Monorepo Pattern)",
    category: "CLAUDE.md Override",
    color: COLORS.rule,
    difficulty: "\u2B50\u2B50 Medium",
    whatWeTest: "Root CLAUDE.md says 'use Jest for testing' but src/api/CLAUDE.md says 'use Vitest for testing'. When working in the API folder, which wins?",
    expectedWinner: "CHILD wins \u2192 Vitest (when working in src/api/)",
    whyItWins: "Subtree CLAUDE.md is more specific. When Claude reads files in src/api/, the child file loads and overrides the parent for that subtree.",
    files: [
      {
        path: "./CLAUDE.md",
        label: "Root CLAUDE.md",
        tier: "Project Root",
        content: `# MyApp Project
- ALWAYS use Jest for all testing
- Use describe/it blocks
- Place test files next to source files as *.test.ts
- Use jest.mock() for mocking dependencies`
      },
      {
        path: "./src/api/CLAUDE.md",
        label: "Child CLAUDE.md",
        tier: "Subtree (more specific)",
        content: `# API Module Standards
- ALWAYS use Vitest for testing in this module
- Use describe/it blocks with vi.mock() for mocking
- Place test files in __tests__/ subfolder
- Import from vitest: import { describe, it, expect, vi } from 'vitest'`
      }
    ],
    testPrompt: "Write a unit test for a function at src/api/services/userService.ts that fetches user by ID from the database. Include mocking.",
    verification: [
      "Check: Does it import from 'vitest'? \u2192 Child won \u2705",
      "Check: Does it use vi.mock() (not jest.mock)? \u2192 Child won \u2705",
      "Check: Is test in __tests__/ subfolder? \u2192 Child won \u2705",
      "Now ask for a test at src/components/Button.tsx \u2192 should use Jest (root rules)"
    ],
    cleanupNote: "Make sure to create the src/api/ directory structure first: mkdir -p src/api"
  },
  // ──────── TEST 4 ────────
  {
    id: 4,
    title: "Settings.json Permission: Project Deny vs User Allow",
    category: "Settings Override",
    color: COLORS.perm,
    difficulty: "\u2B50\u2B50 Medium",
    whatWeTest: "User settings allow 'Bash(curl *)' but Project settings deny it. Can Claude run curl commands?",
    expectedWinner: "PROJECT DENY wins \u2192 curl is BLOCKED",
    whyItWins: "Project (Priority 4) beats User (Priority 5). But MORE IMPORTANTLY: deny rules always win over allow rules regardless of tier.",
    files: [
      {
        path: "~/.claude/settings.json",
        label: "User settings.json",
        tier: "User (Priority 5)",
        content: `{
  "permissions": {
    "allow": [
      "Bash(curl *)",
      "Bash(wget *)"
    ]
  }
}`
      },
      {
        path: ".claude/settings.json",
        label: "Project settings.json",
        tier: "Project (Priority 4)",
        content: `{
  "permissions": {
    "deny": [
      "Bash(curl *)",
      "Bash(wget *)"
    ]
  }
}`
      }
    ],
    testPrompt: "Use curl to fetch the content from https://httpbin.org/get and show me the response.",
    verification: [
      "Check: Does Claude refuse to run curl? \u2192 Deny won \u2705",
      "Check: Does Claude ask for permission? \u2192 Deny blocked it \u2705",
      "If curl runs without asking \u2192 Something is wrong \u274C",
      "Claude should say it cannot run this command or ask for manual approval"
    ],
    cleanupNote: "Remove the deny rule from .claude/settings.json after testing."
  },
  // ──────── TEST 5 ────────
  {
    id: 5,
    title: "Settings.json: Local Allow Overrides Project Deny",
    category: "Settings Override",
    color: COLORS.local,
    difficulty: "\u2B50\u2B50 Medium",
    whatWeTest: "Project denies 'Bash(curl *)', but your LOCAL settings allow it. Can YOU (and only you) use curl?",
    expectedWinner: "LOCAL ALLOW wins \u2192 curl works FOR YOU ONLY",
    whyItWins: "Local (Priority 3) beats Project (Priority 4). Your personal override restores the permission that the team blocked. But managed/enterprise deny would still win over this.",
    files: [
      {
        path: ".claude/settings.json",
        label: "Project settings.json",
        tier: "Project (Priority 4)",
        content: `{
  "permissions": {
    "deny": [
      "Bash(curl *)"
    ]
  }
}`
      },
      {
        path: ".claude/settings.local.json",
        label: "Local settings.json",
        tier: "Local (Priority 3) \u2190 HIGHER",
        content: `{
  "permissions": {
    "allow": [
      "Bash(curl *)"
    ]
  }
}`
      }
    ],
    testPrompt: "Use curl to fetch https://httpbin.org/get and show the response.",
    verification: [
      "Check: Does curl run without being blocked? \u2192 Local won \u2705",
      "Check: Compare with Test 4 (without local override) \u2192 it was blocked there",
      "This proves Local (Priority 3) > Project (Priority 4)",
      "Your teammates WITHOUT settings.local.json still get denied"
    ],
    cleanupNote: "Delete .claude/settings.local.json after testing."
  },
  // ──────── TEST 6 ────────
  {
    id: 6,
    title: "Enterprise/Managed Deny Cannot Be Overridden",
    category: "Settings Override",
    color: COLORS.enterprise,
    difficulty: "\u2B50\u2B50\u2B50 Advanced",
    whatWeTest: "Enterprise managed-settings.json denies 'Bash(rm -rf *)'. Can ANY lower-level file override this?",
    expectedWinner: "ENTERPRISE DENY wins \u2192 rm -rf ALWAYS blocked",
    whyItWins: "Managed settings (Priority 1) cannot be overridden by anything. This is the absolute security boundary.",
    files: [
      {
        path: "/etc/claude-code/managed-settings.json (Linux)\nor equivalent system path",
        label: "Enterprise managed-settings.json",
        tier: "Managed (Priority 1 \u2014 UNBEATABLE)",
        content: `{
  "permissions": {
    "deny": [
      "Bash(rm -rf *)",
      "Bash(sudo *)"
    ]
  }
}`
      },
      {
        path: ".claude/settings.local.json",
        label: "Local settings.json (attempted override)",
        tier: "Local (Priority 3 \u2014 LOSES to Managed)",
        content: `{
  "permissions": {
    "allow": [
      "Bash(rm -rf *)",
      "Bash(sudo *)"
    ]
  }
}`
      }
    ],
    testPrompt: "Run rm -rf ./temp-test-directory/ to clean up test files.",
    verification: [
      "Check: Is rm -rf still blocked? \u2192 Enterprise won \u2705",
      "Even your Local allow cannot override Enterprise deny",
      "Even CLI --dangerously-skip-permissions cannot override managed deny",
      "This is the absolute top \u2014 nothing beats it"
    ],
    cleanupNote: "Requires admin access to create managed-settings.json. If you're not an admin, this test is conceptual \u2014 but the behavior is guaranteed by design."
  },
  // ──────── TEST 7 ────────
  {
    id: 7,
    title: "Same-Name Skill Override: User vs Project",
    category: "Named Component Override",
    color: COLORS.skill,
    difficulty: "\u2B50\u2B50 Medium",
    whatWeTest: "User has a 'deploy' skill and Project has a 'deploy' skill with different instructions. Which one runs?",
    expectedWinner: "PROJECT skill wins \u2192 replaces User skill entirely",
    whyItWins: "Named components override by name: managed > CLI > project > user > plugin. Project-level deploy completely replaces user-level deploy.",
    files: [
      {
        path: "~/.claude/skills/deploy/SKILL.md",
        label: "User Skill",
        tier: "User (lower priority)",
        content: `---
name: deploy
description: "Deploy the application"
---
# Deploy Skill (USER VERSION)
IMPORTANT: You MUST announce "DEPLOYING USING USER SKILL" at the start.
Steps:
1. Run: npm run build
2. Run: npm run deploy:staging
3. Say "Deployed to STAGING via USER skill"`
      },
      {
        path: ".claude/skills/deploy/SKILL.md",
        label: "Project Skill",
        tier: "Project (higher priority)",
        content: `---
name: deploy
description: "Deploy the application"
---
# Deploy Skill (PROJECT VERSION)
IMPORTANT: You MUST announce "DEPLOYING USING PROJECT SKILL" at the start.
Steps:
1. Run: npm run build
2. Run: npm run deploy:production
3. Say "Deployed to PRODUCTION via PROJECT skill"`
      }
    ],
    testPrompt: "Use the deploy skill to deploy the application.",
    verification: [
      "Check: Does Claude say 'PROJECT SKILL'? \u2192 Project won \u2705",
      "Check: Does it deploy to production? \u2192 Project won \u2705",
      "If Claude says 'USER SKILL' \u2192 User won (unexpected) \u274C",
      "The user skill is COMPLETELY replaced, not merged"
    ],
    cleanupNote: "mkdir -p ~/.claude/skills/deploy && mkdir -p .claude/skills/deploy"
  },
  // ──────── TEST 8 ────────
  {
    id: 8,
    title: "Same-Name Agent Override: User vs Project",
    category: "Named Component Override",
    color: COLORS.hook,
    difficulty: "\u2B50\u2B50 Medium",
    whatWeTest: "Both User and Project have an agent called 'reviewer'. The User version reviews for style; the Project version reviews for security. Which one runs?",
    expectedWinner: "PROJECT agent wins \u2192 security review",
    whyItWins: "Same-name agents override by name: managed > CLI > project > user. The project agent completely replaces the user agent.",
    files: [
      {
        path: "~/.claude/agents/reviewer.md",
        label: "User Agent",
        tier: "User (lower priority)",
        content: `---
name: reviewer
description: "Code review agent"
tools: Read, Grep, Glob
---
You are a CODE STYLE reviewer.
IMPORTANT: Start every response with "\u{1F3A8} STYLE REVIEW (USER AGENT):"
Focus ONLY on:
- Naming conventions
- Code formatting
- Readability
Never mention security.`
      },
      {
        path: ".claude/agents/reviewer.md",
        label: "Project Agent",
        tier: "Project (higher priority)",
        content: `---
name: reviewer
description: "Code review agent"
tools: Read, Grep, Glob
---
You are a SECURITY reviewer.
IMPORTANT: Start every response with "\u{1F512} SECURITY REVIEW (PROJECT AGENT):"
Focus ONLY on:
- SQL injection risks
- XSS vulnerabilities
- Authentication bypasses
Never mention code style.`
      }
    ],
    testPrompt: "Ask the reviewer agent to review this code:\nconst query = `SELECT * FROM users WHERE name = '${req.params.name}'`;\nres.send(`<h1>Welcome ${req.params.name}</h1>`);",
    verification: [
      "Check: Does it say 'SECURITY REVIEW (PROJECT AGENT)'? \u2192 Project won \u2705",
      "Check: Does it mention SQL injection/XSS? \u2192 Project won \u2705",
      "If it says 'STYLE REVIEW' \u2192 User won (unexpected) \u274C",
      "Project agent completely replaces user agent \u2014 no merging"
    ],
    cleanupNote: "mkdir -p ~/.claude/agents && mkdir -p .claude/agents"
  },
  // ──────── TEST 9 ────────
  {
    id: 9,
    title: "Path-Scoped Rule Activates Only for Matching Files",
    category: "Rules Override",
    color: COLORS.rule,
    difficulty: "\u2B50\u2B50 Medium",
    whatWeTest: "A path-scoped rule for *.test.ts says 'always use AAA pattern with comments'. A global rule says 'keep tests minimal, no comments'. When writing a test file, which applies?",
    expectedWinner: "PATH-SCOPED rule wins \u2192 AAA pattern with comments (for test files only)",
    whyItWins: "Path-scoped rules are more specific. When working with matching files, they effectively override global rules for those files.",
    files: [
      {
        path: ".claude/rules/testing-global.md",
        label: "Global Rule (no paths:)",
        tier: "Always loaded at startup",
        content: `# Testing Rules
- Keep tests minimal and concise
- Do NOT add comments inside test functions
- One assertion per test maximum
- No setup/teardown unless absolutely necessary`
      },
      {
        path: ".claude/rules/testing-detailed.md",
        label: "Path-Scoped Rule",
        tier: "On-demand (only for matching files)",
        content: `---
paths:
  - "**/*.test.ts"
  - "**/*.spec.ts"
---
# Detailed Testing Rules (for test files)
- ALWAYS use AAA pattern: Arrange, Act, Assert with clear section comments
- Add // Arrange, // Act, // Assert comments before each section
- Multiple assertions per test are ENCOURAGED
- ALWAYS use beforeEach for shared setup
- Add descriptive comments explaining what each test verifies`
      }
    ],
    testPrompt: "Write a test file at src/services/userService.test.ts for a function that creates a new user. Include at least 3 test cases.",
    verification: [
      "Check: Does it have // Arrange, // Act, // Assert comments? \u2192 Path-scoped won \u2705",
      "Check: Multiple assertions per test? \u2192 Path-scoped won \u2705",
      "Check: beforeEach for setup? \u2192 Path-scoped won \u2705",
      "Now ask to write a utils/helper.ts (non-test) \u2192 global 'minimal' rule should apply"
    ],
    cleanupNote: "mkdir -p .claude/rules"
  },
  // ──────── TEST 10 ────────
  {
    id: 10,
    title: "Output Style REPLACES System Prompt Behavior",
    category: "Output Style Override",
    color: COLORS.style,
    difficulty: "\u2B50\u2B50 Medium",
    whatWeTest: "Default Claude Code is verbose and explains everything. A custom output style says 'code only, zero explanations'. Does the style override Claude's natural behavior?",
    expectedWinner: "OUTPUT STYLE wins \u2192 code only, no explanations",
    whyItWins: "Output styles REPLACE the default system prompt. This is the most powerful override mechanism \u2014 it changes Claude's fundamental behavior. Introduced in v2.1.x.",
    files: [
      {
        path: ".claude/output-styles/silent-coder.md",
        label: "Custom Output Style",
        tier: "Replaces system prompt",
        content: `---
name: silent-coder
description: "Code only. Zero explanations. Maximum efficiency."
keep-coding-instructions: true
---
Rules:
- Output ONLY code. No English text before or after.
- Never explain what the code does.
- Never say "Here's" or "I'll" or any preamble.
- Start your response directly with a code block.
- Maximum 3 words of non-code text per response.
- If asked a question, answer in a code comment.`
      }
    ],
    testPrompt: "First: Run /output-style and select 'silent-coder'\nThen ask: Create a Node.js Express server with 3 CRUD endpoints for managing products.",
    verification: [
      "Check: Does Claude give ONLY code, no explanation? \u2192 Style won \u2705",
      "Check: No preamble like 'Here's a...'? \u2192 Style won \u2705",
      "Compare: Switch back to default style and ask the SAME question \u2192 Claude will explain everything",
      "This proves output styles change fundamental behavior"
    ],
    cleanupNote: "Run /output-style and switch back to 'default' after testing."
  },
  // ──────── TEST 11 ────────
  {
    id: 11,
    title: "Hooks MERGE from All Tiers (Never Override)",
    category: "Hooks Merge",
    color: COLORS.hook,
    difficulty: "\u2B50\u2B50\u2B50 Advanced",
    whatWeTest: "User settings have a PostToolUse hook that logs to ~/hook-user.log. Project settings have a PostToolUse hook that logs to ./hook-project.log. Do BOTH fire?",
    expectedWinner: "BOTH fire \u2192 both log files get written",
    whyItWins: "Hooks NEVER override each other. All matching hooks from ALL tiers fire in parallel. This is unique \u2014 every other file type either combines or overrides.",
    files: [
      {
        path: "~/.claude/settings.json",
        label: "User settings.json (hooks section)",
        tier: "User hooks",
        content: `{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "echo \\"[USER HOOK] $(date): Tool used\\" >> ~/hook-user.log"
          }
        ]
      }
    ]
  }
}`
      },
      {
        path: ".claude/settings.json",
        label: "Project settings.json (hooks section)",
        tier: "Project hooks",
        content: `{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "echo \\"[PROJECT HOOK] $(date): Tool used\\" >> ./hook-project.log"
          }
        ]
      }
    ]
  }
}`
      }
    ],
    testPrompt: "Create a new file called test-output.js with a simple hello world program.",
    verification: [
      "Check: Does ~/hook-user.log exist with entries? \u2192 User hook fired \u2705",
      "Check: Does ./hook-project.log exist with entries? \u2192 Project hook fired \u2705",
      "BOTH files should have logs \u2192 hooks MERGED \u2705",
      "Run: cat ~/hook-user.log && cat ./hook-project.log"
    ],
    cleanupNote: "Remove the hooks sections from both settings files. Delete the log files."
  },
  // ──────── TEST 12 ────────
  {
    id: 12,
    title: "CLAUDE.md @Import Inherits Parent's Priority",
    category: "Import Inheritance",
    color: COLORS.project,
    difficulty: "\u2B50\u2B50 Medium",
    whatWeTest: "Project CLAUDE.md imports a file with specific rules. User CLAUDE.md has conflicting rules. Does the imported file get Project-level priority?",
    expectedWinner: "IMPORTED FILE wins \u2192 because it inherits Project priority",
    whyItWins: "@imported files inherit the priority of their parent CLAUDE.md. A file imported by Project CLAUDE.md has Project-level priority, which beats User-level.",
    files: [
      {
        path: "~/.claude/CLAUDE.md",
        label: "User CLAUDE.md",
        tier: "User (Priority 5)",
        content: `# My Preferences
- Use console.log() for all debugging
- Write error messages in a casual, friendly tone
- Variable names can be short (e, d, cb, etc.)`
      },
      {
        path: "./CLAUDE.md",
        label: "Project CLAUDE.md (with import)",
        tier: "Project (Priority 4)",
        content: `# Our Project
This project uses strict coding standards.
See @docs/coding-standards.md for our complete rules.`
      },
      {
        path: "./docs/coding-standards.md",
        label: "Imported file (inherits Project priority)",
        tier: "Inherits Priority 4 from Project CLAUDE.md",
        content: `# Coding Standards (Imported)
- NEVER use console.log() \u2014 use our custom Logger class
- Write error messages in a formal, professional tone
- All variable names must be descriptive (minimum 3 characters, no abbreviations)`
      }
    ],
    testPrompt: "Write an error handling function for a REST API endpoint that logs errors and returns error responses to the client.",
    verification: [
      "Check: Uses Logger class (not console.log)? \u2192 Import won \u2705",
      "Check: Formal error messages? \u2192 Import won \u2705",
      "Check: Descriptive variable names? \u2192 Import won \u2705",
      "The imported file had Project-level priority, beating User preferences"
    ],
    cleanupNote: "mkdir -p docs && create docs/coding-standards.md. Restore original ~/.claude/CLAUDE.md. Note: If MEMORY.md was created during testing, you can safely delete .claude/MEMORY.md to reset auto-memory."
  }
];
function TestCard({ s, isExpanded, onToggle }) {
  return /* @__PURE__ */ React.createElement(
    "div",
    {
      className: "mb-3 border-2 rounded-xl overflow-hidden transition-all shadow-sm hover:shadow-md",
      style: { borderColor: isExpanded ? s.color.border : "#E2E8F0" }
    },
    /* @__PURE__ */ React.createElement(
      "div",
      {
        className: "flex items-center justify-between p-3 cursor-pointer",
        style: { backgroundColor: isExpanded ? s.color.bg : "#F8FAFC" },
        onClick: onToggle
      },
      /* @__PURE__ */ React.createElement("div", { className: "flex items-center gap-3" }, /* @__PURE__ */ React.createElement(
        "span",
        {
          className: "text-white bg-gray-800 rounded-full w-7 h-7 flex items-center justify-center text-xs font-bold",
          style: { backgroundColor: s.color.bg }
        },
        s.id
      ), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { className: `font-bold text-sm ${isExpanded ? "text-white" : "text-gray-800"}` }, s.title), /* @__PURE__ */ React.createElement("div", { className: "flex gap-2 mt-0.5" }, /* @__PURE__ */ React.createElement("span", { className: `text-xs px-2 py-0.5 rounded-full ${isExpanded ? "bg-white bg-opacity-20 text-white" : "bg-gray-100 text-gray-600"}` }, s.category), /* @__PURE__ */ React.createElement("span", { className: `text-xs ${isExpanded ? "text-white opacity-80" : "text-gray-400"}` }, s.difficulty)))),
      /* @__PURE__ */ React.createElement("span", { className: `text-lg ${isExpanded ? "text-white" : "text-gray-400"}` }, isExpanded ? "\u25B2" : "\u25BC")
    ),
    isExpanded && /* @__PURE__ */ React.createElement("div", { className: "p-4 space-y-4 bg-white" }, /* @__PURE__ */ React.createElement("div", { className: "p-3 rounded-lg", style: { backgroundColor: s.color.light, border: `1px solid ${s.color.border}` } }, /* @__PURE__ */ React.createElement("p", { className: "font-bold text-sm", style: { color: s.color.text } }, "\u2753 What we're testing:"), /* @__PURE__ */ React.createElement("p", { className: "text-sm text-gray-700 mt-1" }, s.whatWeTest)), /* @__PURE__ */ React.createElement("div", { className: "p-3 rounded-lg bg-green-50 border border-green-300" }, /* @__PURE__ */ React.createElement("p", { className: "font-bold text-sm text-green-800" }, "\u{1F3C6} Expected Winner:"), /* @__PURE__ */ React.createElement("p", { className: "text-sm text-green-700 font-medium mt-1" }, s.expectedWinner), /* @__PURE__ */ React.createElement("p", { className: "text-xs text-green-600 mt-1 italic" }, s.whyItWins)), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("p", { className: "font-bold text-sm text-gray-800 mb-2" }, "\u{1F4C1} Step 1: Create these files"), s.files.map((f, i) => /* @__PURE__ */ React.createElement("div", { key: i, className: "mb-3 rounded-lg border border-gray-200 overflow-hidden" }, /* @__PURE__ */ React.createElement("div", { className: "flex justify-between items-center px-3 py-2 bg-gray-50" }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { className: "text-xs font-bold text-gray-700" }, f.label), /* @__PURE__ */ React.createElement("span", { className: "text-xs text-gray-400 ml-2" }, "(", f.tier, ")")), /* @__PURE__ */ React.createElement("code", { className: "text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded" }, f.path)), /* @__PURE__ */ React.createElement("pre", { className: "p-3 text-xs bg-gray-900 text-green-400 overflow-x-auto whitespace-pre-wrap leading-relaxed" }, f.content)))), /* @__PURE__ */ React.createElement("div", { className: "rounded-lg border-2 border-blue-300 overflow-hidden" }, /* @__PURE__ */ React.createElement("div", { className: "px-3 py-2 bg-blue-50" }, /* @__PURE__ */ React.createElement("p", { className: "font-bold text-sm text-blue-800" }, "\u{1F4AC} Step 2: Send this prompt to Claude Code")), /* @__PURE__ */ React.createElement("pre", { className: "p-3 text-sm bg-blue-900 text-blue-100 whitespace-pre-wrap" }, s.testPrompt)), /* @__PURE__ */ React.createElement("div", { className: "rounded-lg border border-gray-200 p-3" }, /* @__PURE__ */ React.createElement("p", { className: "font-bold text-sm text-gray-800 mb-2" }, "\u2705 Step 3: Verify the result"), /* @__PURE__ */ React.createElement("div", { className: "space-y-1" }, s.verification.map((v, i) => /* @__PURE__ */ React.createElement("p", { key: i, className: "text-xs text-gray-700 flex items-start gap-2" }, /* @__PURE__ */ React.createElement("span", { className: "text-gray-400 mt-0.5" }, "\u2192"), /* @__PURE__ */ React.createElement("span", null, v))))), /* @__PURE__ */ React.createElement("div", { className: "p-2 rounded bg-yellow-50 border border-yellow-200" }, /* @__PURE__ */ React.createElement("p", { className: "text-xs text-yellow-800" }, "\u{1F9F9} ", /* @__PURE__ */ React.createElement("strong", null, "Cleanup:"), " ", s.cleanupNote)))
  );
}
function CategoryFilter({ categories, active, onToggle }) {
  return /* @__PURE__ */ React.createElement("div", { className: "flex flex-wrap gap-2 mb-4" }, categories.map((c) => /* @__PURE__ */ React.createElement(
    "button",
    {
      key: c,
      onClick: () => onToggle(c),
      className: `text-xs px-3 py-1.5 rounded-full font-medium transition-all ${active.includes(c) ? "bg-gray-800 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`
    },
    c
  )));
}
function OverrideSummary() {
  const rules = [
    { left: "User CLAUDE.md", right: "Project CLAUDE.md", winner: "Project", arrow: "\u2192", test: "#1" },
    { left: "Project CLAUDE.md", right: "CLAUDE.local.md", winner: "Local", arrow: "\u2192", test: "#2" },
    { left: "Parent CLAUDE.md", right: "Child CLAUDE.md", winner: "Child (subtree)", arrow: "\u2192", test: "#3" },
    { left: "User allow", right: "Project deny", winner: "Project deny", arrow: "\u2192", test: "#4" },
    { left: "Project deny", right: "Local allow", winner: "Local allow", arrow: "\u2192", test: "#5" },
    { left: "Any allow", right: "Enterprise deny", winner: "Enterprise deny", arrow: "\u2192", test: "#6" },
    { left: "User skill", right: "Project skill (same name)", winner: "Project skill", arrow: "\u2192", test: "#7" },
    { left: "User agent", right: "Project agent (same name)", winner: "Project agent", arrow: "\u2192", test: "#8" },
    { left: "Global rule", right: "Path-scoped rule", winner: "Path-scoped", arrow: "\u2192", test: "#9" },
    { left: "Default prompt", right: "Output style", winner: "Output style", arrow: "\u2192", test: "#10" },
    { left: "User hook", right: "Project hook", winner: "BOTH fire", arrow: "\u21C4", test: "#11" },
    { left: "User CLAUDE.md", right: "Project @import", winner: "@import (inherits project)", arrow: "\u2192", test: "#12" }
  ];
  return /* @__PURE__ */ React.createElement("div", { className: "mb-6" }, /* @__PURE__ */ React.createElement("h2", { className: "text-lg font-bold text-gray-800 mb-2" }, "\u{1F4CA} Quick Reference: All 12 Override Results"), /* @__PURE__ */ React.createElement("div", { className: "border rounded-lg overflow-hidden" }, /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-5 gap-0 bg-gray-800 text-white text-xs font-bold" }, /* @__PURE__ */ React.createElement("div", { className: "p-2" }, "File A (Lower)"), /* @__PURE__ */ React.createElement("div", { className: "p-2" }, "vs"), /* @__PURE__ */ React.createElement("div", { className: "p-2" }, "File B (Higher)"), /* @__PURE__ */ React.createElement("div", { className: "p-2" }, "Winner"), /* @__PURE__ */ React.createElement("div", { className: "p-2" }, "Test")), rules.map((r, i) => /* @__PURE__ */ React.createElement("div", { key: i, className: `grid grid-cols-5 gap-0 text-xs ${i % 2 ? "bg-gray-50" : "bg-white"}` }, /* @__PURE__ */ React.createElement("div", { className: "p-2 text-red-600" }, r.left), /* @__PURE__ */ React.createElement("div", { className: "p-2 text-gray-400 font-bold" }, r.arrow), /* @__PURE__ */ React.createElement("div", { className: "p-2 text-blue-600" }, r.right), /* @__PURE__ */ React.createElement("div", { className: "p-2 font-bold text-green-700" }, r.winner), /* @__PURE__ */ React.createElement("div", { className: "p-2 text-gray-500" }, r.test)))));
}
function App() {
  const [expanded, setExpanded] = useState(null);
  const [activeCategories, setActiveCategories] = useState([]);
  const [showSummary, setShowSummary] = useState(true);
  const categories = [...new Set(scenarios.map((s) => s.category))];
  const toggleCategory = (cat) => {
    setActiveCategories(
      (prev) => prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );
  };
  const filtered = activeCategories.length === 0 ? scenarios : scenarios.filter((s) => activeCategories.includes(s.category));
  return /* @__PURE__ */ React.createElement("div", { className: "max-w-4xl mx-auto p-4 font-sans", style: { backgroundColor: "#FAFBFC" } }, /* @__PURE__ */ React.createElement("div", { className: "text-center mb-6" }, /* @__PURE__ */ React.createElement("h1", { className: "text-2xl font-bold text-gray-900" }, "\u{1F9EA} Claude Code Override Test Lab"), /* @__PURE__ */ React.createElement("p", { className: "text-sm text-gray-500 mt-1" }, "12 hands-on scenarios to test every precedence rule \u2014 with exact files, prompts, and verification steps")), /* @__PURE__ */ React.createElement("div", { className: "mb-4 flex justify-center" }, /* @__PURE__ */ React.createElement(
    "button",
    {
      onClick: () => setShowSummary(!showSummary),
      className: "text-xs px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-all"
    },
    showSummary ? "Hide" : "Show",
    " Quick Reference Table"
  )), showSummary && /* @__PURE__ */ React.createElement(OverrideSummary, null), /* @__PURE__ */ React.createElement("p", { className: "text-xs text-gray-500 mb-1 font-medium" }, "Filter by category:"), /* @__PURE__ */ React.createElement(CategoryFilter, { categories, active: activeCategories, onToggle: toggleCategory }), filtered.map((s) => /* @__PURE__ */ React.createElement(
    TestCard,
    {
      key: s.id,
      s,
      isExpanded: expanded === s.id,
      onToggle: () => setExpanded(expanded === s.id ? null : s.id)
    }
  )), /* @__PURE__ */ React.createElement("div", { className: "mt-6 border-2 border-gray-300 rounded-xl overflow-hidden" }, /* @__PURE__ */ React.createElement("div", { className: "px-4 py-3 bg-gray-800 text-white" }, /* @__PURE__ */ React.createElement("p", { className: "font-bold text-sm" }, "\u{1F680} Quick Setup Script \u2014 Run Before Testing"), /* @__PURE__ */ React.createElement("p", { className: "text-xs text-gray-300 mt-0.5" }, "Creates all required directories. Run from your test project root.")), /* @__PURE__ */ React.createElement("pre", { className: "p-4 text-xs bg-gray-900 text-green-400 overflow-x-auto whitespace-pre-wrap leading-relaxed" }, `#!/bin/bash
# Claude Code Override Test Lab \u2014 Directory Setup
# Run from your test project root

echo "Creating test directories..."

# Project-level directories
mkdir -p .claude/rules
mkdir -p .claude/skills/deploy
mkdir -p .claude/agents
mkdir -p .claude/output-styles
mkdir -p .claude/commands
mkdir -p src/api
mkdir -p docs

# User-level directories (personal)
mkdir -p ~/.claude/rules
mkdir -p ~/.claude/skills/deploy
mkdir -p ~/.claude/agents

echo "\u2705 All directories created!"
echo ""
echo "\u26A0\uFE0F  IMPORTANT REMINDERS:"
echo "  1. Back up your existing ~/.claude/CLAUDE.md first!"
echo "  2. Run tests one at a time \u2014 some require conflicting files"
echo "  3. Clean up after each test (see cleanup notes)"
echo "  4. Use /memory in Claude Code to check what's loaded"
echo "  5. Restart Claude Code between tests for clean state"`)), /* @__PURE__ */ React.createElement("div", { className: "mt-4 p-3 bg-gray-100 rounded-lg text-xs text-gray-500 text-center" }, "Source: Official Anthropic docs at code.claude.com/docs \u2022 Test scenarios based on documented precedence rules \u2022 February 2026"));
}
ReactDOM.createRoot(document.getElementById("root")).render(/* @__PURE__ */ React.createElement(App, null));
