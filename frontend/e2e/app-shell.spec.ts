import { test, expect } from '@playwright/test';
import { mockCoreApi } from './fixtures';

test.describe('Discovery shell', () => {
  test.beforeEach(async ({ page }) => {
    await mockCoreApi(page);
  });

  test('nav brand and discovery heading render', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('app-shell')).toBeVisible();
    await expect(page.getByText('Options research terminal')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Ticker discovery' })).toBeVisible({
      timeout: 20_000,
    });
  });

  test('screener mock shows ticker card', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'SPY' })).toBeVisible({ timeout: 20_000 });
  });
});
