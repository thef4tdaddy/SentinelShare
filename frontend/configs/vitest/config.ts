import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify('1.1.0'),
  },
  plugins: [svelte({ hot: false }), tailwindcss()],
  test: {
    environment: 'jsdom',
    setupFiles: [path.resolve(__dirname, '../../src/setupTest.ts')],
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'json-summary'],
    },
  },
  resolve: {
    conditions: ['browser'],
  },
});
