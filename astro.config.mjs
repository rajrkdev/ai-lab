// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import react from '@astrojs/react';
import starlightSidebarTopics from 'starlight-sidebar-topics';
import starlightTags from 'starlight-tags';

// https://astro.build/config
export default defineConfig({
	site: 'https://rajrkdev.github.io',
	base: '/ai-lab',
	integrations: [
		react(),
		starlight({
			title: 'Context',
			customCss: ['./src/styles/custom.css'],
			pagination: true,
			tableOfContents: { minHeadingLevel: 2, maxHeadingLevel: 3 },
			components: {
				PageTitle: './src/components/PageTitle.astro',
				Footer: './src/components/Footer.astro',
			},
			plugins: [
				starlightSidebarTopics(
					[
						{
							label: 'RAG Guides',
							link: '/rag/',
							icon: 'rocket',
							items: [{ label: 'RAG Guides', autogenerate: { directory: 'rag' }, collapsed: false }],
						},
						{
							label: 'BERT Architectures',
							link: '/bert/',
							icon: 'binoculars',
							items: [{ label: 'BERT Architectures', autogenerate: { directory: 'bert' }, collapsed: false }],
						},
						{
							label: 'LangChain Reference',
							link: '/langchain/',
							icon: 'puzzle',
							items: [{ label: 'LangChain Reference', autogenerate: { directory: 'langchain' }, collapsed: false }],
						},
						{
							label: 'Claude Code',
							link: '/claude-code/',
							icon: 'setting',
							items: [{ label: 'Claude Code', autogenerate: { directory: 'claude-code' }, collapsed: false }],
						},
						{
							label: 'Cert Prep',
							link: '/cert/',
							icon: 'star',
							items: [{ label: 'Cert Prep', autogenerate: { directory: 'cert' }, collapsed: false }],
						},
					],
					// Exclude tag pages (starlight-tags) and 404 from topic association
					{ exclude: ['/tags', '/tags/**', '/404'] },
				),
				starlightTags({ sidebar: false }),
			],
			head: [
				{
					tag: 'meta',
					attrs: { name: 'robots', content: 'noindex, nofollow, noarchive, nosnippet, noimageindex' },
				},
				{
					tag: 'meta',
					attrs: { name: 'googlebot', content: 'noindex, nofollow, noarchive, nosnippet, noimageindex' },
				},
				{
					tag: 'meta',
					attrs: { name: 'bingbot', content: 'noindex, nofollow' },
				},
				{
					tag: 'script',
					content: `
(function() {
  var NAV_KEY = 'sl-nav-collapsed';
  var TOC_KEY = 'sl-toc-collapsed';

  // SVG icons â€” chevron panel icons
  var ICON_PANEL_CLOSE = '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18"/><polyline points="16 15 13 12 16 9"/></svg>';
  var ICON_PANEL_OPEN  = '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18"/><polyline points="13 9 16 12 13 15"/></svg>';
  var ICON_RPANEL_CLOSE = '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M15 3v18"/><polyline points="8 9 11 12 8 15"/></svg>';
  var ICON_RPANEL_OPEN  = '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M15 3v18"/><polyline points="11 15 8 12 11 9"/></svg>';

  function setNavCssVar(collapsed) {
    if (collapsed) {
      document.body.style.setProperty('--sl-content-inline-start', '0rem');
    } else {
      document.body.style.removeProperty('--sl-content-inline-start');
    }
  }

  function dispatchResize() {
    // Let React components (and any resize listeners) reflow after sidebar change
    setTimeout(function() { window.dispatchEvent(new Event('resize')); }, 260);
  }

  function applyState() {
    var navCollapsed = localStorage.getItem(NAV_KEY) === '1';
    var tocCollapsed = localStorage.getItem(TOC_KEY) === '1';
    if (navCollapsed) document.documentElement.setAttribute('data-nav-collapsed', '');
    else document.documentElement.removeAttribute('data-nav-collapsed');
    if (tocCollapsed) document.documentElement.setAttribute('data-toc-collapsed', '');
    else document.documentElement.removeAttribute('data-toc-collapsed');
    setNavCssVar(navCollapsed);
  }

  function injectToggles() {
    // Left nav toggle
    var navToggle = document.createElement('button');
    navToggle.id = 'sl-nav-toggle';
    navToggle.setAttribute('aria-label', 'Toggle navigation sidebar');
    navToggle.setAttribute('title', 'Toggle navigation sidebar');
    var navCollapsed = document.documentElement.hasAttribute('data-nav-collapsed');
    navToggle.innerHTML = navCollapsed ? ICON_PANEL_OPEN : ICON_PANEL_CLOSE;
    navToggle.addEventListener('click', function() {
      var collapsed = document.documentElement.toggleAttribute('data-nav-collapsed');
      navToggle.innerHTML = collapsed ? ICON_PANEL_OPEN : ICON_PANEL_CLOSE;
      setNavCssVar(collapsed);
      localStorage.setItem(NAV_KEY, collapsed ? '1' : '0');
      dispatchResize();
    });
    document.body.appendChild(navToggle);

    // Right TOC toggle â€” always inject; CSS hides it when no right sidebar
    var tocToggle = document.createElement('button');
    tocToggle.id = 'sl-toc-toggle';
    tocToggle.setAttribute('aria-label', 'Toggle table of contents');
    tocToggle.setAttribute('title', 'Toggle table of contents');
    var tocCollapsed = document.documentElement.hasAttribute('data-toc-collapsed');
    tocToggle.innerHTML = tocCollapsed ? ICON_RPANEL_OPEN : ICON_RPANEL_CLOSE;
    tocToggle.addEventListener('click', function() {
      var collapsed = document.documentElement.toggleAttribute('data-toc-collapsed');
      tocToggle.innerHTML = collapsed ? ICON_RPANEL_OPEN : ICON_RPANEL_CLOSE;
      localStorage.setItem(TOC_KEY, collapsed ? '1' : '0');
      dispatchResize();
    });
    document.body.appendChild(tocToggle);
  }

  // â”€â”€ TOC scroll sync â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  // Starlight's IntersectionObserver updates aria-current on TOC links but never
  // calls scrollIntoView, so active items below the visible TOC area are invisible.
  // This MutationObserver scrolls the active link into view whenever it changes.
  var tocSyncObserver = null;
  function setupTocScrollSync() {
    if (tocSyncObserver) { tocSyncObserver.disconnect(); tocSyncObserver = null; }
    var tocEl = document.querySelector('starlight-toc');
    if (!tocEl) return;
    var tocContainer = tocEl.closest('.right-sidebar-container');
    tocSyncObserver = new MutationObserver(function() {
      var active = tocEl.querySelector('a[aria-current="true"]');
      if (!active) return;
      if (tocContainer) {
        // Scroll the sticky container so the active link stays in view
        var cRect = tocContainer.getBoundingClientRect();
        var aRect = active.getBoundingClientRect();
        var visible = aRect.top >= cRect.top && aRect.bottom <= cRect.bottom;
        if (!visible) {
          active.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
      } else {
        active.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    });
    tocSyncObserver.observe(tocEl, {
      subtree: true, attributes: true, attributeFilter: ['aria-current']
    });
  }

  // â”€â”€ Left nav scroll sync â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  // Scroll the left sidebar so the active page link is visible.
  // Starlight marks the current page link with aria-current="page".
  // We manually adjust scrollTop so only the sidebar pane scrolls, not the page.
  function scrollNavToActive() {
    var pane = document.querySelector('.sidebar-pane');
    if (!pane) return;
    var active = pane.querySelector('a[aria-current="page"]');
    if (!active) return;
    var paneRect = pane.getBoundingClientRect();
    var activeRect = active.getBoundingClientRect();
    var isVisible = activeRect.top >= paneRect.top && activeRect.bottom <= paneRect.bottom;
    if (!isVisible) {
      // Center the active link within the pane's visible scroll area
      var relativeTop = activeRect.top - paneRect.top + pane.scrollTop;
      pane.scrollTop = Math.max(0, relativeTop - pane.clientHeight / 2 + active.offsetHeight / 2);
    }
  }

  function setup() {
    ['sl-nav-toggle','sl-toc-toggle'].forEach(function(id) {
      var el = document.getElementById(id);
      if (el) el.remove();
    });
    applyState();
    injectToggles();
    // Scroll left nav to show active page link (run immediately + after short delay)
    scrollNavToActive();
    setTimeout(scrollNavToActive, 200);
    // Delay slightly so starlight-toc custom element can finish its own init
    setTimeout(setupTocScrollSync, 300);
  }

  // Apply state immediately to prevent flash before DOM ready
  if (localStorage.getItem(NAV_KEY) === '1') document.documentElement.setAttribute('data-nav-collapsed', '');
  if (localStorage.getItem(TOC_KEY) === '1') document.documentElement.setAttribute('data-toc-collapsed', '');

  document.addEventListener('DOMContentLoaded', setup);
  document.addEventListener('astro:page-load', setup);

  // â”€â”€ Reading progress bar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  // Injected here (global script) so it works on every page without
  // depending on any Starlight component override being rendered.
  var progressBar = null;
  var scrollHandler = null;

  function setupProgressBar() {
    // Remove any listener from a previous page navigation
    if (progressBar && scrollHandler) {
      window.removeEventListener('scroll', scrollHandler);
    }

    // Create the bar element once; reuse on subsequent navigations
    progressBar = document.getElementById('reading-progress');
    if (!progressBar) {
      progressBar = document.createElement('div');
      progressBar.id = 'reading-progress';
      progressBar.setAttribute('role', 'progressbar');
      progressBar.setAttribute('aria-valuenow', '0');
      progressBar.setAttribute('aria-valuemin', '0');
      progressBar.setAttribute('aria-valuemax', '100');
      progressBar.setAttribute('aria-label', 'Reading progress');
      document.body.appendChild(progressBar);
    }

    // Reset width on new page
    progressBar.style.width = '0%';

    scrollHandler = function() {
      var scroll = window.scrollY;
      var height = document.body.scrollHeight - window.innerHeight;
      var pct = height > 0 ? Math.round((scroll / height) * 100) : 0;
      progressBar.style.width = pct + '%';
      progressBar.setAttribute('aria-valuenow', String(pct));
    };

    window.addEventListener('scroll', scrollHandler, { passive: true });
  }

  document.addEventListener('DOMContentLoaded', setupProgressBar);
  document.addEventListener('astro:page-load', setupProgressBar);
})();
					`,
				},
			],

		}),
	],
});

