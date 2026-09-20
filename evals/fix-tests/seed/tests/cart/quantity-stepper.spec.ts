import { test, expect } from '@playwright/test';

test('@cart @quantity-stepper raises the quantity and the row total follows', async ({ page }) => {
  await page.goto('/cart');
  await page.getByRole('button', { name: 'Increase quantity' }).click();
  await page.getByRole('button', { name: 'Increase quantity' }).click();
  await expect(page.getByTestId('qty-input')).toHaveValue('3');
  await expect(page.getByTestId('row-total')).toHaveText('$74.97');
});
