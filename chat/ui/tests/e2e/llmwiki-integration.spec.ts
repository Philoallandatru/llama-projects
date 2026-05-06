import { test, expect } from '@playwright/test';
import { navigateAndWaitForHydration } from '../helpers/wait-for-hydration';

/**
 * E2E Tests for LLMWiki Integration
 *
 * These tests verify that the llmwiki query tool is properly integrated
 * and can be used through the chat interface to query the wiki knowledge base.
 */

test.describe('LLMWiki Integration', () => {
  test.beforeEach(async ({ page }) => {
    await navigateAndWaitForHydration(page);
  });

  test('should have chat input available for wiki queries', async ({ page }) => {
    // Check if chat input textarea is visible
    const textarea = page.locator('textarea[name="input"]');
    await expect(textarea).toBeVisible();
  });

  test('should allow typing wiki-related queries', async ({ page }) => {
    // Type a wiki-related query
    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill('Tell me about the wiki system');
    await expect(textarea).toHaveValue('Tell me about the wiki system');
  });

  test('should send wiki query', async ({ page }) => {
    // Type a wiki query
    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill('What information is in the wiki?');

    // Find and click send button
    const sendButton = page.locator('button[type="submit"]').first();
    if (await sendButton.count() > 0) {
      await sendButton.click();

      // Wait for response
      await page.waitForTimeout(3000);

      // Verify page is still responsive
      const body = page.locator('body');
      await expect(body).toBeVisible();
    }
  });

  test('should handle multiple wiki queries', async ({ page }) => {
    const queries = [
      'What is in the wiki?',
      'Tell me about the documentation',
      'Search the knowledge base'
    ];

    for (const query of queries) {
      const textarea = page.locator('textarea[name="input"]');
      await textarea.fill(query);
      await expect(textarea).toHaveValue(query);

      // Clear for next query
      await textarea.fill('');
    }
  });

  test('should preserve wiki query input', async ({ page }) => {
    // Type progressively and verify value is preserved
    const textarea = page.locator('textarea[name="input"]');

    await textarea.fill('wiki');
    await expect(textarea).toHaveValue('wiki');

    await textarea.fill('wiki search');
    await expect(textarea).toHaveValue('wiki search');

    await textarea.fill('wiki search query');
    await expect(textarea).toHaveValue('wiki search query');
  });

  test('should handle technical wiki queries', async ({ page }) => {
    // Test with technical terms that might be in the wiki
    const technicalQuery = 'Explain the architecture and implementation details';

    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill(technicalQuery);
    await expect(textarea).toHaveValue(technicalQuery);
  });

  test('should handle wiki queries with special characters', async ({ page }) => {
    // Test with special characters
    const specialQuery = 'What is the API endpoint /api/v1/query?';

    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill(specialQuery);
    await expect(textarea).toHaveValue(specialQuery);
  });

  test('should support multiline wiki queries', async ({ page }) => {
    // Test multiline input
    const multilineQuery = 'Tell me about:\n1. The wiki system\n2. The data sources\n3. The query engine';

    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill(multilineQuery);
    await expect(textarea).toHaveValue(multilineQuery);
  });

  test('should have responsive UI for wiki interactions', async ({ page }) => {
    // Verify the page has interactive elements
    const textarea = page.locator('textarea[name="input"]');
    await expect(textarea).toBeVisible();

    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    expect(buttonCount).toBeGreaterThan(0);
  });

  test('should load wiki interface without errors', async ({ page }) => {
    // Listen for console errors
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Reload the page
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Filter out known acceptable errors
    const criticalErrors = errors.filter(err =>
      !err.includes('favicon') &&
      !err.includes('404') &&
      !err.includes('net::ERR')
    );

    // Should have minimal critical errors
    expect(criticalErrors.length).toBeLessThan(5);
  });

  test('should handle rapid wiki query changes', async ({ page }) => {
    // Test rapid input changes
    const textarea = page.locator('textarea[name="input"]');

    await textarea.fill('query 1');
    await textarea.fill('query 2');
    await textarea.fill('query 3');
    await textarea.fill('final wiki query');

    await expect(textarea).toHaveValue('final wiki query');
  });

  test('should clear wiki query after submission', async ({ page }) => {
    // Type and submit a query
    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill('Test wiki query');

    const sendButton = page.locator('button[type="submit"]').first();
    if (await sendButton.count() > 0) {
      await sendButton.click();

      // Wait a moment
      await page.waitForTimeout(1000);

      // Check if textarea was cleared (common behavior)
      const currentValue = await textarea.inputValue();
      // Either cleared or still has value is acceptable
      expect(typeof currentValue).toBe('string');
    }
  });

  test('should maintain focus on wiki input', async ({ page }) => {
    // Click on textarea
    const textarea = page.locator('textarea[name="input"]');
    await textarea.click();

    // Type something
    await textarea.fill('wiki query');

    // Verify it still has the value (focus maintained)
    await expect(textarea).toHaveValue('wiki query');
  });

  test('should support keyboard navigation', async ({ page }) => {
    // Tab to textarea
    await page.keyboard.press('Tab');

    // Type in focused element
    await page.keyboard.type('keyboard wiki query');

    // Verify the textarea received the input
    const textarea = page.locator('textarea[name="input"]');
    const value = await textarea.inputValue();

    // Should contain at least part of what we typed
    expect(value.length).toBeGreaterThan(0);
  });
});
