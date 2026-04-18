import { test, expect } from '@playwright/test';
import { mockCoreApi } from './fixtures';

test.describe('Terminal mode error banner', () => {
  test('shows data issue banner when analyze fails but shell stays up', async ({ page }) => {
    await mockCoreApi(page);

    await page.route('**/api/analyze', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Mock analyze failure' }),
      });
    });
    await page.route('**/api/chart/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [
            { time: '2024-01-02', open: 1, high: 2, low: 0.5, close: 1.5, value: 100 },
            { time: '2024-01-03', open: 1.5, high: 2, low: 1, close: 1.8, value: 110 },
          ],
        }),
      });
    });

    await page.goto('/');
    await page.getByPlaceholder('Search Specific Ticker...').fill('SPY');
    await page.getByRole('button', { name: 'Run ticker search' }).click();

    await expect(page.getByTestId('terminal-error-banner')).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId('terminal-error-banner')).toContainText('Mock analyze failure');
  });
});
