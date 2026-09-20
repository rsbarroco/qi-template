import { test, expect } from '@playwright/test';

test('@checkout @place-order places an order and shows the confirmation', async ({ page }) => {
  await page.goto('/checkout/review');
  await page.getByRole('button', { name: 'Place order' }).click();
  await expect(page.getByTestId('order-confirmation')).toBeVisible();
});
