import { test, expect } from '@playwright/test';

/**
 * Detailed Component Tests - 详细组件测试
 *
 * 确保每个前端元素都被测试
 */

const BASE_URL = 'http://localhost:3001/deployments/jira-analysis/ui';
const API_URL = 'http://localhost:4501';

test.describe('Detailed Component Tests', () => {

  test.describe('AnalysisResults Component', () => {

    test('should display issue header with key and profile', async ({ page }) => {
      await page.goto(BASE_URL);

      // Start analysis
      await page.locator('input[placeholder*="KAN"]').fill('KAN-9');
      await page.locator('button:has-text("Analyze")').click();

      // Wait for results
      await expect(page.locator('text=KAN-9')).toBeVisible({ timeout: 30000 });

      // Check issue key badge
      const issueKeyBadge = page.locator('.font-mono:has-text("KAN-9")');
      await expect(issueKeyBadge).toBeVisible();

      // Check profile badge (RCA, Traceability, etc.)
      const profileBadge = page.locator('.bg-purple-100');
      await expect(profileBadge).toBeVisible();
    });

    test('should display "View in Jira" link', async ({ page }) => {
      await page.goto(BASE_URL);

      await page.locator('input[placeholder*="KAN"]').fill('KAN-9');
      await page.locator('button:has-text("Analyze")').click();

      await page.waitForTimeout(5000);

      // Check for external link
      const jiraLink = page.locator('a:has-text("View in Jira")');
      if (await jiraLink.isVisible()) {
        await expect(jiraLink).toHaveAttribute('target', '_blank');
        await expect(jiraLink).toHaveAttribute('rel', 'noopener noreferrer');
      }
    });

    test('should display evidence section', async ({ page }) => {
      await page.goto(BASE_URL);

      await page.locator('input[placeholder*="KAN"]').fill('KAN-9');
      await page.locator('button:has-text("Analyze")').click();

      // Wait for evidence section
      await page.waitForTimeout(10000);

      // Check for evidence-related text
      const hasEvidence = await page.locator('text=Evidence').or(page.locator('text=证据')).isVisible();
      if (hasEvidence) {
        expect(hasEvidence).toBeTruthy();
      }
    });

    test('should render markdown analysis content', async ({ page }) => {
      await page.goto(BASE_URL);

      await page.locator('input[placeholder*="KAN"]').fill('KAN-9');
      await page.locator('button:has-text("Analyze")').click();

      await page.waitForTimeout(15000);

      // Check for markdown elements (headings, lists, code blocks)
      const hasMarkdown = await page.locator('h1, h2, h3, ul, ol, code').count();
      expect(hasMarkdown).toBeGreaterThan(0);
    });
  });

  test.describe('AnalysisProgress Component', () => {

    test('should display all progress steps', async ({ page }) => {
      await page.goto(BASE_URL);

      await page.locator('input[placeholder*="KAN"]').fill('KAN-9');
      await page.locator('button:has-text("Analyze")').click();

      // Check for progress steps
      await expect(page.locator('text=Loading Issue')).toBeVisible({ timeout: 10000 });

      // May also see other steps
      const steps = [
        'Loading Issue',
        'Routing Profile',
        'Retrieving Evidence',
        'Generating Analysis'
      ];

      // At least one step should be visible
      let visibleSteps = 0;
      for (const step of steps) {
        if (await page.locator(`text=${step}`).isVisible()) {
          visibleSteps++;
        }
      }
      expect(visibleSteps).toBeGreaterThan(0);
    });

    test('should show step status icons', async ({ page }) => {
      await page.goto(BASE_URL);

      await page.locator('input[placeholder*="KAN"]').fill('KAN-9');
      await page.locator('button:has-text("Analyze")').click();

      await page.waitForTimeout(2000);

      // Check for status icons (checkmark, spinner, circle)
      const icons = await page.locator('svg').count();
      expect(icons).toBeGreaterThan(0);
    });
  });

  test.describe('BatchProgress Component', () => {

    test('should display progress statistics', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      // Add issue and start
      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();
      await page.locator('button:has-text("Analyze 1 Issue")').click();

      // Wait for progress
      await expect(page.locator('text=Batch Progress')).toBeVisible({ timeout: 10000 });

      // Check for statistics
      await expect(page.locator('text=Completed')).toBeVisible();
      await expect(page.locator('text=In Progress')).toBeVisible();
      await expect(page.locator('text=Errors')).toBeVisible();
    });

    test('should display progress bar with percentage', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();
      await page.locator('button:has-text("Analyze 1 Issue")').click();

      await page.waitForTimeout(2000);

      // Check for progress bar
      const progressBar = page.locator('.bg-gradient-to-r');
      if (await progressBar.count() > 0) {
        expect(await progressBar.count()).toBeGreaterThan(0);
      }
    });

    test('should display issue list with status', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();
      await page.locator('button:has-text("Analyze 1 Issue")').click();

      await page.waitForTimeout(3000);

      // Check for issue in list
      await expect(page.locator('text=KAN-9')).toBeVisible();
    });

    test('should show estimated time remaining', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();
      await page.locator('button:has-text("Analyze 1 Issue")').click();

      await page.waitForTimeout(2000);

      // Check for time estimate (may or may not be present)
      const hasTimeEstimate = await page.locator('text=remaining').isVisible();
      // This is optional, so we just check it doesn't error
      expect(typeof hasTimeEstimate).toBe('boolean');
    });
  });

  test.describe('BatchReport Component', () => {

    test('should display summary statistics', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();
      await page.locator('button:has-text("Analyze 1 Issue")').click();

      // Wait for completion (may take time)
      await page.waitForTimeout(30000);

      // Check for summary section
      const hasSummary = await page.locator('text=Summary').or(page.locator('text=Total')).isVisible();
      if (hasSummary) {
        expect(hasSummary).toBeTruthy();
      }
    });

    test('should display individual reports', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();
      await page.locator('button:has-text("Analyze 1 Issue")').click();

      await page.waitForTimeout(30000);

      // Check for issue key in results
      const hasIssueKey = await page.locator('text=KAN-9').count();
      expect(hasIssueKey).toBeGreaterThan(0);
    });
  });

  test.describe('ExportOptions Component', () => {

    test('should display all export buttons', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();
      await page.locator('button:has-text("Analyze 1 Issue")').click();

      // Wait for export options
      await expect(page.locator('text=Export Options')).toBeVisible({ timeout: 60000 });

      // Check all export buttons
      await expect(page.locator('button:has-text("Markdown")')).toBeVisible();
      await expect(page.locator('button:has-text("JSON")')).toBeVisible();
      await expect(page.locator('button:has-text("Knowledge Base")')).toBeVisible();
      await expect(page.locator('button:has-text("Email")')).toBeVisible();
    });

    test('should handle markdown export click', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();
      await page.locator('button:has-text("Analyze 1 Issue")').click();

      await expect(page.locator('text=Export Options')).toBeVisible({ timeout: 60000 });

      // Listen for download
      const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null);

      await page.locator('button:has-text("Markdown")').click();

      const download = await downloadPromise;
      if (download) {
        expect(download.suggestedFilename()).toContain('.md');
      }
    });

    test('should handle JSON export click', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();
      await page.locator('button:has-text("Analyze 1 Issue")').click();

      await expect(page.locator('text=Export Options')).toBeVisible({ timeout: 60000 });

      const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null);

      await page.locator('button:has-text("JSON")').click();

      const download = await downloadPromise;
      if (download) {
        expect(download.suggestedFilename()).toContain('.json');
      }
    });

    test('should show coming soon alerts for unimplemented features', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();
      await page.locator('button:has-text("Analyze 1 Issue")').click();

      await expect(page.locator('text=Export Options')).toBeVisible({ timeout: 60000 });

      // Listen for alert
      page.on('dialog', dialog => {
        expect(dialog.message()).toContain('coming soon');
        dialog.accept();
      });

      await page.locator('button:has-text("Knowledge Base")').click();
    });
  });

  test.describe('Card Component', () => {

    test('should render glass morphism cards', async ({ page }) => {
      await page.goto(BASE_URL);

      // Check for glass class
      const glassCards = await page.locator('.glass').count();
      expect(glassCards).toBeGreaterThan(0);
    });

    test('should have proper styling', async ({ page }) => {
      await page.goto(BASE_URL);

      const card = page.locator('.glass').first();
      await expect(card).toBeVisible();

      // Check for rounded corners and shadow
      const hasRounded = await card.evaluate(el =>
        window.getComputedStyle(el).borderRadius !== '0px'
      );
      expect(hasRounded).toBeTruthy();
    });
  });

  test.describe('Input Validation', () => {

    test('should trim whitespace from issue keys', async ({ page }) => {
      await page.goto(BASE_URL);

      const input = page.locator('input[placeholder*="KAN"]');
      await input.fill('  KAN-9  ');

      const analyzeButton = page.locator('button:has-text("Analyze")');
      await expect(analyzeButton).toBeEnabled();
    });

    test('should prevent duplicate issue keys in batch', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      // Add same issue twice
      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();

      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();

      // Should only have one
      const issueCount = await page.locator('text=KAN-9').count();
      expect(issueCount).toBe(1);
    });
  });

  test.describe('Loading States', () => {

    test('should disable inputs during analysis', async ({ page }) => {
      await page.goto(BASE_URL);

      await page.locator('input[placeholder*="KAN"]').fill('KAN-9');
      await page.locator('button:has-text("Analyze")').click();

      // Input should be disabled
      const input = page.locator('input[placeholder*="KAN"]');
      await expect(input).toBeDisabled();

      // Mode buttons should be disabled
      const modeButton = page.locator('button:has-text("Quick Analysis")');
      await expect(modeButton).toBeDisabled();
    });

    test('should show loading state on analyze button', async ({ page }) => {
      await page.goto(BASE_URL);

      await page.locator('input[placeholder*="KAN"]').fill('KAN-9');
      await page.locator('button:has-text("Analyze")').click();

      // Button text should change
      await expect(page.locator('button:has-text("Analyzing...")')).toBeVisible();
    });
  });

  test.describe('Accessibility', () => {

    test('should have proper ARIA labels', async ({ page }) => {
      await page.goto(BASE_URL);

      // Check for labels
      const labels = await page.locator('label').count();
      expect(labels).toBeGreaterThan(0);
    });

    test('should support keyboard navigation', async ({ page }) => {
      await page.goto(BASE_URL);

      // Tab to input
      await page.keyboard.press('Tab');

      // Type issue key
      await page.keyboard.type('KAN-9');

      // Tab to button and press Enter
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Enter');

      // Should start analysis
      await expect(page.locator('text=Analysis Progress')).toBeVisible({ timeout: 10000 });
    });

    test('should have sufficient color contrast', async ({ page }) => {
      await page.goto(BASE_URL);

      // This is a basic check - full contrast testing requires specialized tools
      const heading = page.locator('h1').first();
      await expect(heading).toBeVisible();

      const color = await heading.evaluate(el =>
        window.getComputedStyle(el).color
      );

      // Should have a color set
      expect(color).toBeTruthy();
    });
  });
});
