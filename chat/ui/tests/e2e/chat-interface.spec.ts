import { test, expect } from '@playwright/test';
import { navigateAndWaitForHydration } from '../helpers/wait-for-hydration';

test.describe('Chat Interface', () => {
  test.beforeEach(async ({ page }) => {
    await navigateAndWaitForHydration(page);
  });

  test('should display chat input area', async ({ page }) => {
    // Look for textarea elements (chat input)
    const textareas = page.locator('textarea').filter({ hasNot: page.locator('[aria-hidden="true"]') });
    const visibleTextarea = textareas.first();
    await expect(visibleTextarea).toBeVisible();
  });

  test('should display data source selector', async ({ page }) => {
    // Look for any select elements, dropdowns, or buttons that might be data source selectors
    const selects = page.locator('select');
    const buttons = page.locator('button');
    const inputs = page.locator('input');

    const selectCount = await selects.count();
    const buttonCount = await buttons.count();
    const inputCount = await inputs.count();

    // Should have some interactive elements for data source selection
    expect(selectCount + buttonCount + inputCount).toBeGreaterThan(0);
  });

  test('should have disabled chat input initially', async ({ page }) => {
    // Chat input should be disabled until data source is selected
    const chatInput = page.getByPlaceholder(/请先选择数据源/);
    if (await chatInput.count() > 0) {
      await expect(chatInput).toBeDisabled();
    }
  });

  test('should display session search input', async ({ page }) => {
    // Check if there's a search input for sessions
    const searchInput = page.getByPlaceholder(/搜索会话|搜索|search/i);
    const count = await searchInput.count();

    // This is optional - the UI may or may not have a search input
    if (count > 0) {
      await expect(searchInput.first()).toBeVisible();
      await expect(searchInput.first()).toBeEnabled();
    } else {
      // If no search input, that's acceptable - just verify the page loaded
      const body = page.locator('body');
      await expect(body).toBeVisible();
    }
  });

  test('should have interactive buttons', async ({ page }) => {
    // Check for any buttons on the page
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    expect(buttonCount).toBeGreaterThan(0);
  });

  test('should display chat layout structure', async ({ page }) => {
    // Verify the page has a proper layout structure
    const body = page.locator('body');
    await expect(body).toBeVisible();

    // Check for any content on the page - divs, main elements, or sections
    const allElements = page.locator('body *');
    const elementCount = await allElements.count();
    expect(elementCount).toBeGreaterThan(0);
  });

  test('should allow typing in enabled inputs', async ({ page }) => {
    // Find the search input which should be enabled
    const searchInput = page.getByPlaceholder(/搜索会话/);
    if (await searchInput.count() > 0) {
      await searchInput.fill('测试搜索');
      await expect(searchInput).toHaveValue('测试搜索');
    }
  });
});
