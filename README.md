# QI — Quality Intelligence

Scaffold an AI-assisted QA project in seconds.

QI generates a **Claude-first QA constitution** — a short CLAUDE.md, rules scoped by path,
skills in the [Agent Skills](https://agentskills.io) format, hooks that enforce the gates,
autonomy levels, scripts, ADRs and CI config — customized to your team's stack. The
generated project is ready to use with [Claude Code](https://claude.ai/code) from day one,
with proven patterns for evidence-based QA, assertion validity, coverage tracking and
AI-usage reporting. Because skills and rules are plain markdown in a standard layout,
Codex, Cursor and Copilot can read them too.

## Install

```bash
pip install git+https://github.com/rsbarroco/qi-template
# or: pipx install git+https://github.com/rsbarroco/qi-template
```

## Usage

```bash
qi my-project-tests
```

QI presents a series of selection menus (use arrow keys + space/enter). No free text —
each question has a fixed list of options to choose from.

### Questions and available options

| Question | Options |
|---|---|
| **Task tracker** | Jira / GitHub Issues / Linear / Azure DevOps / None |
| **Documentation platform** | Confluence / Notion / GitHub Wiki / None |
| **SQL databases** | PostgreSQL / MySQL / SQLite / MS SQL Server *(multi-select)* |
| **NoSQL databases** | MongoDB / Redis / DynamoDB / Firestore *(multi-select)* |
| **UI surfaces** | Web (browser) / Mobile — iOS / Mobile — Android *(multi-select)* |
| **Mobile framework** *(if mobile selected)* | Appium (cross-platform) / Detox (React Native) / Espresso + XCUITest (native) |
| **Test framework** | Robot Framework / Playwright / WebdriverIO / Cypress / Jest-Vitest / Custom / None |
| **Performance testing** | k6 / Locust / JMeter / Gatling / Artillery / None |
| **Cloud provider** | AWS / GCP / Azure / None |
| **Async queues** | SQS / Pub-Sub / Kafka / RabbitMQ *(multi-select)* |
| **CI/CD** | GitHub Actions / GitLab CI / Jenkins / None |

Selecting "None" for any question skips the related files — only what's relevant to your
stack gets generated.

> **About Python:** `scripts/qa_track.py` and `scripts/coverage_report.py` are standalone
> Python 3 utilities. They are independent of the test framework you choose — even if your
> tests run in TypeScript or another language, these scripts still need Python 3. The
> generated `PREREQUISITES.md` lists every system dependency for your specific stack.

### Options

```
qi [OUTPUT_DIR] [--dry-run]

  OUTPUT_DIR    Where to create the project (default: ./<project-slug>)
  --dry-run     Print the file list without writing any files
```

---

## What gets generated

### Always generated (every project)

| File | Purpose |
|---|---|
| `CLAUDE.md` | AI constitution — under 200 lines, only the non-negotiable; points at rules, skills, hooks and decisions |
| `COVERAGE.md` | Coverage tracker template, recomputed by `scripts/coverage_report.py` |
| `AUTONOMY.md` + `.claude/autonomy.json` | What the agent may do alone per task (levels 0–3), how a task earns more, session override, TDD phases |
| `.claude/settings.json` + `.claude/hooks/` | The gates as code: `protect_paths.py` (no secrets, no generated files, no approvals, `QI_PHASE` TDD guard), `guard_bash.py` (no force-push, no push to main, no `--no-verify`, no reading `.env`, autonomy gates), `stop_gate.py` (no ending a turn with COVERAGE.md stale). Each has `--self-test` |
| `.claude/rules/assertion-validity.md` | 6 principles for valid QA assertions — `paths: tests/**, specs/**, qa/**` |
| `.claude/rules/evidence-based-qa.md` | What counts as evidence — `paths: tests/**, qa/**, reports/**` |
| `.claude/rules/environment-safety.md` | Dev/staging OK, prod never — always on |
| `.claude/rules/connection-validation.md` | Pre-flight connector checklist — always on |
| `.claude/rules/coverage-sync.md` | Keeping coverage numbers in sync — `paths: specs/**, COVERAGE.md` |
| `.claude/rules/feedback-loop.md` | Post-session debrief process |
| `.claude/rules/reusable-test-data.md` | Reusable E2E test data pattern — `paths: tests/**` |
| `.claude/rules/dependencies.md` | Newest stable release, after proof: what "validated" means and who merges |
| `.claude/skills/<name>/SKILL.md` | One folder per skill, frontmatter with `name` and a third-person `description`, body under 500 lines. Core set: `ticket-intake`, `verify-ticket`, `gap-analysis`, `sprint-report`, `json-schema`, `fix-tests`, `diagnose`, `report-bug` |
| `docs/decisions/` | Architecture decision records (MADR): README, TEMPLATE and `0001-hooks-enforce-the-constitution` |
| `scripts/qa_track.py` | AI-usage activity tracker |
| `scripts/coverage_report.py` | Recomputes COVERAGE.md from specs; `--check` for gaps, `--verify` for drift (used by the stop hook) |
| `specs/README.md` | How to write domain specs |
| `qa/dossiers/TEMPLATE.md` | Ticket dossier: comments, attachments, PRs, linked tickets, with sources |
| `PREREQUISITES.md` | System dependencies for your stack (Python, Node.js, Java…) |

Skills whose steps write outside the repo (`report-bug` files a ticket, `comm-broadcast`
posts to the team channel) carry `disable-model-invocation: true`: they run only when a
human invokes them.

### Generated conditionally (based on your answers)

| Condition | File |
|---|---|
| Tracker + doc platform or test repo | `.claude/rules/pipeline.md`, `.claude/agents/*`, skills `handoff-protocol`, `convention-check`, `discovery` (+ `bdd-writer` with a test repo) |
| Communication platform selected | `.claude/skills/comm-broadcast/SKILL.md` (human-invoked only) |
| Any SQL database selected | `.claude/skills/sql-query/SKILL.md` |
| Any NoSQL database selected | `.claude/skills/nosql-query/SKILL.md` + `scripts/nosql_query.py` |
| Web UI selected | `.claude/skills/web-ui/SKILL.md`, `.claude/rules/test-execution-path.md` |
| iOS or Android selected | `.claude/skills/mobile/SKILL.md` (tailored to Appium / Detox / native) |
| AWS / GCP / Azure selected | `.claude/skills/cloud-logs/SKILL.md` |
| Any queue selected | `.claude/skills/queue-testing/SKILL.md` |
| Performance tool selected | `.claude/skills/performance/SKILL.md` (k6 / Locust / JMeter / Gatling / Artillery); the load command is gated by the `execute-on-staging` level |
| Confluence selected | `.claude/rules/confluence-editing.md` |
| GitHub Actions selected | `.github/workflows/tests.yml`, `.github/dependabot.yml` (pip, npm when the framework needs it, actions; weekly, grouped) |
| GitLab CI selected | `.gitlab-ci.yml` |

### Hooks and autonomy in one minute

```bash
python3 .claude/hooks/guard_bash.py --self-test        # every hook ships its own cases
QI_PHASE=red claude                                    # only tests may change this session
QI_AUTONOMY_OVERRIDE="execute-on-staging=2" claude     # raise one level, one session
```

A hook refusal is a rule, not a bug to work around. Levels in `.claude/autonomy.json`
change only through the promotion rule in `AUTONOMY.md`, in a PR the QA engineer opens.

---

## Adding new options

The available choices live in [`qi/prompts.py`](qi/prompts.py). To add a new tracker,
database, or cloud provider, add a `questionary.Choice` to the relevant list and update
the corresponding Jinja2 template in [`qi/templates/`](qi/templates/).

---

## Design principles

- **Claude-first, declared** — designed for Claude Code; works with any AI that reads markdown
- **Framework-agnostic** — delivers process and AI prompts, not a test framework
- **Conditional output** — only the skills/rules relevant to your stack are generated
- **Proven patterns** — rules and skills derived from real QA work, not theory
- **Enforced, not just written** — the non-negotiable rules exist twice: as prose and as hooks
- **Portable** — install from git anywhere; skills and rules in a standard layout other agents read

---

## Development

```bash
git clone https://github.com/rsbarroco/qi-template
cd qi-template
pip install -e ".[dev]"
python -m pytest -q                       # unit + generated-script + hooks + acceptance (Gherkin) tests
python -m evals run ticket-intake --dry-run   # eval graders on the untouched fixture
```

See `tests/README.md` for the test pyramid and `evals/README.md` for the agent evals.

```bash
# (kept for copy-paste)
pytest tests/ -v
```

## License

MIT. See [LICENSE](LICENSE).
