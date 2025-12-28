import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';
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
  const backendPath = path.join(projectRoot, 'backend');
  const venvActivate = `source ${path.join(projectRoot, 'venv/bin/activate')}`;
  
  // Python script to generate token
  const pythonScript = `
import sys
import os
sys.path.append('${projectRoot}')

from backend.security import generate_dashboard_token
print(generate_dashboard_token('${email}'))
`;

  try {
    // Run python command
    const output = execSync(`${venvActivate} && python3 -c "${pythonScript}"`, {
      shell: '/bin/bash', 
      encoding: 'utf-8',
      env: { ...process.env, PYTHONPATH: backendPath, SECRET_KEY: process.env.SECRET_KEY }
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
    
    const loginButton = page.getByRole('button', { name: /Access Dashboard/i });
    if (await loginButton.isVisible()) {
        await page.getByPlaceholder('Enter dashboard password...').fill('testpass');
        await loginButton.click();
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
