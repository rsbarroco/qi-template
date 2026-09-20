# 0001 — A skill gets an eval suite when its work lands on disk

**Status:** accepted
**Date:** 2026-09-20
**Deciders:** QA engineer (rsbarroco)

## Context

The promotion rule in the generated `AUTONOMY.md` moves a task up a level only when the
skill that performs it has an eval suite of at least three cases, one of them a refusal.
The template generates twenty skills. Five suites exist. The obvious reading — write the
other fifteen — does not survive contact with how the runner grades.

`evals/runner.py` renders a fixture project, runs `claude -p` inside it with
`Read, Glob, Grep, Edit, Write` and a narrow `Bash` allowlist, and grades **the final
state of the disk and the final answer**. Nothing else. There is no database, no browser,
no cloud account, no message broker and no load generator in a run.

That is fine for a skill whose output is a file, a diff or an argued answer. It is not
fine for `sql-query`, `nosql-query`, `web-ui`, `mobile`, `cloud-logs`, `queue-testing`
and `performance`, whose whole job is to touch a live service and come back with
evidence. A suite for those would have to seed a fake transcript of a query that never
ran and grade the agent for reformatting it. That measures fluency at describing work,
which is the exact failure mode — *asserted without showing* — the human label column
exists to catch. A suite that rewards it is worse than no suite.

## Decision

A skill gets an eval suite when its work is visible in the final state of the run: a file
written, a file deliberately left alone, or an answer that carries the argument. Skills
that must reach a live service to do their job get no suite until the runner can give
them one, and the tasks that depend on them stay at their current level.

Today that splits the catalogue in two:

- **Suite required** — `ticket-intake`, `gap-analysis`, `report-bug`, `fix-tests`,
  `diagnose`, `verify-ticket`, `sprint-report`, `json-schema`, and the four
  coordination skills `bdd-writer`, `convention-check`, `discovery`, `handoff-protocol`.
- **Blocked on infrastructure** — `sql-query`, `nosql-query`, `web-ui`, `mobile`,
  `cloud-logs`, `queue-testing`, `performance`.

`comm-broadcast` is in neither list: it is capped at level 0 by consequence, so no
promotion is available to unblock.

## Consequences

`execute-on-dev` and `execute-on-staging` can be promoted on the evidence of
`verify-ticket`, which builds the matrix and holds the approval gate, but never on the
evidence of the skills that drive the browser or the database. A project that leans on
those surfaces keeps a human in the loop for longer. That is the honest reading of what
has been measured, and it is the intended cost.

Unblocking the seven is a runner change, not a case-writing exercise: fixtures that
stand up a throwaway Postgres, a static site the browser can be pointed at, and a local
queue, plus the tools to reach them in `DEFAULT_ALLOWED_TOOLS`. Until someone does that
work, the gap is a known limit with a name, not an oversight.

## Confirmation

`tests/test_evals_suites.py` holds every suite that exists to the shape the promotion
rule reads — three cases, one refusal, every grader known, every path in a query present
in `seed/`, and at least one grader still failing on the untouched fixture. It does not
require a suite per skill, and this ADR is why. `evals/README.md` carries the same two
lists next to the commands, so the next person writing a suite reads the boundary before
writing a fixture that cannot be graded.
