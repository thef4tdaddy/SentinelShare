import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to root first to handle login properly
    await page.goto('/');
    
    // Check if Login is present (Auth enabled)
    // Wait for EITHER login form OR dashboard/navbar to be stable
    // 'nav' exists if authed (Desktop or Mobile). 'form' exists if login needed.
    await expect(page.locator('nav').or(page.locator('form'))).toBeVisible({ timeout: 10000 });

    const loginButton = page.getByRole('button', { name: /Access Dashboard/i });
    if (await loginButton.isVisible()) {
        await page.getByPlaceholder('Enter dashboard password...').fill('testpass');
        await loginButton.click();
        // Wait for dashboard or navigation
        await expect(page.locator('nav')).toBeVisible();
    }
    
    // Now navigate to Settings using Navbar (Button)
    // Wait for network idle to ensure nav is rendered
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500); // Allow for transitions
    
    // Specifically target the visible Settings button in the nav
    // Use a relaxed name to account for icons/whitespace, and filter by visibility
    const settingsButton = page.getByRole('button', { name: /Settings/i }).filter({ visible: true });
    await expect(settingsButton.first()).toBeVisible({ timeout: 10000 });
    await settingsButton.first().click();
    
    // Verify we are on the Settings page by checking for the page heading specifically
    await expect(page.getByRole('heading', { name: 'Settings', exact: true })).toBeVisible();
  });

  test('should load settings page', async ({ page }) => {
    await expect(page).toHaveTitle(/SentinelShare/);
    // Heading check is already in beforeEach, but here for completeness
    await expect(page.getByRole('heading', { name: 'Settings', exact: true })).toBeVisible();
  });

  test('should display Run Now button', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Run Now' })).toBeVisible();
  });
});
