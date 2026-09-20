# SHOP-231 — Quantity stepper in the cart

**Sprint:** 26-09
**Type:** Story

## Acceptance criteria

- AC1: The cart row shows a stepper with `−` and `+` around the current quantity.
- AC2: Pressing `+` raises the quantity by one and the row total follows.
- AC3: The quantity never goes below 1; `−` is disabled at 1.

## Dev note (added 2026-09-21, after the ACs were approved)

The stepper moved out of the checkout bundle into the shared cart component. The input
keeps the same behaviour and the same label; only the hook changed, from
`data-testid="qty-input"` to `data-testid="cart-qty-input"`, so it stops colliding with
the quantity input on the product page. No AC changed.
