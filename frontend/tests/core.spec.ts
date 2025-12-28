import { test, expect } from '@playwright/test';

test.describe('Core Pages Smoke Test', () => {
  test('should load dashboard', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/SentinelShare/);
  });

  // Assuming /login route exists, if not we will adjust later
  // test('should load login page', async ({ page }) => {
  //   await page.goto('/login');
  //   await expect(page).toHaveTitle(/Login/);
  // });
});
