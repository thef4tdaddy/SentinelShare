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
