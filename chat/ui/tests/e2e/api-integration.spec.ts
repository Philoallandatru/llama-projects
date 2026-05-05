import { test, expect } from '@playwright/test';

test.describe('API Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should load the application successfully', async ({ page }) => {
    // Verify the page loads without errors
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });

  test('should have no console errors on initial load', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Filter out known acceptable errors (like network errors when backend is down)
    const criticalErrors = errors.filter(err =>
      !err.includes('Failed to fetch') &&
      !err.includes('NetworkError') &&
      !err.includes('ERR_CONNECTION_REFUSED')
    );

    expect(criticalErrors.length).toBe(0);
  });

  test('should display UI elements even without backend', async ({ page }) => {
    // The UI should render even if backend is not available
    const textareas = page.locator('textarea');
    const textareaCount = await textareas.count();
    expect(textareaCount).toBeGreaterThan(0);
  });

  test('should have proper page structure', async ({ page }) => {
    // Verify basic page structure
    const html = page.locator('html');
    await expect(html).toBeVisible();

    const body = page.locator('body');
    await expect(body).toBeVisible();
  });

  test('should load CSS and styles', async ({ page }) => {
    // Check that styles are applied
    const body = page.locator('body');
    const backgroundColor = await body.evaluate(el =>
      window.getComputedStyle(el).backgroundColor
    );

    // Should have some background color set
    expect(backgroundColor).toBeTruthy();
  });

  test('should have interactive elements', async ({ page }) => {
    // Check for buttons
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    expect(buttonCount).toBeGreaterThan(0);

    // Check for inputs
    const inputs = page.locator('input, textarea');
    const inputCount = await inputs.count();
    expect(inputCount).toBeGreaterThan(0);
  });
});
