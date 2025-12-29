import { test, expect } from '@playwright/test';
import { execFileSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Helper to generate a valid action link signature using Backend logic
function generateActionSignature(cmd: string, arg: string, ts: string): string {
  const projectRoot = path.resolve(__dirname, '../../');
  
  const pythonScript = `
import sys
import os
import hashlib
import hmac

project_root = os.environ.get('APP_PROJECT_ROOT', '.')
sys.path.append(project_root)

# Setup Environment
from backend.security import generate_hmac_signature

cmd = os.environ.get('CMD')
arg = os.environ.get('ARG')
ts = os.environ.get('TS')

msg = f"{cmd}:{arg}:{ts}"
# We manually generate here or reuse security function if it matches logic
# security.py has generate_hmac_signature(msg)
print(generate_hmac_signature(msg))
`;

  try {
    const pythonExecutable = path.join(projectRoot, 'venv/bin/python3');
    const output = execFileSync(pythonExecutable, ['-c', pythonScript], {
      encoding: 'utf-8',
      env: { 
        ...process.env, 
        PYTHONPATH: projectRoot, 
        APP_PROJECT_ROOT: projectRoot,
        CMD: cmd,
        ARG: arg,
        TS: ts,
        SECRET_KEY: process.env.SECRET_KEY || "test-secret" // Ensure matches what backend uses in test
      }
    });
    return output.trim();
  } catch (e) {
    console.error("Failed to generate signature:", e);
    throw e;
  }
}

test.describe('Public Action Links', () => {

  test('Public Access: STOP action should work without login', async ({ page }) => {
    const cmd = "STOP";
    const arg = "spam.com";
    const ts = Math.floor(Date.now() / 1000).toString();
    const sig = generateActionSignature(cmd, arg, ts);

    // Navigate to the quick action URL
    await page.goto(`/api/actions/quick?cmd=${cmd}&arg=${arg}&ts=${ts}&sig=${sig}`);

    // Verify successful HTML response
    await expect(page.getByRole('heading', { name: 'Action Confirmed' })).toBeVisible();
    await expect(page.getByText('Successfully Blocked: spam.com')).toBeVisible();
  });

  test('Public Access: SETTINGS action should show preferences', async ({ page }) => {
    const cmd = "SETTINGS";
    const arg = "none";
    const ts = Math.floor(Date.now() / 1000).toString();
    const sig = generateActionSignature(cmd, arg, ts);

    await page.goto(`/api/actions/quick?cmd=${cmd}&arg=${arg}&ts=${ts}&sig=${sig}`);

    // Verify settings page
    await expect(page.getByRole('heading', { name: 'Current Settings' })).toBeVisible();
    // Should pass without 401
  });

  test('Public Access: Should fail with invalid signature', async ({ page }) => {
    const cmd = "STOP";
    const arg = "hacker.com";
    const ts = Math.floor(Date.now() / 1000).toString();
    const sig = "invalid-sig";

    const response = await page.goto(`/api/actions/quick?cmd=${cmd}&arg=${arg}&ts=${ts}&sig=${sig}`);
    
    // Expect 403 Forbidden (from router), NOT 401 (from middleware)
    expect(response?.status()).toBe(403);
  });
});
