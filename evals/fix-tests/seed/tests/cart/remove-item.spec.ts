import { test, expect } from '@playwright/test';

test('@cart @remove-item empties the row when the last unit is removed', async ({ page }) => {
  await page.goto('/cart');
  await page.getByRole('button', { name: 'Remove' }).click();
  await expect(page.getByTestId('cart-empty')).toBeVisible();
});
