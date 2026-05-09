import { test, expect } from '@playwright/test';

/**
 * E2E Integration Tests for Jira Analysis System
 *
 * Tests the integration between frontend UI and backend API:
 * - Deep Analysis workflow
 * - Batch Analysis workflow
 * - SSE streaming
 * - UI interactions
 */

const BASE_URL = 'http://localhost:3001/deployments/jira-analysis/ui';
const API_URL = 'http://localhost:4501';

test.describe('Jira Analysis E2E Tests', () => {

  test.beforeEach(async ({ page }) => {
    // Check backend health before each test
    const response = await page.request.get(`${API_URL}/health`);
    expect(response.ok()).toBeTruthy();
    const health = await response.json();
    expect(health.status).toBe('healthy');
    expect(health.workflows.deep_analysis).toBe(true);
    expect(health.workflows.batch_analysis).toBe(true);
  });

  test.describe('Deep Analysis Page', () => {

    test('should load deep analysis page correctly', async ({ page }) => {
      await page.goto(BASE_URL);

      // Check page title and hero section
      await expect(page.locator('h1')).toContainText('Analyze Jira Issues');
      await expect(page.locator('text=AI-Powered Deep Analysis')).toBeVisible();

      // Check input elements
      await expect(page.locator('input[placeholder*="KAN"]')).toBeVisible();
      await expect(page.locator('button:has-text("Analyze")')).toBeVisible();

      // Check analysis mode buttons
      await expect(page.locator('button:has-text("Deep Analysis")')).toBeVisible();
      await expect(page.locator('button:has-text("Quick Analysis")')).toBeVisible();
    });

    test('should validate empty issue key', async ({ page }) => {
      await page.goto(BASE_URL);

      const analyzeButton = page.locator('button:has-text("Analyze")');

      // Button should be disabled when input is empty
      await expect(analyzeButton).toBeDisabled();

      // Type and clear input
      await page.locator('input[placeholder*="KAN"]').fill('KAN-9');
      await expect(analyzeButton).toBeEnabled();

      await page.locator('input[placeholder*="KAN"]').clear();
      await expect(analyzeButton).toBeDisabled();
    });

    test('should start deep analysis and show progress', async ({ page }) => {
      await page.goto(BASE_URL);

      // Fill in issue key
      await page.locator('input[placeholder*="KAN"]').fill('KAN-9');

      // Click analyze button
      await page.locator('button:has-text("Analyze")').click();

      // Wait for progress section to appear
      await expect(page.locator('text=Analysis Progress')).toBeVisible({ timeout: 10000 });

      // Check for progress steps
      await expect(page.locator('text=Loading Issue')).toBeVisible();

      // Button should show "Analyzing..." and be disabled
      await expect(page.locator('button:has-text("Analyzing...")')).toBeVisible();
      await expect(page.locator('button:has-text("Analyzing...")')).toBeDisabled();
    });

    test('should display analysis results', async ({ page }) => {
      await page.goto(BASE_URL);

      // Start analysis
      await page.locator('input[placeholder*="KAN"]').fill('KAN-9');
      await page.locator('button:has-text("Analyze")').click();

      // Wait for results (may take 15-20 seconds)
      await expect(page.locator('text=Issue 概览').or(page.locator('text=Analysis Results'))).toBeVisible({
        timeout: 30000
      });

      // Check if results are displayed
      const hasResults = await page.locator('text=KAN-9').isVisible();
      expect(hasResults).toBeTruthy();
    });

    test('should handle SSE streaming events', async ({ page }) => {
      await page.goto(BASE_URL);

      // Monitor network requests
      const sseRequests: any[] = [];
      page.on('request', request => {
        if (request.url().includes('/api/analyze')) {
          sseRequests.push(request);
        }
      });

      // Start analysis
      await page.locator('input[placeholder*="KAN"]').fill('KAN-9');
      await page.locator('button:has-text("Analyze")').click();

      // Wait a bit for SSE connection
      await page.waitForTimeout(2000);

      // Verify SSE request was made
      expect(sseRequests.length).toBeGreaterThan(0);
      expect(sseRequests[0].method()).toBe('POST');
    });
  });

  test.describe('Batch Analysis Page', () => {

    test('should load batch analysis page correctly', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      // Check page title
      await expect(page.locator('h1')).toContainText('Generate Reports');
      await expect(page.locator('text=Batch Analysis & Reports')).toBeVisible();

      // Check configuration panel
      await expect(page.locator('text=Batch Configuration')).toBeVisible();
      await expect(page.locator('text=Issue Keys')).toBeVisible();
      await expect(page.locator('text=Analysis Mode')).toBeVisible();

      // Check mode buttons
      await expect(page.locator('button:has-text("Strict")')).toBeVisible();
      await expect(page.locator('button:has-text("Balanced")')).toBeVisible();
      await expect(page.locator('button:has-text("Exploratory")')).toBeVisible();
    });

    test('should add and remove issue keys', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      // Add first issue
      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();

      // Verify issue was added
      await expect(page.locator('text=KAN-9')).toBeVisible();
      await expect(page.locator('text=1 issue added')).toBeVisible();

      // Add second issue
      await page.locator('input[placeholder*="PROJ"]').fill('KAN-14');
      await page.locator('button:has-text("Add")').click();

      // Verify both issues
      await expect(page.locator('text=KAN-14')).toBeVisible();
      await expect(page.locator('text=2 issues added')).toBeVisible();

      // Remove first issue
      await page.locator('text=KAN-9').locator('..').locator('button').click();

      // Verify only one issue remains
      await expect(page.locator('text=KAN-9')).not.toBeVisible();
      await expect(page.locator('text=1 issue added')).toBeVisible();
    });

    test('should add issue key with Enter key', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      // Type issue key and press Enter
      const input = page.locator('input[placeholder*="PROJ"]');
      await input.fill('KAN-9');
      await input.press('Enter');

      // Verify issue was added
      await expect(page.locator('text=KAN-9')).toBeVisible();

      // Input should be cleared
      await expect(input).toHaveValue('');
    });

    test('should change analysis mode', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      // Default should be Balanced
      const balancedButton = page.locator('button:has-text("Balanced")');
      await expect(balancedButton).toHaveClass(/bg-purple-600/);

      // Click Strict
      await page.locator('button:has-text("Strict")').click();
      await expect(page.locator('button:has-text("Strict")')).toHaveClass(/bg-purple-600/);

      // Click Exploratory
      await page.locator('button:has-text("Exploratory")').click();
      await expect(page.locator('button:has-text("Exploratory")')).toHaveClass(/bg-purple-600/);
    });

    test('should toggle retrieve evidence checkbox', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      // Find checkbox
      const checkbox = page.locator('input[type="checkbox"]');

      // Should be checked by default
      await expect(checkbox).toBeChecked();

      // Uncheck
      await checkbox.click();
      await expect(checkbox).not.toBeChecked();

      // Check again
      await checkbox.click();
      await expect(checkbox).toBeChecked();
    });

    test('should disable analyze button when no issues', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      const analyzeButton = page.locator('button:has-text("Analyze")');

      // Should be disabled initially
      await expect(analyzeButton).toBeDisabled();

      // Add an issue
      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();

      // Should be enabled now
      await expect(analyzeButton).toBeEnabled();
      await expect(analyzeButton).toContainText('Analyze 1 Issue');
    });

    test('should start batch analysis and show progress', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      // Add issues
      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();

      // Start analysis
      await page.locator('button:has-text("Analyze 1 Issue")').click();

      // Wait for progress section
      await expect(page.locator('text=Batch Progress')).toBeVisible({ timeout: 10000 });

      // Check for progress indicators
      await expect(page.locator('text=Completed')).toBeVisible();
      await expect(page.locator('text=In Progress')).toBeVisible();
      await expect(page.locator('text=Errors')).toBeVisible();
    });

    test('should display batch results and export options', async ({ page }) => {
      await page.goto(`${BASE_URL}/reports`);

      // Add issue and start analysis
      await page.locator('input[placeholder*="PROJ"]').fill('KAN-9');
      await page.locator('button:has-text("Add")').click();
      await page.locator('button:has-text("Analyze 1 Issue")').click();

      // Wait for results (may take time)
      await expect(page.locator('text=Export Options')).toBeVisible({ timeout: 60000 });

      // Check export buttons
      await expect(page.locator('button:has-text("Markdown")')).toBeVisible();
      await expect(page.locator('button:has-text("JSON")')).toBeVisible();
      await expect(page.locator('button:has-text("Knowledge Base")')).toBeVisible();
      await expect(page.locator('button:has-text("Email")')).toBeVisible();
    });
  });

  test.describe('API Integration', () => {

    test('should successfully call deep analysis API', async ({ page }) => {
      const response = await page.request.post(`${API_URL}/api/analyze`, {
        data: {
          issue_key: 'KAN-9',
          mode: 'balanced',
          retrieve_evidence: true
        }
      });

      expect(response.ok()).toBeTruthy();
      expect(response.headers()['content-type']).toContain('text/event-stream');
    });

    test('should successfully call batch analysis API', async ({ page }) => {
      const response = await page.request.post(`${API_URL}/api/batch-analyze`, {
        data: {
          issue_keys: ['KAN-9'],
          mode: 'balanced',
          retrieve_evidence: true
        }
      });

      expect(response.ok()).toBeTruthy();
      expect(response.headers()['content-type']).toContain('text/event-stream');
    });

    test('should handle CORS correctly', async ({ page }) => {
      await page.goto(BASE_URL);

      // Make API request from frontend
      const response = await page.evaluate(async (apiUrl) => {
        const res = await fetch(`${apiUrl}/health`);
        return {
          ok: res.ok,
          status: res.status
        };
      }, API_URL);

      expect(response.ok).toBeTruthy();
      expect(response.status).toBe(200);
    });
  });

  test.describe('Error Handling', () => {

    test('should handle invalid issue key gracefully', async ({ page }) => {
      await page.goto(BASE_URL);

      // Try with invalid issue key
      await page.locator('input[placeholder*="KAN"]').fill('INVALID-999999');
      await page.locator('button:has-text("Analyze")').click();

      // Should show progress initially
      await expect(page.locator('text=Analysis Progress')).toBeVisible({ timeout: 10000 });

      // May show error or complete with error message
      // (depends on backend error handling)
    });

    test('should handle network errors', async ({ page }) => {
      await page.goto(BASE_URL);

      // Intercept and fail the request
      await page.route('**/api/analyze', route => route.abort());

      await page.locator('input[placeholder*="KAN"]').fill('KAN-9');
      await page.locator('button:has-text("Analyze")').click();

      // Should handle error gracefully (button should re-enable)
      await page.waitForTimeout(2000);
      await expect(page.locator('button:has-text("Analyze")')).toBeEnabled();
    });
  });

  test.describe('Responsive Design', () => {

    test('should work on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);

      // Check if elements are visible
      await expect(page.locator('h1')).toBeVisible();
      await expect(page.locator('input[placeholder*="KAN"]')).toBeVisible();
      await expect(page.locator('button:has-text("Analyze")')).toBeVisible();
    });

    test('should work on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto(BASE_URL);

      await expect(page.locator('h1')).toBeVisible();
      await expect(page.locator('input[placeholder*="KAN"]')).toBeVisible();
    });
  });
});
