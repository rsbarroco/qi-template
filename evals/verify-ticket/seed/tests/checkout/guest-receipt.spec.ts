import { test, expect } from '@playwright/test';

/**
 * [Documentation] SHOP-260 AC1 — a guest receives an email receipt at the address
 * entered at checkout.
 */
test('@checkout @guest-receipt sends a receipt to the guest address', async ({ page, request }) => {
  await page.goto('/checkout/guest');
  await page.getByLabel('Email').fill('guest@acme.test');
  await page.getByRole('button', { name: 'Place order' }).click();
  const inbox = await request.get('/api/test/mailbox?to=guest@acme.test');
  expect((await inbox.json()).messages).toHaveLength(1);
});
