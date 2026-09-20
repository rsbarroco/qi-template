import { test, expect } from '@playwright/test';

test('@cart @remove-item removes a row and recalculates the total', async ({ page }) => {
  await page.goto('/cart');
  await page.getByTestId('cart-row-anvil').getByLabel('Remove').click();
  await expect(page.getByTestId('cart-total')).toHaveText('$0.00');
});
