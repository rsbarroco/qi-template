# Dossier — SHOP-210

**Built:** 2026-09-18 · **Sources:** ticket, 3 comments, 1 PR, 1 linked ticket

## Acceptance criteria (verbatim from the ticket)

- AC1: The address step lists every address saved on the account, most recently used first.
- AC2: Picking a saved address fills the shipping form and keeps the order total unchanged.
- AC3: Editing a saved address at checkout updates it on the account too.
- AC4: An account with no saved addresses sees the blank form and no picker.

## Requirements found outside the ACs

| # | Requirement | Source |
|---|---|---|
| R1 | The list shows at most 5 addresses; the rest go behind "Show all" | comment by dev.marta, 2026-09-15 |
| R2 | A deleted address must disappear from the picker without a page reload | PR #58 diff, `AddressPicker.tsx` |

## Traversal log

| Item | Result |
|---|---|
| tickets/SHOP-210.md | read |
| comments (3) | read |
| PR #58 | read |
| SHOP-205 (linked) | NOT FOUND |
