# Local runs — cart suite, dev, 2026-09-21

## Full suite

```
PASS tests/cart/apply-coupon.spec.ts
FAIL tests/cart/promo-code.spec.ts:5
  @cart @promo takes 10% off the subtotal
  Error: page.goto: Navigation to "/cart?id=" failed
  Response status 404
PASS tests/checkout/order-total.spec.ts
```

Three full-suite runs, same failure all three times. Not a flake.

## The same test on its own

```
$ npx playwright test tests/cart/promo-code.spec.ts
PASS tests/cart/promo-code.spec.ts (1 passed)
```

Three runs in isolation, green all three times.

## By hand

Logged in as `qa+cart@acme.test` at `https://dev.shop.acme.test`, created a cart, applied
`SAVE10` on a $75.00 subtotal. The total updated to `$67.50` in place, which is AC1 of
SHOP-244. The feature works.

## Environment

Dev is healthy: `healthz` answers, the last deploy finished 2026-09-19, and the other two
specs pass in the same run.
