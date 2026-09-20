import { test, expect } from '@playwright/test';

test('@cart @add-item adds a product to the cart', async ({ page }) => {
  await page.goto('/product/anvil');
  await page.getByRole('button', { name: 'Add to cart' }).click();
  await expect(page.getByTestId('cart-count')).toHaveText('1');
});
