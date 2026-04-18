import type { Page } from '@playwright/test';

/** Minimal JSON so discovery + initial portfolio load succeed without a backend. */
export async function mockCoreApi(page: Page) {
  await page.route('**/api/portfolio', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        cash_balance: 10000,
        total_return: 0,
        win_rate: 0.5,
        average_kelly_sizing: 0.1,
        positions: [],
      }),
    });
  });

  await page.route('**/api/screener', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        top_opportunities: [
          {
            ticker: 'SPY',
            category: 'etf',
            current_price: 450,
            urgency: 'LOW',
            narrative: 'Mock row for E2E',
          },
        ],
      }),
    });
  });
}
