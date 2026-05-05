import { test, expect } from '@playwright/test';

test('simple navigation test', async ({ page }) => {
  // Use relative path to leverage baseURL
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Check that page loaded
  const body = page.locator('body');
  await expect(body).toBeVisible();

  console.log('Page title:', await page.title());
  console.log('Page URL:', page.url());
});
