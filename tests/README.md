# Tests

Four layers, cheapest first. Every layer runs in CI on every pull request; only the last
one costs tokens and runs on the maintainer's machine.

| Layer | Where | What it proves | Runs in |
|---|---|---|---|
| **Unit** | `tests/test_*.py` | `Config`, prompts (scripted `questionary`), generator context, every template renders for every tracker × CI combination with no Jinja leftovers, CI files are valid YAML, eval graders can fail, labels and report arithmetic | < 1 s |
| **Generated scripts** | `tests/test_qa_track_script.py`, `tests/test_coverage_report_script.py` | The `qa_track.py` and `coverage_report.py` that ship inside generated projects, executed as subprocesses against a freshly rendered project | ~2 s |
| **Acceptance (ATDD)** | `tests/acceptance/features/*.feature` + step files | Gherkin scenarios from the user's side: scaffolding a stack, tracking a ticket to close, coverage that cannot drift, and an intake whose graders accept a compliant agent and catch a sloppy one | ~3 s |
| **Evals** | `evals/` | Whether a real agent actually follows the generated skills. Needs `claude -p` and a login; see `evals/README.md` | maintainer, on demand |

## Rules we hold ourselves to

- **Red first.** A new behaviour starts as a failing test. The commit that adds the test
  says what it expects; the next commit makes it pass. When a test is added for existing
  code and passes immediately, it is a characterisation test and is labelled as such.
- **Every grader must be able to fail.** `test_dry_run_grades_untouched_fixture_and_at_least_one_grader_fails_per_case`
  fails the build if an eval case would pass on an empty fixture.
- **Scripts are tested as scripts.** The generated Python is run with `subprocess`, not
  imported, because that is how agents run it.
- **Acceptance scenarios are written from the outside.** Steps talk about tickets, sprints
  and coverage, not about functions. If a step needs to know a function name, it is a
  unit test.
- **No network, no tokens.** The fake `claude` in `tests/test_evals_runner.py` stands in
  for the CLI. Anything that needs a model belongs in `evals/`.

## Running

```bash
pip install -e ".[dev]"
python -m pytest -q                      # everything
python -m pytest -q tests/acceptance     # only the Gherkin scenarios
python -m pytest -q -k coverage          # one topic
python -m evals run ticket-intake --dry-run   # graders on the untouched fixture
```
