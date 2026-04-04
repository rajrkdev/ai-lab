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

  // --sl-content-inline-start is set on body[data-has-sidebar] by Starlight.
  // We must override it on body directly to make content rescale on toggle.
  function setNavCssVar(collapsed) {
    if (collapsed) {
      document.body.style.setProperty('--sl-content-inline-start', '0rem');
    } else {
      document.body.style.removeProperty('--sl-content-inline-start');
    }
  }

  // right sidebar width is driven by a CSS var on .right-sidebar-container
  function setTocCssVar(collapsed) {
    var toc = document.querySelector('.right-sidebar-container');
    if (!toc) return;
    if (collapsed) {
      toc.style.width = '0';
      toc.style.minWidth = '0';
      toc.style.overflow = 'hidden';
      toc.style.padding = '0';
      toc.style.transition = 'width 0.25s ease';
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
    if (tocCollapsed) document.documentElement.setAttribute('data-toc-collapsed', '');
    setNavCssVar(navCollapsed);
    setTocCssVar(tocCollapsed);
  }

  function injectToggles() {
    if (document.getElementById('sl-nav-toggle')) return;

    var navToggle = document.createElement('button');
    navToggle.id = 'sl-nav-toggle';
    navToggle.setAttribute('aria-label', 'Toggle navigation sidebar');
    navToggle.setAttribute('title', 'Toggle navigation');
    navToggle.textContent = document.documentElement.hasAttribute('data-nav-collapsed') ? '›' : '‹';
    navToggle.addEventListener('click', function() {
      var collapsed = document.documentElement.toggleAttribute('data-nav-collapsed');
      navToggle.textContent = collapsed ? '›' : '‹';
      setNavCssVar(collapsed);
      localStorage.setItem(NAV_KEY, collapsed ? '1' : '0');
    });
    document.body.appendChild(navToggle);

    // Only show TOC toggle if there is a right sidebar on this page
    var tocContainer = document.querySelector('.right-sidebar-container');
    if (tocContainer) {
      var tocToggle = document.createElement('button');
      tocToggle.id = 'sl-toc-toggle';
      tocToggle.setAttribute('aria-label', 'Toggle table of contents');
      tocToggle.setAttribute('title', 'Toggle table of contents');
      tocToggle.textContent = document.documentElement.hasAttribute('data-toc-collapsed') ? '‹' : '›';
      tocToggle.addEventListener('click', function() {
        var collapsed = document.documentElement.toggleAttribute('data-toc-collapsed');
        tocToggle.textContent = collapsed ? '‹' : '›';
        setTocCssVar(collapsed);
        localStorage.setItem(TOC_KEY, collapsed ? '1' : '0');
      });
      document.body.appendChild(tocToggle);
      // Apply current state to the newly found container
      setTocCssVar(document.documentElement.hasAttribute('data-toc-collapsed'));
    }
  }

  applyState();
  document.addEventListener('DOMContentLoaded', function() { applyState(); injectToggles(); });
  document.addEventListener('astro:page-load', function() {
    // Re-inject toggles (new DOM after navigation)
    var old = document.getElementById('sl-nav-toggle');
    if (old) old.remove();
    var oldToc = document.getElementById('sl-toc-toggle');
    if (oldToc) oldToc.remove();
    applyState();
    injectToggles();
  });
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
