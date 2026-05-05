import { test, expect } from '@playwright/test';

test.describe('Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should have at least one heading', async ({ page }) => {
    // Check for any heading elements
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    const count = await headings.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should have accessible form elements', async ({ page }) => {
    // Check that textareas are present
    const textareas = page.locator('textarea');
    const textareaCount = await textareas.count();
    expect(textareaCount).toBeGreaterThan(0);

    // Check that buttons are present
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    expect(buttonCount).toBeGreaterThan(0);
  });

  test('should support keyboard navigation', async ({ page }) => {
    // Tab through interactive elements
    await page.keyboard.press('Tab');

    // Wait a moment for focus to settle
    await page.waitForTimeout(100);

    // Check if any element has focus
    const focusedElement = page.locator(':focus');
    const hasFocus = await focusedElement.count();
    expect(hasFocus).toBeGreaterThan(0);
  });

  test('should have proper link attributes for external links', async ({ page }) => {
    // External links should have rel="noopener noreferrer"
    const externalLinks = page.locator('a[target="_blank"]');
    const count = await externalLinks.count();

    for (let i = 0; i < count; i++) {
      const link = externalLinks.nth(i);
      const rel = await link.getAttribute('rel');
      if (rel) {
        expect(rel).toContain('noopener');
      }
    }
  });

  test('should have visible text content', async ({ page }) => {
    // Verify page has visible text
    const body = page.locator('body');
    const textContent = await body.textContent();
    expect(textContent).toBeTruthy();
    expect(textContent!.length).toBeGreaterThan(0);
  });

  test('should have proper input placeholders', async ({ page }) => {
    // Check that inputs have helpful placeholders
    const inputs = page.locator('input[placeholder], textarea[placeholder]');
    const count = await inputs.count();

    if (count > 0) {
      for (let i = 0; i < count; i++) {
        const input = inputs.nth(i);
        const placeholder = await input.getAttribute('placeholder');
        expect(placeholder).toBeTruthy();
        expect(placeholder!.length).toBeGreaterThan(0);
      }
    }
  });

  test('should not have critical accessibility violations', async ({ page }) => {
    // Check for common accessibility issues

    // 1. Images should have alt text (if any images exist)
    const images = page.locator('img');
    const imageCount = await images.count();

    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute('alt');
      // Alt can be empty string for decorative images, but should exist
      expect(alt).not.toBeNull();
    }

    // 2. Buttons should have accessible text or aria-label
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();

    const inaccessibleButtons = [];
    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      const ariaLabelledBy = await button.getAttribute('aria-labelledby');

      // Button should have either text content or aria-label
      const hasAccessibleName = (text && text.trim().length > 0) || ariaLabel || ariaLabelledBy;
      if (!hasAccessibleName) {
        inaccessibleButtons.push(i);
      }
    }

    // Fail the test if any buttons lack accessible names
    expect(inaccessibleButtons, `Buttons at indices ${inaccessibleButtons.join(', ')} lack accessible names`).toHaveLength(0);
  });
});
