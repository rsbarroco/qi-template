# QI — Quality Intelligence

Scaffold an AI-assisted QA project in seconds.

QI generates a **Claude-first QA constitution** — CLAUDE.md, rules, skills, scripts, and
CI config — customized to your team's stack. The generated project is ready to use with
[Claude Code](https://claude.ai/code) from day one, with proven patterns for evidence-based
QA, assertion validity, coverage tracking, and AI-usage reporting.

## Install

```bash
pip install git+https://github.com/rsbarroco/QI-template
# or: pipx install git+https://github.com/rsbarroco/QI-template
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
| `CLAUDE.md` | AI constitution — rules, constraints, workflow |
| `COVERAGE.md` | Coverage tracker template |
| `.claude/rules/assertion-validity.md` | 6 principles for valid QA assertions |
| `.claude/rules/evidence-based-qa.md` | What counts as evidence |
| `.claude/rules/environment-safety.md` | Dev/staging OK, prod never |
| `.claude/rules/connection-validation.md` | Pre-flight connector checklist |
| `.claude/rules/coverage-sync.md` | Keeping coverage numbers in sync |
| `.claude/rules/feedback-loop.md` | Post-session debrief process |
| `.claude/rules/reusable-test-data.md` | Reusable E2E test data pattern |
| `.claude/skills/ticket-intake.md` | QA intake workflow: track, dossier, inventory, author, approve, execute, automate, sync |
| `.claude/skills/verify-ticket.md` | Verification loop (RTM → evidence → transition) |
| `.claude/skills/gap-analysis.md` | Coverage gap analysis |
| `.claude/skills/sprint-report.md` | End-of-sprint AI-usage report |
| `.claude/skills/json-schema.md` | Payload validation + silent no-op detection |
| `scripts/qa_track.py` | AI-usage activity tracker |
| `scripts/coverage_report.py` | Recomputes COVERAGE.md from specs |
| `specs/README.md` | How to write domain specs |
| `qa/dossiers/TEMPLATE.md` | Ticket dossier: comments, attachments, PRs, linked tickets, with sources |
| `PREREQUISITES.md` | System dependencies for your stack (Python, Node.js, Java…) |

### Generated conditionally (based on your answers)

| Condition | File |
|---|---|
| Any SQL database selected | `.claude/skills/sql-query.md` |
| Any NoSQL database selected | `.claude/skills/nosql-query.md` |
| Web UI selected | `.claude/skills/web-ui.md` |
| iOS or Android selected | `.claude/skills/mobile.md` (tailored to Appium / Detox / native) |
| AWS / GCP / Azure selected | `.claude/skills/cloud-logs.md` |
| Any queue selected | `.claude/skills/queue-testing.md` |
| Performance tool selected | `.claude/skills/performance.md` (k6 / Locust / JMeter / Gatling / Artillery) |
| GitHub Actions selected | `.github/workflows/tests.yml` |
| GitLab CI selected | `.gitlab-ci.yml` |

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
- **Portable** — install from git anywhere; no registry account needed

---

## Development

```bash
git clone https://github.com/rsbarroco/QI-template
cd QI-template
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
