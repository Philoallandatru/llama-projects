import { test, expect } from '@playwright/test';

test('debug baseURL', async ({ page }) => {
  console.log('Attempting to navigate with full URL...');
  await page.goto('http://localhost:3000/deployments/chat/ui', { timeout: 30000 });
  await page.waitForLoadState('networkidle');

  console.log('Page title:', await page.title());
  console.log('Page URL:', page.url());

  const body = page.locator('body');
  await expect(body).toBeVisible();
});
