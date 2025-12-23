import js from '@eslint/js';
import globals from 'globals';
import tseslint from 'typescript-eslint';
import svelte from 'eslint-plugin-svelte';
import architectureRules from './eslint-rules/architecture.js';
import strictTypingRules from './eslint-rules/strict-typing.js';
import exclusions from './config-modules/exclusions.js';

export default tseslint.config(
  { ignores: ['dist', '.svelte-kit'] },
  
  // Base configs
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...svelte.configs['flat/recommended'],

  // App-wide settings
  {
    languageOptions: {
      ecmaVersion: 2020,
      globals: {
        ...globals.browser,
        __APP_VERSION__: 'readonly',
      },
    },
  },

  // Node Scripts
  {
    files: ['scripts/**/*.js', '*.config.js'],
    languageOptions: {
      globals: {
        ...globals.node,
      }
    }
  },

  // Svelte-specific parser setup
  {
    files: ['**/*.svelte'],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
        extraFileExtensions: ['.svelte'],
      },
    },
  },
  {
    files: ['src/components/EmailTemplateEditor.svelte'],
    rules: {
      'svelte/no-at-html-tags': 'off'
    }
  },

  // Custom Rules (Shared)
  {
    files: ['**/*.{ts,tsx,svelte}'],
    rules: {
      ...architectureRules,
      ...strictTypingRules,
      'svelte/no-at-html-tags': 'warn', 
      ...exclusions,
    },
  },

  // Architecture enforcement block
  {
    files: ['src/pages/**/*.{ts,tsx,svelte}', 'src/components/**/*.{ts,tsx,svelte}'],
    rules: {
      ...architectureRules,
    },
  },
);
