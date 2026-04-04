// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import react from '@astrojs/react';

// https://astro.build/config
export default defineConfig({
	site: 'https://rajrkdev.github.io',
	base: '/ai-lab',
	integrations: [
		react(),
		starlight({
			title: 'AI Lab',
			customCss: ['./src/styles/custom.css'],
			head: [
				{
					tag: 'script',
					content: `
(function() {
  var NAV_KEY = 'sl-nav-collapsed';
  var TOC_KEY = 'sl-toc-collapsed';

  // SVG icons — chevron panel icons
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

  function setTocStyles(collapsed) {
    var toc = document.querySelector('.right-sidebar-container');
    if (!toc) return;
    if (collapsed) {
      toc.style.width = '0';
      toc.style.minWidth = '0';
      toc.style.overflow = 'hidden';
      toc.style.padding = '0';
    } else {
      toc.style.width = '';
      toc.style.minWidth = '';
      toc.style.overflow = '';
      toc.style.padding = '';
    }
  }

  function applyState() {
    var navCollapsed = localStorage.getItem(NAV_KEY) === '1';
    var tocCollapsed = localStorage.getItem(TOC_KEY) === '1';
    if (navCollapsed) document.documentElement.setAttribute('data-nav-collapsed', '');
    else document.documentElement.removeAttribute('data-nav-collapsed');
    if (tocCollapsed) document.documentElement.setAttribute('data-toc-collapsed', '');
    else document.documentElement.removeAttribute('data-toc-collapsed');
    setNavCssVar(navCollapsed);
    setTocStyles(tocCollapsed);
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
    });
    document.body.appendChild(navToggle);

    // Right TOC toggle — only if right sidebar exists on this page
    var tocContainer = document.querySelector('.right-sidebar-container');
    if (tocContainer) {
      var tocToggle = document.createElement('button');
      tocToggle.id = 'sl-toc-toggle';
      tocToggle.setAttribute('aria-label', 'Toggle table of contents');
      tocToggle.setAttribute('title', 'Toggle table of contents');
      var tocCollapsed = document.documentElement.hasAttribute('data-toc-collapsed');
      tocToggle.innerHTML = tocCollapsed ? ICON_RPANEL_OPEN : ICON_RPANEL_CLOSE;
      tocToggle.addEventListener('click', function() {
        var collapsed = document.documentElement.toggleAttribute('data-toc-collapsed');
        tocToggle.innerHTML = collapsed ? ICON_RPANEL_OPEN : ICON_RPANEL_CLOSE;
        setTocStyles(collapsed);
        localStorage.setItem(TOC_KEY, collapsed ? '1' : '0');
      });
      document.body.appendChild(tocToggle);
      setTocStyles(tocCollapsed);
    }
  }

  function setup() {
    ['sl-nav-toggle','sl-toc-toggle'].forEach(function(id) {
      var el = document.getElementById(id);
      if (el) el.remove();
    });
    applyState();
    injectToggles();
  }

  // Apply state immediately to prevent flash before DOM ready
  if (localStorage.getItem(NAV_KEY) === '1') document.documentElement.setAttribute('data-nav-collapsed', '');
  if (localStorage.getItem(TOC_KEY) === '1') document.documentElement.setAttribute('data-toc-collapsed', '');

  document.addEventListener('DOMContentLoaded', setup);
  document.addEventListener('astro:page-load', setup);
})();
					`,
				},
			],
			sidebar: [
				{ label: 'Documentation', autogenerate: { directory: 'docs' } },
				{ label: 'Interactive Diagrams', autogenerate: { directory: 'diagrams' } },
				{ label: 'RAG Guides', autogenerate: { directory: 'rag' } },
				{ label: 'BERT Architectures', autogenerate: { directory: 'bert' } },
				{ label: 'LangChain Reference', autogenerate: { directory: 'langchain' } },
				{ label: 'Cert Prep', autogenerate: { directory: 'cert' } },
				{ label: 'Prompts & Templates', autogenerate: { directory: 'prompts' } },
			],
		}),
	],
});
