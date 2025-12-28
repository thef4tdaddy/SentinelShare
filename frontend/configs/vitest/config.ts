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
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: ['tests/**', '**/node_modules/**', '**/dist/**', '**/cypress/**', '**/.{idea,git,cache,output,temp}/**'],
  },
  resolve: {
    conditions: ['browser'],
  },
});
