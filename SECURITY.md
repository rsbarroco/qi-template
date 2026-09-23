# Security & guardrails

## Threat model for the agent-facing hooks

The hooks in `.claude/hooks/` (`guard_bash.py`, `protect_paths.py`, `stop_gate.py`) are
**tripwires, not a sandbox**. They pattern-match the surface of a command or file path
and deny the common, accidental ways an agent could force-push, push to `main`,
bypass verification, or read a secret. A sufficiently different phrasing of the same
action can slip past a regex (see `guard_bash.py`'s test cases for the ones we know
about and have closed).

That is expected, not a bug to chase indefinitely. Real protection for anything a
hook can't fully cover has to live somewhere the agent cannot rewrite:

- **Branch protection on `main`** in this repository's GitHub settings, so no
  history-rewriting push or bypassed review can land regardless of what ran
  locally.
- **Secrets that never live on the agent's working disk** (use your CI/CD
  provider's secret store, not a `.env` file the agent's shell can reach).
- **CI as the last rung of the enforcement ladder** — independent of both the
  agent and a distracted human, gated on the `test` job in
  `.github/workflows/tests.yml`.

## Recommended branch protection for `main`

Settings → Branches → Add rule → branch name pattern `main`:

- Require a pull request before merging (at least 1 approval)
- Require status checks to pass before merging → select the `test` check
- Require conversation resolution before merging
- Do not allow bypassing the above settings (include administrators)

Equivalent via the GitHub CLI/API:

```bash
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  repos/rsbarroco/qi-template/branches/main/protection \
  -f required_status_checks='{"strict":true,"contexts":["test"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"required_approving_review_count":1}' \
  -f restrictions=null
```

## Reporting a bypass

If you find a way past `guard_bash.py` or `protect_paths.py` that isn't covered by
their test suites, please open an issue with the exact command or path. Bypasses
are treated as bugs in the tripwire, not as proof the model is malicious — closing
them is how the guardrails earn trust.
