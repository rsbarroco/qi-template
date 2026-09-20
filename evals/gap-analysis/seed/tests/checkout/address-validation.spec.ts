import { test, expect } from '@playwright/test';

test('@checkout @address rejects a postcode that is too short', async ({ page }) => {
  await page.goto('/checkout/address');
  await page.getByLabel('Postcode').fill('12');
  await page.getByRole('button', { name: 'Continue' }).click();
  await expect(page.getByRole('alert')).toContainText('Postcode');
});
