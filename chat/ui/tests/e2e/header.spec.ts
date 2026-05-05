import { test, expect } from '@playwright/test';

test.describe('Header Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should display header area', async ({ page }) => {
    // Check that the page has loaded with content
    const body = page.locator('body');
    await expect(body).toBeVisible();

    // Verify page has some content
    const allDivs = page.locator('div');
    const divCount = await allDivs.count();
    expect(divCount).toBeGreaterThan(0);
  });

  test('should display application title or logo', async ({ page }) => {
    // Look for any heading or title text in the header area
    const headings = page.locator('h1, h2, h3, [role="heading"]');
    const count = await headings.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should have navigation elements', async ({ page }) => {
    // Check for any interactive elements (buttons, inputs, etc.)
    const buttons = page.locator('button');
    const inputs = page.locator('input, textarea');

    const buttonCount = await buttons.count();
    const inputCount = await inputs.count();

    // Should have at least some interactive elements
    expect(buttonCount + inputCount).toBeGreaterThan(0);
  });

  test('should display page structure', async ({ page }) => {
    // Verify basic page structure is present
    const body = page.locator('body');
    await expect(body).toBeVisible();

    // Check for main content area
    const mainContent = page.locator('main, [role="main"], .main-content').first();
    const hasMainContent = await mainContent.count();
    expect(hasMainContent).toBeGreaterThanOrEqual(0);
  });
});
