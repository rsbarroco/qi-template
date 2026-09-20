# SHOP-210 — Saved addresses at checkout

**Sprint:** 26-09
**Type:** Story

## Description

A returning customer can pick one of their saved addresses at checkout instead of
typing it again.

## Acceptance criteria

- AC1: The address step lists every address saved on the account, most recently used first.
- AC2: Picking a saved address fills the shipping form and keeps the order total unchanged.
- AC3: Editing a saved address at checkout updates it on the account too.
- AC4: An account with no saved addresses sees the blank form and no picker.

## Validation steps

Dev environment, checkout page `/checkout/address`.
