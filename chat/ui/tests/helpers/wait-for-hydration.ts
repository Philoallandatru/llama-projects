import { Page } from '@playwright/test';

/**
 * Wait for the Next.js page to complete client-side hydration.
 * The app uses next/dynamic with ssr:false, so we need to wait for:
 * 1. Network to be idle
 * 2. The main chat textarea to appear (indicates hydration complete)
 */
export async function waitForHydration(page: Page) {
  // Wait for network to settle
  await page.waitForLoadState('networkidle');

  // Wait for the chat input textarea to appear (key indicator of hydration)
  await page.waitForSelector('textarea[name="input"]', {
    timeout: 30000,
    state: 'visible'
  });

  // Small additional wait to ensure all components are mounted
  await page.waitForTimeout(1000);
}

/**
 * Navigate to the chat UI and wait for hydration.
 * Uses the full URL to avoid baseURL configuration issues.
 * Retries on connection refused to handle server startup delays.
 */
export async function navigateAndWaitForHydration(page: Page) {
  const maxRetries = 3;
  const retryDelay = 2000;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      await page.goto('http://localhost:9876/deployments/chat/ui');
      await waitForHydration(page);
      return;
    } catch (error) {
      if (attempt === maxRetries) {
        throw error;
      }
      if (error instanceof Error && error.message.includes('ERR_CONNECTION_REFUSED')) {
        await page.waitForTimeout(retryDelay);
        continue;
      }
      throw error;
    }
  }
}
