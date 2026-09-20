import { test, expect } from '@playwright/test';
import { createCart, activeCartId } from '../support/session';

test.afterAll(async ({ request }) => {
  // Housekeeping: the coupon suite leaves a cart behind on dev otherwise.
  await request.delete(`/api/carts/${activeCartId}`);
});

test('@cart @coupon applies a fixed-amount coupon', async ({ page, request }) => {
  const cart = await createCart(request);
  await page.goto(`/cart?id=${cart}`);
  await page.getByLabel('Coupon').fill('ANVIL5');
  await page.getByRole('button', { name: 'Apply' }).click();
  await expect(page.getByTestId('cart-total')).toHaveText('$70.00');
});
