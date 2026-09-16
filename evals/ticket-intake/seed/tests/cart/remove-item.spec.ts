import { test, expect } from '@playwright/test';

/**
 * [Documentation] SHOP-102 AC1 — clicking the trash icon removes the row and the
 * cart total is recalculated. Fixture data for the eval harness; not a real suite.
 */
test('remove item from cart recalculates the total', async ({ page }) => {
  await page.goto('/cart');
  await page.getByRole('button', { name: 'Remove Blue Mug' }).click();
  await expect(page.getByTestId('cart-total')).toHaveText('$40.00');
});
