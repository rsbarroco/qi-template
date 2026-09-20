import { test, expect } from '@playwright/test';

test('@checkout @tax adds 8.25% sales tax to the order total', async ({ page }) => {
  await page.goto('/checkout/review');
  await expect(page.getByTestId('subtotal')).toHaveText('$100.00');
  await expect(page.getByTestId('tax-line')).toHaveText('$8.25');
  await expect(page.getByTestId('order-total')).toHaveText('$108.25');
});
