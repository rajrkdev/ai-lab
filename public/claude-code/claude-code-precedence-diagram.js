"use strict";
const { useState } = React;
const COLORS = {
  enterprise: { bg: "#DC2626", light: "#FEE2E2", border: "#EF4444", text: "#991B1B" },
  project: { bg: "#2563EB", light: "#DBEAFE", border: "#3B82F6", text: "#1E40AF" },
  user: { bg: "#7C3AED", light: "#EDE9FE", border: "#8B5CF6", text: "#5B21B6" },
  local: { bg: "#059669", light: "#D1FAE5", border: "#10B981", text: "#065F46" },
  auto: { bg: "#D97706", light: "#FEF3C7", border: "#F59E0B", text: "#92400E" },
  plugin: { bg: "#EC4899", light: "#FCE7F3", border: "#F472B6", text: "#9D174D" },
  system: { bg: "#475569", light: "#F1F5F9", border: "#94A3B8", text: "#1E293B" }
};
function PrecedencePyramid() {
  const [hoveredLevel, setHoveredLevel] = useState(null);
  const levels = [
    {
      id: "enterprise",
      label: "ENTERPRISE / MANAGED",
      priority: "Priority 1 (HIGHEST)",
      color: COLORS.enterprise,
      width: "40%",
      files: ["managed-settings.json", "managed-mcp.json", "Enterprise CLAUDE.md"],
      description: "Deployed by IT/DevOps via MDM. Cannot be overridden by any lower level. If enterprise says 'deny rm -rf', no one can allow it.",
      analogy: "Think of this as company law \u2014 like a government rule that every citizen must follow.",
      overrides: "Overrides EVERYTHING below it",
      overriddenBy: "Nothing \u2014 this is the absolute top"
    },
    {
      id: "cli",
      label: "CLI ARGUMENTS",
      priority: "Priority 2",
      color: { bg: "#0F172A", light: "#E2E8F0", border: "#334155", text: "#0F172A" },
      width: "50%",
      files: ["--model", "--dangerously-skip-permissions", "--append-system-prompt", "--agents"],
      description: "Temporary, session-only overrides passed when launching Claude Code. Gone when the session ends.",
      analogy: "Like a temporary override pass \u2014 valid only for this one visit.",
      overrides: "Overrides Local, Project, and User settings",
      overriddenBy: "Enterprise/Managed settings"
    },
    {
      id: "local",
      label: "LOCAL PROJECT",
      priority: "Priority 3",
      color: COLORS.local,
      width: "60%",
      files: [".claude/settings.local.json", "CLAUDE.local.md"],
      description: "Your personal overrides for THIS project only. Auto-gitignored \u2014 never shared with your team.",
      analogy: "Like sticky notes on YOUR monitor \u2014 only you see them, only for this workspace.",
      overrides: "Overrides Shared Project and User settings",
      overriddenBy: "Enterprise and CLI args"
    },
    {
      id: "project",
      label: "SHARED PROJECT",
      priority: "Priority 4",
      color: COLORS.project,
      width: "72%",
      files: [".claude/settings.json", "./CLAUDE.md", ".claude/rules/*.md", ".claude/agents/*.md", ".claude/skills/*/SKILL.md", ".claude/commands/*.md", ".claude/output-styles/*.md", ".mcp.json", ".claude/MEMORY.md"],
      description: "Team-wide settings committed to version control. Everyone on the team gets the same rules. Includes auto-generated MEMORY.md (v2.1.59) where Claude records discovered project facts.",
      analogy: "Like the team handbook \u2014 everyone follows the same standards.",
      overrides: "Overrides User settings",
      overriddenBy: "Enterprise, CLI, and Local settings"
    },
    {
      id: "user",
      label: "USER (PERSONAL)",
      priority: "Priority 5 (LOWEST)",
      color: COLORS.user,
      width: "85%",
      files: ["~/.claude/settings.json", "~/.claude/CLAUDE.md", "~/.claude/rules/*.md", "~/.claude/agents/*.md", "~/.claude/skills/*/SKILL.md", "~/.claude/commands/*.md", "~/.claude/output-styles/*.md", "~/.claude.json"],
      description: "Your personal defaults that apply to ALL projects. The baseline that everything builds on.",
      analogy: "Like your personal preferences \u2014 how you like to work, regardless of which project.",
      overrides: "This is the foundation \u2014 defaults for everything",
      overriddenBy: "Everything above it"
    }
  ];
  return /* @__PURE__ */ React.createElement("div", { className: "mb-8" }, /* @__PURE__ */ React.createElement("h2", { className: "text-xl font-bold text-center mb-2", style: { color: "#1E293B" } }, "\u{1F3D4}\uFE0F The Precedence Pyramid \u2014 Who Overrides Whom?"), /* @__PURE__ */ React.createElement("p", { className: "text-center text-sm text-gray-500 mb-4" }, "Higher position = higher priority. Click any level for details."), /* @__PURE__ */ React.createElement("div", { className: "flex flex-col items-center gap-1" }, levels.map((level) => /* @__PURE__ */ React.createElement(
    "div",
    {
      key: level.id,
      className: "cursor-pointer transition-all duration-200 rounded-lg",
      style: {
        width: level.width,
        backgroundColor: hoveredLevel === level.id ? level.color.light : level.color.bg,
        color: hoveredLevel === level.id ? level.color.text : "white",
        border: `2px solid ${level.color.border}`,
        padding: "8px 14px",
        transform: hoveredLevel === level.id ? "scale(1.02)" : "scale(1)"
      },
      onClick: () => setHoveredLevel(hoveredLevel === level.id ? null : level.id),
      onMouseEnter: () => setHoveredLevel(level.id),
      onMouseLeave: () => setHoveredLevel(null)
    },
    /* @__PURE__ */ React.createElement("div", { className: "flex justify-between items-center" }, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-sm" }, level.label), /* @__PURE__ */ React.createElement("span", { className: "text-xs opacity-80" }, level.priority))
  ))), hoveredLevel && (() => {
    const level = levels.find((l) => l.id === hoveredLevel);
    return /* @__PURE__ */ React.createElement("div", { className: "mt-4 p-4 rounded-lg border-2", style: { borderColor: level.color.border, backgroundColor: level.color.light } }, /* @__PURE__ */ React.createElement("h3", { className: "font-bold text-base mb-1", style: { color: level.color.text } }, level.label, " \u2014 ", level.priority), /* @__PURE__ */ React.createElement("p", { className: "text-sm text-gray-700 mb-2" }, level.description), /* @__PURE__ */ React.createElement("p", { className: "text-sm italic text-gray-600 mb-2" }, "\u{1F4A1} ", level.analogy), /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-2 gap-3 text-xs" }, /* @__PURE__ */ React.createElement("div", { className: "bg-white p-2 rounded border" }, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-green-700" }, "\u2705 Overrides:"), /* @__PURE__ */ React.createElement("p", { className: "text-gray-700" }, level.overrides)), /* @__PURE__ */ React.createElement("div", { className: "bg-white p-2 rounded border" }, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-red-700" }, "\u274C Overridden by:"), /* @__PURE__ */ React.createElement("p", { className: "text-gray-700" }, level.overriddenBy))), /* @__PURE__ */ React.createElement("div", { className: "mt-2" }, /* @__PURE__ */ React.createElement("span", { className: "text-xs font-bold text-gray-600" }, "Files at this level:"), /* @__PURE__ */ React.createElement("div", { className: "flex flex-wrap gap-1 mt-1" }, level.files.map((f, i) => /* @__PURE__ */ React.createElement("span", { key: i, className: "text-xs px-2 py-0.5 bg-white rounded border", style: { borderColor: level.color.border } }, f)))));
  })());
}
function MarkdownFileCard({ file, isExpanded, onToggle }) {
  return /* @__PURE__ */ React.createElement(
    "div",
    {
      className: "border-2 rounded-lg mb-3 overflow-hidden transition-all cursor-pointer",
      style: { borderColor: file.color.border, backgroundColor: isExpanded ? file.color.light : "white" },
      onClick: onToggle
    },
    /* @__PURE__ */ React.createElement("div", { className: "flex items-center justify-between p-3", style: { backgroundColor: file.color.bg } }, /* @__PURE__ */ React.createElement("div", { className: "flex items-center gap-2" }, /* @__PURE__ */ React.createElement("span", { className: "text-lg" }, file.icon), /* @__PURE__ */ React.createElement("span", { className: "font-bold text-white text-sm" }, file.name)), /* @__PURE__ */ React.createElement("div", { className: "flex items-center gap-2" }, /* @__PURE__ */ React.createElement("span", { className: "text-xs px-2 py-0.5 rounded-full bg-white bg-opacity-20 text-white" }, file.loadBehavior), /* @__PURE__ */ React.createElement("span", { className: "text-white text-xs" }, isExpanded ? "\u25B2" : "\u25BC"))),
    isExpanded && /* @__PURE__ */ React.createElement("div", { className: "p-4 text-sm space-y-3" }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-gray-800" }, "\u{1F4CD} Location:"), /* @__PURE__ */ React.createElement("code", { className: "ml-2 text-xs bg-gray-100 px-2 py-1 rounded" }, file.location)), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-gray-800" }, "\u{1F3AF} Purpose:"), /* @__PURE__ */ React.createElement("p", { className: "text-gray-700 mt-1" }, file.purpose)), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-gray-800" }, "\u{1F504} When it loads:"), /* @__PURE__ */ React.createElement("p", { className: "text-gray-700 mt-1" }, file.whenLoads)), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-gray-800" }, "\u{1F3C6} Priority:"), /* @__PURE__ */ React.createElement("p", { className: "text-gray-700 mt-1" }, file.priority)), /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-2 gap-2" }, /* @__PURE__ */ React.createElement("div", { className: "bg-green-50 p-2 rounded border border-green-200" }, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-green-700 text-xs" }, "\u2705 Wins against:"), /* @__PURE__ */ React.createElement("p", { className: "text-xs text-gray-700 mt-1" }, file.winsAgainst)), /* @__PURE__ */ React.createElement("div", { className: "bg-red-50 p-2 rounded border border-red-200" }, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-red-700 text-xs" }, "\u274C Loses to:"), /* @__PURE__ */ React.createElement("p", { className: "text-xs text-gray-700 mt-1" }, file.losesTo))), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-gray-800" }, "\u{1F465} Shared with team?"), /* @__PURE__ */ React.createElement("span", { className: "ml-2 text-gray-700" }, file.shared)), /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-gray-800" }, "\u{1F4B0} Token cost:"), /* @__PURE__ */ React.createElement("span", { className: "ml-2 text-gray-700" }, file.tokenCost)), file.example && /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-gray-800" }, "\u{1F4DD} Example content:"), /* @__PURE__ */ React.createElement("pre", { className: "mt-1 bg-gray-900 text-green-400 p-3 rounded text-xs overflow-x-auto whitespace-pre-wrap" }, file.example)), file.specialNotes && /* @__PURE__ */ React.createElement("div", { className: "bg-yellow-50 p-2 rounded border border-yellow-300" }, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-yellow-800 text-xs" }, "\u26A0\uFE0F Important:"), /* @__PURE__ */ React.createElement("p", { className: "text-xs text-gray-700 mt-1" }, file.specialNotes)))
  );
}
function ConflictScenarios() {
  const scenarios = [
    {
      title: "User says '2-space indent' but Project says '4-space indent'",
      userFile: "~/.claude/CLAUDE.md",
      projectFile: "./CLAUDE.md",
      winner: "Project wins \u2014 4-space indent",
      reason: "Project-level is more specific than user-level. The project rule overrides.",
      color: COLORS.project
    },
    {
      title: "Project allows 'npm run *' but Enterprise denies it",
      userFile: ".claude/settings.json \u2192 allow",
      projectFile: "managed-settings.json \u2192 deny",
      winner: "Enterprise wins \u2014 command is BLOCKED",
      reason: "Enterprise/Managed has highest priority. Deny rules from managed settings can never be overridden.",
      color: COLORS.enterprise
    },
    {
      title: "Project denies 'curl *' but your Local settings allow it",
      userFile: ".claude/settings.json \u2192 deny",
      projectFile: ".claude/settings.local.json \u2192 allow",
      winner: "Local wins \u2014 curl is ALLOWED (for you only)",
      reason: "Local project (priority 3) beats shared project (priority 4). But ONLY for you \u2014 teammates still get the deny.",
      color: COLORS.local
    },
    {
      title: "User skill 'deploy' vs Project skill 'deploy'",
      userFile: "~/.claude/skills/deploy/SKILL.md",
      projectFile: ".claude/skills/deploy/SKILL.md",
      winner: "Project skill wins \u2014 overrides by name",
      reason: "Skills override by name: managed > CLI > project > user > plugin. Same-name project skill replaces user skill.",
      color: COLORS.project
    },
    {
      title: "CLAUDE.md says 'use TypeScript' but Output Style says 'write Python only'",
      userFile: "./CLAUDE.md (adds to user message)",
      projectFile: "output-styles/python.md (replaces system prompt)",
      winner: "Both apply but output style is MORE POWERFUL",
      reason: "Output styles replace the system prompt. CLAUDE.md adds context as user message. Both load, but system prompt instructions carry more weight.",
      color: { bg: "#0F172A", light: "#E2E8F0", border: "#334155", text: "#0F172A" }
    },
    {
      title: "Deny at ANY level vs Allow at ANY level (permissions)",
      userFile: "Any settings.json \u2192 allow: ['Bash(rm *)']",
      projectFile: "Any settings.json \u2192 deny: ['Bash(rm *)']",
      winner: "DENY always wins \u2014 regardless of which level",
      reason: "Special rule: For permissions, deny is evaluated FIRST. A deny at any tier cannot be overridden by an allow at any tier. This is a safety mechanism.",
      color: COLORS.enterprise
    }
  ];
  const [expandedIdx, setExpandedIdx] = useState(null);
  return /* @__PURE__ */ React.createElement("div", { className: "mb-8" }, /* @__PURE__ */ React.createElement("h2", { className: "text-xl font-bold mb-2", style: { color: "#1E293B" } }, "\u2694\uFE0F Real Conflict Scenarios \u2014 Who Wins?"), /* @__PURE__ */ React.createElement("p", { className: "text-sm text-gray-500 mb-3" }, "Click each scenario to see the detailed resolution."), scenarios.map((s, i) => /* @__PURE__ */ React.createElement(
    "div",
    {
      key: i,
      className: "border rounded-lg mb-2 cursor-pointer overflow-hidden transition-all",
      style: { borderColor: expandedIdx === i ? s.color.border : "#E2E8F0" },
      onClick: () => setExpandedIdx(expandedIdx === i ? null : i)
    },
    /* @__PURE__ */ React.createElement("div", { className: "flex items-center justify-between p-3 bg-gray-50" }, /* @__PURE__ */ React.createElement("span", { className: "font-medium text-sm text-gray-800" }, "\u2753 ", s.title), /* @__PURE__ */ React.createElement("span", { className: "text-xs text-gray-400" }, expandedIdx === i ? "\u25B2" : "\u25BC")),
    expandedIdx === i && /* @__PURE__ */ React.createElement("div", { className: "p-3 space-y-2" }, /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-2 gap-2 text-xs" }, /* @__PURE__ */ React.createElement("div", { className: "bg-gray-100 p-2 rounded" }, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-gray-600" }, "File A:"), /* @__PURE__ */ React.createElement("p", { className: "text-gray-700" }, s.userFile)), /* @__PURE__ */ React.createElement("div", { className: "bg-gray-100 p-2 rounded" }, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-gray-600" }, "File B:"), /* @__PURE__ */ React.createElement("p", { className: "text-gray-700" }, s.projectFile))), /* @__PURE__ */ React.createElement("div", { className: "p-2 rounded-lg", style: { backgroundColor: s.color.light, border: `2px solid ${s.color.border}` } }, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-sm", style: { color: s.color.text } }, "\u{1F3C6} ", s.winner), /* @__PURE__ */ React.createElement("p", { className: "text-xs text-gray-700 mt-1" }, s.reason)))
  )));
}
function LoadingTimeline() {
  const phases = [
    {
      phase: "Phase 1: Session Start",
      label: "Always loaded (permanent token cost)",
      color: "#059669",
      items: [
        "Enterprise CLAUDE.md",
        "~/.claude/CLAUDE.md (User)",
        "./CLAUDE.md (Project)",
        "./CLAUDE.local.md (Local)",
        "Parent directory CLAUDE.md files",
        "@imported files from all CLAUDE.md",
        "All global rules (.claude/rules/*.md without paths: frontmatter)",
        "~/.claude/rules/*.md (user rules)",
        "MEMORY.md (first 200 lines)",
        "All skill/agent/command frontmatter (names + descriptions only)"
      ]
    },
    {
      phase: "Phase 2: On-Demand",
      label: "Loaded when Claude enters relevant area",
      color: "#D97706",
      items: [
        "Path-scoped rules (when matching files are touched)",
        "Subtree/child CLAUDE.md (when Claude reads files in that directory)",
        "Skill full body (when Claude decides to use it or user invokes /skill)",
        "MEMORY.md topic files (when Claude reads them)"
      ]
    },
    {
      phase: "Phase 3: User-Invoked",
      label: "Loaded only when you explicitly trigger",
      color: "#7C3AED",
      items: [
        "Slash commands (/command-name)",
        "Sub-agents (via delegation or explicit call)",
        "Skills (via /skill-name or auto-invocation)",
        "Output styles (via /output-style command)"
      ]
    },
    {
      phase: "Phase 4: Auto-Generated",
      label: "Claude writes these \u2014 not you",
      color: "#EC4899",
      items: [
        "MEMORY.md + topic files (~/.claude/projects/<project>/memory/)",
        "Sub-agent MEMORY.md (persistent across invocations)"
      ]
    }
  ];
  return /* @__PURE__ */ React.createElement("div", { className: "mb-8" }, /* @__PURE__ */ React.createElement("h2", { className: "text-xl font-bold mb-2", style: { color: "#1E293B" } }, "\u23F1\uFE0F When Does Each File Load?"), /* @__PURE__ */ React.createElement("p", { className: "text-sm text-gray-500 mb-3" }, "Files load at different times \u2014 earlier = more token cost."), /* @__PURE__ */ React.createElement("div", { className: "space-y-3" }, phases.map((p, i) => /* @__PURE__ */ React.createElement("div", { key: i, className: "rounded-lg border-2 overflow-hidden", style: { borderColor: p.color } }, /* @__PURE__ */ React.createElement("div", { className: "px-3 py-2 text-white font-bold text-sm flex justify-between", style: { backgroundColor: p.color } }, /* @__PURE__ */ React.createElement("span", null, p.phase), /* @__PURE__ */ React.createElement("span", { className: "text-xs opacity-80" }, p.label)), /* @__PURE__ */ React.createElement("div", { className: "p-3 grid grid-cols-2 gap-1" }, p.items.map((item, j) => /* @__PURE__ */ React.createElement("div", { key: j, className: "text-xs text-gray-700 flex items-start gap-1" }, /* @__PURE__ */ React.createElement("span", { style: { color: p.color } }, "\u25CF"), /* @__PURE__ */ React.createElement("span", null, item))))))));
}
function SettingsHierarchy() {
  const tiers = [
    { tier: 1, name: "Managed", file: "managed-settings.json", loc: "macOS: /Library/Application Support/ClaudeCode/  |  Linux: /etc/claude-code/  |  Windows: C:\\ProgramData\\ClaudeCode\\", desc: "IT-deployed, cannot be overridden. Also: server-managed settings from Anthropic for Enterprise.", color: COLORS.enterprise },
    { tier: 2, name: "CLI Args", file: "command line flags", loc: "claude --model opus --dangerously-skip-permissions", desc: "Session-only. Overrides everything except Managed.", color: { bg: "#0F172A", light: "#E2E8F0", border: "#334155", text: "#0F172A" } },
    { tier: 3, name: "Local Project", file: ".claude/settings.local.json", loc: ".claude/settings.local.json (auto-gitignored)", desc: "Your personal project overrides. Not shared with team.", color: COLORS.local },
    { tier: 4, name: "Shared Project", file: ".claude/settings.json", loc: ".claude/settings.json (version-controlled)", desc: "Team settings. Everyone gets same config.", color: COLORS.project },
    { tier: 5, name: "User", file: "~/.claude/settings.json", loc: "~/.claude/settings.json", desc: "Your personal global defaults for all projects.", color: COLORS.user }
  ];
  return /* @__PURE__ */ React.createElement("div", { className: "mb-8" }, /* @__PURE__ */ React.createElement("h2", { className: "text-xl font-bold mb-2", style: { color: "#1E293B" } }, "\u2699\uFE0F Settings.json \u2014 5-Tier Hierarchy"), /* @__PURE__ */ React.createElement("p", { className: "text-sm text-gray-500 mb-3" }, "Settings MERGE across tiers. Higher tier wins on conflicts. Special rule: DENY always wins."), /* @__PURE__ */ React.createElement("div", { className: "space-y-2" }, tiers.map((t) => /* @__PURE__ */ React.createElement("div", { key: t.tier, className: "flex items-stretch gap-2 rounded-lg border-2 overflow-hidden", style: { borderColor: t.color.border } }, /* @__PURE__ */ React.createElement("div", { className: "flex items-center justify-center px-3 text-white font-bold text-lg", style: { backgroundColor: t.color.bg, minWidth: "42px" } }, t.tier), /* @__PURE__ */ React.createElement("div", { className: "flex-1 p-2" }, /* @__PURE__ */ React.createElement("div", { className: "flex items-center gap-2" }, /* @__PURE__ */ React.createElement("span", { className: "font-bold text-sm", style: { color: t.color.text } }, t.name), /* @__PURE__ */ React.createElement("code", { className: "text-xs bg-gray-100 px-2 py-0.5 rounded" }, t.file)), /* @__PURE__ */ React.createElement("p", { className: "text-xs text-gray-600 mt-0.5" }, t.desc), /* @__PURE__ */ React.createElement("p", { className: "text-xs text-gray-400 mt-0.5 italic" }, t.loc))))), /* @__PURE__ */ React.createElement("div", { className: "mt-3 p-3 bg-red-50 border-2 border-red-300 rounded-lg" }, /* @__PURE__ */ React.createElement("p", { className: "text-sm font-bold text-red-800" }, "\u{1F6A8} Critical Rule for Permissions"), /* @__PURE__ */ React.createElement("p", { className: "text-xs text-red-700 mt-1" }, "DENY rules always win regardless of tier. If ", /* @__PURE__ */ React.createElement("strong", null, "any"), " settings file at ", /* @__PURE__ */ React.createElement("strong", null, "any"), " level says ", /* @__PURE__ */ React.createElement("code", null, 'deny: ["Bash(rm -rf *)"]'), ", no allow rule at any other level can override it. Evaluation order: deny first \u2192 ask second \u2192 allow last.")));
}
function DirectoryMap() {
  return /* @__PURE__ */ React.createElement("div", { className: "mb-8" }, /* @__PURE__ */ React.createElement("h2", { className: "text-xl font-bold mb-2", style: { color: "#1E293B" } }, "\u{1F4C1} Complete Directory Map \u2014 Every File Claude Code Reads"), /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-2 gap-3" }, /* @__PURE__ */ React.createElement("div", { className: "border-2 rounded-lg overflow-hidden", style: { borderColor: COLORS.user.border } }, /* @__PURE__ */ React.createElement("div", { className: "px-3 py-2 text-white font-bold text-sm", style: { backgroundColor: COLORS.user.bg } }, "\u{1F464} User Level (~/.claude/)"), /* @__PURE__ */ React.createElement("pre", { className: "p-3 text-xs text-gray-700 bg-gray-50 leading-relaxed whitespace-pre-wrap" }, `~/.claude/
\u251C\u2500\u2500 CLAUDE.md          \u2190 Personal memory
\u251C\u2500\u2500 settings.json      \u2190 Global settings
\u251C\u2500\u2500 rules/             \u2190 Personal rules
\u2502   \u2514\u2500\u2500 *.md
\u251C\u2500\u2500 agents/            \u2190 Personal subagents
\u2502   \u2514\u2500\u2500 *.md
\u251C\u2500\u2500 skills/            \u2190 Personal skills
\u2502   \u2514\u2500\u2500 */SKILL.md
\u251C\u2500\u2500 commands/          \u2190 Personal commands
\u2502   \u2514\u2500\u2500 *.md
\u251C\u2500\u2500 output-styles/     \u2190 Personal styles
\u2502   \u2514\u2500\u2500 *.md
\u251C\u2500\u2500 projects/          \u2190 Auto memory
\u2502   \u2514\u2500\u2500 <project>/memory/
\u2502       \u251C\u2500\u2500 MEMORY.md
\u2502       \u2514\u2500\u2500 *.md (topics)
\u2514\u2500\u2500 plugins/cache/     \u2190 Plugin cache`)), /* @__PURE__ */ React.createElement("div", { className: "border-2 rounded-lg overflow-hidden", style: { borderColor: COLORS.project.border } }, /* @__PURE__ */ React.createElement("div", { className: "px-3 py-2 text-white font-bold text-sm", style: { backgroundColor: COLORS.project.bg } }, "\u{1F4E6} Project Level (./ and .claude/)"), /* @__PURE__ */ React.createElement("pre", { className: "p-3 text-xs text-gray-700 bg-gray-50 leading-relaxed whitespace-pre-wrap" }, `project-root/
\u251C\u2500\u2500 CLAUDE.md          \u2190 Project memory
\u251C\u2500\u2500 CLAUDE.local.md    \u2190 Personal (gitignored)
\u251C\u2500\u2500 .mcp.json          \u2190 MCP servers
\u251C\u2500\u2500 .claude/
\u2502   \u251C\u2500\u2500 CLAUDE.md      \u2190 Alt project memory
\u2502   \u251C\u2500\u2500 settings.json  \u2190 Team settings
\u2502   \u251C\u2500\u2500 settings.local.json \u2190 Personal
\u2502   \u251C\u2500\u2500 rules/         \u2190 Project rules
\u2502   \u2502   \u2514\u2500\u2500 *.md
\u2502   \u251C\u2500\u2500 agents/        \u2190 Project subagents
\u2502   \u2502   \u2514\u2500\u2500 *.md
\u2502   \u251C\u2500\u2500 skills/        \u2190 Project skills
\u2502   \u2502   \u2514\u2500\u2500 */SKILL.md
\u2502   \u251C\u2500\u2500 commands/      \u2190 Project commands
\u2502   \u2502   \u2514\u2500\u2500 *.md
\u2502   \u2514\u2500\u2500 output-styles/ \u2190 Project styles
\u2502       \u2514\u2500\u2500 *.md
\u2514\u2500\u2500 child-dir/
    \u2514\u2500\u2500 CLAUDE.md      \u2190 Subtree memory`))), /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-2 gap-3 mt-3" }, /* @__PURE__ */ React.createElement("div", { className: "border-2 rounded-lg overflow-hidden", style: { borderColor: COLORS.enterprise.border } }, /* @__PURE__ */ React.createElement("div", { className: "px-3 py-2 text-white font-bold text-sm", style: { backgroundColor: COLORS.enterprise.bg } }, "\u{1F3E2} Enterprise Level (System dirs)"), /* @__PURE__ */ React.createElement("pre", { className: "p-3 text-xs text-gray-700 bg-gray-50 leading-relaxed whitespace-pre-wrap" }, `macOS:
/Library/Application Support/ClaudeCode/
\u251C\u2500\u2500 CLAUDE.md              \u2190 Org instructions
\u251C\u2500\u2500 managed-settings.json  \u2190 Enforced settings
\u2514\u2500\u2500 managed-mcp.json       \u2190 Enforced MCP

Linux:
/etc/claude-code/
\u251C\u2500\u2500 CLAUDE.md
\u251C\u2500\u2500 managed-settings.json
\u2514\u2500\u2500 managed-mcp.json

Windows:
C:\\ProgramData\\ClaudeCode\\
\u251C\u2500\u2500 CLAUDE.md
\u251C\u2500\u2500 managed-settings.json
\u2514\u2500\u2500 managed-mcp.json`)), /* @__PURE__ */ React.createElement("div", { className: "border-2 rounded-lg overflow-hidden", style: { borderColor: COLORS.plugin.border } }, /* @__PURE__ */ React.createElement("div", { className: "px-3 py-2 text-white font-bold text-sm", style: { backgroundColor: COLORS.plugin.bg } }, "\u{1F50C} Plugin Structure"), /* @__PURE__ */ React.createElement("pre", { className: "p-3 text-xs text-gray-700 bg-gray-50 leading-relaxed whitespace-pre-wrap" }, `my-plugin/
\u251C\u2500\u2500 .claude-plugin/
\u2502   \u2514\u2500\u2500 plugin.json    \u2190 Manifest (optional)
\u251C\u2500\u2500 commands/          \u2190 /plugin-name:cmd
\u2502   \u2514\u2500\u2500 *.md
\u251C\u2500\u2500 agents/            \u2190 Subagents
\u2502   \u2514\u2500\u2500 *.md
\u251C\u2500\u2500 skills/            \u2190 Skills
\u2502   \u2514\u2500\u2500 */SKILL.md
\u251C\u2500\u2500 hooks/
\u2502   \u2514\u2500\u2500 hooks.json     \u2190 Lifecycle hooks
\u251C\u2500\u2500 output-styles/
\u2502   \u2514\u2500\u2500 *.md
\u251C\u2500\u2500 .mcp.json          \u2190 MCP servers
\u2514\u2500\u2500 .lsp.json          \u2190 LSP servers

Cached at: ~/.claude/plugins/cache/
Commands namespaced: /plugin-name:cmd`))));
}
function OverrideRulesTable() {
  const rules = [
    { fileType: "CLAUDE.md", mechanism: "ADDITIVE (all levels combine)", resolution: "More specific wins on conflicts. Enterprise > Project > User. Child dir overrides parent for files in that subtree.", merge: "Combine" },
    { fileType: "Rules (.claude/rules/)", mechanism: "ADDITIVE (all rules load)", resolution: "Path-scoped rules only load when matching files touched. When active, they effectively override global rules for those files.", merge: "Combine" },
    { fileType: "Settings.json", mechanism: "MERGE across tiers", resolution: "Higher tier wins for same key. Managed > CLI > Local > Project > User. Deny rules always win across all tiers.", merge: "Merge" },
    { fileType: "Skills", mechanism: "OVERRIDE by name", resolution: "Same-name skill: managed > CLI > project > user > plugin. Higher priority replaces lower.", merge: "Replace" },
    { fileType: "Sub-agents", mechanism: "OVERRIDE by name", resolution: "Same-name agent: managed > CLI > project > user > plugin.", merge: "Replace" },
    { fileType: "Commands", mechanism: "OVERRIDE by name", resolution: "Same-name command: project > user > plugin.", merge: "Replace" },
    { fileType: "Output Styles", mechanism: "ONE active at a time", resolution: "Only one style active. Selection stored in settings.local.json. Can be set at any tier via outputStyle key.", merge: "Replace" },
    { fileType: "MCP Servers", mechanism: "OVERRIDE by name", resolution: "Same-name server: enterprise > local > project > user.", merge: "Replace" },
    { fileType: "Hooks", mechanism: "MERGE all tiers", resolution: "All matching hooks from ALL tiers fire in parallel. They never override \u2014 they combine.", merge: "Combine" },
    { fileType: "Permissions", mechanism: "DENY always wins", resolution: "Deny evaluated first at every tier. Allow cannot override deny. Ask falls back to user prompt.", merge: "Special" }
  ];
  return /* @__PURE__ */ React.createElement("div", { className: "mb-8" }, /* @__PURE__ */ React.createElement("h2", { className: "text-xl font-bold mb-2", style: { color: "#1E293B" } }, "\u{1F4CB} Master Override Rules \u2014 Every File Type"), /* @__PURE__ */ React.createElement("div", { className: "border rounded-lg overflow-hidden" }, /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-4 gap-0 bg-gray-800 text-white text-xs font-bold" }, /* @__PURE__ */ React.createElement("div", { className: "p-2 border-r border-gray-600" }, "File Type"), /* @__PURE__ */ React.createElement("div", { className: "p-2 border-r border-gray-600" }, "How They Interact"), /* @__PURE__ */ React.createElement("div", { className: "p-2 border-r border-gray-600" }, "Conflict Resolution"), /* @__PURE__ */ React.createElement("div", { className: "p-2" }, "Behavior")), rules.map((r, i) => /* @__PURE__ */ React.createElement("div", { key: i, className: `grid grid-cols-4 gap-0 text-xs ${i % 2 === 0 ? "bg-white" : "bg-gray-50"}` }, /* @__PURE__ */ React.createElement("div", { className: "p-2 font-bold text-gray-800 border-r border-gray-200" }, r.fileType), /* @__PURE__ */ React.createElement("div", { className: "p-2 text-gray-700 border-r border-gray-200" }, r.mechanism), /* @__PURE__ */ React.createElement("div", { className: "p-2 text-gray-700 border-r border-gray-200" }, r.resolution), /* @__PURE__ */ React.createElement("div", { className: "p-2" }, /* @__PURE__ */ React.createElement("span", { className: `px-2 py-0.5 rounded-full text-xs font-bold ${r.merge === "Combine" ? "bg-green-100 text-green-800" : r.merge === "Merge" ? "bg-blue-100 text-blue-800" : r.merge === "Replace" ? "bg-orange-100 text-orange-800" : "bg-red-100 text-red-800"}` }, r.merge))))));
}
function App() {
  const allFiles = [
    {
      name: "Enterprise CLAUDE.md",
      icon: "\u{1F3E2}",
      location: "/Library/Application Support/ClaudeCode/CLAUDE.md (macOS) | /etc/claude-code/CLAUDE.md (Linux)",
      color: COLORS.enterprise,
      loadBehavior: "Always at start",
      purpose: "Organization-wide instructions deployed by IT/DevOps. Contains company coding standards, security policies, and compliance requirements. Every developer in the org sees these instructions.",
      whenLoads: "Loaded first at every session start. Permanent token cost.",
      priority: "HIGHEST priority (Priority 1). Cannot be overridden by any other CLAUDE.md file.",
      winsAgainst: "Everything \u2014 User CLAUDE.md, Project CLAUDE.md, Local CLAUDE.md, all rules, all settings",
      losesTo: "Nothing. This is the absolute top of the hierarchy.",
      shared: "Yes \u2014 all users in organization via MDM/Group Policy/Ansible deployment",
      tokenCost: "Permanent \u2014 every token counts against every session for every user",
      example: `# Company Policy
- All code must pass security scan before commit
- Use approved libraries only (see @/shared/approved-libs.md)
- Never commit API keys or secrets
- Follow SOC 2 compliance standards`,
      specialNotes: "Deployed via configuration management systems. Individual developers cannot edit this file. If enterprise says 'always use TypeScript', no project or user setting can say otherwise."
    },
    {
      name: "User CLAUDE.md",
      icon: "\u{1F464}",
      location: "~/.claude/CLAUDE.md",
      color: COLORS.user,
      loadBehavior: "Always at start",
      purpose: "Your personal preferences that apply to ALL your projects. Code style preferences, personal tool shortcuts, communication preferences.",
      whenLoads: "Loaded at every session start, after Enterprise but before Project files.",
      priority: "LOWEST priority among CLAUDE.md files (Priority 5). Overridden by Project and Local files.",
      winsAgainst: "Nothing in the CLAUDE.md hierarchy \u2014 this is the baseline foundation",
      losesTo: "Enterprise CLAUDE.md, Project CLAUDE.md, CLAUDE.local.md, and child-directory CLAUDE.md files",
      shared: "No \u2014 personal to you only, applies across all your projects",
      tokenCost: "Permanent \u2014 loaded every session. Keep under 50 lines.",
      example: `# Personal Preferences
- I prefer early returns in functions
- Use descriptive variable names
- Comments in English
- Concise responses, no emojis
- When in doubt, ask before making changes`,
      specialNotes: "If User says '2-space indent' but Project says '4-space indent', the Project wins. User is the fallback when no project-level instruction exists."
    },
    {
      name: "Project CLAUDE.md",
      icon: "\u{1F4E6}",
      location: "./CLAUDE.md or ./.claude/CLAUDE.md (root preferred if both exist)",
      color: COLORS.project,
      loadBehavior: "Always at start",
      purpose: "Team-shared project instructions committed to version control. Architecture decisions, coding standards, build commands, testing conventions.",
      whenLoads: "Loaded at session start. If both ./CLAUDE.md and ./.claude/CLAUDE.md exist, the root location (./CLAUDE.md) is preferred.",
      priority: "Medium-high (Priority 4). Overrides User but overridden by Local and Enterprise.",
      winsAgainst: "User CLAUDE.md (~/.claude/CLAUDE.md) on any conflicting instruction",
      losesTo: "Enterprise CLAUDE.md, CLI args, and CLAUDE.local.md",
      shared: "Yes \u2014 version-controlled, shared with entire team via git",
      tokenCost: "Permanent \u2014 loaded every session. Keep under 300 lines. Use @imports for detail files.",
      example: `# MyProject
## Tech Stack
Next.js 14, TypeScript strict, Prisma + PostgreSQL

## Commands
- Build: npm run build
- Test: npm test
- Lint: npm run lint

## Conventions
- Use Server Components by default
- Validate inputs with Zod

See @docs/architecture.md for full details`,
      specialNotes: "Use /init to auto-generate this file. The @import syntax pulls in additional files (max 5 recursive hops). This is the single most important file for team collaboration."
    },
    {
      name: "CLAUDE.local.md",
      icon: "\u{1F512}",
      location: "./CLAUDE.local.md (auto-added to .gitignore)",
      color: COLORS.local,
      loadBehavior: "Always at start",
      purpose: "Your personal overrides for THIS project only. Machine-specific URLs, sandbox configs, WIP notes, debugging strategies.",
      whenLoads: "Loaded at session start, after Project CLAUDE.md.",
      priority: "Highest among project-level CLAUDE.md files (Priority 3). Overrides Project CLAUDE.md.",
      winsAgainst: "Project CLAUDE.md and User CLAUDE.md on any conflicting instruction",
      losesTo: "Enterprise CLAUDE.md and CLI arguments only",
      shared: "No \u2014 auto-gitignored. Only exists on your machine.",
      tokenCost: "Permanent \u2014 loaded every session. Use for machine-specific context only.",
      example: `# My Local Setup
- Database: postgresql://localhost:5432/myapp_dev
- Redis: localhost:6379
- Currently working on: auth refactor (branch: feature/auth)
- My sandbox: https://sandbox-123.example.com`,
      specialNotes: "Only exists in one worktree. For multi-worktree setups, use @~/.claude/my-project-notes.md import from Project CLAUDE.md instead."
    },
    {
      name: "Parent Directory CLAUDE.md",
      icon: "\u{1F4C2}",
      location: "Any CLAUDE.md found recursing upward from cwd toward /",
      color: COLORS.project,
      loadBehavior: "Always at start",
      purpose: "Provides context from parent directories in monorepos. If you run Claude in foo/bar/, it loads both foo/CLAUDE.md and foo/bar/CLAUDE.md.",
      whenLoads: "All found files loaded in full at session start.",
      priority: "Closer-to-cwd files are more specific and win conflicts with parent files.",
      winsAgainst: "CLAUDE.md files in directories further from your cwd",
      losesTo: "Enterprise, Local, and CLAUDE.md files closer to your current directory",
      shared: "Depends on whether they're version-controlled",
      tokenCost: "Permanent \u2014 ALL found parent files are loaded. Be careful in deep directory structures.",
      example: `# In monorepo-root/CLAUDE.md:
This is a monorepo with React frontend and Node backend.

# In monorepo-root/packages/api/CLAUDE.md:
This package uses Express.js with middleware pattern.`,
      specialNotes: "Claude searches upward but stops BEFORE the filesystem root (/). This enables layered instructions in monorepos."
    },
    {
      name: "Child/Subtree CLAUDE.md",
      icon: "\u{1F33F}",
      location: "CLAUDE.md in any subdirectory below cwd",
      color: { bg: "#0D9488", light: "#CCFBF1", border: "#14B8A6", text: "#115E59" },
      loadBehavior: "On-demand",
      purpose: "Provides module-specific context when Claude reads files in that subdirectory. Loaded lazily to save tokens.",
      whenLoads: "NOT loaded at start. Only loaded when Claude reads files in that specific subtree.",
      priority: "Most specific when active \u2014 overrides parent CLAUDE.md for files in its subtree.",
      winsAgainst: "Parent directory CLAUDE.md and root CLAUDE.md for files within this subtree",
      losesTo: "Enterprise and CLAUDE.local.md",
      shared: "Yes if version-controlled",
      tokenCost: "ZERO until triggered \u2014 then costs tokens for the rest of the session.",
      example: `# src/api/CLAUDE.md
## API Module Standards
- Use Zod for input validation
- Return 400 with field-level errors
- Cursor-based pagination, max 100 per page
- Rate limit: 1000 req/hr authenticated`,
      specialNotes: "This is how you achieve zero-cost-until-needed context. Put specialized instructions in subdirectories instead of bloating root CLAUDE.md."
    },
    {
      name: "Global Rules (.claude/rules/*.md)",
      icon: "\u{1F4CF}",
      location: ".claude/rules/*.md (no paths: frontmatter)",
      color: COLORS.project,
      loadBehavior: "Always at start",
      purpose: "Modular project instructions that apply globally. Equivalent to putting the content in CLAUDE.md but organized into separate files.",
      whenLoads: "All .md files in .claude/rules/ discovered recursively at session start (if no paths: frontmatter).",
      priority: "Same as Project CLAUDE.md. Loaded alongside project memory.",
      winsAgainst: "User-level rules and User CLAUDE.md",
      losesTo: "Enterprise, Local, and path-scoped rules (when matching files are active)",
      shared: "Yes \u2014 version-controlled with the project",
      tokenCost: "Permanent \u2014 every rule without paths: costs tokens at startup.",
      example: `# .claude/rules/testing.md
# Testing Standards
- Use Vitest for unit tests
- Mock external APIs in tests
- Aim for 80% coverage on new code
- Test error cases, not just happy path`,
      specialNotes: "Supports subdirectories for organization. Supports symlinks for sharing across projects."
    },
    {
      name: "Path-Scoped Rules",
      icon: "\u{1F3AF}",
      location: ".claude/rules/*.md (WITH paths: frontmatter)",
      color: { bg: "#0284C7", light: "#E0F2FE", border: "#0EA5E9", text: "#0C4A6E" },
      loadBehavior: "On-demand",
      purpose: "Rules that only activate when Claude works with files matching specific glob patterns. The key mechanism for context-aware, zero-cost loading.",
      whenLoads: "NOT loaded at start. Only loaded when Claude reads/edits files matching the paths: globs.",
      priority: "When active, effectively overrides global rules for matching files due to greater specificity.",
      winsAgainst: "Global rules for the matching files, because path-scoped rules are more specific",
      losesTo: "Enterprise policy",
      shared: "Yes \u2014 version-controlled",
      tokenCost: "ZERO until triggered. This is how you keep context lean.",
      example: `---
paths:
  - "src/api/**/*.ts"
  - "tests/api/**/*.test.ts"
---
# API Security Rules
- Always validate JWT tokens
- Rate limit all endpoints
- Log suspicious access patterns
- Never expose internal error details`,
      specialNotes: "Glob patterns support brace expansion: src/**/*.{ts,tsx}. Known issue: path-scoped rules may sometimes load at start in some versions."
    },
    {
      name: "User-Level Rules",
      icon: "\u{1F464}\u{1F4CF}",
      location: "~/.claude/rules/*.md",
      color: COLORS.user,
      loadBehavior: "Always at start",
      purpose: "Personal rules that apply to all your projects. Universal preferences and workflows.",
      whenLoads: "Loaded at session start, before project-level rules.",
      priority: "Lower than project rules. Project rules override on conflict.",
      winsAgainst: "These are the baseline \u2014 overridden by everything more specific",
      losesTo: "Project rules, Local, Enterprise",
      shared: "No \u2014 personal to you",
      tokenCost: "Permanent \u2014 loaded every session across all projects.",
      example: `# ~/.claude/rules/preferences.md
- I prefer functional programming patterns
- Use early returns
- Keep functions under 30 lines
- TypeScript strict mode always`,
      specialNotes: "Known issue: paths: frontmatter in user-level rules may be ignored in some versions."
    },
    {
      name: "Skills (.claude/skills/*/SKILL.md)",
      icon: "\u{1F6E0}\uFE0F",
      location: ".claude/skills/<skill-name>/SKILL.md (project) | ~/.claude/skills/<skill-name>/SKILL.md (user)",
      color: { bg: "#B45309", light: "#FEF3C7", border: "#F59E0B", text: "#78350F" },
      loadBehavior: "Progressive disclosure",
      purpose: "Reusable multi-step workflows. Only metadata loads at start; full instructions load on-demand when invoked.",
      whenLoads: "Phase 1: name + description from frontmatter loaded at start (~100 tokens). Phase 2: Full SKILL.md body loaded only when Claude invokes it.",
      priority: "Override by name: managed > CLI > project > user > plugin.",
      winsAgainst: "User skill (same name) if this is a project skill",
      losesTo: "Managed/CLI skill with same name",
      shared: "Project skills: yes. User skills: no.",
      tokenCost: "Minimal at start (~100 tokens per skill for frontmatter). Full body loaded on-demand only.",
      example: `---
name: deploy
description: "Deploy the application to staging or production"
allowed-tools: Bash, Read
---
# Deploy Skill
1. Run tests: npm test
2. Build: npm run build
3. Deploy to $1 environment
4. Verify health check`,
      specialNotes: "Skills replaced slash commands as the primary extension mechanism. Commands still work. $ARGUMENTS and $1/$2 placeholders are supported."
    },
    {
      name: "Slash Commands (.claude/commands/*.md)",
      icon: "\u26A1",
      location: ".claude/commands/*.md (project) | ~/.claude/commands/*.md (user)",
      color: { bg: "#6D28D9", light: "#EDE9FE", border: "#8B5CF6", text: "#4C1D95" },
      loadBehavior: "User-invoked",
      purpose: "Predecessor to skills. Quick command templates invoked via /command-name. Still fully supported.",
      whenLoads: "Frontmatter scanned at start for autocomplete. Full content loaded only when user types /command-name.",
      priority: "If a skill and command share the same name, the skill takes precedence.",
      winsAgainst: "User commands if this is a project command",
      losesTo: "Same-name skill",
      shared: "Project commands: yes. User commands: no.",
      tokenCost: "Minimal at start (frontmatter only). Full content on invocation.",
      example: `---
description: "Review code for best practices"
allowed-tools: Read, Grep, Glob
---
Review the code in $ARGUMENTS for:
1. Security vulnerabilities
2. Performance issues
3. Code style violations
Provide actionable suggestions.`,
      specialNotes: "Subdirectories create namespace labels: .claude/commands/frontend/component.md creates /component with label '(project:frontend)'."
    },
    {
      name: "Sub-agents (.claude/agents/*.md)",
      icon: "\u{1F916}",
      location: ".claude/agents/*.md (project) | ~/.claude/agents/*.md (user)",
      color: { bg: "#0369A1", light: "#E0F2FE", border: "#0284C7", text: "#0C4A6E" },
      loadBehavior: "Always at start",
      purpose: "Specialized AI instances with their own context window, tool permissions, and system prompt. Run independently from main session.",
      whenLoads: "Loaded at session start. Run in separate context windows when delegated to.",
      priority: "Override by name: managed > CLI (--agents) > project > user > plugin.",
      winsAgainst: "User agent (same name) if this is a project agent",
      losesTo: "Managed/CLI agent with same name",
      shared: "Project agents: yes. User agents: no.",
      tokenCost: "Frontmatter at start (~100-200 tokens). Execution uses SEPARATE context window \u2014 does not consume main session tokens.",
      example: `---
name: code-reviewer
description: "Reviews code for quality and security"
tools: Read, Grep, Glob
model: sonnet
---
You are a senior code reviewer.
Focus on security, performance, and maintainability.
Provide specific line-number references.`,
      specialNotes: "Sub-agents cannot spawn other sub-agents (no infinite nesting). Built-in agents: Explore (Haiku, read-only), Plan (Sonnet, research), General (Sonnet, full)."
    },
    {
      name: "Output Styles (.claude/output-styles/*.md)",
      icon: "\u{1F3A8}",
      location: ".claude/output-styles/*.md (project) | ~/.claude/output-styles/*.md (user)",
      color: { bg: "#BE185D", light: "#FCE7F3", border: "#EC4899", text: "#831843" },
      loadBehavior: "User-invoked",
      purpose: "MOST POWERFUL file type. Directly REPLACES Claude Code's system prompt default instructions. Can repurpose Claude Code beyond software engineering.",
      whenLoads: "Loaded when user selects via /output-style. Selection persists in settings.local.json.",
      priority: "Only one style active at a time. Can be set at any settings tier via outputStyle key.",
      winsAgainst: "Default system prompt instructions. CLAUDE.md adds context; output styles REPLACE the foundation.",
      losesTo: "Nothing in terms of system prompt control \u2014 this is the most powerful override",
      shared: "Project styles: yes. User styles: no.",
      tokenCost: "Replaces existing system prompt text \u2014 no additional cost, may even reduce tokens.",
      example: `---
name: concise
description: "Minimal output, no explanations"
keep-coding-instructions: true
---
Be extremely concise. No pleasantries.
Code only, no explanations unless asked.
Maximum 5 lines of non-code text per response.`,
      specialNotes: "CRITICAL: Without keep-coding-instructions: true, the default software engineering instructions are REMOVED. Built-in styles: Default, Explanatory, Learning."
    },
    {
      name: "Auto Memory (MEMORY.md)",
      icon: "\u{1F9E0}",
      location: "~/.claude/projects/<project>/memory/MEMORY.md + topic files",
      color: COLORS.auto,
      loadBehavior: "First 200 lines at start",
      purpose: "Claude writes these notes FOR ITSELF. Learnings, patterns, and insights discovered during sessions. You don't write these \u2014 Claude does.",
      whenLoads: "First 200 lines of MEMORY.md loaded at every session start. Topic files (debugging.md, etc.) loaded on-demand when Claude reads them.",
      priority: "Informational \u2014 does not override CLAUDE.md instructions. Both combine additively.",
      winsAgainst: "No conflict with other files \u2014 additive information",
      losesTo: "Explicit CLAUDE.md instructions always take priority over auto-discovered patterns",
      shared: "No \u2014 stored outside the repo at ~/.claude/projects/",
      tokenCost: "First 200 lines permanent. Topic files on-demand.",
      example: `# MEMORY.md (written by Claude)
## Project Patterns
- Uses pnpm, not npm
- Tests require local Redis instance
- API follows REST conventions with Zod validation

## Debugging Notes
See debugging.md for PostgreSQL connection patterns`,
      specialNotes: "Control with CLAUDE_CODE_DISABLE_AUTO_MEMORY env var (0=force on, 1=force off). Use /memory to edit. Per-project, derived from git root."
    },
    {
      name: "@Imported Files",
      icon: "\u{1F4CE}",
      location: "Any file referenced via @path/to/file in CLAUDE.md",
      color: COLORS.system,
      loadBehavior: "With parent file",
      purpose: "Pull external files into CLAUDE.md context. Enables modular documentation without bloating the main file.",
      whenLoads: "Loaded when the parent CLAUDE.md file loads. Imports are recursive up to 5 hops deep.",
      priority: "Same as the parent CLAUDE.md that imports them.",
      winsAgainst: "Same as parent file",
      losesTo: "Same as parent file",
      shared: "Depends on where the parent CLAUDE.md is stored",
      tokenCost: "ADDS to parent's permanent token cost. Every imported file is loaded every session.",
      example: `# In CLAUDE.md:
See @README.md for overview
Git workflow: @docs/git-instructions.md
Personal prefs: @~/.claude/my-project-notes.md`,
      specialNotes: "Relative paths resolve from the importing file's location, NOT the working directory. Not evaluated inside markdown code blocks. First use in a project shows an approval dialog."
    }
  ];
  const [expandedFile, setExpandedFile] = useState(null);
  const [activeTab, setActiveTab] = useState("pyramid");
  const tabs = [
    { id: "pyramid", label: "\u{1F3D4}\uFE0F Precedence", desc: "Who overrides whom" },
    { id: "files", label: "\u{1F4C4} All Files", desc: "Every markdown file" },
    { id: "conflicts", label: "\u2694\uFE0F Conflicts", desc: "Real scenarios" },
    { id: "timeline", label: "\u23F1\uFE0F Loading", desc: "When files load" },
    { id: "settings", label: "\u2699\uFE0F Settings", desc: "JSON hierarchy" },
    { id: "dirs", label: "\u{1F4C1} Directories", desc: "Complete map" },
    { id: "rules", label: "\u{1F4CB} Rules Table", desc: "Override rules" }
  ];
  return /* @__PURE__ */ React.createElement("div", { className: "max-w-4xl mx-auto p-4 font-sans", style: { backgroundColor: "#FAFBFC" } }, /* @__PURE__ */ React.createElement("div", { className: "text-center mb-6" }, /* @__PURE__ */ React.createElement("h1", { className: "text-2xl font-bold", style: { color: "#0F172A" } }, "Claude Code: Complete File Hierarchy & Precedence Guide"), /* @__PURE__ */ React.createElement("p", { className: "text-sm text-gray-500 mt-1" }, "Every markdown file, every config, every conflict resolution rule")), /* @__PURE__ */ React.createElement("div", { className: "flex flex-wrap gap-1 mb-6 justify-center" }, tabs.map((tab) => /* @__PURE__ */ React.createElement(
    "button",
    {
      key: tab.id,
      className: `px-3 py-2 rounded-lg text-xs font-medium transition-all ${activeTab === tab.id ? "bg-gray-800 text-white shadow-md" : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"}`,
      onClick: () => setActiveTab(tab.id)
    },
    /* @__PURE__ */ React.createElement("div", null, tab.label),
    /* @__PURE__ */ React.createElement("div", { className: "text-xs opacity-70" }, tab.desc)
  ))), activeTab === "pyramid" && /* @__PURE__ */ React.createElement(PrecedencePyramid, null), activeTab === "files" && /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("h2", { className: "text-xl font-bold mb-2", style: { color: "#1E293B" } }, "\u{1F4C4} Every Markdown File Claude Code Reads"), /* @__PURE__ */ React.createElement("p", { className: "text-sm text-gray-500 mb-3" }, "Click any file for complete details including examples, priority, and conflict behavior."), allFiles.map((file, i) => /* @__PURE__ */ React.createElement(
    MarkdownFileCard,
    {
      key: i,
      file,
      isExpanded: expandedFile === i,
      onToggle: () => setExpandedFile(expandedFile === i ? null : i)
    }
  ))), activeTab === "conflicts" && /* @__PURE__ */ React.createElement(ConflictScenarios, null), activeTab === "timeline" && /* @__PURE__ */ React.createElement(LoadingTimeline, null), activeTab === "settings" && /* @__PURE__ */ React.createElement(SettingsHierarchy, null), activeTab === "dirs" && /* @__PURE__ */ React.createElement(DirectoryMap, null), activeTab === "rules" && /* @__PURE__ */ React.createElement(OverrideRulesTable, null), /* @__PURE__ */ React.createElement("div", { className: "mt-6 p-3 bg-gray-100 rounded-lg border" }, /* @__PURE__ */ React.createElement("p", { className: "text-xs font-bold text-gray-600 mb-2" }, "Color Legend:"), /* @__PURE__ */ React.createElement("div", { className: "flex flex-wrap gap-2" }, [
    { label: "Enterprise", color: COLORS.enterprise.bg },
    { label: "Project", color: COLORS.project.bg },
    { label: "User", color: COLORS.user.bg },
    { label: "Local", color: COLORS.local.bg },
    { label: "Auto-generated", color: COLORS.auto.bg },
    { label: "Plugin", color: COLORS.plugin.bg }
  ].map((item) => /* @__PURE__ */ React.createElement("div", { key: item.label, className: "flex items-center gap-1 text-xs text-gray-700" }, /* @__PURE__ */ React.createElement("div", { className: "w-3 h-3 rounded", style: { backgroundColor: item.color } }), item.label))));
}
ReactDOM.createRoot(document.getElementById("root")).render(/* @__PURE__ */ React.createElement(App, null));
