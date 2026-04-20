import { platform } from 'node:os';
import { test, expect } from '@playwright/test';
import { mockCoreApi } from './fixtures';

test.describe('Command palette', () => {
  test.beforeEach(async ({ page }) => {
    await mockCoreApi(page);
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Ticker discovery' })).toBeVisible({
      timeout: 20_000,
    });
  });

  test('opens with Control+K and shows dialog', async ({ page }) => {
    await page.keyboard.press('Control+K');
    await expect(page.getByRole('dialog', { name: 'Command palette' })).toBeVisible();
    await expect(page.getByPlaceholder('Filter commands…')).toBeVisible();
  });

  test('Escape closes palette', async ({ page }) => {
    await page.keyboard.press('Control+K');
    await expect(page.getByRole('dialog', { name: 'Command palette' })).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog', { name: 'Command palette' })).not.toBeVisible();
  });

  test('opens with Meta+K on macOS', async ({ page }) => {
    test.skip(platform() !== 'darwin', 'Shortcut is Meta+K on macOS only');
    await page.keyboard.press('Meta+K');
    await expect(page.getByRole('dialog', { name: 'Command palette' })).toBeVisible();
  });
});
