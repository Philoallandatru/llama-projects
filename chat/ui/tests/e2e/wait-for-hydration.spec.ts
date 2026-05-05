import { test, expect } from '@playwright/test';
import { navigateAndWaitForHydration } from '../helpers/wait-for-hydration';

test.describe('Wait for Client-Side Hydration', () => {
  test('should wait for page to fully hydrate', async ({ page }) => {
    await navigateAndWaitForHydration(page);

    console.log('Page title:', await page.title());
    console.log('Textareas:', await page.locator('textarea').count());
    console.log('Inputs:', await page.locator('input').count());
    console.log('Buttons:', await page.locator('button').count());

    // Take a screenshot to see what's rendered
    await page.screenshot({ path: 'hydrated-page.png', fullPage: true });

    // Verify chat interface is present
    const textareaCount = await page.locator('textarea').count();
    expect(textareaCount).toBeGreaterThan(0);
  });
});
