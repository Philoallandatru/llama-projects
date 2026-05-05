import { chromium, FullConfig } from '@playwright/test';

const MAX_RETRIES = 3;
const RETRY_DELAYS_MS = [500, 1000, 2000];
const BASE_URL = 'http://localhost:9876/deployments/chat/ui';

async function waitForServer(config: FullConfig) {
  const baseURL = config.use?.baseURL || BASE_URL;

  const browser = await chromium.launch();
  const page = await browser.newPage();

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      await page.goto(baseURL, { timeout: 10000 });
      console.log(`✓ Server ready at ${baseURL}`);
      await browser.close();
      return;
    } catch (error) {
      if (attempt === MAX_RETRIES) {
        await browser.close();
        throw new Error(`Server not available at ${baseURL} after ${MAX_RETRIES} attempts`);
      }
      const delay = RETRY_DELAYS_MS[attempt - 1];
      console.log(`Server not ready, retrying in ${delay}ms... (attempt ${attempt}/${MAX_RETRIES})`);
      await page.waitForTimeout(delay);
    }
  }

  await browser.close();
}

export default async function globalSetup(config: FullConfig) {
  await waitForServer(config);
}
