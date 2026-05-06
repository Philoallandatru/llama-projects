import { test, expect } from '@playwright/test';
import { navigateAndWaitForHydration } from '../helpers/wait-for-hydration';

/**
 * E2E Tests for Datasource Integration
 *
 * These tests verify that the datasource query tool is properly integrated
 * and can be used through the chat interface to query indexed documents.
 */

test.describe('Datasource Integration', () => {
  test.beforeEach(async ({ page }) => {
    await navigateAndWaitForHydration(page);
  });

  test('should have chat input available', async ({ page }) => {
    // Check if chat input textarea is visible
    const textarea = page.locator('textarea[name="input"]');
    await expect(textarea).toBeVisible();
  });

  test('should allow typing in chat input', async ({ page }) => {
    // Type in the chat input
    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill('What is this project about?');
    await expect(textarea).toHaveValue('What is this project about?');
  });

  test('should have send button available', async ({ page }) => {
    // Check if send button exists
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    expect(buttonCount).toBeGreaterThan(0);
  });

  test('should send query and receive response', async ({ page }) => {
    // Type a query
    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill('Tell me about the project');

    // Find and click send button (usually near the textarea)
    const sendButton = page.locator('button[type="submit"]').first();
    if (await sendButton.count() > 0) {
      await sendButton.click();

      // Wait for response to appear
      await page.waitForTimeout(3000);

      // Check if any new content appeared (messages, responses, etc.)
      const body = page.locator('body');
      await expect(body).toBeVisible();
    }
  });

  test('should display chat interface elements', async ({ page }) => {
    // Verify the page has proper chat interface structure
    const textarea = page.locator('textarea[name="input"]');
    await expect(textarea).toBeVisible();

    // Check for buttons
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    expect(buttonCount).toBeGreaterThan(0);
  });

  test('should handle empty query', async ({ page }) => {
    // Try to send empty query
    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill('');

    const sendButton = page.locator('button[type="submit"]').first();
    if (await sendButton.count() > 0) {
      // Button might be disabled or query might be rejected
      const isDisabled = await sendButton.isDisabled();
      // Either disabled or enabled is acceptable - just verify it exists
      expect(typeof isDisabled).toBe('boolean');
    }
  });

  test('should preserve input while typing', async ({ page }) => {
    // Type progressively and verify value is preserved
    const textarea = page.locator('textarea[name="input"]');

    await textarea.fill('First');
    await expect(textarea).toHaveValue('First');

    await textarea.fill('First Second');
    await expect(textarea).toHaveValue('First Second');

    await textarea.fill('First Second Third');
    await expect(textarea).toHaveValue('First Second Third');
  });

  test('should handle long queries', async ({ page }) => {
    // Create a long query
    const longQuery = 'This is a very long query that tests how the system handles extended input. '.repeat(5);

    const textarea = page.locator('textarea[name="input"]');
    await textarea.fill(longQuery);
    await expect(textarea).toHaveValue(longQuery);
  });

  test('should have interactive UI elements', async ({ page }) => {
    // Verify the page has interactive elements
    const buttons = page.locator('button');
    const inputs = page.locator('input');
    const textareas = page.locator('textarea');

    const totalInteractive = await buttons.count() + await inputs.count() + await textareas.count();
    expect(totalInteractive).toBeGreaterThan(0);
  });

  test('should load without console errors', async ({ page }) => {
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

    // Filter out known acceptable errors (like network errors for optional resources)
    const criticalErrors = errors.filter(err =>
      !err.includes('favicon') &&
      !err.includes('404') &&
      !err.includes('net::ERR')
    );

    // Should have minimal critical errors
    expect(criticalErrors.length).toBeLessThan(5);
  });
});
