import { test, expect } from '@playwright/test';

test('@checkout @order-total shows the order total on the review step', async ({ page }) => {
  await page.goto('/checkout/review');
  await expect(page.getByTestId('order-total')).toHaveText('$108.25');
});
