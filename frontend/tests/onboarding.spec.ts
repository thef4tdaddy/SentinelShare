import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/SentinelShare/);
});

test('login page renders', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('button', { name: /Access Dashboard/i })).toBeVisible();
});

test('successful login flow (mocked)', async ({ page }) => {
  // Mock the login API
  await page.route('**/api/auth/login', async route => {
    await route.fulfill({ status: 200, body: JSON.stringify({ status: 'success' }) });
  });

  // Mock the "me" auth check API called on mount (return 401 to force login screen)
  await page.route('**/api/auth/me', async route => {
    await route.fulfill({ 
        status: 401, 
        body: JSON.stringify({ authenticated: false }) 
    });
  });

  // Mock dashboard stats to avoid loading errors
  await page.route('**/api/dashboard', async route => {
      await route.fulfill({
          status: 200,
          body: JSON.stringify({ stats: { total: 0, forwarded: 0, blocked: 0 }, recent: [] })
      });
  });

  await page.goto('/');
  await page.fill('input[type="password"]', 'any_password');
  await page.click('button[type="submit"]');

  // Verify we navigated to dashboard (by checking for a dashboard-specific element)
  await expect(page.getByText('Single-User Access')).not.toBeVisible();
  // Assuming the dashboard has a specific header or element. 
  // Based on file list, maybe "Activity Feed" or just checking URL?
  // Let's assume URL changes or "SentinelShare" stays but "Single-User Access" is gone.
  // Ideally check for a logout button or settings icon.
  await expect(page.getByRole('button', { name: /Settings/i })).toBeVisible({ timeout: 10000 });
});
