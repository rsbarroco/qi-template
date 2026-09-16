# Evals — do the generated skills actually steer the agent?

A skill is a prompt. A prompt is a hypothesis about agent behaviour. This folder holds
the experiments that test the hypothesis, so every change to a template is measured
against a baseline instead of eyeballed.

Method, in the order Anthropic recommends for Agent Skills: **evals before extensive
documentation**. Three cases per skill, a baseline run, then iterate.

## How a run works

```
evals/<skill>/
  fixture.json         Config used to render a throwaway project with the generator
  seed/                Files copied on top of the rendered project (tickets, specs, tests)
  cases/<case>.json    query + expected behaviour + code graders
  runs.jsonl           one line per run (cost, duration, turns, grader results)
  labels.jsonl         one line per human verdict (pass/fail + one-sentence critique)
```

1. The runner renders `fixture.json` with the real generator into `evals/.runs/…/project/`,
   copies `seed/` on top, and commits it as the baseline.
2. It runs `claude -p "<query>"` inside that project with the login of whoever is running
   it. No API key is needed; a Claude Code subscription is enough. `--max-budget-usd`
   caps every run.
3. **Graders look at the final state of the disk and at the final answer, never at the
   transcript.** Did the tracking record appear? Did any file under `tests/` change?
   Does the answer contain an evidence table? A grader is code; it does not judge prose.
4. The run is appended to `runs.jsonl`. A human labels it later.

## Why humans label the first 30 runs

Code graders catch mechanics. They cannot tell whether the agent *asserted without
showing*, which is the verdict that matters most to the author of this template. So the
first 30 runs of every skill get a human `pass`/`fail` with a one-sentence critique. Only
after that does an LLM judge enter, and its prompt is tuned until it agrees with the
human labels. Never fully retire the human column.

## Commands

```bash
pip install -e ".[dev]"

python -m evals run ticket-intake                 # 1 run of every case
python -m evals run ticket-intake --case happy-path --runs 5
python -m evals run ticket-intake --dry-run       # render + seed, no claude call, grade as-is

python -m evals label ticket-intake               # walk through unlabeled runs
python -m evals report ticket-intake              # pass rates, cost, human agreement
```

## Reading a report

| Column | Meaning |
|---|---|
| graders | share of runs where every code grader passed |
| human | share of labeled runs marked `pass` |
| agree | share of labeled runs where graders and human agree; low agreement means the graders miss what you care about, so write a new grader, not a new rule |
| cost | mean `total_cost_usd` per run as reported by `claude -p` |

## Rules for writing a case

- One case per behaviour, three per skill minimum: the happy path, the case where the
  skill must **refuse** or stop at a gate, and the ambiguous case where the right
  answer is a question, not an invention.
- `expected_behavior` is for the human labeler. `graders` are for the machine. Both are
  required.
- A grader must be able to fail. Run the case with `--dry-run` first: on the untouched
  fixture at least one grader per case must fail, or the case proves nothing.
- Fixture seeds are fake. Ticket keys, names and URLs must never be real client data.

## Known baseline gaps this harness is meant to expose

- Generated skills live at `.claude/skills/<name>.md`. Claude Code discovers skills at
  `.claude/skills/<name>/SKILL.md`, so today the agent only follows a skill if it reads
  the file because `CLAUDE.md` told it to. The `ticket-intake` evals measure how often
  that actually happens. Fixing the layout is a separate change; this harness is how we
  will know the fix worked.
