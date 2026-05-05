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
 */
export async function navigateAndWaitForHydration(page: Page) {
  await page.goto('http://localhost:3000/deployments/chat/ui');
  await waitForHydration(page);
}
