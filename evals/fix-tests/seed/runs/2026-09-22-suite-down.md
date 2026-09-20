# Nightly run — full suite, dev, 2026-09-22

412 of 412 tests failed. Every failure is the same line:

```
Error: apiRequestContext.get: connect ECONNREFUSED 10.0.3.14:443
  at tests/support/login.ts:12
```

The two previous nights were green. Nothing was merged between them: the last commit on
`main` is from 2026-09-20.

A deploy to dev started at 02:14 and is still marked `in progress` in the deploy log.
`https://dev.shop.acme.test/healthz` does not answer.
