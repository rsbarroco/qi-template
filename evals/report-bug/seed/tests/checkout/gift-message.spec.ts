import { test, expect } from '@playwright/test';

test('@checkout @gift-message shows the gift message on the confirmation page', async ({ page }) => {
  await page.goto('/checkout/review');
  await page.getByLabel('Gift message').fill('Happy birthday Marta');
  await page.getByRole('button', { name: 'Place order' }).click();
  await expect(page.getByTestId('gift-message-value')).toHaveText('Happy birthday Marta');
});
