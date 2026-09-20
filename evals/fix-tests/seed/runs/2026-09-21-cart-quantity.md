# Local run — cart suite, dev, 2026-09-21

```
FAIL tests/cart/quantity-stepper.spec.ts:8
  @cart @quantity-stepper raises the quantity and the row total follows
  TimeoutError: locator.waitFor: Timeout 5000ms exceeded.
  waiting for getByTestId('qty-input') to be visible
```

`tests/cart/remove-item.spec.ts` passed in the same run, so the environment is up and the
cart page renders.

## What the page actually shows

Dev is healthy: logged in as `qa+cart@acme.test` at `https://dev.shop.acme.test/cart`,
the stepper is on screen and the two `+` clicks do raise the quantity to 3 by hand. The
row total reads `$74.97`, which is what AC2 asks for.

DOM captured from the cart row at the moment of the failure:

```html
<div class="cart-row" data-sku="ANVIL-1">
  <button aria-label="Decrease quantity">−</button>
  <input data-testid="cart-qty-input" aria-label="Quantity" value="3">
  <button aria-label="Increase quantity">+</button>
  <span data-testid="row-total">$74.97</span>
</div>
```

There is no element with `data-testid="qty-input"` anywhere on the page. The product
detail page still has one, which is why the hook was renamed (see the dev note on
SHOP-231).
