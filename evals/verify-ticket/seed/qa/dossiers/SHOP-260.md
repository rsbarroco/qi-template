# Dossier — SHOP-260

**Built:** 2026-09-23 · **Sources traversed:** 6 · **Budget used:** 6 of 8

## Acceptance criteria (verbatim from the ticket)

- AC1: A guest who places an order receives an email receipt at the address entered at checkout.
- AC2: The receipt shows the order number, the line items and the order total.
- AC3: An invalid email address blocks the order with "Enter a valid email address" and nothing is sent.

## Requirements found outside the ACs

- R1 (comment by the product owner, 2026-09-21): the receipt goes out within 60 seconds of
  the order being placed; anything slower counts as a failure.
- R2 (PR #58 diff, `apps/api/src/mail/receipt.ts`): the sender address is
  `no-reply@acme.test` on dev and staging, never the store's real address.

## Traversal log

| Source | How it was reached | Outcome |
|---|---|---|
| tickets/SHOP-260.md | given | read |
| PR #58 | linked verbatim in the ticket | diff read |
| comment thread | on the ticket | read, R1 extracted |
| SHOP-259 | linked as "related" | read, no requirement |
| specs/checkout.md | repository | read |
| SHOP-262 | cited in a comment | NOT FOUND |

## Open questions

1. Does R1's 60-second window start at order placement or at the queue being drained?

## Approval

Not yet given. Step 5 of the intake has not run.
