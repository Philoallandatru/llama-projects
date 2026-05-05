import { Page } from '@playwright/test';

const HYDRATION_TIMEOUT = 30000;
const COMPONENT_MOUNT_DELAY = 1000;

/**
 * Wait for the Next.js page to complete client-side hydration.
 * The app uses next/dynamic with ssr:false, so we need to wait for:
 * 1. Network to be idle
 * 2. The main chat textarea to appear (indicates hydration complete)
 */
export async function waitForHydration(page: Page) {
  await page.waitForLoadState('networkidle');
  await page.waitForSelector('textarea[name="input"]', {
    timeout: HYDRATION_TIMEOUT,
    state: 'visible'
  });
  await page.waitForTimeout(COMPONENT_MOUNT_DELAY);
}

/**
 * Navigate to the chat UI and wait for hydration.
 * Server availability is verified by global setup before tests run.
 */
export async function navigateAndWaitForHydration(page: Page) {
  await page.goto('http://localhost:9876/deployments/chat/ui');
  await waitForHydration(page);
}
