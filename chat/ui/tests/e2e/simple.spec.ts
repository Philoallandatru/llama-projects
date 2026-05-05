import { test, expect } from '@playwright/test';
import { navigateAndWaitForHydration } from '../helpers/wait-for-hydration';

test('simple navigation test', async ({ page }) => {
  await navigateAndWaitForHydration(page);

  // Check that page loaded
  const body = page.locator('body');
  await expect(body).toBeVisible();

  console.log('Page title:', await page.title());
  console.log('Page URL:', page.url());
});
