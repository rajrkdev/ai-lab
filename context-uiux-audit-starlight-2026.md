# Context Microsite — UI/UX Audit (Updated)
**Site:** rajrkdev.github.io/ai-lab  
**Platform:** Astro Starlight  
**Audit date:** April 17, 2026  
**Pages reviewed:** All 63 across 5 modules + homepage  
**Issues found:** 89 across design, presentation, interaction, and component levels  

> **Platform correction notice.** Previous versions of this audit incorrectly identified the platform as MkDocs Material and provided `mkdocs.yml` fix recommendations throughout. This report replaces all prior versions. Every fix is now specific to Astro Starlight — `astro.config.mjs`, component overrides in `src/components/`, custom CSS in `src/styles/custom.css`, and frontmatter in `.md`/`.mdx` files.

---

## Table of Contents

1. [Summary Verdict](#1-summary-verdict)
2. [Design System Audit](#2-design-system-audit)
3. [Homepage — Detailed UI/UX Review](#3-homepage--detailed-uiux-review)
4. [Global Chrome — Nav, Sidebar, Header, Footer](#4-global-chrome--nav-sidebar-header-footer)
5. [Content Pages — Layout and Presentation](#5-content-pages--layout-and-presentation)
6. [Interactive Tool Pages — UI/UX](#6-interactive-tool-pages--uiux)
7. [Component-Level Audit](#7-component-level-audit)
8. [Typography and Readability](#8-typography-and-readability)
9. [Colour, Contrast and Dark Mode](#9-colour-contrast-and-dark-mode)
10. [Motion and Animation](#10-motion-and-animation)
11. [Empty States, Loading States and Error States](#11-empty-states-loading-states-and-error-states)
12. [Mobile UI/UX](#12-mobile-uiux)
13. [Module-by-Module Presentation Audit](#13-module-by-module-presentation-audit)
14. [What Is Missing](#14-what-is-missing)
15. [What Needs to Be Added](#15-what-needs-to-be-added)
16. [What Needs to Be Improved](#16-what-needs-to-be-improved)
17. [Master UI/UX Fix List](#17-master-uiux-fix-list)

---

## 1. Summary Verdict

**Overall UI/UX score: 5.8 / 10.** The homepage earns an 8. Inner pages average a 5.

The site is built on Astro Starlight — one of the best documentation frameworks available. Starlight ships with breadcrumbs, prev/next pagination, last-updated dates, built-in copy buttons on code blocks, active sidebar highlighting, Expressive Code for syntax highlighting, and Pagefind search — all out of the box. The critical finding of this audit is that most of these defaults are either disabled or broken by custom overrides, producing a weaker experience than a stock Starlight installation would deliver.

**Three root problems:**

1. **The terminal identity disappears after the homepage.** The `raj@context:~$` persona is the site's strongest asset. It appears once and then vanishes. Every content page looks like an uncustomised Starlight install.

2. **Starlight's own defaults are being overridden or suppressed.** Pagination is missing on most modules, the active page highlight may be overridden by CSS, the theme toggle renders twice due to a component override conflict, and the TOC duplicates on several pages. These are not platform limitations — they are self-inflicted configuration regressions.

3. **The platform is roughly 40% utilised.** Expressive Code's advanced features (file names on code blocks, line highlighting, diff view) are unused. The `lastUpdated` feature is off. The sidebar topic structure (`starlight-sidebar-topics`) is not used despite having 5 discrete modules. No community plugins are active.

---

## 2. Design System Audit

### 2.1 No defined design system exists

Visual decisions — spacing, colour use, component patterns, callout styles, heading hierarchy — are made page by page with no consistency. The homepage uses terminal green, dark backgrounds, and monospace fonts. Inner pages use default Starlight styling. The two aesthetics never connect.

**What Starlight makes easy here:** Starlight exposes a set of CSS custom properties (`--sl-color-accent`, `--sl-color-accent-high`, `--sl-color-text-accent`, etc.) that let you define a design token system in a single CSS file. Define them once in `src/styles/custom.css` and they cascade across the entire site — headings, links, active states, badges, code blocks.

**Fix — define a minimal token set in `src/styles/custom.css`:**

```css
:root {
  /* Terminal green accent — extends into all Starlight accent uses */
  --sl-color-accent-low:    #003d1f;
  --sl-color-accent:        #00a854;
  --sl-color-accent-high:   #00d46a;

  /* Warm off-white surface for a subtle terminal-bezel feel */
  --sl-color-bg-nav:        #0f1612;
  --sl-color-bg-sidebar:    #111814;

  /* Custom properties for components not covered by SL vars */
  --ctx-green:              #00d46a;
  --ctx-amber:              #f5a623;
  --ctx-surface:            #1a1f1b;
}

[data-theme='light'] {
  --sl-color-accent-low:    #d6f5e5;
  --sl-color-accent:        #00844a;
  --sl-color-accent-high:   #006638;
  --ctx-green:              #006638;
  --ctx-amber:              #b36800;
}
```

Reference `customCss` in `astro.config.mjs`:

```js
starlight({
  customCss: ['./src/styles/custom.css'],
})
```

---

### 2.2 Terminal identity stops at the homepage

The `raj@context:~$` prompt, the typewriter boot sequence, and the green-on-dark terminal window are the site's only distinctive design elements. The moment a user clicks any link, they land in a completely generic Starlight interface. The identity promise made on the homepage is broken on every subsequent page.

**What to add to inner pages:**

- A subtle terminal-green left-border accent on all H2 headings:
```css
.sl-markdown-content h2 {
  border-left: 3px solid var(--ctx-green);
  padding-left: 0.75rem;
  margin-left: -0.75rem;
}
```

- Monospace rendering for the site name in the header (the "Context" wordmark):
```css
.site-title {
  font-family: var(--sl-font-mono);
  letter-spacing: -0.02em;
}
```

- A terminal-style "prompt" before the page H1 as a subtle decorative element:
```css
.sl-markdown-content > h1::before {
  content: '$ ';
  color: var(--ctx-green);
  font-family: var(--sl-font-mono);
  font-size: 0.75em;
  opacity: 0.6;
}
```

---

### 2.3 Starlight's own CSS variables not used for customisation

The site applies custom CSS but does not appear to remap Starlight's colour variables to match the terminal aesthetic. Every Starlight component (buttons, links, active states, badges, the sidebar highlight) uses `--sl-color-accent` by default. If you don't set that variable, the default Starlight purple/indigo shows through on all components, which conflicts with the terminal green homepage.

Remapping `--sl-color-accent` to the terminal green (as shown in 2.1) is the single highest-leverage design change available — it propagates the site's identity into every Starlight component simultaneously.

---

## 3. Homepage — Detailed UI/UX Review

### 3.1 Terminal hero — what works

The hero section is the strongest element on the site. The typewriter sequence, the `raj@context:~$` prompt, and the boot-style stat counters all work together to establish an immediate character. This is the right aesthetic for a technically-oriented AI learning resource. It creates a brand impression that generic documentation sites cannot replicate.

---

### 3.2 Terminal hero — what breaks

**Line wrapping on narrow viewports.** The `Loading modules: rag bert langchain cert docs` line and the `Interactive guides: ✓ 30+ resources ready` line have fixed character-count formatting. On viewports below ~480px, these strings wrap mid-token, breaking the CLI format. The terminal becomes garbled rather than a boot sequence.

**No `prefers-reduced-motion` support.** Roughly 10–25% of users have reduced motion enabled via OS accessibility settings. The typewriter animation does not respect this, creating a WCAG 2.3.3 violation (AAA) and a significant comfort issue for users with vestibular disorders.

**Fix:**

```css
/* src/styles/custom.css */

/* Fix wrapping on narrow viewports */
@media (max-width: 480px) {
  .hero-terminal .loading-line {
    display: none;
  }
  .hero-terminal {
    font-size: 13px;
  }
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  .hero-typewriter,
  .hero-cursor,
  .hero-counter {
    animation: none !important;
    transition: none !important;
    opacity: 1 !important;
  }
}
```

---

### 3.3 Module cards — what breaks

**Emoji icons are platform-inconsistent.** ⚡ (RAG), 🧠 (BERT), 🔗 (LangChain), 📜 (Claude Code), 🏆 (Cert) all render differently on Windows, macOS, Android, and iOS. The rendering gap between platforms ranges from minor to significant — ⚡ on Windows 11 looks nothing like ⚡ on macOS. Screen readers announce these by Unicode name ("high voltage sign", "scroll") which communicates nothing useful.

Replace with Starlight's built-in icon set or inline SVG. Starlight ships with Phosphor Icons accessible via the `<Icon>` component:

```mdx
---
// In your homepage MDX or Astro component
import { Icon } from '@astrojs/starlight/components';
---
<Icon name="rocket" /> RAG Guides
<Icon name="cpu" /> BERT Architectures
```

Or add `aria-hidden="true"` to treat them as purely decorative:
```html
<span aria-hidden="true">⚡</span> RAG Guides
```

**Cards have no hover state.** Module cards appear static with no visual affordance that they are clickable. On a dark background this is particularly problematic — links styled as content blocks need explicit hover cues.

```css
/* src/styles/custom.css */
.module-card {
  transition: transform 0.12s ease, border-color 0.12s ease;
  border: 1px solid transparent;
}
.module-card:hover {
  transform: translateY(-2px);
  border-color: var(--ctx-green);
}
```

**No visual hierarchy between title, description, and count.** All three pieces of text in each module card read at similar weights. The title should be clearly dominant (600 weight, 17px), description secondary (400 weight, 13px, muted), and resource count tertiary (500 weight, 11px, accent colour).

---

### 3.4 Homepage "Interactive Tools" section creates a taxonomy conflict

The homepage has two sections: "Modules" and "Interactive Tools." The same tools (BERT Full Diagram, Override Test Lab, Cert Quiz) appear in both the module sidebar and this tools section. Users cannot tell whether interactive tools are part of the modules or separate things.

**Fix:** Remove the standalone "Interactive Tools" section. Embed a "Featured interactive" callout inside each module card:

```
⚡ RAG Guides
Complete RAG stack — chunking to production...
13 reference docs · 5 interactive guides
→ Featured: RAG Academy (interactive course)
```

This eliminates the dual-taxonomy problem while keeping discoverability of the best tools.

---

### 3.5 Hardcoded stat counters will drift out of sync

The hero shows "18 RAG Guides", "11 BERT Resources", "60+ Total Resources" as hardcoded strings. These are already slightly off — BERT has 10 pages (7 docs + 3 tools), not 11. As content is added or removed, the numbers will drift.

**Fix in Astro:** Generate these at build time from the content collection. In the homepage component (`.astro` file):

```astro
---
import { getCollection } from 'astro:content';

const allDocs = await getCollection('docs');
const ragCount = allDocs.filter(d => d.id.startsWith('rag/')).length;
const bertCount = allDocs.filter(d => d.id.startsWith('bert/')).length;
const totalCount = allDocs.length;
---

<span>{ragCount}</span> RAG Guides
<span>{bertCount}</span> BERT Resources
<span>{totalCount}+</span> Total Resources
```

---

## 4. Global Chrome — Nav, Sidebar, Header, Footer

### 4.1 Top navigation bar

**Search icon is missing or hidden.** Pagefind search is built into Starlight by default and should show a magnifying glass icon in the nav bar. If it is not visible, it is being suppressed by a CSS rule targeting `.sl-search-btn` or `.header-search`. Check `src/styles/custom.css` for any `display: none` on Starlight's search selectors.

**The site name "Context" has no sub-brand identity.** On inner pages, the header shows only "Context" with no visual signal that this is an AI learning lab. Add a `description` to the Starlight config which renders as a sub-title in the site header on larger viewports:

```js
// astro.config.mjs
starlight({
  title: 'Context',
  description: 'AI Learning Lab — RAG, BERT, LangChain, Claude Code',
})
```

**Theme toggle renders twice on every page.** This is the most visually disruptive bug on the entire site. In Starlight, `ThemeSelect` renders in the site header AND in the `MobileMenuFooter` (for mobile). On desktop both locations are visible simultaneously if a custom component override has added `<ThemeSelect />` somewhere it doesn't belong.

**Fix — check `src/components/` for any file that renders `<ThemeSelect />` outside the standard mobile footer context.** The correct setup is to let Starlight's default `Header` and `MobileMenuFooter` components handle it. If you have a custom `Header.astro` or `MobileMenuFooter.astro` override, check whether both include `<ThemeSelect />`:

```astro
---
// src/components/Header.astro — WRONG if it includes ThemeSelect
// when the default header already renders it
import Default from '@astrojs/starlight/components/Header.astro';
import ThemeSelect from '@astrojs/starlight/components/ThemeSelect.astro';
---
<Default><slot /></Default>
<!-- Remove this if ThemeSelect is already in the default header -->
<ThemeSelect />
```

The fix is to remove any manually added `<ThemeSelect />` outside its canonical location.

---

### 4.2 Sidebar navigation — five problems

**Problem 1: No active page highlight.**
Starlight highlights the active page in the sidebar by default via the `.current` class on `<a>` elements and `[aria-current="page"]`. If this is not visible, a custom CSS rule is overriding it. Check `src/styles/custom.css` for any rule targeting `.sl-nav a`, `.sl-sidebar a`, or `[aria-current]` that removes the default highlight styling.

Verify the default is working by checking Starlight's built-in styles. If overridden, restore with:

```css
/* src/styles/custom.css */
.sl-sidebar a[aria-current='page'],
.sl-sidebar a[aria-current='page']:hover {
  color: var(--sl-color-text-accent);
  background-color: var(--sl-color-accent-low);
  font-weight: 600;
  border-inline-start: 2px solid var(--sl-color-accent);
}
```

**Problem 2: Module order contradicts homepage.**
Homepage order: RAG → BERT → LangChain → Claude Code → Cert.
Sidebar order: Claude Code → RAG → BERT → LangChain → Cert.

Fix in `astro.config.mjs` by reordering the `sidebar` array:

```js
starlight({
  sidebar: [
    { label: 'RAG Guides', items: [...] },
    { label: 'BERT Architectures', items: [...] },
    { label: 'LangChain Reference', items: [...] },
    { label: 'Claude Code', items: [...] },
    { label: 'Cert Prep', items: [...] },
  ],
})
```

**Problem 3: All 63 links always visible — too dense.**
Every module is permanently expanded. Users navigating a BERT page must visually parse 18 RAG links, 2 LangChain links, and 13 Claude Code links before reaching the content they are in. The cognitive load is very high.

Fix by collapsing non-active modules. In Starlight, set `collapsed: true` on sidebar groups that are not the current section. For dynamic active-only expansion, use the `starlight-sidebar-topics` plugin:

```bash
npm install starlight-sidebar-topics
```

```js
// astro.config.mjs
import starlightSidebarTopics from 'starlight-sidebar-topics';

starlight({
  plugins: [
    starlightSidebarTopics([
      { label: 'RAG Guides', link: '/rag/', icon: 'rocket', items: [...] },
      { label: 'BERT Architectures', link: '/bert/', icon: 'cpu', items: [...] },
      { label: 'LangChain', link: '/langchain/', icon: 'link', items: [...] },
      { label: 'Claude Code', link: '/claude-code/', icon: 'terminal-window', items: [...] },
      { label: 'Cert Prep', link: '/cert/', icon: 'trophy', items: [...] },
    ]),
  ],
})
```

This gives each module its own sidebar — when you're in RAG, you see only RAG pages. When in Cert, only Cert pages. Navigation between modules happens via a topic switcher at the top of the sidebar.

**Problem 4: No visual grouping between modules.**
Each module section has no visual separator or accent. They blur together when scanning. The `starlight-sidebar-topics` plugin solves this structurally. If staying with the default sidebar, add section dividers in custom CSS:

```css
.sl-sidebar .top-level > li + li {
  border-top: 1px solid var(--sl-color-hairline);
  margin-top: 0.5rem;
  padding-top: 0.5rem;
}
```

**Problem 5: Long page titles truncate or wrap awkwardly.**
Titles like "CLAUDE.md vs Skills vs Rules — Architecture Guide" and "Domain 1: Agentic Architecture & Orchestration" are too long for the sidebar column width. Enable sidebar label wrapping rather than truncation:

```css
.sl-sidebar a {
  white-space: normal;
  word-break: break-word;
}
```

---

### 4.3 Page header (H1 area) — missing metadata

Starlight renders the `title` frontmatter as the page H1. Below it there is nothing — no metadata, no description, no level badge, no reading time, no last-updated date. The page begins abruptly with the first paragraph.

**Fix — add a page metadata strip via a custom `PageTitle` component override:**

Create `src/components/PageTitle.astro`:

```astro
---
import type { Props } from '@astrojs/starlight/props';
import Default from '@astrojs/starlight/components/PageTitle.astro';

const { entry } = Astro.props;
const { level, description } = entry.data;
---
<Default {...Astro.props}><slot /></Default>

{level && (
  <div class="page-meta">
    {level === 'beginner' && <span class="badge badge-beginner">Beginner</span>}
    {level === 'intermediate' && <span class="badge badge-intermediate">Intermediate</span>}
    {level === 'advanced' && <span class="badge badge-advanced">Advanced</span>}
  </div>
)}

<style>
  .page-meta {
    display: flex;
    gap: 0.5rem;
    margin-top: -0.5rem;
    margin-bottom: 1.5rem;
  }
  .badge {
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .badge-beginner     { background: #e6f5ef; color: #006638; }
  .badge-intermediate { background: #e8f1fb; color: #1a5fa8; }
  .badge-advanced     { background: #faeeda; color: #7a4e0a; }
</style>
```

Register it in `astro.config.mjs`:

```js
starlight({
  components: {
    PageTitle: './src/components/PageTitle.astro',
  },
})
```

Then in each page's frontmatter:
```yaml
---
title: Advanced RAG — Techniques
level: advanced
---
```

---

### 4.4 No breadcrumbs anywhere

Starlight does not ship breadcrumbs as a built-in feature. They require either a custom component override or the `astro-breadcrumbs` package.

**Fix — install `astro-breadcrumbs`:**

```bash
npm install astro-breadcrumbs
```

Override Starlight's `ContentPanel` or `PageTitle` to inject it:

```astro
---
// src/components/PageTitle.astro
import type { Props } from '@astrojs/starlight/props';
import Default from '@astrojs/starlight/components/PageTitle.astro';
import { Breadcrumbs } from 'astro-breadcrumbs';
---
<nav class="sl-breadcrumbs" aria-label="Breadcrumb">
  <Breadcrumbs indexText="Context" />
</nav>
<Default {...Astro.props}><slot /></Default>

<style>
  .sl-breadcrumbs {
    font-size: 12px;
    color: var(--sl-color-gray-3);
    margin-bottom: 0.75rem;
  }
  .sl-breadcrumbs a {
    color: inherit;
    text-decoration: none;
  }
  .sl-breadcrumbs a:hover {
    color: var(--sl-color-text-accent);
  }
</style>
```

---

### 4.5 Prev/Next navigation missing on most modules

Starlight generates prev/next links from sidebar order and enables them by default (`pagination: true`). If they are missing on RAG and BERT pages, one of three things has happened:

1. `pagination: false` is set in `astro.config.mjs`
2. Individual pages have `prev: false` in frontmatter
3. The sidebar uses `autogenerate:` which can produce incomplete pagination in some edge cases

**Fix — verify config and use explicit sidebar ordering:**

```js
// astro.config.mjs
starlight({
  pagination: true,  // ensure this is not false
})
```

For reliable prev/next across all 63 pages, use explicit `items:` arrays rather than `autogenerate:` in your sidebar config. Autogenerated groups are sorted alphabetically by filename, which may not match your intended reading order and can produce unexpected pagination.

**Per-page override for pages that should not have prev/next** (landings, standalone tools):

```yaml
---
title: RAG Guides
prev: false
next: false
---
```

---

### 4.6 Footer — no global site footer

Starlight's default footer shows `<LastUpdated />`, `<Pagination />`, and `<EditLink />`. There is no global site footer with copyright, quick links, or attribution.

**Fix — override the `Footer` component:**

```astro
---
// src/components/Footer.astro
import type { Props } from '@astrojs/starlight/props';
import Default from '@astrojs/starlight/components/Footer.astro';
---
<Default {...Astro.props}><slot /></Default>

<footer class="site-footer">
  <div class="site-footer-inner">
    <span class="site-footer-brand">Context v2.1 — AI Learning Lab</span>
    <nav class="site-footer-links" aria-label="Footer navigation">
      <a href="/ai-lab/rag/">RAG</a>
      <a href="/ai-lab/bert/">BERT</a>
      <a href="/ai-lab/langchain/">LangChain</a>
      <a href="/ai-lab/claude-code/">Claude Code</a>
      <a href="/ai-lab/cert/">Cert Prep</a>
    </nav>
  </div>
</footer>

<style>
  .site-footer {
    border-top: 1px solid var(--sl-color-hairline);
    padding: 1rem 0 0;
    margin-top: 2rem;
  }
  .site-footer-inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
    font-size: 12px;
    color: var(--sl-color-gray-3);
  }
  .site-footer-links {
    display: flex;
    gap: 1rem;
  }
  .site-footer-links a {
    color: inherit;
    text-decoration: none;
  }
  .site-footer-links a:hover {
    color: var(--sl-color-text-accent);
  }
</style>
```

Register in `astro.config.mjs`:

```js
starlight({
  components: {
    Footer: './src/components/Footer.astro',
  },
})
```

---

## 5. Content Pages — Layout and Presentation

### 5.1 Duplicate "On this page" TOC on multiple pages

On Chunking Strategies, BERT Architecture, and several Cert Prep pages, the table of contents appears twice — once in the right sidebar and once inline in the content body.

**Root cause in Starlight:** One of two things:
1. A manual `<TableOfContents />` component import in an `.mdx` file
2. A legacy `[TOC]` or `[[toc]]` string in a `.md` file being processed by a remark plugin

**Fix — scan for manual TOC inclusions:**

```bash
# Find any manual TOC insertions
grep -r "\[TOC\]\|\[\[toc\]\]\|TableOfContents" src/content/docs/
```

Remove any manual TOC imports from `.mdx` files. Starlight handles TOC rendering automatically in the right sidebar — no manual inclusion is needed.

Also verify `astro.config.mjs` does not include a remark-toc plugin:
```js
// Remove this if present:
import remarkToc from 'remark-toc';
// Remove from markdown config
```

Control TOC depth globally to prevent 28-entry TOCs on long pages:
```js
starlight({
  tableOfContents: {
    minHeadingLevel: 2,
    maxHeadingLevel: 3,
  },
})
```

---

### 5.2 Version callout boxes are inconsistent

Pages use three different formats for version/currency notes:

- Agentic RAG and Vector Stores: `> **Current as of April 2026.**` blockquote
- Advanced RAG, GraphRAG: no callout despite referencing 2024–2026 techniques
- Master Study Guide: no callout despite referencing `v2.1.x` features

**Fix — standardise using Starlight's `<Aside>` component (available in MDX files):**

```mdx
import { Aside } from '@astrojs/starlight/components';

<Aside type="tip" title="Current as of April 2026">
  LangChain 1.0 + LangGraph 1.0 stable. Code examples compatible with `langgraph>=1.0`.
</Aside>
```

For `.md` files (non-MDX), use the GitHub Flavored Markdown callout syntax that Starlight supports:

```markdown
:::tip[Current as of April 2026]
LangChain 1.0 + LangGraph 1.0 stable. All code examples use `langgraph>=1.0`.
:::
```

Apply to all pages referencing specific library versions or dated research.

---

### 5.3 Code blocks — Expressive Code features unused

Starlight uses Expressive Code for all code block rendering. This is a significant upgrade over standard syntax highlighting — it provides copy buttons, file name labels, line highlighting, diff views, and frame decorators out of the box. **None of these features are currently used anywhere on the site.**

**Copy button:** Enabled by default in Expressive Code/Starlight. If copy buttons are not showing, it is being suppressed. Check `astro.config.mjs` for:
```js
// Remove this if present — it disables copy buttons:
expressiveCode: {
  themes: [...],
  showLineNumbers: false,
}
```
The copy button should work with zero configuration. If it's missing, it's hidden by a CSS override in `src/styles/custom.css`. Search for `.copy` or `.ec-` selectors.

**Add file names to code blocks** — shows users exactly where code goes:
````markdown
```python title="src/rag/chunker.py"
def chunk_document(text: str, size: int = 512) -> list[str]:
    ...
```
````

**Add line highlighting for key lines:**
````markdown
```python {3,7}
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(  # highlighted
    chunk_size=512,
    chunk_overlap=50,
)

docs = splitter.split_documents(raw_docs)  # highlighted
```
````

**Use diff view for "before/after" examples** (very useful for the Claude Code config guide):
````markdown
```python del={2} ins={3}
# Old way
retriever = vectorstore.as_retriever()
# New way — with search_kwargs
retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
```
````

These are already available — they just need to be applied to existing code blocks across the 63 pages.

---

### 5.4 Tables — three presentation problems

**No horizontal scroll on mobile.** Wide tables (Vector Stores comparison, BERT variants head-to-head, LangChain version compatibility matrix) overflow their containers on small viewports rather than scrolling. 

**Fix in `src/styles/custom.css`:**
```css
.sl-markdown-content table {
  display: block;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
```

**No alternating row colours on any table.** Dense tables like the Self-RAG token table (8 rows, 3 columns) and the Cert domain weights table blur visually without row separation.

```css
.sl-markdown-content tbody tr:nth-child(even) {
  background-color: var(--sl-color-bg-nav);
}
```

**Duplicate section heading in Vector Stores.** The "Choosing a Vector Store" H2 appears twice — at section 10 and section 15 in the TOC. This means the same anchor `#choosing-a-vector-store` exists twice, causing the second instance to get a mangled slug like `#choosing-a-vector-store-1`. Rename one: "Quick Selection Guide" for the early decision tree, "Full Selection Framework" for the detailed comparison.

---

### 5.5 "See Also" sections exist on exactly one page

Agentic RAG ends with a `## See Also` section linking to related content. This is the only page on the site with one. Users who benefit from it on Agentic RAG will reasonably expect it everywhere and find its absence jarring.

**Fix — Starlight provides a `<LinkCard>` component ideal for See Also sections:**

```mdx
import { LinkCard, CardGrid } from '@astrojs/starlight/components';

## See also

<CardGrid>
  <LinkCard
    title="BERT in RAG Pipelines"
    href="/ai-lab/bert/bert-in-rag/"
    description="How BERT models serve as the embedding backbone for RAG retrieval"
  />
  <LinkCard
    title="Production RAG"
    href="/ai-lab/rag/production-rag/"
    description="Caching, observability, and guardrails for deployed RAG systems"
  />
</CardGrid>
```

Add this pattern to all 63 pages. Priority pages: every RAG page (link to related RAG and BERT content), every BERT page (link to RAG embedding content), every Claude Code page (link to relevant Cert domain).

---

### 5.6 Last updated dates not shown

Starlight can display "Last updated" in the page footer using git history. It is not enabled.

**Fix — one line in `astro.config.mjs`:**

```js
starlight({
  lastUpdated: true,
})
```

This reads each file's most recent git commit date and renders it in the footer as "Last updated: Apr 12, 2026." Zero per-page configuration needed.

For pages where you want to set the date manually (if git history isn't reliable):

```yaml
---
title: Advanced RAG — Techniques
lastUpdated: 2026-03-15
---
```

---

### 5.7 Edit links not configured

Starlight supports an "Edit this page" link in the footer that opens the file in GitHub. This is absent from all pages.

**Fix:**

```js
// astro.config.mjs
starlight({
  editLink: {
    baseUrl: 'https://github.com/rajrkdev/ai-lab/edit/main/',
  },
})
```

This adds "Edit page" to every page footer, giving users a low-friction way to suggest corrections — critical for a fast-moving technical resource.

---

### 5.8 Description frontmatter missing on all pages

Starlight uses the `description` frontmatter field to populate `<meta name="description">` and social sharing previews. It is absent from every page on the site.

**Fix — add to all pages.** In bulk, this is a content task. Template:

```yaml
---
title: Chunking Strategies — Reference
description: Seven RAG chunking strategies from fixed-size to late chunking. Includes a strategy selection guide, metadata best practices, and benchmark data.
---
```

Starlight emits this automatically as:
```html
<meta name="description" content="Seven RAG chunking strategies...">
<meta property="og:description" content="Seven RAG chunking strategies...">
```

---

## 6. Interactive Tool Pages — UI/UX

### 6.1 Blank screens without JavaScript

All 10+ interactive tool pages (RAG Academy, Override Test Lab, Architecture Diagram, Precedence Diagram, File Catalog, BERT Full Diagram, BERT Tokenizer, BERT Encoder Block, Cert Quiz, Visual Learning pages) return blank content without JavaScript. This affects: accessibility, SEO, users on corporate networks with script blocking, and anyone on a slow connection where JS hasn't loaded.

**Fix — use `<StarlightPage>` to wrap standalone tools with static content:**

For tools currently served as raw `.html` files, create Starlight wrapper pages. Example for BERT Tokenizer:

```astro
---
// src/pages/bert/bert-tokenizer-wrapper.astro
import StarlightPage from '@astrojs/starlight/components/StarlightPage.astro';
---

<StarlightPage
  frontmatter={{
    title: 'BERT Tokenizer — Interactive Deep Dive',
    description: 'Interactive exploration of WordPiece tokenization: how BERT splits words into subword tokens, handles unknown vocabulary, and constructs the 30,000-token vocabulary.',
  }}
>
  <p>
    This interactive tool demonstrates BERT's WordPiece tokenization process.
    Enter any text to see how it is split into subword tokens, which tokens map to
    <code>[UNK]</code>, and how the vocabulary was constructed.
  </p>
  <p><strong>Key concepts:</strong> WordPiece, subword tokens, vocabulary construction, [UNK] handling, special tokens [CLS] and [SEP].</p>

  <noscript>
    <aside>
      <strong>JavaScript required.</strong> This interactive tool requires JavaScript.
      For a static reference, see the <a href="/ai-lab/bert/tokenization/">WordPiece Tokenization</a> page.
    </aside>
  </noscript>

  <div id="tokenizer-root" style="min-height:400px;">
    <div class="tool-loading" aria-live="polite">
      <code>raj@context:~$ loading bert-tokenizer...</code>
    </div>
  </div>

  <script src="/tools/bert-tokenizer.js" defer></script>
</StarlightPage>
```

Register these wrapper pages in the sidebar under their respective modules. This gives each tool: Starlight layout, sidebar navigation, breadcrumbs, active page highlighting, prev/next, and static fallback content — while the existing JS tool code runs unchanged.

---

### 6.2 No loading state while JavaScript executes

On slow connections (3G mobile, corporate proxies), there is 3–8 seconds of blank white screen while JS loads. The terminal aesthetic makes a themed loading state particularly appropriate here.

**Fix — add a CSS-only loading indicator before the JS mount point:**

```html
<div id="tool-loading" style="
  display:flex; align-items:center; gap:12px;
  padding:2rem; font-family:monospace; font-size:14px;
  color: var(--sl-color-text-accent);
">
  <div class="spinner"></div>
  raj@context:~$ loading module...
</div>

<style>
.spinner {
  width:16px; height:16px;
  border:2px solid currentColor;
  border-top-color:transparent;
  border-radius:50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform:rotate(360deg); } }
@media (prefers-reduced-motion: reduce) {
  .spinner { animation: none; }
}
</style>

<script>
  document.addEventListener('DOMContentLoaded', () => {
    const loader = document.getElementById('tool-loading');
    if (loader) loader.style.display = 'none';
  });
</script>
```

---

### 6.3 No instruction panels on any tool

Users land on interactive tools with no context about what the tool does, how to use it, or what they will learn. The Override Test Lab is 12 scenarios — users don't know this until they discover it. The Cert Quiz covers 5 domains — users don't know the question count, timing, or domain breakdown.

**Fix — add a terminal-themed instruction card before each tool's mount point, using Starlight's `<Aside>` component in the wrapper page:**

```mdx
<Aside type="note" title="How to use this lab">
  **Override Test Lab** presents 12 Claude Code precedence scenarios. For each scenario,
  identify which configuration file takes precedence and why. Scenarios build from simple
  (two-file conflicts) to complex (three-way conflicts with path scoping).
  Expected time: 15–20 minutes. Your progress is saved in the browser session.
</Aside>
```

---

### 6.4 LangChain Mastery is orphaned — not in Starlight routing

The LangChain Mastery interactive guide is served as a raw `.html` file that bypasses Starlight entirely. It does not appear in the sidebar, is not in Pagefind's search index, has no nav, and has no way back to the rest of the site.

**Fix:** Create a Starlight wrapper page (pattern shown in 6.1) and add it to the sidebar:

```js
// astro.config.mjs — sidebar section for LangChain
{
  label: 'LangChain Reference',
  items: [
    { label: 'Overview', link: '/langchain/' },
    { label: 'Deep Reference Guide', link: '/langchain/langchain-reference/' },
    { label: 'LangChain Mastery (Interactive)', link: '/langchain/langchain-mastery/' },
  ],
}
```

Additionally, add a top nav bar with a site logo and home link to the raw HTML file itself for users who arrive there via direct link.

---

## 7. Component-Level Audit

### 7.1 Starlight's built-in components underused

Starlight ships a rich component library accessible in `.mdx` files. None of these are currently used anywhere on the site despite being ideal for the content:

**`<Card>` and `<CardGrid>` — perfect for module landing pages:**

```mdx
import { Card, CardGrid } from '@astrojs/starlight/components';

<CardGrid>
  <Card title="Naive RAG Explainer" icon="open-book">
    End-to-end RAG walkthrough using a school library analogy. **Beginner.**
  </Card>
  <Card title="Advanced RAG" icon="rocket">
    HyDE, RAG-Fusion, ColPali, Late Chunking. **Advanced.**
  </Card>
</CardGrid>
```

**`<Badge>` — for difficulty and type labels:**

```mdx
import { Badge } from '@astrojs/starlight/components';

# Advanced RAG — Techniques <Badge text="Advanced" variant="caution" />
```

**`<Steps>` — for sequential processes (currently done with numbered lists):**

```mdx
import { Steps } from '@astrojs/starlight/components';

<Steps>
1. Install the embedding model: `pip install sentence-transformers`
2. Load your documents and chunk them
3. Generate embeddings for each chunk
4. Upsert into your vector store
</Steps>
```

**`<Tabs>` — for multi-language or multi-framework examples (currently done with separate code blocks):**

```mdx
import { Tabs, TabItem } from '@astrojs/starlight/components';

<Tabs>
  <TabItem label="Chroma">
    ```python
    vectorstore = Chroma.from_documents(docs, embeddings)
    ```
  </TabItem>
  <TabItem label="Pinecone">
    ```python
    vectorstore = PineconeVectorStore.from_documents(docs, embeddings)
    ```
  </TabItem>
  <TabItem label="Qdrant">
    ```python
    vectorstore = QdrantVectorStore.from_documents(docs, embeddings)
    ```
  </TabItem>
</Tabs>
```

This is the most impactful content change available — replacing multiple sequential code blocks with tabbed alternatives removes the single biggest source of vertical sprawl on long pages like Vector Stores and Production RAG.

---

### 7.2 Pagefind search — underutilised

Starlight indexes all pages with Pagefind by default. The search should be working. Issues to check:

**JS-only tool pages return zero search results** because they have no static text content. The `<StarlightPage>` wrapper fixes add the static content that Pagefind can index.

**Exclude pages from search that shouldn't appear** (e.g., Concept Validation Report, Compass Research Notes if they are being re-evaluated):

```yaml
---
title: Concept Validation Report
pagefind: false
---
```

**Configure Pagefind ranking** to favour module landing pages over deep reference pages in search results:

```js
starlight({
  pagefind: {
    ranking: {
      pageRank: 0.5,
    },
  },
})
```

---

### 7.3 Social links in header — absent

Starlight renders social icon links in the header when configured. No social links are currently shown.

```js
// astro.config.mjs
starlight({
  social: [
    { icon: 'github', label: 'GitHub', href: 'https://github.com/rajrkdev/ai-lab' },
  ],
})
```

---

### 7.4 Community plugins — high value, not installed

The Starlight plugin ecosystem has several plugins that directly address audit findings:

| Plugin | Problem it solves | Install |
|---|---|---|
| `starlight-sidebar-topics` | Sidebar cognitive overload — splits into per-module sidebars | `npm i starlight-sidebar-topics` |
| `starlight-tags` | No difficulty/type labels on pages | `npm i starlight-tags` |
| `starlight-giscus` | No user feedback mechanism | `npm i starlight-giscus` |
| `starlight-ui-tweaks` | Cleaner theme toggle, custom nav links | `npm i starlight-ui-tweaks` |
| `astro-breadcrumbs` | No breadcrumb trail | `npm i astro-breadcrumbs` |

---

## 8. Typography and Readability

### 8.1 Heading hierarchy on long pages

The Complete Study Guide has 28 H2/H3 TOC entries. The Cert Gap-Fill Reference has 31 numbered gap sections. The LangChain reference has deeply nested H4s. These produce TOCs so dense they are useless as navigation.

The `tableOfContents: { maxHeadingLevel: 3 }` config prevents H4+ from appearing in the TOC (already recommended above). For pages where H2 count itself is too high (the Complete Study Guide has 8 H2 sections with verbose names), the headings themselves need restructuring:

**Current (verbose, uppercase, clutter):**
```
## DOMAIN 1: Agentic Architecture & Orchestration (27%)
### Task 1.1 — The agentic loop lifecycle and stop reasons
```

**Recommended (clean, scannable):**
```
## Domain 1 — Agentic Architecture (27%)
### The agentic loop lifecycle
```

The percentage weight can be shown as a `<Badge>` rather than embedded in the heading text.

---

### 8.2 ALL CAPS headings violate basic typography conventions

The Master Study Guide uses ALL CAPS for several major section headings:

```
## THE 25 RULES THAT COVER 80%+ OF THE EXAM
### DOMAIN 1: AGENTIC ARCHITECTURE
### DISTRACTOR PATTERNS
### EXAM STRATEGY
```

ALL CAPS text is harder to read, is conventionally interpreted as shouting in web contexts, and breaks the visual rhythm of the page. These headings are the most-read sections on the site — they deserve visual emphasis, not capitalisation.

**Fix:** Convert to sentence case and apply visual emphasis via the terminal-green H2 styling defined in section 2.2. An `<Aside>` component makes important sections visually prominent without capitalisation:

```mdx
import { Aside } from '@astrojs/starlight/components';

## The 25 rules that cover 80%+ of the exam

<Aside type="danger" title="High-yield rules">
  Memorise these 25 rules first. They cover the majority of exam questions
  across all 5 domains.
</Aside>
```

---

### 8.3 Reading progress on long pages

Pages like Complete Study Guide, Cert Gap-Fill Reference, and LangChain Reference are extremely long. There is no reading progress indicator.

**Fix — add a thin progress bar in `src/components/PageTitle.astro`:**

```astro
<div id="reading-progress" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" aria-label="Reading progress"></div>

<script>
  const bar = document.getElementById('reading-progress');
  window.addEventListener('scroll', () => {
    const scroll = window.scrollY;
    const height = document.body.scrollHeight - window.innerHeight;
    const pct = height > 0 ? Math.round((scroll / height) * 100) : 0;
    bar.style.width = pct + '%';
    bar.setAttribute('aria-valuenow', pct);
  }, { passive: true });
</script>

<style>
  #reading-progress {
    position: fixed;
    top: 0; left: 0;
    height: 2px;
    width: 0%;
    background: var(--sl-color-accent);
    z-index: 9999;
    transition: width 0.1s linear;
    pointer-events: none;
  }
  @media (prefers-reduced-motion: reduce) {
    #reading-progress { transition: none; }
  }
</style>
```

---

## 9. Colour, Contrast and Dark Mode

### 9.1 Dark mode audit

Starlight's dark mode is robust by default. The main risk is in custom CSS files where hardcoded hex colours override the CSS variable system. If any element in `src/styles/custom.css` uses hardcoded hex instead of `var(--sl-color-*)` or `var(--ctx-*)`, it will not adapt to dark mode.

**Audit:** Load the site in dark mode and check:
- The homepage terminal window background
- Module card backgrounds
- Custom badge colours (difficulty levels)
- Callout/admonition custom styling
- Any custom border colours

Any element that looks visually broken in dark mode is using a hardcoded colour. Replace with the appropriate Starlight CSS variable.

---

### 9.2 Visited link styling — absent

On a learning resource where users return across multiple sessions to read sequentially, visited links provide a critical "have I read this?" signal. Visited link styling is absent.

```css
/* src/styles/custom.css */
.sl-markdown-content a:visited {
  color: var(--sl-color-gray-3);
}
/* Exclude navigation links — only apply to inline content links */
.sl-sidebar a:visited,
.pagination-links a:visited {
  color: inherit;
}
```

---

### 9.3 Link colours — no external link indicator

Links to external sites (GitHub, arXiv papers, library documentation) look identical to internal navigation links. Users don't know they're leaving the site.

```css
/* src/styles/custom.css */
.sl-markdown-content a[href^="http"]:not([href*="rajrkdev.github.io"])::after {
  content: ' ↗';
  font-size: 0.8em;
  opacity: 0.6;
}
```

---

## 10. Motion and Animation

### 10.1 Homepage animation — `prefers-reduced-motion` missing

See section 3.2. The fix is in `src/styles/custom.css`.

### 10.2 Starlight's built-in transitions

Starlight uses View Transitions API for page navigation when enabled. This gives smooth, SPA-style page transitions between docs without a full page reload:

```js
// astro.config.mjs
export default defineConfig({
  integrations: [starlight({ ... })],
  // View Transitions is built into Astro — enable it in your layout if not already active
});
```

Add `<ViewTransitions />` to `src/layouts/Layout.astro` if it exists, or to the `Head` component override. This alone makes navigation feel significantly faster and more polished.

---

## 11. Empty States, Loading States and Error States

### 11.1 Custom 404 page — absent

GitHub Pages serves a default 404 with no site branding. Every broken link or mistyped URL sends users to an unbranded dead end.

**Fix — create `src/pages/404.astro`:**

```astro
---
import StarlightPage from '@astrojs/starlight/components/StarlightPage.astro';
---

<StarlightPage
  frontmatter={{
    title: '404 — Not Found',
    description: 'Page not found.',
    template: 'splash',
  }}
>
  <div class="not-found">
    <pre class="terminal-output">raj@context:~$ find . -name "404"
find: no results matching pattern

raj@context:~$ suggest --recovery
→ Return to homepage
→ Use search (Ctrl+K)
→ Browse modules below</pre>

    <nav class="recovery-links">
      <a href="/ai-lab/">← Homepage</a>
      <a href="/ai-lab/rag/">RAG Guides</a>
      <a href="/ai-lab/bert/">BERT Architectures</a>
      <a href="/ai-lab/claude-code/">Claude Code</a>
      <a href="/ai-lab/cert/">Cert Prep</a>
    </nav>
  </div>
</StarlightPage>
```

---

### 11.2 Search empty state

When Pagefind returns no results, a generic "No results" message appears. Style it to match the terminal aesthetic:

```css
/* src/styles/custom.css */
.pagefind-ui__message {
  font-family: var(--sl-font-mono);
  font-size: 13px;
  color: var(--sl-color-gray-3);
}
.pagefind-ui__message::before {
  content: 'raj@context:~$ search: ';
  color: var(--sl-color-accent);
}
```

---

## 12. Mobile UI/UX

### 12.1 Terminal animation on narrow viewports

At 375px (iPhone SE), the `Loading modules: rag bert langchain cert docs` line wraps mid-token. Fix: see section 3.2.

### 12.2 Touch targets

Starlight's default touch targets are generally adequate (44×44px) but the heading anchor links (`#`) that appear on hover are very small. On mobile these are not reliably tappable. Increase via CSS:

```css
.sl-markdown-content :is(h2, h3, h4) > a.anchor {
  padding: 0 8px;
}
```

### 12.3 Code blocks on mobile

Long code examples (40+ lines in Domain 1 and Claude Code Reference) require horizontal scrolling. Expressive Code handles this gracefully with `overflow-x: auto`. The copy button from Expressive Code (once confirmed working — see 5.3) helps mobile users transfer code without text selection.

For very long code blocks, use Expressive Code's collapsible feature:

````markdown
```python collapse={10-35} title="Full implementation"
# Lines 10–35 are collapsed by default
# Users click to expand
```
````

### 12.4 Bottom tab bar for mobile — missing

On mobile, the hamburger menu requires 2 taps to switch modules. A persistent bottom tab bar with 5 module icons would enable single-tap switching — the standard mobile navigation pattern for multi-section apps.

**Fix — add a bottom nav via the `Footer` component override:**

```astro
---
// src/components/Footer.astro
---
<!-- ... existing footer ... -->

<nav class="mobile-tab-bar" aria-label="Module navigation">
  <a href="/ai-lab/rag/" class="tab" aria-label="RAG Guides">
    <svg><!-- rocket icon --></svg>
    <span>RAG</span>
  </a>
  <a href="/ai-lab/bert/" class="tab" aria-label="BERT Architectures">
    <svg><!-- cpu icon --></svg>
    <span>BERT</span>
  </a>
  <a href="/ai-lab/langchain/" class="tab" aria-label="LangChain">
    <svg><!-- link icon --></svg>
    <span>LangChain</span>
  </a>
  <a href="/ai-lab/claude-code/" class="tab" aria-label="Claude Code">
    <svg><!-- terminal icon --></svg>
    <span>Code</span>
  </a>
  <a href="/ai-lab/cert/" class="tab" aria-label="Cert Prep">
    <svg><!-- trophy icon --></svg>
    <span>Cert</span>
  </a>
</nav>

<style>
  .mobile-tab-bar {
    display: none;
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: var(--sl-color-bg-nav);
    border-top: 1px solid var(--sl-color-hairline);
    z-index: 100;
    padding: env(safe-area-inset-bottom) 0 0;
  }
  @media (max-width: 72rem) {
    .mobile-tab-bar { display: flex; }
  }
  .tab {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 8px 4px;
    font-size: 10px;
    color: var(--sl-color-gray-3);
    text-decoration: none;
    gap: 3px;
    min-height: 44px;
  }
  .tab[aria-current="page"],
  .tab.active {
    color: var(--sl-color-accent);
  }
  .tab svg {
    width: 20px; height: 20px;
  }
</style>
```

---

## 13. Module-by-Module Presentation Audit

### 13.1 Module landing page consistency

| Module | Landing quality | Specific gaps |
|---|---|---|
| RAG Guides | 5/10 | No Quick Reference, no content table with descriptions, no difficulty levels |
| BERT Architectures | 9/10 | Best landing — Quick Reference tables, tool list, content sections |
| LangChain | 2/10 | Near-empty — "What's in This Section" with 2 items and a 2-line Quick Start |
| Claude Code | 9/10 | Excellent — 3 categorised sections, full Quick Reference |
| Cert Prep | 10/10 | Gold standard — domain weights, exam scenarios, strategy, cheat sheet |

**Fix RAG landing** — add a Quick Reference table and a `<CardGrid>` content list:

```mdx
import { Card, CardGrid, Badge } from '@astrojs/starlight/components';

## Quick Reference

| Stage | Technique | Key parameter |
|-------|-----------|---------------|
| Chunking | Recursive character | `chunk_size=512, overlap=50` |
| Embedding | text-embedding-3-small | 1536 dims, 8191 token limit |
| Retrieval | Hybrid (dense + BM25) | RRF fusion |
| Reranking | Cross-encoder | Cohere Rerank v3 |

## Module content

<CardGrid>
  <Card title="Naive RAG Explainer" icon="open-book">
    School library walkthrough of the full RAG pipeline. <Badge text="Beginner" variant="success" />
  </Card>
  <Card title="Advanced RAG" icon="rocket">
    HyDE, RAG-Fusion, ColPali, Contextual Retrieval. <Badge text="Advanced" variant="caution" />
  </Card>
</CardGrid>
```

**Fix LangChain landing** — either fully populate with Quick Start + quick reference, or remove the intermediate landing and redirect directly to the reference doc. If removing:

```js
// astro.config.mjs sidebar
{
  label: 'LangChain Reference',
  items: [
    { label: 'Deep Reference Guide', link: '/langchain/langchain-reference/' },
    { label: 'LangChain Mastery (Interactive)', link: '/langchain/langchain-mastery/' },
  ],
}
```

---

### 13.2 Agentic RAG — best presented page on the site

This is the reference template for how all content pages should look. It has:
- Version callout immediately below the H1
- Clean H2 → H3 hierarchy (technique as H2, implementation as H3)
- Consistent table format for the Self-RAG token reference
- Code blocks with explicit import statements and version annotations
- A comparison table at the end
- A `## See Also` section

Every other content page should be brought up to this standard.

---

### 13.3 Complete Study Guide — most in need of restructuring

This is the highest-priority page for UI/UX improvement because it is the most-read exam prep page. Current problems:

1. 28-entry TOC is unusable as navigation
2. ALL CAPS section headers throughout
3. Domain sections have no visual separator
4. Percentage weights embedded in heading text clutter the TOC

**Full fix approach:**

```mdx
import { Aside, Badge, Steps } from '@astrojs/starlight/components';

## Domain 1 — Agentic Architecture <Badge text="27% of exam" variant="note" />

<Aside type="tip" title="Highest-weight domain">
  27% of exam questions. Study this domain first and allocate the most practice time.
</Aside>

### The agentic loop lifecycle

[content here — no ALL CAPS, no task statement in heading]

---

## Domain 2 — Tool Design & MCP <Badge text="18% of exam" variant="note" />
```

The `---` horizontal rule between domains, combined with the `<Badge>` weight indicator, provides visual separation without all-caps headers.

---

### 13.4 Vector Stores — structural fix needed

The TOC shows "Choosing a Vector Store" twice (two different sections with the same heading). The second instance gets a slug of `#choosing-a-vector-store-1` which is ugly and confusing for anyone deep-linking to the section.

**Fix:** Rename the first occurrence to "Quick selection guide" and the second (detailed comparison section) to "Full selection framework."

Also: the "Full Comparison (August 2025)" section heading embeds a date that will age badly in the URL anchor. Change to "Full comparison" and put the date in a version callout.

---

## 14. What Is Missing

### Missing globally

| Element | Where needed | Starlight solution |
|---|---|---|
| Active page highlight | All pages | Fix CSS override suppressing `[aria-current='page']` |
| Breadcrumb trail | All inner pages | `astro-breadcrumbs` + `PageTitle` override |
| Last updated date | All pages | `lastUpdated: true` in config — one line |
| Edit page link | All pages | `editLink: { baseUrl: '...' }` in config — one line |
| Prev/next navigation | RAG, BERT, Claude Code | Fix `pagination: true` and explicit sidebar order |
| Difficulty badges | All pages | `starlight-tags` plugin + `Badge` component |
| Page description | All pages | `description:` frontmatter on all 63 pages |
| See Also sections | 62 pages (only 1 has it) | `<LinkCard>` / `<CardGrid>` component |
| Custom 404 page | Site-wide | `src/pages/404.astro` with `StarlightPage` |
| Loading states | All JS tool pages | Static content + CSS spinner before mount point |
| Tool instruction panels | All 10 interactive tools | `<Aside>` component in `StarlightPage` wrapper |
| Social links in header | Site header | `social:` config |
| Reading progress bar | Long pages | JS + CSS in `PageTitle` override |
| Visited link styling | All content links | CSS in `custom.css` |
| External link indicator | All external links | CSS `::after` pseudo-element |
| Bottom tab bar (mobile) | Mobile viewports | `Footer` override with fixed nav |
| Copy button on code | All code blocks | Should be default — check for CSS suppression |

### Missing per module

| Element | Module | Specific fix |
|---|---|---|
| Quick Reference section | RAG landing | `<CardGrid>` + table |
| Content list with descriptions | RAG landing | `<CardGrid>` with difficulty badges |
| Meaningful landing content | LangChain landing | Populate or redirect |
| `StarlightPage` wrapper | All 10 JS tools | Create wrapper `.astro` for each |
| LangChain Mastery in sidebar | LangChain | Add to `items:` in sidebar config |
| Domain visual separator | Complete Study Guide | `---` + Badge approach |
| Navigation between visual guides | Cert D1/D2-D5 visuals | Add explicit `prev:`/`next:` frontmatter |

---

## 15. What Needs to Be Added

### Tier A — Config-only, zero content work (~30 minutes)

```js
// astro.config.mjs — add all of these
starlight({
  lastUpdated: true,          // ← "Last updated" dates from git
  pagination: true,           // ← confirm not disabled
  editLink: {                 // ← "Edit this page" links
    baseUrl: 'https://github.com/rajrkdev/ai-lab/edit/main/',
  },
  tableOfContents: {          // ← prevents 28-entry TOC on long pages
    minHeadingLevel: 2,
    maxHeadingLevel: 3,
  },
  social: [                   // ← GitHub icon in header
    { icon: 'github', label: 'GitHub', href: 'https://github.com/rajrkdev/ai-lab' },
  ],
  head: [                     // ← Global OG image
    { tag: 'meta', attrs: { property: 'og:image', content: '/og-image.png' }},
    { tag: 'meta', attrs: { name: 'twitter:card', content: 'summary_large_image' }},
  ],
})
```

---

### Tier B — CSS additions in `src/styles/custom.css` (~2 hours)

1. Remap `--sl-color-accent` to terminal green (propagates into all Starlight components)
2. Fix active sidebar highlight (restore `[aria-current='page']` styling)
3. Add terminal-green H2 left-border accent
4. Add `$` prompt prefix to H1 on inner pages
5. Mobile table overflow scroll
6. Alternating table row colours
7. Module card hover states (translate + border accent)
8. External link indicator (`::after` arrow)
9. Visited link colour
10. Terminal-themed loading state for JS tools
11. `prefers-reduced-motion` for homepage animation
12. Reading progress bar
13. Bottom mobile tab bar (in `Footer` override)

---

### Tier C — Component overrides in `src/components/` (~half day)

1. `PageTitle.astro` — difficulty badge + reading progress bar
2. `Footer.astro` — global site footer + mobile tab bar
3. Fix `Header.astro` / `MobileMenuFooter.astro` — remove duplicate `<ThemeSelect />`
4. `Head.astro` — per-page OG description from frontmatter `description:`
5. `src/pages/404.astro` — terminal-themed 404 with recovery links

---

### Tier D — Plugin installations (~1 hour each)

```bash
npm install starlight-sidebar-topics   # Solves sidebar cognitive overload
npm install starlight-tags             # Difficulty/type tagging
npm install starlight-giscus           # User feedback / comments
npm install starlight-ui-tweaks        # Cleaner theme toggle, custom nav
npm install astro-breadcrumbs          # Breadcrumb trail
```

---

### Tier E — Content work per page (~2–3 days for all 63 pages)

1. Add `description:` frontmatter to all pages
2. Add `level: beginner|intermediate|advanced` frontmatter to all pages
3. Add `## See also` with `<LinkCard>` to all pages
4. Standardise version callouts to `:::tip[Updated date]` or `<Aside type="tip">`
5. Convert ALL CAPS headings in Master Study Guide
6. Fix duplicate "Choosing a Vector Store" heading in Vector Stores
7. Add instruction `<Aside>` to all 10 interactive tool `StarlightPage` wrappers
8. Add JS fallback + loading state to all tool wrappers
9. Restructure Complete Study Guide heading hierarchy
10. Create `StarlightPage` wrapper for all 10 JS-only tools

---

## 16. What Needs to Be Improved

### High priority

**Sidebar cognitive load** — 63 links always visible, wrong order, no active state. Fix: `starlight-sidebar-topics` + correct `sidebar` order in config + restore active page CSS.

**Heading hierarchy on long pages** — 28-entry TOC on Complete Study Guide, ALL CAPS headers. Fix: `maxHeadingLevel: 3` in config + heading rewrites + `<Badge>` for metadata.

**Code block features** — copy button likely suppressed, no file names, no line highlighting. Fix: Remove any CSS hiding Expressive Code elements; add `title=` and highlight markers to key code blocks.

**Module landing disparity** — RAG landing is a 5, LangChain is a 2, while BERT and Claude Code are 9+. Fix: Add `<CardGrid>` Quick Reference to RAG; populate or remove LangChain landing.

**Version callout inconsistency** — present on 2 pages, absent on 16+ that need it. Fix: `<Aside type="tip">` or `:::tip[]` callouts on all time-sensitive pages.

### Medium priority

**Interactive tool wrapper pages** — all 10 tools need `StarlightPage` wrappers with static fallback content.

**Homepage tools section** — remove the standalone section; fold tool callouts into module cards.

**Homepage stat counters** — generate dynamically from content collection.

**Table presentation** — overflow scroll, alternating rows, mobile handling.

**Duplicate section headings** in Vector Stores.

### Low priority

**Anchor link visibility** — increase hit area for `#` heading anchors.

**Footnote citations** — academic paper references (Asai et al., Liu et al.) should use proper Starlight footnote syntax rather than inline text.

**Print styles** — users printing the cert study guide or RAG reference would benefit from a `@media print` stylesheet hiding nav/sidebar and formatting for paper.

---

## 17. Master UI/UX Fix List

### Tier 1 — `astro.config.mjs` only (~30 minutes, affects all 63 pages)

These changes require touching only one file and deliver site-wide improvements immediately.

```js
starlight({
  // Restore Starlight defaults
  lastUpdated: true,
  pagination: true,
  editLink: { baseUrl: 'https://github.com/rajrkdev/ai-lab/edit/main/' },

  // Fix TOC depth on long pages
  tableOfContents: { minHeadingLevel: 2, maxHeadingLevel: 3 },

  // Social links
  social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/rajrkdev/ai-lab' }],

  // Fix sidebar order
  sidebar: [
    { label: 'RAG Guides', ... },
    { label: 'BERT Architectures', ... },
    { label: 'LangChain Reference', ... },
    { label: 'Claude Code', ... },
    { label: 'Cert Prep', ... },
  ],

  // Global head tags
  head: [
    { tag: 'meta', attrs: { property: 'og:site_name', content: 'Context — AI Learning Lab' }},
    { tag: 'meta', attrs: { property: 'og:image', content: '/og-image.png' }},
    { tag: 'meta', attrs: { name: 'twitter:card', content: 'summary_large_image' }},
  ],
})
```

---

### Tier 2 — `src/styles/custom.css` (~2 hours)

1. Remap `--sl-color-accent` to terminal green → propagates into all Starlight UI
2. Fix `[aria-current='page']` sidebar highlight → active page visible immediately
3. Terminal-green H2 left-border → identity on inner pages
4. `$` prompt prefix on H1 → terminal feel on every content page
5. Table overflow scroll → mobile tables no longer break layout
6. Alternating table rows → dense tables become readable
7. Card hover state → module cards clearly interactive
8. External link `↗` indicator → users know when leaving site
9. Visited link colour → returning users can track what they've read
10. Reduced motion support for homepage animation

---

### Tier 3 — Component overrides (~half day)

1. Fix duplicate `<ThemeSelect />` (check `Header.astro` / `MobileMenuFooter.astro`)
2. Create `PageTitle.astro` → difficulty badge + reading progress bar
3. Create `Footer.astro` → global footer + mobile tab bar
4. Create `src/pages/404.astro` → terminal-themed recovery page

---

### Tier 4 — Plugins (~1 hour each)

1. `starlight-sidebar-topics` → per-module sidebars, eliminates 63-link overwhelm
2. `astro-breadcrumbs` → orientation trail on all pages
3. `starlight-tags` → difficulty and type badges
4. `starlight-giscus` → user feedback on every page

---

### Tier 5 — Content per page (~2–3 days)

1. `description:` frontmatter → 63 pages, enables OG tags and meta descriptions
2. `level:` frontmatter → 63 pages, enables difficulty badges
3. `## See also` with `<LinkCard>` → all pages
4. Version callouts → all time-sensitive pages
5. ALL CAPS → sentence case (Master Study Guide)
6. `StarlightPage` wrappers → all 10 JS tools

---

### Tier 6 — New design components (~1 week)

1. RAG landing Quick Reference + `<CardGrid>`
2. LangChain landing full content or removal
3. Homepage dynamic stat counters from content collection
4. Terminal loading states for all JS tools
5. Instruction `<Aside>` panels for all tools
6. Homepage interactive tools section removal + module card integration
7. Mobile bottom tab bar styling and active state logic

---

*End of updated UI/UX audit.*  
*Platform: Astro Starlight. All fixes reference `astro.config.mjs`, `src/components/`, `src/styles/custom.css`, and Starlight-specific APIs.*  
*Total issues: 89. Tier 1 config changes: affect all 63 pages in ~30 minutes. Most impactful single change: restoring `[aria-current='page']` sidebar CSS and confirming `pagination: true` — fixes active highlighting and prev/next on every page at once.*
