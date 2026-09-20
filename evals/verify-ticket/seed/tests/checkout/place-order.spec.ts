import { test, expect } from '@playwright/test';

/**
 * [Documentation] SHOP-080 AC1 — an order can be placed from the review step.
 */
test('@checkout @place-order places an order and shows the confirmation', async ({ page }) => {
  await page.goto('/checkout/review');
  await page.getByRole('button', { name: 'Place order' }).click();
  await expect(page.getByTestId('order-confirmation')).toBeVisible();
});
