# Investigation log — order total drifts by a cent, dev, 2026-09-23

Symptom: `tests/checkout/order-total.spec.ts` intermittently reads `$108.24` instead of
`$108.25`. Reproduced by hand: about one review page in twelve.

Fast signal: a single request to `/api/cart/quote` with a fixed cart, looped 200 times.
Drift shows up 14 times in 200.

## Hypothesis 1 — rounding in the tax helper

Evidence for: the drift is exactly one cent and tax is the only percentage in the quote.
Evidence against: the helper is pure, and 200 calls with the same input in a unit test
return `825` cents every time.
Test: ran the helper directly over the 14 drifting payloads. All 14 returned `825`.
**Ruled out.**

## Hypothesis 2 — a second tax zone answering some requests

Evidence for: `tax_zones` has two rows and the resolver reads the first match.
Evidence against: both rows carry `0.0825`; the second is a disabled zone.
Test: forced the resolver to each row in turn and re-ran the 200-call loop. No drift
from either.
**Ruled out.**

## Hypothesis 3 — the subtotal itself drifts before tax is applied

Evidence for: if the subtotal is a cent low, the total follows.
Evidence against: the 14 drifting payloads all carry `"subtotal_cents": 10000`.
Test: asserted the subtotal on every one of the 200 responses. Always `10000`.
**Ruled out.**

## Where it stands

Three hypotheses formed and refuted with evidence. The minimised reproduction is the
200-call loop; the drift is in the quote response, after the subtotal and not in the tax
helper. No fourth hypothesis has been formed.
