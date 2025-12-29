import { test, expect } from '@playwright/test';
import { execFileSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Helper to mint a token using the Backend's own logic
// This ensures we test integration with the real security.py
function mintAuthToken(email: string): string {
  // Assume we are running from 'frontend/tests/' directory (where this file is), 
  // so actual backend code is at '../../backend' relative to this file.
  // BUT the venv is at PROJECT_ROOT/venv (so '../../venv').
  // Let's rely on absolute paths resolved from __dirname.
  
  const projectRoot = path.resolve(__dirname, '../../');
  
  // Python script to generate token
  const pythonScript = `
import sys
import os
# Use environment variables to avoid shell injection / interpolation risks
project_root = os.environ.get('APP_PROJECT_ROOT', '.')
email = os.environ.get('APP_TEST_EMAIL', '')

sys.path.append(project_root)

from backend.security import generate_dashboard_token
print(generate_dashboard_token(email))
`;

  try {
    const pythonExecutable = path.join(projectRoot, 'venv/bin/python3');
    // Use execFileSync to avoid shell injection via interpolated strings
    const output = execFileSync(pythonExecutable, ['-c', pythonScript], {
      encoding: 'utf-8',
      env: { 
        ...process.env, 
        PYTHONPATH: projectRoot, 
        SECRET_KEY: process.env.SECRET_KEY,
        APP_PROJECT_ROOT: projectRoot,
        APP_TEST_EMAIL: email
      }
    });
    return output.trim();
  } catch (e) {
    console.error("Failed to mint token:", e);
    throw e;
  }
}

test.describe('Token Authentication System', () => {

  test('Admin/Sender Side: should login via password', async ({ page }) => {
    await page.goto('/');
    
    // Wait for app to load - expect login form on fresh start
    const loginInput = page.getByPlaceholder('Enter dashboard password...');
    try {
        await loginInput.waitFor({ state: 'visible', timeout: 5000 });
        // If visible, perform login
        await loginInput.fill('testpass');
        await page.getByRole('button', { name: /Access Dashboard/i }).click();
    } catch {
        // If timeout, assume we might be logged in or page is stuck.
        // Proceed to check dashboard to fail with a clear error if neither is found.
        console.log('Login form not detected, checking for dashboard directly...');
    }
    
    // Verify Admin Access via Dashboard heading
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 10000 });
  });

  test('Receiver Side: should login successfully with a valid token containing special chars', async ({ page }) => {
    // 1. Generate a token for a user with '+' (gmail alias style)
    const testEmail = 'playwright+test@example.com';
    const rawToken = mintAuthToken(testEmail);
    
    console.log(`Minted Token for ${testEmail}: ${rawToken}`);

    // 2. Simulate the Email Link behavior (URL encoded)
    const safeToken = encodeURIComponent(rawToken);
    
    // 3. Navigate as Receiver
    await page.goto(`/?token=${safeToken}`);

    // 4. Verify Receiver Access via Sendee heading
    // Note: Navbar is hidden for sendee view for better security/UX
    await expect(page.getByRole('heading', { name: 'Forwarding Preferences' })).toBeVisible({ timeout: 10000 });
  });

  test('should fail with an invalid token', async ({ page }) => {
     await page.goto('/?token=invalid-garbage-token');
     // Should see Access Denied error on the page
     await expect(page.getByText('Access Denied')).toBeVisible();
  });
});
