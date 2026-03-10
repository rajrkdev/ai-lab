#!/usr/bin/env python3
"""
Validate structural integrity of concepts documented in the ai-lab repo.

Checks:
1. Every file referenced in index.md exists.
2. Every markdown file has a valid front-matter title (if it has front-matter).
3. Required concept sections are present in Claude-Training.md.
4. Required file-type entries are present in the catalog.
5. Every code block in markdown files has a language hint.
6. No broken internal markdown links between .md files.

Exits 0 on success, 1 on failure. Writes concept-validation-results.json.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
RESULTS: list[dict] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def result(check: str, status: str, detail: str = "") -> None:
    entry = {"check": check, "status": status, "detail": detail}
    RESULTS.append(entry)
    icon = "✅" if status == "PASS" else ("⚠️ " if status == "WARN" else "❌")
    print(f"{icon} [{status}] {check}" + (f": {detail}" if detail else ""))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Check 1: Files referenced in index.md exist
# ---------------------------------------------------------------------------

def check_index_references() -> None:
    index_path = ROOT / "index.md"
    if not index_path.exists():
        result("index.md exists", "FAIL", "index.md not found")
        return
    result("index.md exists", "PASS")

    content = read(index_path)

    # Internal .md links like [text](page-name) or [text](page-name.md)
    md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    for link_text, href in md_links:
        if href.startswith("http") or href.startswith("#") or href.startswith("mailto"):
            continue
        # Strip anchors
        href_clean = href.split("#")[0].strip()
        if not href_clean:
            continue
        # Try as-is and with .md extension
        candidates = [ROOT / href_clean, ROOT / (href_clean + ".md")]
        found = any(c.exists() for c in candidates)
        check_name = f"index.md link → {href_clean}"
        if found:
            result(check_name, "PASS")
        else:
            result(check_name, "FAIL", f"Referenced file '{href_clean}' not found")


# ---------------------------------------------------------------------------
# Check 2: Front-matter title present in every .md that has front-matter
# ---------------------------------------------------------------------------

def check_frontmatter_titles() -> None:
    for md_file in ROOT.glob("*.md"):
        if md_file.name.startswith("."):
            continue
        content = read(md_file)
        if content.startswith("---"):
            # Has front-matter
            end = content.find("\n---", 3)
            if end != -1:
                fm = content[3:end]
                has_title = bool(re.search(r'^title\s*:', fm, re.MULTILINE))
                if has_title:
                    result(f"front-matter title in {md_file.name}", "PASS")
                else:
                    result(f"front-matter title in {md_file.name}", "WARN",
                           "Front-matter present but no 'title:' field")


# ---------------------------------------------------------------------------
# Check 3: Required module headers in Claude-Training.md
# ---------------------------------------------------------------------------

REQUIRED_MODULES = [
    "Module 1",
    "Module 2",
    "Module 3",
    "Module 4",
    "Module 5",
    "Module 6",
    "Module 7",
    "Module 8",
]

def check_training_modules() -> None:
    training = ROOT / "Claude-Training.md"
    if not training.exists():
        result("Claude-Training.md exists", "FAIL")
        return
    result("Claude-Training.md exists", "PASS")
    content = read(training)
    for module in REQUIRED_MODULES:
        if module in content:
            result(f"Training module '{module}' present", "PASS")
        else:
            result(f"Training module '{module}' present", "FAIL",
                   f"'{module}' heading not found in Claude-Training.md")


# ---------------------------------------------------------------------------
# Check 4: Required concept sections in the training document
# ---------------------------------------------------------------------------

REQUIRED_CONCEPTS = {
    "CLAUDE.md": "CLAUDE.md configuration",
    "hooks": "Hooks system",
    "MCP": "Model Context Protocol",
    "agent": "Agent / multi-agent",
    "RAG": "Retrieval-Augmented Generation",
    "CI/CD": "CI/CD integration",
    "token": "Token / context window management",
    "skill": "Skills system",
}

def check_concept_coverage() -> None:
    training = ROOT / "Claude-Training.md"
    catalog = ROOT / "claude-code-all-markdown-files-catalog.md"
    config_guide = ROOT / "claude-code-config-guide.md"

    all_content = ""
    for path in (training, catalog, config_guide):
        if path.exists():
            all_content += read(path)

    for keyword, label in REQUIRED_CONCEPTS.items():
        if re.search(re.escape(keyword), all_content, re.IGNORECASE):
            result(f"Concept coverage: {label}", "PASS")
        else:
            result(f"Concept coverage: {label}", "FAIL",
                   f"Keyword '{keyword}' not found in documentation")


# ---------------------------------------------------------------------------
# Check 5: File-type catalog completeness (≥16 entries)
# ---------------------------------------------------------------------------

def check_catalog_completeness() -> None:
    catalog = ROOT / "claude-code-all-markdown-files-catalog.md"
    if not catalog.exists():
        result("Catalog file exists", "FAIL")
        return
    result("Catalog file exists", "PASS")
    content = read(catalog)
    # Count numbered headings like "### 1." "### 2." … "### 16."
    entries = re.findall(r'###\s+\d+\.', content)
    count = len(entries)
    if count >= 16:
        result(f"Catalog has ≥16 file-type entries (found {count})", "PASS")
    else:
        result(f"Catalog has ≥16 file-type entries (found {count})", "FAIL",
               "Expected at least 16 numbered sections")


# ---------------------------------------------------------------------------
# Check 6: Code blocks have language hints
# ---------------------------------------------------------------------------

def check_code_block_languages() -> None:
    files_checked = 0
    missing: list[str] = []
    for md_file in ROOT.glob("*.md"):
        if md_file.name.startswith("."):
            continue
        content = read(md_file)
        # Count opening fences that have no language hint.
        # A fence line is an opening fence when we are NOT already inside a
        # code block (in_block is False); it is a closing fence when we ARE
        # inside a block (in_block is True).
        lines = content.splitlines()
        bare_opening = 0
        in_block = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                if not in_block:
                    # Opening fence — check if it has a language
                    lang = stripped[3:].strip()
                    if not lang:
                        bare_opening += 1
                    in_block = True
                else:
                    # Closing fence
                    in_block = False
        if bare_opening:
            missing.append(f"{md_file.name} ({bare_opening} unlabelled opening fences)")
        files_checked += 1
    if missing:
        result(
            f"Code blocks have language hints ({files_checked} files checked)",
            "WARN",
            "Files with unlabelled opening fences: " + ", ".join(missing),
        )
    else:
        result(
            f"Code blocks have language hints ({files_checked} files checked)",
            "PASS",
        )


# ---------------------------------------------------------------------------
# Check 7: Internal .md cross-links resolve
# ---------------------------------------------------------------------------

def check_internal_md_links() -> None:
    all_md = {p.stem: p for p in ROOT.glob("*.md")}
    broken: list[str] = []
    for md_file in ROOT.glob("*.md"):
        content = read(md_file)
        links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md[^)]*)\)', content)
        for _, href in links:
            href_clean = href.split("#")[0].strip()
            stem = Path(href_clean).stem
            if stem not in all_md and not (ROOT / href_clean).exists():
                broken.append(f"{md_file.name} → {href_clean}")
    if broken:
        result("Internal .md cross-links", "FAIL",
               "Broken links: " + "; ".join(broken))
    else:
        result("Internal .md cross-links", "PASS")


# ---------------------------------------------------------------------------
# Check 8: Key Claude Code facts — sanity checks on documented values
# ---------------------------------------------------------------------------

FACT_CHECKS: list[tuple[str, str, str]] = [
    # (description, file_stem, regex_pattern)
    ("200K token context window documented",
     "Claude-Training",
     r'200[,\s]?K\s+token'),
    ("CLAUDE.md hierarchy documented (CLI flags highest priority)",
     "Claude-Training",
     r'CLI\s+flags'),
    ("Hooks PreToolUse event documented",
     "Claude-Training",
     r'PreToolUse'),
    ("Hooks PostToolUse event documented",
     "Claude-Training",
     r'PostToolUse'),
    ("Hooks exit code 2 for blocking error documented",
     "Claude-Training",
     r'exit\s+code\s+2'),
    ("MCP JSON-RPC 2.0 documented",
     "Claude-Training",
     r'JSON-RPC\s+2\.0'),
    ("MCP Tools/Resources/Prompts primitives documented",
     "Claude-Training",
     r'Tools.*Resources.*Prompts|Prompts.*Resources.*Tools'),
    ("Extended thinking 'ultrathink' trigger documented",
     "Claude-Training",
     r'ultrathink'),
    ("Agent teams CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS env var documented",
     "Claude-Training",
     r'CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS'),
    ("Subagent memory MEMORY.md documented in catalog",
     "claude-code-all-markdown-files-catalog",
     r'MEMORY\.md'),
    ("CLAUDE.local.md gitignored — documented in catalog",
     "claude-code-all-markdown-files-catalog",
     r'CLAUDE\.local\.md'),
    ("Rules path-scoping documented in config guide",
     "claude-code-config-guide",
     r'path.?scoped|paths:'),
    ("Skills on-demand loading documented in config guide",
     "claude-code-config-guide",
     r'on.?demand'),
    ("Import @path syntax documented in config guide",
     "claude-code-config-guide",
     r'@path|@.*\.md'),
    ("anthropics/claude-code-action GitHub Action documented",
     "Claude-Training",
     r'anthropics/claude-code-action'),
]

def check_key_facts() -> None:
    file_cache: dict[str, str] = {}
    for desc, file_stem, pattern in FACT_CHECKS:
        if file_stem not in file_cache:
            path = ROOT / (file_stem + ".md")
            file_cache[file_stem] = read(path) if path.exists() else ""
        content = file_cache[file_stem]
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            result(f"Fact check: {desc}", "PASS")
        else:
            result(f"Fact check: {desc}", "FAIL",
                   f"Pattern '{pattern}' not found in {file_stem}.md")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 70)
    print("  Concept Validation — ai-lab repository")
    print("=" * 70)
    print()

    check_index_references()
    print()
    check_frontmatter_titles()
    print()
    check_training_modules()
    print()
    check_concept_coverage()
    print()
    check_catalog_completeness()
    print()
    check_code_block_languages()
    print()
    check_internal_md_links()
    print()
    check_key_facts()
    print()

    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    warned = sum(1 for r in RESULTS if r["status"] == "WARN")
    failed = sum(1 for r in RESULTS if r["status"] == "FAIL")
    total = len(RESULTS)

    summary = {
        "total": total,
        "passed": passed,
        "warned": warned,
        "failed": failed,
        "results": RESULTS,
    }

    out_path = ROOT / "concept-validation-results.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Results written to {out_path}")
    print()
    print("=" * 70)
    print(f"  SUMMARY: {passed} passed | {warned} warned | {failed} failed | {total} total")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
