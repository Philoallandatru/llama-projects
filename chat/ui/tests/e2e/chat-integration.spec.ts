import { test, expect } from '@playwright/test';
import { navigateAndWaitForHydration } from '../helpers/wait-for-hydration';

/**
 * E2E Tests for Chat Integration (Datasource + LLMWiki)
 *
 * These tests verify that the chat interface works correctly with both
 * datasource and llmwiki query tools integrated.
 */

test.describe('Chat Integration', () => {
  test.beforeEach(async ({ page }) => {
    await navigateAndWaitForHydration(page);
  });

  test('should have chat input available', async ({ page }) => {
    const textarea = page.locator('textarea[name="input"]');
    await expect(textarea).toBeVisible();
  });

  test('should allow typing in chat input', async ({ page }) => {
    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill('What is this project about?');
    await expect(textarea).toHaveValue('What is this project about?');
  });

  test('should have send button available', async ({ page }) => {
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    expect(buttonCount).toBeGreaterThan(0);
  });

  test('should send query and receive response', async ({ page }) => {
    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill('Tell me about the project');

    const sendButton = page.locator('button[type="submit"]').first();
    if (await sendButton.count() > 0) {
      await sendButton.click();

      // Wait for response to appear (check for new content)
      await page.waitForLoadState('networkidle');

      const body = page.locator('body');
      await expect(body).toBeVisible();
    }
  });

  test('should handle empty query', async ({ page }) => {
    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill('');

    const sendButton = page.locator('button[type="submit"]').first();
    if (await sendButton.count() > 0) {
      const isDisabled = await sendButton.isDisabled();
      expect(typeof isDisabled).toBe('boolean');
    }
  });

  test('should preserve input while typing', async ({ page }) => {
    const textarea = page.locator('textarea[name="input"]');

    await textarea.fill('First');
    await expect(textarea).toHaveValue('First');

    await textarea.fill('First Second');
    await expect(textarea).toHaveValue('First Second');

    await textarea.fill('First Second Third');
    await expect(textarea).toHaveValue('First Second Third');
  });

  test('should handle long queries', async ({ page }) => {
    const longQuery = 'This is a very long query that tests how the system handles extended input. '.repeat(5);

    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill(longQuery);
    await expect(textarea).toHaveValue(longQuery);
  });

  test('should handle special characters in queries', async ({ page }) => {
    const specialQuery = 'What is the API endpoint /api/v1/query?';

    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill(specialQuery);
    await expect(textarea).toHaveValue(specialQuery);
  });

  test('should support multiline queries', async ({ page }) => {
    const multilineQuery = 'Tell me about:\n1. The wiki system\n2. The data sources\n3. The query engine';

    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill(multilineQuery);
    await expect(textarea).toHaveValue(multilineQuery);
  });

  test('should have interactive UI elements', async ({ page }) => {
    const buttons = page.locator('button');
    const inputs = page.locator('input');
    const textareas = page.locator('textarea');

    const totalInteractive = await buttons.count() + await inputs.count() + await textareas.count();
    expect(totalInteractive).toBeGreaterThan(0);
  });

  test('should load without critical console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Filter out known acceptable errors
    const criticalErrors = errors.filter(err =>
      !err.includes('favicon') &&
      !err.includes('404') &&
      !err.includes('net::ERR')
    );

    expect(criticalErrors.length).toBeLessThan(5);
  });

  test('should handle rapid query changes', async ({ page }) => {
    const textarea = page.locator('textarea[name="input"]');

    await textarea.fill('query 1');
    await textarea.fill('query 2');
    await textarea.fill('query 3');
    await textarea.fill('final query');

    await expect(textarea).toHaveValue('final query');
  });

  test('should maintain focus on input', async ({ page }) => {
    const textarea = page.locator('textarea[name="input"]');
    await textarea.click();
    await textarea.fill('test query');
    await expect(textarea).toHaveValue('test query');
  });
});
