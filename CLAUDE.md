# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Jekyll-based static documentation site about Claude Code configuration, architecture patterns, and training materials. The site is deployed to GitHub Pages from the `dev` branch and provides interactive diagrams, comprehensive guides, and training resources for Claude Code mastery.

**Live site**: Deployed via GitHub Pages from `dev` branch
**Theme**: Jekyll Midnight theme
**Primary audience**: Developers learning advanced Claude Code configuration and architecture

## Architecture

### Content Structure

The repository contains three primary content types:

1. **Interactive Diagrams** (`.jsx` files + `.html` wrappers)
   - `claude-code-architecture-diagram.jsx` - Full lifecycle visual flow of 16 markdown file types
   - `claude-code-precedence-diagram.jsx` - Complete file hierarchy and precedence guide
   - `override-test-lab.jsx` - 12 hands-on test scenarios for precedence rules
   - Each has a corresponding `.html` wrapper file for browser rendering

2. **Markdown Documentation** (`.md` files)
   - `claude-code-all-markdown-files-catalog.md` - Complete catalog of all 16 Claude Code markdown file types
   - `claude-code-config-guide.md` - Architecture guide comparing CLAUDE.md vs Rules vs Skills
   - `Claude-Training.md` - 8-module training program for elite Claude Code mastery
   - `index.md` - Site homepage with navigation

3. **Reference Documents** (`.docx` files)
   - Word document versions for offline reference (excluded from Jekyll build via `_config.yml`)

### Jekyll Configuration

- **Config file**: `_config.yml`
- **Theme**: jekyll-theme-midnight
- **Markdown engine**: kramdown with rouge syntax highlighting
- **Excluded files**: README.md, LICENSE, .gitignore, and all `*.docx` files
- **Default layout**: All pages use `default` layout via frontmatter defaults

## Common Tasks

### Building and Testing Locally

This is a GitHub Pages site using Jekyll. To test locally:

```bash
# Install dependencies (first time only)
bundle install

# Serve locally
bundle exec jekyll serve

# Build without serving
bundle exec jekyll build
```

The built site outputs to `_site/` directory (git-ignored).

### Deployment

Deployment is automated via GitHub Actions:
- **Trigger**: Push to `dev` branch or manual workflow dispatch
- **Workflow**: `.github/workflows/jekyll-gh-pages.yml`
- **Process**: Checkout → Setup Pages → Build with Jekyll → Upload artifact → Deploy
- No manual deployment steps required

### Working with Content

**Adding new markdown documentation:**
1. Create `.md` file in repository root
2. Add YAML frontmatter with `layout: default` and `title:`
3. Content automatically appears in site build
4. Add navigation links to `index.md` if needed

**Adding new interactive diagrams:**
1. Create `.jsx` file with React component
2. Create corresponding `.html` wrapper file
3. Link from `index.md`

**Editing existing content:**
- Markdown files can be edited directly
- Jekyll automatically rebuilds on push to `dev` branch via GitHub Actions

## File Organization

```
/
├── .github/workflows/          # GitHub Actions for deployment
│   └── jekyll-gh-pages.yml     # Auto-deploy workflow
├── _config.yml                 # Jekyll configuration
├── index.md                    # Homepage with navigation
├── *.md                        # Documentation pages
├── *.jsx                       # Interactive diagram React components
├── *.html                      # HTML wrappers for JSX diagrams
├── *.docx                      # Offline reference docs (excluded from build)
└── *.png                       # Images (e.g., architecture diagrams)
```

## Content Guidelines

**When editing documentation:**

- Maintain consistency with existing technical depth - these guides are comprehensive reference materials
- All claims about Claude Code behavior should be accurate to official documentation (as of 2025-2026)
- Include specific file paths, token counts, and command syntax where relevant
- Use code blocks with language identifiers for syntax highlighting
- Preserve the existing frontmatter structure in markdown files

**When working with the catalog and guide files:**

- `claude-code-all-markdown-files-catalog.md` - Authoritative reference for all 16 Claude Code file types
- `claude-code-config-guide.md` - Decision framework for CLAUDE.md vs Rules vs Skills
- `Claude-Training.md` - 8-module training curriculum, targets .NET/Azure developers

These are the core reference materials - changes should maintain accuracy and comprehensiveness.

## Git Workflow

- **Main branch**: `main` (for PRs and releases)
- **Deploy branch**: `dev` (triggers GitHub Pages deployment)
- **Commit style**: Conventional commits preferred but not enforced
- **Untracked files**: `Learning-prompt-template.md` is currently untracked (new file)

## Key Technical Details

**Jekyll-specific:**
- This is a static site generator - no server-side code execution
- Liquid templating available but not heavily used in this repo
- GitHub Pages builds automatically from `dev` branch
- Local builds require Ruby + Bundler environment

**React diagrams:**
- `.jsx` files contain React components for interactive diagrams
- Rendered client-side in browser via `.html` wrapper files
- These are standalone React apps, not part of Jekyll build process

## Maintenance Notes

**When adding new Claude Code features to documentation:**
1. Update the relevant catalog or guide file with accurate details
2. Include version/date information where applicable (e.g., "Introduced in v2.0.64")
3. Verify against official Claude Code documentation
4. Update navigation links in `index.md` if adding new top-level pages

**File naming conventions:**
- Markdown docs: lowercase-with-hyphens.md
- Interactive diagrams: descriptive-name.jsx + matching .html wrapper
- Keep filenames concise but descriptive
