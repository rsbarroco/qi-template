import { test, expect } from '@playwright/test';
import { currentCart } from '../support/session';

test('@cart @promo takes 10% off the subtotal', async ({ page }) => {
  await page.goto(`/cart?id=${currentCart()}`);
  await page.getByLabel('Promo code').fill('SAVE10');
  await page.getByRole('button', { name: 'Apply' }).click();
  await expect(page.getByTestId('cart-total')).toHaveText('$67.50');
});
