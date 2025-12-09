import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig({
  plugins: [svelte({ hot: false }), tailwindcss()],
  test: {
    environment: 'jsdom',
    setupFiles: [path.resolve(__dirname, '../../src/setupTest.ts')],
    globals: true,
  },
  resolve: {
    conditions: ['browser'],
  },
});
