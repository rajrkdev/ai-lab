// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://rajrkdev.github.io',
	base: '/ai-lab',
	integrations: [
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

  function applyState() {
    if (localStorage.getItem(NAV_KEY) === '1') {
      document.documentElement.setAttribute('data-nav-collapsed', '');
    }
    if (localStorage.getItem(TOC_KEY) === '1') {
      document.documentElement.setAttribute('data-toc-collapsed', '');
    }
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
      localStorage.setItem(NAV_KEY, collapsed ? '1' : '0');
    });
    document.body.appendChild(navToggle);

    var tocToggle = document.createElement('button');
    tocToggle.id = 'sl-toc-toggle';
    tocToggle.setAttribute('aria-label', 'Toggle table of contents');
    tocToggle.setAttribute('title', 'Toggle table of contents');
    tocToggle.textContent = document.documentElement.hasAttribute('data-toc-collapsed') ? '‹' : '›';
    tocToggle.addEventListener('click', function() {
      var collapsed = document.documentElement.toggleAttribute('data-toc-collapsed');
      tocToggle.textContent = collapsed ? '‹' : '›';
      localStorage.setItem(TOC_KEY, collapsed ? '1' : '0');
    });
    document.body.appendChild(tocToggle);
  }

  // Apply persisted state immediately to avoid flash
  applyState();

  // Inject buttons after DOM ready, and on each Astro page navigation
  document.addEventListener('DOMContentLoaded', injectToggles);
  document.addEventListener('astro:page-load', function() {
    applyState();
    injectToggles();
  });
})();
					`,
				},
			],
			sidebar: [
				{ label: 'Documentation', autogenerate: { directory: 'docs' } },
				{ label: 'RAG Guides', autogenerate: { directory: 'rag' } },
				{ label: 'BERT Architectures', autogenerate: { directory: 'bert' } },
				{ label: 'LangChain Reference', autogenerate: { directory: 'langchain' } },
				{ label: 'Cert Prep', autogenerate: { directory: 'cert' } },
				{ label: 'Prompts & Templates', autogenerate: { directory: 'prompts' } },
			],
		}),
	],
});
