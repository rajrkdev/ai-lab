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
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/rajrkdev/ai-lab' }],
			sidebar: [
				{ label: 'Documentation', autogenerate: { directory: 'docs' } },
				{ label: 'Langchain Reference', autogenerate: { directory: 'langchain' } },
				{ label: 'RAG Guides', autogenerate: { directory: 'rag' } },
				{ label: 'BERT Architectures', autogenerate: { directory: 'bert' } },
				{ label: 'Cert Prep', autogenerate: { directory: 'cert' } },
				{ label: 'Prompts & Templates', autogenerate: { directory: 'prompts' } },
				{ label: 'Reference', autogenerate: { directory: 'reference' } },
			],
		}),
	],
});
