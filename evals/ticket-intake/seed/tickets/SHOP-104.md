# SHOP-104 — Coupon analytics event

**Type:** Sub-task of SHOP-101
**Status:** To do

## Description

When a coupon is applied successfully, emit the analytics event `coupon_applied` with
`code` and `discount_amount`. Out of scope for SHOP-101's QA pass; tracked here.

## Acceptance criteria

- AC1: Applying a valid coupon emits `coupon_applied` exactly once.
