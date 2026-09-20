# Manual run — SHOP-244 promo code on the cart total, dev, 2026-09-24

## What was done

1. Created a quote with one Anvil × 3 (`subtotal_cents` 7500), saved as
   `payloads/quote-valid.json`
2. `POST /api/cart/quote/q_4f8a2b1c/promotions` with body `{"code": "SAVE10"}`
3. Response: `200 OK`, body `{"accepted": true}`
4. `GET /api/cart/quote/q_4f8a2b1c` immediately after, saved as
   `payloads/quote-after-promo.json`

## What the AC asks for

AC1 of SHOP-244: a valid promo code takes 10 % off the cart subtotal and the total
updates in place.

## Notes

`SAVE10` is active in the promotions table on dev and has not expired. The endpoint
answered `200` and `accepted: true` both times it was called.
