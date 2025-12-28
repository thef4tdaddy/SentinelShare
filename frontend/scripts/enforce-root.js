import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

const ALLOWED = new Set([
  '.gitignore',
  '.husky',
  '.prettierrc',
  '.prettierrc.js',
  'README.md',
  'commitlint.config.js',
  'configs',
  'dist',
  'eslint.config.js',
  'index.html',
  'node_modules',
  'package-lock.json',
  'package.json',
  'postcss.config.js',
  'public',
  'scripts',
  'src',
  'svelte.config.js', // Added
  'tailwind.config.js',
  'tsconfig.app.json',
  'tsconfig.json',
  'tsconfig.node.json',
  'vite.config.ts',
  'vitest.config.ts', // Added
  'coverage', // Vitest coverage
  '.ruff_cache', // Backend linting cache
  'CHANGELOG.md',
  'lhci-auth.cjs',
  'lighthouserc.json',
  'playwright.config.ts',
  'tests',
  'playwright-report',
  'test-results'
]);

// Ignored patterns (e.g., temporary files)
const IGNORED_EXTENSIONS = ['.log', '.DS_Store'];

console.log('🔍 Checking root directory cleanliness...');

try {
  const files = fs.readdirSync(rootDir);
  const unknownFiles = files.filter(file => {
    if (ALLOWED.has(file)) return false;
    if (IGNORED_EXTENSIONS.some(ext => file.endsWith(ext))) return false;
    return true;
  });

  if (unknownFiles.length > 0) {
    console.error('❌ Root directory contains unapproved files:');
    unknownFiles.forEach(f => console.error(`   - ${f}`));
    console.error('\nPlease move these files to frontend/configs/ or src/, or update scripts/enforce-root.js if necessary.');
    process.exit(1);
  }

  console.log('✅ Root directory is clean.');
} catch (err) {
  console.error('Failed to scan directory:', err);
  process.exit(1);
}
