# SHOP-101 — Coupon code applies a percentage discount at checkout

**Sprint:** 26-09
**Type:** Story
**Status:** In QA
**Assignee:** dev.marta

## Description

Customers can enter a coupon code on the checkout page. Valid percentage coupons reduce
the order subtotal; invalid or expired codes show an inline error and leave the total
unchanged.

## Acceptance criteria

- AC1: Entering a valid code `SAVE10` on the checkout page reduces the subtotal by 10 %
  and shows the discount as a separate line.
- AC2: Entering an unknown code shows the error "Coupon not recognised" and the subtotal
  is unchanged.
- AC3: Entering an expired code shows the error "Coupon expired" and the subtotal is
  unchanged.
- AC4: The applied coupon is stored on the order record (`orders.coupon_code`) when the
  order is placed.

## Validation steps

Dev environment, checkout page `/checkout`, test cart with two items totalling 100.00.

## Links

- Parent: SHOP-100 (Epic — Promotions)
- Child: SHOP-104 (Coupon analytics event)
- Pull request: #42
- Comments: `tickets/SHOP-101/comments.md`
- Attachments: `tickets/SHOP-101/attachments/`
