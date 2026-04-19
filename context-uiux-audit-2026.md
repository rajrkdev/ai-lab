# Context Microsite — Deep UI/UX Audit
**Site:** rajrkdev.github.io/ai-lab  
**Audit date:** April 15, 2026  
**Scope:** Design, presentation, layout, interaction, visual hierarchy, typography, components, patterns  
**Pages reviewed:** All 63 across 5 modules + homepage  

---

## Table of Contents

1. [Summary Verdict](#1-summary-verdict)
2. [Design System Audit](#2-design-system-audit)
3. [Homepage — Detailed UI/UX Review](#3-homepage--detailed-uiux-review)
4. [Global Chrome — Nav, Sidebar, Header, Footer](#4-global-chrome--nav-sidebar-header-footer)
5. [Content Pages — Layout & Presentation](#5-content-pages--layout--presentation)
6. [Interactive Tool Pages — UI/UX](#6-interactive-tool-pages--uiux)
7. [Component-Level Audit](#7-component-level-audit)
8. [Typography & Readability](#8-typography--readability)
9. [Colour, Contrast & Dark Mode](#9-colour-contrast--dark-mode)
10. [Motion & Animation](#10-motion--animation)
11. [Empty States, Loading States & Error States](#11-empty-states-loading-states--error-states)
12. [Mobile UI/UX](#12-mobile-uiux)
13. [Module-by-Module Presentation Audit](#13-module-by-module-presentation-audit)
14. [What Is Missing — Design Elements Not Present](#14-what-is-missing--design-elements-not-present)
15. [What Needs to Be Added](#15-what-needs-to-be-added)
16. [What Needs to Be Improved](#16-what-needs-to-be-improved)
17. [Master UI/UX Fix List](#17-master-uiux-fix-list)

---

## 1. Summary Verdict

The site runs on MkDocs Material — a solid, well-designed documentation framework — but is operating far below the potential of the platform. The homepage makes a strong first impression with its terminal aesthetic. The moment a user clicks into any content page, however, the experience becomes generic documentation with no personality, no orientation cues, and inconsistent presentation. The content is world-class. The presentation does not do it justice.

**Three core UI/UX problems run through every page:**

1. **No sense of place.** No active nav highlighting, no breadcrumbs, no progress indicators. Users cannot tell where they are at any moment.
2. **The terminal identity disappears after the homepage.** The bash persona that makes the homepage memorable vanishes completely on every inner page. The design language has no depth.
3. **The MkDocs Material feature set is roughly 30% utilised.** Copy buttons missing on code blocks. No reading time. No "last updated" dates. No TOC auto-scroll. No prev/next. These are single-line config changes that would transform the reading experience.

**Score: 5.8 / 10** — the homepage earns an 8, inner pages earn a 5.

---

## 2. Design System Audit

### 2.1 There is no defined design system

The site has no documented or consistent design system. Visual decisions — spacing, colour use, heading hierarchy, component patterns, callout styles — are made page by page and module by module, producing a fragmented experience.

**Evidence observed:**

- The homepage uses a dark terminal background with green text, monospace fonts, and stat counters. Inner pages use the default MkDocs Material light/dark theme with none of these elements.
- Callout boxes appear on some pages (Agentic RAG has `> **Current as of April 2026.**` blockquotes) but not consistently. Some pages use `!!! note` admonitions, some use plain blockquotes, some use bold text paragraphs.
- Tables have different column structures, header styles, and density across pages.
- Code block language tags are missing on some blocks and present on others.

**What to do:** Define a design token set for MkDocs Material and apply it globally via `extra.css`. At minimum, standardise:
- One callout/admonition style for "current as of" version notes
- One style for "See Also" sections
- One style for comparison tables
- One style for code blocks (language tag, copy button, line numbers where useful)

---

### 2.2 The design identity ends at the homepage

The `raj@context:~$` terminal persona is the site's strongest visual asset. It is used exactly once — on the homepage hero. Every inner page looks like a stock MkDocs Material installation. The brand promise made on the homepage ("this is a technically-minded, distinctive resource") is immediately broken when the user navigates to any content page.

**What the user experiences:**
- Homepage: distinctive, dark, terminal aesthetic, animated, character-rich
- Any content page: plain white (or dark) MkDocs documentation with no personality markers

**What to do:**
- Add a persistent terminal-inspired `[Context v2.1]` badge or watermark in the top navigation bar
- Style the page header with a subtle left-border accent using the site's terminal green
- Use monospace for section anchors/slugs displayed in the corner of headings
- Consider a terminal-green accent colour for all active states, hover states, and link underlines throughout inner pages

---

### 2.3 Colour usage is entirely delegated to the MkDocs theme defaults

There is no custom colour palette applied beyond the theme's default blue/purple accent. The terminal green from the homepage (`#00ff41`-adjacent tones) appears nowhere in the inner pages. The homepage stat cards, module cards, and terminal window use ad-hoc background colours not tied to any system.

**What to do:** Define a minimal 3-colour accent system:
- `--ctx-green`: terminal green, used for active states, links, "current/fresh" signals
- `--ctx-amber`: used for warnings, "important" callouts, exam tips
- `--ctx-surface`: a slightly warm off-white (the terminal bezel aesthetic) used for card backgrounds

Apply these as custom CSS variables in `extra.css` and reference them in component styles.

---

## 3. Homepage — Detailed UI/UX Review

### 3.1 Terminal hero — what works

The hero section is the best-executed element on the entire site. The typewriter/bash sequence establishes personality in the first 3 seconds. The `Initializing Context v2.1…` → `Loading modules:` → stat counter pattern mirrors the experience of watching a tool boot up, which resonates immediately with the technical audience.

**Specific strengths:**
- The `raj@context:~$` prompt is immediately legible and characterful
- Stat counters (18, 11, 3, 13, 13, 60+) give instant content density signal before the user reads a word
- The `explore —all` command before the module cards is a clever framing device

### 3.2 Terminal hero — what breaks

**Line wrapping on narrow viewports.** The module list on the `Loading modules:` line — `rag bert langchain cert docs` — and the `Interactive guides: ✓ 30+ resources ready` line both have fixed formatting. On viewports below ~480px, these wrap mid-line in a way that destroys the CLI illusion. The terminal becomes garbled text instead of a boot sequence.

**The animation has no reduced-motion respect.** Users who have `prefers-reduced-motion: reduce` set (roughly 25% of users with vestibular disorders or motion sensitivity) will still see the typewriter animation. This is both an accessibility issue and a design issue — animated content should always respect this preference.

**Fix:**
```css
@media (prefers-reduced-motion: reduce) {
  .hero-terminal * {
    animation: none !important;
    transition: none !important;
  }
}

@media (max-width: 480px) {
  .hero-loading-modules { 
    display: none; /* Hide verbose boot line, keep the clean command */
  }
}
```

---

### 3.3 Module cards — what works

The module cards communicate content type well. Each has: an emoji icon, a name, a 1–2 sentence scope description, and a resource count breakdown ("13 reference docs · 5 interactive guides"). The breakdown format is specifically good — it tells users what kind of content they'll find before clicking.

### 3.4 Module cards — what breaks

**Emoji icons are inconsistent in meaning and rendering.** ⚡ for RAG (why lightning?), 🧠 for BERT (on-theme), 🔗 for LangChain (chains → links, ok), 📜 for Claude Code (scroll for code docs?), 🏆 for Cert Prep (trophy, fine). The RAG emoji especially is non-obvious. More importantly, emoji render completely differently across Windows, macOS, Android, and iOS. The ⚡ on macOS looks nothing like the ⚡ on Windows 11.

**The module cards have no visual hierarchy between title, description, and count.** All three pieces of information have similar visual weight. The title should be dominant, the description secondary, and the count tertiary. Currently the description can be as visually prominent as the title.

**Cards have no hover state or visual affordance that they're clickable.** On most platforms they appear as static content blocks. A subtle lift (transform: translateY(-2px)) or border accent on hover would make the interaction obvious.

**Fix:**
```css
.module-card {
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.module-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.module-card .title {
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 6px;
}
.module-card .description {
  font-size: 13px;
  color: var(--muted);
  margin-bottom: 8px;
}
.module-card .count {
  font-size: 11px;
  font-weight: 600;
  color: var(--ctx-green);
}
```

---

### 3.5 Homepage "Interactive Tools" section — design problem

The second section on the homepage lists 10 interactive tools in a grid. These same tools also appear in their module sidebars. The section creates a design problem: it presents two parallel taxonomies (by module, and by type) on the same page with no visual signal explaining the relationship.

A user who sees both the module card for BERT and the "BERT Full Diagram" interactive tool card has no way to know they're related. The two sections look co-equal but serve different organisational logics.

**What to do:** Remove the standalone Interactive Tools grid. Fold interactive tool callouts into the module cards themselves. Each module card could include a "Featured interactive:" line pointing to the module's best tool. This eliminates the taxonomy conflict and concentrates user attention.

---

### 3.6 Homepage lacks a clear visual hierarchy between hero, modules, and tools

The page has three visual sections — hero, modules grid, interactive tools grid — but no visual separators or hierarchy signals. All three compete for equal attention. A user who scrolls quickly will not naturally understand the progression from "what is this site" (hero) → "what modules exist" (modules) → "what tools exist" (tools).

**Fix:** Add a clear section divider and label between each section. A thin horizontal rule and a section heading like `## Modules` and `## Interactive Tools` with consistent typography would create a page rhythm. Better: replace the flat stacking with a Z-pattern layout where the hero introduces, the modules go left, and a "featured tools" mini-section goes right or below with reduced visual weight.

---

## 4. Global Chrome — Nav, Sidebar, Header, Footer

### 4.1 Top navigation bar

**What works:** The site name "Context" in the top left, the search hint, and the theme toggle are all present. The bar is clean and uncluttered.

**What breaks:**

**The search hint "CtrlK" is text, not a button.** There is no magnifying glass icon. Mouse users who don't know keyboard shortcuts have no visible search affordance. The search is the primary navigation tool on a 63-page site — it needs to be visible and tappable.

**No secondary identity signal in the nav bar.** After reading the homepage and understanding the site's terminal persona, the nav bar on inner pages shows only "Context" — a generic, minimal name with no sub-brand signal. Adding a small tagline or category pill ("AI Learning Lab" or "v2.1") next to the name would maintain context across navigation.

**The theme toggle is present twice.** See critical bug in Section 16.1. On every single inner page, "Select theme Dark/Light/Auto" appears in both the top nav bar and somewhere in the sidebar/content body. This is the most visually disruptive rendering bug on the site.

**Fix for search visibility:**
```yaml
# mkdocs.yml
theme:
  features:
    - search.suggest
    - search.highlight
```
And verify no CSS is hiding `.md-search__icon` or `.md-search__form`.

---

### 4.2 Sidebar navigation

**What works:** The sidebar correctly lists all modules and their sub-pages. It is always accessible. The module sections are collapsible.

**What breaks, in detail:**

**No active page indicator.** This is the most critical navigation failure on the entire site. When a user is on "Chunking Strategies", the sidebar shows all 63 pages in the same visual weight with no differentiation. There is no bold text, no accent, no underline, no background highlight indicating which page is currently active. The user must read the H1 in the content area to know where they are.

**Module order contradicts the homepage.** Homepage order: RAG → BERT → LangChain → Claude Code → Cert. Sidebar order: Claude Code → RAG → BERT → LangChain → Cert. This is a direct sequence contradiction that breaks mental model on every visit.

**The sidebar is overly dense.** All 63 pages are permanently visible as expanded text links. On a page like "Domain 1: Agentic Architecture & Orchestration", a user in the Cert Prep module must visually parse 13 Claude Code links, 18 RAG links, 8 BERT links, and 2 LangChain links before reaching the Cert Prep section. The cognitive load of this sidebar is very high.

**There is no visual grouping or separation between modules.** Each module section bleeds into the next. A thin horizontal rule, a background accent, or a bold section header above each module group would create visual breaks that make the sidebar scannable.

**Sidebar link typography is too small.** MkDocs Material defaults to around 12–13px for sidebar links. On a site with long page titles ("CLAUDE.md vs Skills vs Rules — Architecture Guide", "Domain 1: Agentic Architecture & Orchestration"), these titles truncate or wrap awkwardly in the available sidebar width.

**Fix:** In `mkdocs.yml`:
```yaml
theme:
  features:
    - navigation.tracking    # active page highlighted
    - navigation.instant     # required for tracking to work
    - navigation.sections    # section-level grouping in sidebar
    - navigation.expand      # expand active section only
    - navigation.prune       # collapse non-active modules
```

`navigation.prune` is the most important feature here — it shows only the active module fully expanded and collapses all others, reducing the cognitive load from 63 links to ~15 at any time.

---

### 4.3 Page header (H1 area)

**What works:** H1 headings are clear and large. The Agentic RAG page displays a version callout right below the H1 (`> **Current as of April 2026.**`) which is an excellent design pattern.

**What breaks:**

**No metadata line below the H1.** A standard documentation practice is to show a metadata strip directly below the H1 containing: last updated date, reading time, difficulty level, page type. None of these exist. Users must infer all of this from the content itself.

**No visual treatment that distinguishes the H1 from the rest of the content.** The H1 flows directly into the page content. There is no visual pause — no subtitle, no metadata, no divider — between the title and the first paragraph. This makes pages feel like they begin abruptly.

**The breadcrumb trail is absent.** On "Domain 1: Agentic Architecture & Orchestration", there is no "Context → Cert Prep → Domain 1" trail anywhere visible. Deep-linked users have no orientation.

**Fix — add a page header component via MkDocs template override:**
```html
<div class="page-header">
  <div class="page-meta">
    <span class="level-badge {{ page.meta.level }}">{{ page.meta.level }}</span>
    <span class="reading-time">{{ page.meta.reading_time }} min read</span>
    <span class="last-updated">Updated {{ page.meta.git_revision_date }}</span>
  </div>
</div>
```

---

### 4.4 Footer

**What is present on Cert Prep pages:** Previous/Next navigation links in the footer. This is the single best UX feature on any inner page. It enables linear traversal through the study sequence without returning to the sidebar.

**What is absent on all other pages:** Previous/Next navigation. RAG, BERT, Claude Code, and LangChain have no footer navigation links. A user who finishes "Chunking Strategies" sees a blank footer with no prompt to continue to "Embedding Models".

**What is absent everywhere:** A global site footer. There is no footer with: copyright notice, "built by" attribution, links to other sections, last-site-updated date, or any other site-wide element. The page simply ends.

**Fix:**

Enable globally in `mkdocs.yml`:
```yaml
theme:
  features:
    - navigation.footer
```

Add a global footer via `mkdocs.yml`:
```yaml
extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/rajrkdev/ai-lab
```

And create `overrides/partials/footer.html` with: site name, version, built-with credit, and useful quick-links.

---

## 5. Content Pages — Layout & Presentation

### 5.1 Content width and reading line length

MkDocs Material defaults to approximately 70–80 characters per line in the content area, which is within the optimal 60–75 character range for comfortable reading. This is correct and should be preserved. Do not widen the content area — longer line lengths reduce reading speed and comprehension.

**What is wrong:** On very wide viewports (1440px+), the content column doesn't grow, but the sidebar takes up excessive space leaving a very wide right margin. The right sidebar (TOC) sits far from the content. Consider reducing the sidebar minimum widths on ultra-wide screens.

---

### 5.2 H1 → H2 → H3 hierarchy usage

The heading hierarchy across pages is inconsistently applied:

**Well-structured (Agentic RAG, Vector Stores):** Clean H1 → H2 → H3 hierarchy. Each H2 is a major topic, H3 is a sub-topic within it. The Vector Stores page uses H2 for each store (FAISS, Chroma, Pinecone) and H3 for sub-topics within each store.

**Poorly structured (Complete Study Guide, Cert Gap-Fill):** The Complete Study Guide uses `## DOMAIN 1: Agentic Architecture & Orchestration (27%)` as an H2 with inline ALL CAPS content. Headings contain percentages, task counts, and domain codes. H3 sub-headings contain task statements as full sentence descriptions. This creates a heading hierarchy that reads more like a document outline than navigation landmarks.

**The "On this page" TOC reveals the heading problem clearly.** On the Complete Study Guide, the TOC has 28 entries — far too many for a single-page TOC to be useful as navigation. Pages with more than 10–12 H2/H3 items should be split or reorganised.

**Fix:** Audit all pages with TOC entry counts above 12. For pages like Complete Study Guide, Cert Gap-Fill Reference, and the main LangChain reference, either split into sub-pages or reorganise the heading hierarchy so the TOC contains only top-level sections.

---

### 5.3 Version callout boxes — inconsistent usage

Several pages display version/currency callouts, but the format varies completely:

**Agentic RAG:** Uses a blockquote:
```
> **Current as of April 2026.**
> LangChain 1.0 + LangGraph 1.0 released October 2025 — stable APIs...
```

**Vector Stores:** Uses a blockquote:
```
> **Current as of April 2026.** Ecosystem evolves quickly...
> **Key 2026 trends:** Hybrid search...
```

**BERT Variants:** No version callout despite having dated information (ModernBERT Dec 2024).

**Chunking Strategies:** No version callout despite referencing "Late Chunking (JinaAI, 2024)".

**Production RAG:** No version callout.

**Fix:** Define a single admonition type for version callouts and apply consistently to all pages with time-sensitive content:

```markdown
!!! tip "Current as of April 2026"
    LangChain 1.0 + LangGraph 1.0 stable. Code examples compatible with `langgraph>=1.0`.
```

Apply this to: all RAG pages, all LangChain pages, the BERT Variants page, and any Claude Code page referencing specific versions.

---

### 5.4 Code blocks — presentation issues

Code blocks are the most frequently used component on the site. Their current implementation has multiple presentation gaps:

**No copy button.** Every code block requires manual text selection. For long code examples (the Domain 1 Cert page has 40+ line Python blocks), mobile users cannot reasonably copy code. This is a significant friction point for a resource where "read then implement" is the primary use pattern.

**No language label on many blocks.** Some blocks show the language (`python`, `yaml`, `bash`) and some don't. Inconsistent labelling makes blocks harder to scan. A user looking for the "YAML frontmatter" example within a page can't scan for it visually.

**No line numbers on long blocks.** Code blocks longer than ~20 lines would benefit from line numbers so explanatory text can reference "line 7" rather than quoting the code again.

**Code blocks inside comparison sections have no visual differentiation.** On pages like Vector Stores and BERT Variants where multiple code examples appear side by side for comparison, there is no visual wrapper distinguishing "Chroma example" from "Pinecone example" other than a heading above each one.

**Fix in `mkdocs.yml`:**
```yaml
markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
      linenums_style: pymdownx-inline
  - pymdownx.superfences
  - pymdownx.inlinehilite

theme:
  features:
    - content.code.copy
    - content.code.annotate
    - content.code.select
```

**Fix for comparison code blocks:** Use tabbed code blocks where multiple implementations of the same concept appear together:
```markdown
=== "Chroma"
    ```python
    # Chroma implementation
    ```

=== "Pinecone"
    ```python
    # Pinecone implementation
    ```
```

---

### 5.5 Tables — presentation issues

Tables appear extensively across the site (BERT model comparison, Vector Store comparison, Domain weights, Self-RAG token table in Agentic RAG). Several consistent problems:

**No table captions.** Tables appear without a title or caption describing what they show. The Self-RAG token table in Agentic RAG is the best example — it's a genuinely informative table with Token, Type, and Meaning columns, but it has no title explaining "Self-RAG Reflection Tokens" to a user who scrolls past the surrounding prose.

**Tables extend to full content width even when they don't need to.** A 2-column table with short values (BERT model size table: Model | Parameters) stretches to fill the full content column, creating large empty cells. Tables should be width-constrained based on content.

**No horizontal scroll on overflow.** On mobile, wide tables (Vector Store comparison with 7+ columns) will either overflow their container or compress columns to illegibility. They need `overflow-x: auto` on a wrapper.

**Alternating row colours are absent on many tables.** The Agentic RAG Self-RAG token table has 8 rows with similar structure — without alternating `background` on `tr:nth-child(even)`, rows blur together.

**Fix in `extra.css`:**
```css
/* Scrollable tables on mobile */
.md-typeset table:not([class]) {
  display: block;
  overflow-x: auto;
  white-space: nowrap;
}

/* Alternating rows */
.md-typeset table:not([class]) tr:nth-child(even) td {
  background-color: var(--md-code-bg-color);
}

/* Width-constrained narrow tables */
.md-typeset .narrow-table {
  width: auto;
  display: inline-table;
}
```

---

### 5.6 Admonition / callout usage

MkDocs Material has a rich set of admonitions: `!!! note`, `!!! warning`, `!!! tip`, `!!! important`, `!!! danger`. These are used inconsistently across the site:

- Agentic RAG uses blockquote (`>`) for version notes
- Master Study Guide uses all-caps headers for domain rules (no admonition)
- BERT Variants uses inline bold text for "Why Remove NSP?" emphasis
- Production RAG uses plain headers for guardrails and caching sections

The result is that important callouts — exam tips, version warnings, "don't do this" anti-patterns — are visually indistinguishable from regular content.

**Fix — standardise callout usage across the site:**

| Use case | Admonition type |
|---|---|
| Version/currency note | `!!! tip "Current as of [date]"` |
| Exam tip (Cert pages) | `!!! success "Exam tip"` |
| Anti-pattern / wrong approach | `!!! warning "Anti-pattern"` |
| Breaking change / important | `!!! danger "Breaking change"` |
| Related content | `!!! info "See also"` |
| Performance numbers / benchmarks | `!!! example "Benchmark"` |

Apply this taxonomy consistently across all 63 pages.

---

### 5.7 "See Also" sections

The Agentic RAG page ends with a `## See Also` section listing 5 related pages. This is excellent — it is the only page on the site that does this. No other page has a See Also section.

The presence of See Also on this page and nowhere else is itself a design problem: it looks like a one-off feature rather than a site pattern. Users who benefit from it on Agentic RAG will reasonably expect it on every page and be disappointed.

**Fix:** Add a `## See Also` section to every page with 2–4 cross-links. Standardise the visual treatment so it looks consistent across all pages. Consider using the `!!! info "See also"` admonition for visual consistency:

```markdown
!!! info "See also"
    - [BERT in RAG Pipelines](../bert/bert-in-rag.md) — how BERT models power RAG retrieval
    - [Production RAG](./production-rag.md) — deploying your retrieval pipeline
    - [LangChain Reference](../langchain/langchain-reference.md) — framework for building RAG chains
```

---

### 5.8 Duplicate "On this page" TOC

On pages including Chunking Strategies, BERT Architecture, and multiple Cert Prep pages, the in-page table of contents appears twice — once in the right sidebar (correct) and once inline in the content body, typically above the first H2 section. The inline instance adds 20–30 lines of repeated navigation before the actual content begins.

This is the most visually disruptive rendering bug on individual content pages. A user arrives at "Chunking Strategies" expecting content and instead sees a wall of links repeating the sidebar exactly.

**Fix:** Search all markdown files for manual `[TOC]` insertions and remove them. Check `mkdocs.yml` for any plugin configuration inserting TOC twice. In Material theme, `toc.integrate` should be used only if you want the TOC in the sidebar (not inline):
```yaml
theme:
  features:
    - toc.follow    # auto-scroll TOC
    # do NOT add toc.integrate if you have a right sidebar
```

---

## 6. Interactive Tool Pages — UI/UX

### 6.1 Blank screens — the worst user experience on the site

The following pages return blank white (or dark) screens when JavaScript is disabled or hasn't loaded: RAG Academy, Override Test Lab, Architecture Diagram, Precedence Diagram, File Catalog, BERT Full Diagram, BERT Tokenizer, BERT Encoder Block, Cert Quiz, Domain Visual Learning pages.

This is not just an accessibility issue — it is the worst possible user experience. A blank page communicates: "this site is broken." Users who arrive via deep link, on slow connections where JS hasn't yet loaded, or in environments with script blocking (corporate networks, privacy browsers) see absolutely nothing.

**Even before fixing the JS dependency, add a loading state.** At minimum, show a terminal-themed loading animation that matches the site's personality:

```html
<div id="loading-state" style="text-align:center; padding: 4rem 1rem; font-family: monospace;">
  <p style="color: var(--ctx-green);">raj@context:~$ loading interactive module...</p>
  <p style="color: var(--muted); margin-top: 1rem;">⠋ Initializing...</p>
</div>
<div id="app-root"></div>
<script>
  document.getElementById('app-root').addEventListener('DOMContentLoaded', () => {
    document.getElementById('loading-state').style.display = 'none';
  });
</script>
```

This at minimum:
1. Confirms the page is working (not broken)
2. Maintains the terminal identity on tool pages
3. Gives users feedback that content is loading

---

### 6.2 No instruction panel or onboarding for any tool

Every interactive tool loads directly into the tool interface without any instruction, goal-setting, or orientation. Users must discover how to interact through trial and error.

**Tool-specific problems:**

**Override Test Lab** — Described as "12 hands-on scenarios covering every Claude Code precedence rule." When a user lands on this page (assuming JS works), they have no idea what to expect. How long does it take? What will they learn? Do scenarios build on each other? Is there a final score?

**Cert Quiz** — No visible instruction about: how many questions, whether it's timed, whether answers can be changed, whether results are saved, or which domains are covered.

**RAG Academy** — No orientation about: course length, prerequisite knowledge, whether progress is saved, or what the user will build.

**Fix for all tools:** Add a persistent "How to use this" panel that appears once (dismissible, stored in sessionStorage) when the tool first loads. Format it in the terminal aesthetic:

```
raj@context:~$ describe --tool cert-quiz

Tool: Cert Quiz
Questions: 50 (multiple choice, 10 per domain)
Time: ~25 minutes
Domains: All 5 (weighted by exam %)
Scoring: Real-time feedback with explanation
Progress: Saved in browser session

Press any key to begin, or type 'skip' to go directly to questions.
```

---

### 6.3 No feedback or result communication from tools

After completing the Cert Quiz, Override Test Lab, or RAG Academy modules, what does the user see? Are results summarised? Is there a score? Is there direction on what to do next based on results?

Without feedback loops, interactive tools are one-time experiences with no connection to the rest of the learning path. A user who scores 60% on the Cert Quiz has no in-tool guidance pointing them to the specific domain pages where they're weak.

**Fix:** Design a results screen for every assessment tool:
- Score or completion status
- Domain-by-domain breakdown (for Cert Quiz)
- "Next recommended reading" links based on results
- Option to retry or share

---

## 7. Component-Level Audit

### 7.1 Search component

**Current state:** Keyboard-only accessible (Ctrl+K). No visible icon. No search on mobile.

**What users need:**
- A visible search icon in the top nav bar (tap target ≥ 44×44px on mobile)
- Instant search results as the user types (MkDocs Material default)
- Search result previews showing the page name, section, and a text excerpt
- Keyboard navigation within results (arrow keys)

**What's missing that MkDocs Material can provide:**
```yaml
theme:
  features:
    - search.highlight    # highlight query terms in results
    - search.suggest      # typeahead suggestions
    - search.share        # shareable search URLs
```

---

### 7.2 Theme toggle component

**Current state:** Renders twice on every page. Controls: Dark / Light / Auto.

**What should change:**
- Fix the duplicate rendering (see Section 4.1)
- Auto mode should be the default and labelled clearly as "Follow system"
- Consider using icon-only toggle (moon/sun) in the top nav rather than a text dropdown

---

### 7.3 Heading anchor links

When hovering over any H2 or H3, MkDocs Material shows a `#` anchor link. This is correct behavior. **What's missing:** the anchor links are the only way to share a deep link to a section. For a learning resource where instructors, colleagues, and study partners share specific sections, deep link affordance is important. The `#` icon is very small and easy to miss.

**Fix:** Make the anchor icon slightly larger and more visible on hover:
```css
.md-typeset [id] .headerlink {
  font-size: 0.9em;
  opacity: 0.6;
}
.md-typeset [id]:hover .headerlink {
  opacity: 1;
}
```

Also add MkDocs Material's `content.tooltips` feature so hovering links shows a tooltip preview.

---

### 7.4 Blockquotes

Blockquotes are used in two ways across the site:
1. As version callout boxes (Agentic RAG, Vector Stores)
2. As general semantic quotations

The default MkDocs Material blockquote styling (left border + slight indentation) does not visually distinguish these two uses. A version note callout and a genuine quotation look identical.

**Fix:** Reserve `>` blockquotes for semantic quotations. Use `!!! tip "Version"` admonitions for all version/currency notes. Ensure the distinction is documented in a contribution guide.

---

### 7.5 Navigation tabs (absent — should be considered)

For a site with 5 major modules, top-level navigation tabs would make module switching much faster. Currently, switching from the BERT module to the Cert module requires: clicking the Cert section header in the sidebar (which may be collapsed) → clicking the landing page. With navigation tabs, the top nav bar would show:

`Context | RAG | BERT | LangChain | Claude Code | Cert Prep`

Clicking any tab jumps directly to that module's landing page. This reduces module-switching from 2–3 clicks to 1.

**Fix:**
```yaml
theme:
  features:
    - navigation.tabs
    - navigation.tabs.sticky  # keeps tabs visible on scroll
```

This works best with the sidebar showing only the active module's pages.

---

### 7.6 Tags/badges component (absent — should be added)

No page has a difficulty badge, content type badge, or "interactive" indicator. These are absent from: the sidebar, the page headers, the module landing pages, and anywhere in the content.

**Fix — define a badge system in MkDocs Material:**
```yaml
# mkdocs.yml
plugins:
  - tags
```

Then in page frontmatter:
```yaml
---
tags:
  - beginner
  - interactive
  - reference
---
```

Tags render as clickable badges and can be used as a filter in search results.

---

### 7.7 Inline content callouts for "current as of" notes

The Agentic RAG and Vector Stores pages open with `> **Current as of April 2026.**` blockquotes. These are well-placed and informative. However, they use different content lengths and formats:

- Agentic RAG: 3-line blockquote with LangGraph version info, stability note, and compatibility
- Vector Stores: 3-line blockquote with version note and "Key 2026 trends" section
- Advanced RAG: No callout despite referencing Nov 2024 and Oct 2024 techniques
- GraphRAG: No callout despite referencing 2025 and 2026 research

**Fix:** Standardise to a 1–2 line format and apply to every page referencing a specific year or version. A MkDocs Material admonition is more visually distinctive:

```markdown
!!! tip inline end "Updated April 2026"
    LangChain 1.0 + LangGraph 1.0. Code compatible with `langgraph>=1.0`.
```

The `inline end` parameter floats the callout to the right of the opening paragraph, which is a much better visual treatment than a full-width blockquote.

---

## 8. Typography & Readability

### 8.1 Body text size

MkDocs Material defaults to 16px body text. This is correct for readability. The current site appears to use this default, which should be preserved.

### 8.2 Code font

MkDocs Material uses a monospace font for code blocks. The rendering appears correct across the content pages reviewed. Line height within code blocks could be slightly increased for very dense blocks (the Domain 1 multi-agent orchestration examples are particularly dense).

### 8.3 Long-form page readability

Several pages — Complete Study Guide, Cert Gap-Fill Reference, LangChain Deep Reference, and the main Claude Code Reference — are extremely long single-page documents. The LangChain reference alone covers: mental model, ecosystem architecture, package split, LCEL, LLM wrappers, prompt templates, agents, memory, RAG pipelines, and production patterns. This is an entire book condensed into one scrolling page.

**The problem:** Long pages without visual breaks, section dividers, or reading progress indicators become fatiguing. Users lose their place. Return visitors cannot quickly find the section they need.

**What to add:**

1. **Section summary cards** at the top of very long pages (5+ H2 sections): a 3-column grid of H2 sections with their anchor links, like a mini-TOC with visual preview.

2. **Progress indicator** for long pages: a thin horizontal progress bar at the top of the viewport that fills as the user scrolls. This is a reading progress pattern common on long-form editorial sites. Implementation:

```javascript
window.addEventListener('scroll', () => {
  const scroll = window.scrollY;
  const height = document.body.scrollHeight - window.innerHeight;
  const progress = (scroll / height) * 100;
  document.querySelector('.reading-progress').style.width = `${progress}%`;
});
```

3. **Sticky section heading** that shows the current H2 in a small fixed element at the top of the page as the user scrolls. This is the `toc.follow` feature in MkDocs Material, which should be enabled.

---

### 8.4 Heading hierarchy in long reference pages

The Complete Study Guide page has 28 TOC entries across 5 domains, each with multiple task statements. The heading hierarchy used is:
- H2: domain name + weight (`## DOMAIN 1: Agentic Architecture & Orchestration (27%)`)
- H3: task statement (`### Task 1.1 — The agentic loop lifecycle and stop reasons`)

This creates a TOC so long it is useless as navigation. Each H3 entry reads as a full sentence, making the TOC dense and hard to scan.

**Fix:** Flatten the heading hierarchy on this page:
- Use **bold** within H3 sections to highlight key terms instead of creating more H3s
- Move the domain weight percentage out of the H2 text and into a badge or meta element
- Group related tasks under descriptive H2s rather than numbered task statements

---

### 8.5 ALL CAPS usage in headings

The Master Study Guide uses:
```
## THE 25 RULES THAT COVER 80%+ OF THE EXAM
### DOMAIN 1: AGENTIC ARCHITECTURE
### DISTRACTOR PATTERNS
### FIVE CROSS-CUTTING PATTERNS
### EXAM STRATEGY
```

ALL CAPS headings are:
- Harder to read (uppercase text has less visual differentiation between letter shapes)
- Interpreted as shouting in online typography conventions
- Not scannable — they don't visually distinguish themselves from other headings
- Inconsistent with every other page on the site

**Fix:** Convert all ALL CAPS headings to title case or sentence case. Add visual emphasis through font weight, colour, or an accent element rather than capitalisation. The important sections deserve visual prominence, not capitalisation:

```markdown
## 25 rules that cover 80%+ of the exam
### Domain 1 — Agentic architecture

!!! warning "Distractor patterns"
    These wrong-answer patterns appear repeatedly...
```

---

## 9. Colour, Contrast & Dark Mode

### 9.1 Dark mode

The site has Dark/Light/Auto theme support — this is a genuine strength for a developer-focused audience. The Auto mode correctly follows system preference.

**What works:** The basic dark mode implementation is functional. Text is readable, backgrounds invert correctly, code blocks maintain syntax highlighting.

**What to verify:** Custom colours in any bespoke CSS (the homepage terminal green, the stat counter backgrounds) need explicit dark mode variants. If `--ctx-green: #00a86b` works on a light background but is specified with a hardcoded hex rather than a CSS variable, it may become illegible in dark mode.

**Check:** Load the site in dark mode and audit:
- The homepage terminal window background (should be near-black, not invert to white)
- Module card backgrounds on the homepage
- The version callout blockquotes (dark backgrounds with light text should invert correctly)
- All custom table styling

---

### 9.2 Colour contrast on current badges and callouts

The Agentic RAG version callout `> **Current as of April 2026.**` uses the default MkDocs blockquote styling — a grey left border and slightly offset indentation. The grey border may have insufficient contrast against a light grey page background in some themes.

**Fix:** Switch to the `!!! tip` admonition which has a green left border and coloured title bar, providing much better contrast and visual prominence.

---

### 9.3 Link colour and state

In the default MkDocs Material theme, links use the accent colour (typically blue or purple depending on configuration). **What's missing:**

- **Visited link styling.** On a learning resource where users read pages in sequence over multiple sessions, visited links (`a:visited`) should display differently to help users track which pages they've already read. MkDocs Material supports this via custom CSS:

```css
.md-typeset a:visited {
  color: var(--md-typeset-a-color);
  opacity: 0.7;
}
```

- **External link indicator.** Links that open external sites should have a visual indicator (small arrow icon `↗`) so users know they're leaving the site. MkDocs Material's `content.tooltips` feature and `attr_list` extension can add this.

---

## 10. Motion & Animation

### 10.1 Homepage animation — well executed, needs reduced-motion support

The typewriter/boot sequence is the site's best animation. It is purposeful (it tells a story about what the site does), well-paced (not too fast, not too slow), and appropriate for the technical audience.

**Missing:** `prefers-reduced-motion` media query support. This affects roughly 10–25% of users who have enabled reduced motion in their OS settings (macOS: Accessibility → Reduce Motion; Windows: Settings → Ease of Access → Reduce Motion).

**Fix:**
```css
@media (prefers-reduced-motion: reduce) {
  .hero-typewriter { animation: none; }
  .hero-cursor { animation: none; }
  /* Show final state immediately */
  .hero-typewriter { 
    opacity: 1;
    content: attr(data-final-text);
  }
}
```

---

### 10.2 Sidebar collapse/expand animation

MkDocs Material animates sidebar section expansion. This is subtle and appropriate — it helps users track which section is being opened. Keep this.

---

### 10.3 Page transitions

MkDocs Material's `navigation.instant` feature gives SPA-style instant page transitions. This should be enabled — it makes the site feel much faster, especially between pages in the same module. Without it, each navigation click reloads the full page including the sidebar.

```yaml
theme:
  features:
    - navigation.instant
    - navigation.instant.prefetch  # hover-based prefetch
    - navigation.instant.progress  # progress indicator for slow loads
```

---

## 11. Empty States, Loading States & Error States

### 11.1 Empty states — completely absent

The site has no designed empty states. This matters in the following scenarios:

**When a search returns no results.** MkDocs Material shows a default "No results found" message, but it's unstyled and generic. For a site with the terminal persona, a styled empty state would maintain the experience:

```
raj@context:~$ search --query "your search term"
> No results found in corpus.
> Suggestions:
>   - Check spelling
>   - Try broader terms (e.g., "chunking" instead of "recursive character chunking")
>   - Browse modules: rag/ bert/ langchain/ claude-code/ cert/
```

**When an interactive tool is loading.** See Section 6.1. Currently: blank white screen. Should be: a terminal-themed loading animation.

**When JavaScript fails.** See Section 9.1 in the full audit. Currently: blank white screen. Should be: a static fallback with content description.

---

### 11.2 Loading states — absent for interactive tools

Interactive tools (Cert Quiz, RAG Academy, Override Test Lab, BERT diagrams) show nothing while JavaScript is executing. On slow connections (3G mobile, corporate proxies), this can mean 3–8 seconds of blank white screen.

**Fix — add a CSS-only spinner while JS loads:**
```html
<style>
.loading-screen {
  display: flex; align-items: center; justify-content: center;
  height: 300px; font-family: monospace; flex-direction: column; gap: 12px;
}
.loading-spinner {
  width: 24px; height: 24px; border: 2px solid var(--ctx-green);
  border-top-color: transparent; border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
<div class="loading-screen" id="loading">
  <div class="loading-spinner"></div>
  <span>raj@context:~$ loading module...</span>
</div>
<script>
  // Hide loading screen once app has mounted
  window.addEventListener('load', () => {
    document.getElementById('loading').style.display = 'none';
  });
</script>
```

---

### 11.3 Error states — completely absent

**404 page:** The site uses GitHub Pages' default 404 page. No site branding, no navigation, no way to recover. This is a lost-user experience for every broken link.

**Tool errors:** If an interactive tool encounters a JavaScript error, the user sees whatever the browser's default error display is (or nothing). No graceful error handling exists anywhere.

**Fix — create `docs/404.md`:**
```markdown
---
title: 404 — Not Found
hide:
  - navigation
  - toc
---

# raj@context:~$ 404

```bash
$ find / -name "{{ request.path }}"
find: no results matching pattern

$ suggest --similar
→ Did you mean one of these?
```

**Try these instead:**

- [← Homepage](/ai-lab/)
- [RAG Guides](/ai-lab/rag/)
- [BERT Architectures](/ai-lab/bert/)
- [Claude Code](/ai-lab/claude-code/)
- [Cert Prep](/ai-lab/cert/)
- [Search the site →](#){ .search-trigger }
```

---

## 12. Mobile UI/UX

### 12.1 Layout audit at key breakpoints

**375px (iPhone SE, iPhone 8):**
- Hero terminal animation: likely wraps and breaks the CLI format. The `Loading modules: rag bert langchain cert docs` line is ~52 characters — at 375px with monospace font, this may overflow or wrap mid-token.
- Module card grid: likely collapses to single column, which is correct.
- Stat counter grid: may become a 2-column grid, which is fine.

**390px (iPhone 14, 15):**
- Similar to 375px issues. Add 16px horizontal padding to the terminal container.

**768px (iPad portrait):**
- The sidebar typically collapses to a hamburger menu on this breakpoint. Content should flow full-width.
- Interactive tool pages may have layouts designed for wider screens.

**1024px (iPad landscape, smaller laptops):**
- Both sidebar and content area should be visible. Right TOC sidebar may become too narrow.

---

### 12.2 Touch targets

Several interactive elements may have insufficient touch target sizes (minimum 44×44px per WCAG 2.5.5):

- Sidebar collapse/expand triangles: typically 16–20px, insufficient
- Heading anchor link `#` icons: typically 14–16px, far too small
- The search "CtrlK" text hint: not a button at all, 0px touch target

**Fix:** Add `min-height: 44px; min-width: 44px` to all interactive elements that currently have smaller dimensions. For anchor links, increase the hover area via padding:

```css
.md-typeset [id] .headerlink {
  padding: 0 8px;
  min-width: 44px;
  display: inline-flex;
  align-items: center;
}
```

---

### 12.3 Code blocks on mobile

Long code examples (40+ lines, common in Claude Code Reference and Cert Domain pages) require horizontal scrolling on mobile. This is unavoidable for actual code, but several improvements would help:

- Enable `content.code.copy` so users can copy without manual selection
- Add `overflow-x: auto` to the code block wrapper to enable smooth horizontal scroll rather than page overflow
- Consider collapsing very long code blocks behind a "Show full example" toggle that expands them:

```markdown
??? example "Full implementation (48 lines)"
    ```python
    # Long code here
    ```
```

The `???` syntax creates a collapsed admonition that the user must click to expand. Prevents long code from dominating mobile layouts.

---

### 12.4 Mobile navigation

On mobile, the sidebar collapses to a hamburger menu. **What's missing:**

- **Tab bar at the bottom** for the 5 modules. Bottom navigation is far more accessible on mobile than a hamburger menu. A persistent bottom bar with: Home | RAG | BERT | Code | Cert would allow single-tap module switching.
- **Search icon in the top bar** (not a hamburger). Currently the search is invisible on mobile.
- **Swipe gestures** for prev/next page. On cert prep pages with prev/next navigation, swipe left/right would be a natural mobile interaction.

---

## 13. Module-by-Module Presentation Audit

### 13.1 Homepage → Module landing design consistency

Each module landing page uses a different structure:

| Module | Landing page structure |
|---|---|
| RAG | TOC + sub-page list only, no Quick Reference |
| BERT | TOC + sub-page list + **Quick Reference tables** ✅ |
| LangChain | TOC + 2-item list + minimal Quick Start ❌ |
| Claude Code | TOC + categorised sections + **Quick Reference** ✅ |
| Cert Prep | TOC + exam overview + domain weights + **everything** ✅ |

BERT and Claude Code landings are the template. RAG and LangChain landings are significantly behind. LangChain's landing is effectively useless.

**Fix — RAG landing:** Add a Quick Reference section:
```markdown
## Quick Reference

| Stage | Input | Output | Key technique |
|-------|-------|--------|---------------|
| Chunking | Documents | Chunks | Recursive character |
| Embedding | Chunks | Vectors | text-embedding-3-small |
| Retrieval | Query | Top-k chunks | Hybrid (dense + BM25) |
| Reranking | Top-k | Re-ordered | Cross-encoder |
| Generation | Context | Answer | Claude Sonnet |
```

**Fix — LangChain landing:** See Section 4 of the main audit. Either fully populate or remove.

---

### 13.2 Agentic RAG page — best content presentation on the site

The Agentic RAG page is the best-presented content page on the site. It has:
- A version callout immediately after the H1
- Clean H2 → H3 hierarchy (each technique is an H2, implementation details are H3)
- Consistent table format for Self-RAG tokens
- Properly formatted LangGraph code with version-compatible imports
- A comparison table at the end ("Comparison: All Agentic RAG Approaches")
- A `## See Also` section linking to related pages

This page should be used as the reference template for how all content pages should be formatted.

---

### 13.3 Vector Stores page — structural problem

The Vector Stores page has the TOC listing "Choosing a Vector Store" **twice** — at position 10 and again at position 15. This suggests the same section heading was used for two different sections. One of the headings needs to be renamed (e.g., "Quick Selection Guide" vs "Full Decision Framework").

Additionally, the "Full Comparison (August 2025)" table heading uses a specific date in the heading, which will age poorly in the URL anchor. Change to "Full comparison" with the date in the table caption instead.

---

### 13.4 Cert Gap-Fill Reference — presentation strength

The Gap-Fill Reference page has 31 numbered gaps, each with a specific knowledge item that needs to be memorised for the exam. The format — presenting exact API parameters, type definitions, and configuration schemas — is the right approach for active recall study. This is one of the best-formatted Cert prep resources on the site.

**One presentation gap:** The three "Quick reference" tables at the bottom (permission mode cheat sheet, SDK parameter name mapping) are excellent but not visually distinguished from the surrounding text. They deserve section headers and a "cheat sheet" visual treatment — perhaps a light background and slightly narrower width to distinguish them as reference cards vs. prose content.

---

### 13.5 Complete Study Guide — presentation problems

This is the longest page on the site and one of the most important for exam takers. Its presentation has the most problems:

1. **28-entry TOC** makes in-page navigation useless — too many items to scan
2. **ALL CAPS section headers** for DOMAIN labels violate every typography guideline
3. **Domain percentages in H2 text** clutter the heading structure
4. **Task statement sub-headings** as full sentences create an awkward TOC density
5. **No visual separation between domains** — the reader cannot easily see where Domain 1 ends and Domain 2 begins when scrolling

**Fix — visual domain separators:**
```html
<div class="domain-divider">
  <span class="domain-label">Domain 2</span>
  <span class="domain-weight">18% of exam</span>
</div>
```

With CSS:
```css
.domain-divider {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 2rem 0;
  padding: 12px 16px;
  background: var(--md-code-bg-color);
  border-left: 4px solid var(--ctx-green);
  border-radius: 0 4px 4px 0;
}
.domain-weight {
  font-size: 0.85em;
  color: var(--md-default-fg-color--light);
}
```

---

## 14. What Is Missing — Design Elements Not Present

The following design elements are entirely absent from the current implementation and should be added:

### Missing globally

| Element | Where needed | Why |
|---|---|---|
| Active page indicator in sidebar | All pages | Users have no sense of location |
| Breadcrumb trail | All inner pages | Orientation for deep-linked users |
| Page metadata strip (level, reading time, last updated) | All pages | Sets user expectations |
| "Start here" / onboarding banner | Homepage, module landings | New user path |
| Difficulty level badge | All pages | Self-selection signal |
| Page type badge (Reference / Guide / Interactive) | All pages | Sets expectations before reading |
| Progress bar while reading | Long pages | Shows position in long documents |
| Visited link styling | All pages | Helps users track what they've read |
| Skip link (functional) | All pages | Keyboard navigation |
| Copy button on code blocks | All code | Mobile and quick-copy use |
| Reading time estimate | All pages | Time management |
| Last updated date | All pages | Content freshness signal |
| "See Also" cross-links | All pages (only on 1 currently) | Discoverability |
| Custom 404 page | Site-wide | Recovery from broken links |
| Custom loading state | All JS tool pages | Feedback that tool is loading |
| Back to top button | Long pages | Navigation on scroll |

### Missing per module

| Element | Module | Specific gap |
|---|---|---|
| Quick Reference section | RAG landing | No summary tables for quick lookup |
| Quick Reference section | LangChain landing | Page is essentially empty |
| Version callout | Advanced RAG | References Nov/Oct 2024 techniques with no version note |
| Version callout | Chunking Strategies | Late Chunking Oct 2024 reference with no date signal |
| Version callout | BERT Variants | ModernBERT Dec 2024 reference with no date signal |
| Content list with descriptions | RAG landing | No scannable overview of sub-pages |
| Instruction panel | All interactive tools | Users don't know how to use the tools |
| Fallback content | All JS-only pages | Blank without JS |
| Navigation between visual guides | Cert D1, D2-D5 visuals | No "continue to next" link |
| Domain dividers | Complete Study Guide | Domains visually blend together |

---

## 15. What Needs to Be Added

Listed by implementation complexity, lowest to highest:

### Configuration-only additions (no code)

1. **`navigation.path`** — breadcrumbs on all pages. One line in `mkdocs.yml`.
2. **`navigation.footer`** — prev/next on all pages. One line in `mkdocs.yml`.
3. **`navigation.top`** — back-to-top button on long pages. One line.
4. **`navigation.instant` + `navigation.instant.prefetch`** — SPA-style transitions. Two lines.
5. **`navigation.prune`** — collapse non-active modules, reducing sidebar cognitive load. One line.
6. **`navigation.tabs` + `navigation.tabs.sticky`** — top-level module tabs. Two lines.
7. **`navigation.tracking`** — active page highlighted in sidebar. One line.
8. **`content.code.copy`** — copy button on all code blocks. One line.
9. **`content.code.annotate`** — inline code annotations. One line.
10. **`search.highlight`, `search.suggest`, `search.share`** — better search. Three lines.
11. **`toc.follow`** — TOC auto-scrolls with page scroll. One line.
12. **`git-revision-date-localized` plugin** — automatic last-updated dates. Five lines.
13. **`readtime` plugin** — reading time estimates. Three lines.
14. **`tags` plugin** — taggable pages for difficulty/type filtering. Three lines.

### CSS additions (extra.css)

15. **Active sidebar highlight** — bold + green accent on current page link
16. **Table improvements** — alternating rows, overflow scroll wrapper, caption styling
17. **Domain dividers** — styled separators for Cert multi-domain pages
18. **Loading state for JS tools** — terminal-themed spinner
19. **Page header metadata strip** — level badge, reading time, last updated inline
20. **Version callout consistency** — standardised admonition for all time-sensitive pages
21. **Reduced motion support** — `prefers-reduced-motion` CSS for homepage animation
22. **Bottom tab bar on mobile** — fixed 5-module navigation

### Template additions (overrides/)

23. **Custom 404 page** — terminal-themed error with navigation
24. **OG/Twitter meta tags** in `head.html` — social sharing previews
25. **Page metadata template** — level, reading time, last updated in page header
26. **Global footer** — site info, quick links, version

### Content additions (per page)

27. **`## See Also` sections** — on all 63 pages (only Agentic RAG has one)
28. **Difficulty frontmatter** — `level: beginner/intermediate/advanced` on all pages
29. **Description frontmatter** — `description:` on all pages for meta tags
30. **Version callouts** — on all time-sensitive pages that currently lack them
31. **Tool instruction panels** — onboarding text for all 10 interactive tools
32. **JS fallback content** — H1 + description + `<noscript>` on all tool pages

---

## 16. What Needs to Be Improved

### High priority improvements

**Sidebar cognitive load.** 63 links always visible, no active indicator, wrong order, no visual grouping. Enabling `navigation.prune` + `navigation.sections` + `navigation.tracking` solves the core problem.

**Heading hierarchy on long pages.** Complete Study Guide (28 TOC entries, ALL CAPS), Cert Gap-Fill (31 numbered items), LangChain Reference (deeply nested). All three need restructuring: shorter headings, smaller sub-sections, visual breaks between major sections.

**Code blocks across the site.** No copy buttons, inconsistent language labels, no line numbers on long examples. Enable Material features + add `pymdownx.highlight` configuration.

**Module landing pages for RAG and LangChain.** Both are significantly weaker than BERT and Claude Code landings. RAG needs a Quick Reference. LangChain needs complete rethinking.

**Table presentation.** No captions, no alternating rows on many tables, no overflow handling for mobile. The Vector Stores "Full Comparison" table is wide enough to require horizontal scroll on most viewports — it needs an overflow wrapper.

**Version callout inconsistency.** Some pages have them, most don't. Standardise to `!!! tip "Updated [date]"` and apply to all pages referencing specific versions or dates.

### Medium priority improvements

**Homepage Interactive Tools section.** Remove or absorb into module cards. The dual listing of the same tools creates a confusing information architecture.

**Module card hover states.** Cards currently appear static. Add `transform: translateY(-2px)` on hover plus a subtle border accent.

**Blockquote visual treatment.** Version callouts use blockquote styling which is too subtle. Switch to named admonitions for version notes.

**Duplicate section headings** in Vector Stores ("Choosing a Vector Store" appears twice). Rename one.

**ALL CAPS headings** in Master Study Guide. Convert to title case with accent colour treatment instead.

**Cert visual learning split.** Three pages (All Domains, D1, D2-D5) with no navigation between them. Add explicit "Next: Domain 1 visual →" and "Next: Domains 2–5 →" links.

### Low priority improvements

**Anchor link visibility.** The `#` anchor links that appear on hover are very small. Increase their hit area.

**Footnotes and citations.** Pages like Advanced RAG and BERT Variants cite academic papers (Asai et al., Self-RAG 2023; Liu et al., RoBERTa 2019) inline in plain text. Using MkDocs Material's footnote syntax `[^1]` would create proper footnote references at the bottom of the page, which is more academically appropriate and visually cleaner.

**Print styles.** Users who want a physical study guide for the cert exam have no print-optimised CSS. Adding a `@media print` stylesheet that removes the sidebar, nav, and TOC and formats content for A4/Letter would serve this use case.

---

## 17. Master UI/UX Fix List

Ordered by effort vs impact. Tier 1 items take under 1 hour combined.

### Tier 1 — One line each in `mkdocs.yml` (do all of these first)

```yaml
theme:
  features:
    - navigation.instant          # SPA transitions
    - navigation.instant.prefetch # hover prefetch
    - navigation.instant.progress # progress on slow loads
    - navigation.tracking         # ✅ ACTIVE PAGE HIGHLIGHT
    - navigation.path             # ✅ BREADCRUMBS
    - navigation.footer           # ✅ PREV/NEXT on all pages
    - navigation.top              # back to top button
    - navigation.prune            # ✅ collapse inactive modules
    - navigation.tabs             # top module tabs
    - navigation.tabs.sticky      # sticky tabs on scroll
    - navigation.sections         # section-level sidebar grouping
    - search.highlight
    - search.suggest
    - search.share
    - content.code.copy           # ✅ copy button on all code
    - content.code.annotate
    - content.code.select
    - content.tooltips
    - toc.follow                  # auto-scroll TOC

plugins:
  - git-revision-date-localized:
      enable_creation_date: true
      type: date
  - readtime
  - tags
```

Items marked ✅ are the highest individual impact. Combined, these 5 changes fix: active page highlighting, breadcrumbs, prev/next navigation, sidebar cognitive load, and copy buttons — all in under 5 minutes.

---

### Tier 2 — CSS additions to `extra.css` (~2 hours total)

1. Fix duplicate theme toggle (locate and remove template duplicate)
2. Fix duplicate TOC (remove manual `[TOC]` insertions)
3. Add table overflow scroll wrapper for mobile
4. Add alternating row colours to all tables
5. Add card hover state to module cards on homepage
6. Add terminal-green accent to active sidebar item
7. Fix homepage animation for narrow viewports
8. Add `prefers-reduced-motion` support to homepage animation

---

### Tier 3 — Template overrides (~half day)

1. Create `overrides/partials/head.html` — OG/Twitter meta tags
2. Create `overrides/partials/footer.html` — global site footer
3. Create page header metadata component (level + reading time + last updated)
4. Create custom 404 page with terminal theme

---

### Tier 4 — Content work per page (~2–3 days for all 63 pages)

1. Add `level:` frontmatter to all pages (beginner/intermediate/advanced)
2. Add `description:` frontmatter to all pages
3. Add `## See Also` to all pages
4. Standardise version callouts to `!!! tip "Updated [date]"` on time-sensitive pages
5. Convert ALL CAPS headings in Master Study Guide
6. Fix duplicate section headings in Vector Stores
7. Add instruction panels to all 10 interactive tool pages
8. Add JS fallback content to all tool pages
9. Restructure Complete Study Guide heading hierarchy
10. Populate the LangChain module landing page

---

### Tier 5 — New design components (~1 week)

1. Reading progress bar for long pages
2. Module bottom tab bar for mobile
3. "Start here" onboarding flow for new visitors
4. Progress tracking (read/unread per page) using localStorage
5. Tool results screens with next-step recommendations
6. Terminal-themed loading states for all JS tool pages
7. Collapsible long code blocks on mobile

---

*End of UI/UX audit.*  
*Total issues identified: 89 across design, presentation, interaction, and component levels.*  
*Tier 1 fixes (mkdocs.yml config changes): 20 items, ~30 minutes, affects all 63 pages.*  
*Most impactful single change: enabling `navigation.tracking` (active page highlight) + `navigation.path` (breadcrumbs) + `navigation.footer` (prev/next) — three config lines that transform the navigation experience site-wide.*
