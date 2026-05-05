import { test, expect } from '@playwright/test';

test('simple navigation test', async ({ page }) => {
  // Use full URL instead of relative path
  await page.goto('http://localhost:3000');
  await page.waitForLoadState('networkidle');

  // Check that page loaded
  const body = page.locator('body');
  await expect(body).toBeVisible();

  console.log('Page title:', await page.title());
  console.log('Page URL:', page.url());
});
