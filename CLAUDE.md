# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Astro + Starlight** documentation site covering Claude Code configuration, RAG architectures, BERT, LangChain, and certification prep. Deployed to GitHub Pages via the `gh-pages` branch.

**Live site**: `https://rajrkdev.github.io/ai-lab`
**Base path**: `/ai-lab`
**Theme**: Astro Starlight
**Primary audience**: Developers learning advanced Claude Code configuration and AI/ML architecture

## Architecture

### Tech Stack

- **Astro v6** with **Starlight** for docs layout and navigation
- **React v19** (via `@astrojs/react`) for interactive diagram components
- Content authored in `.md` / `.mdx` files; React components embedded via MDX

### Content Structure

All documentation lives under `src/content/docs/`, organized into sidebar sections defined in `astro.config.mjs`:

| Directory | Sidebar Label |
|---|---|
| `claude-code/` | Claude Code |
| `rag/` | RAG Guides |
| `bert/` | BERT Architectures |
| `langchain/` | LangChain Reference |
| `cert/` | Cert Prep |

Each directory has an `index.md` as the section landing page.

### Interactive Components

React components live in `src/components/interactive/` and are embedded in `.mdx` files via import. Each component is a self-contained React app (no shared state). Examples: `ArchDiagram.jsx`, `PrecedenceDiagram.jsx`, `OverrideTestLab.jsx`, `RagAcademy.jsx`, `CertQuiz.jsx`.

To add a new interactive component:
1. Create `src/components/interactive/MyComponent.jsx`
2. Create a `.mdx` file in the appropriate content directory
3. Import and render: `import MyComponent from '../../../components/interactive/MyComponent.jsx'`

### Custom Sidebar Toggle

`astro.config.mjs` injects an inline script that adds collapsible left-nav and right-TOC toggle buttons, persisted via `localStorage` keys `sl-nav-collapsed` / `sl-toc-collapsed`. CSS for this lives in `src/styles/custom.css`.

## Common Commands

```bash
npm install          # Install dependencies
npm run dev          # Dev server at localhost:4321
npm run build        # Build to ./dist/
npm run preview      # Preview production build locally
```

## Deployment

- **Trigger**: Push to `main` or `feature/rag-hub` branches
- **Workflow**: `.github/workflows/deploy.yml`
- **Process**: Node 22 → `npm ci` → `astro build` → deploy `./dist` to `gh-pages` branch via `peaceiris/actions-gh-pages`

## Git Workflow

- **Main branch**: `main`
- **Active feature branch**: `feature/rag-hub`
- **Deploy branch**: `gh-pages` (auto-managed by CI; do not push manually)
- Conventional commits preferred but not enforced

## Content Guidelines

- All `.md`/`.mdx` files require Astro frontmatter: at minimum `title:` and optionally `description:` and `sidebar: { order: N }`
- Claims about Claude Code behavior should be accurate to official documentation (as of 2025–2026); include version info where relevant (e.g., "Introduced in v2.0.64")
- Core reference files (not to be degraded in quality):
  - `src/content/docs/claude-code/claude-code-all-markdown-files-catalog.md` — all 16 Claude Code markdown file types
  - `src/content/docs/claude-code/claude-code-config-guide.md` — CLAUDE.md vs Rules vs Skills decision framework
  - `src/content/docs/claude-code/claude-training.md` — 8-module training curriculum (.NET/Azure focus)
