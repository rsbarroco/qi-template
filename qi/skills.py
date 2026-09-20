"""Skill catalogue: the frontmatter every generated skill carries.

Generated skills follow the Agent Skills layout (https://agentskills.io): one folder per
skill, `SKILL.md` inside, YAML frontmatter with `name` and a third-person `description`,
body under 500 lines, scripts next to the skill when they serve only that skill. Skills
whose steps write to a system outside the repo (a tracker, a chat channel) are marked
`disable-model-invocation: true`, so only a human invocation (`/name`) runs them.
"""
from __future__ import annotations

from dataclasses import dataclass

MAX_BODY_LINES = 500


@dataclass(frozen=True)
class SkillMeta:
    name: str
    description: str          # third person, what it does and when to use it
    side_effect: bool = False # writes outside the repo -> disable-model-invocation

    @property
    def template(self) -> str:
        return f"skills/{self.name}.md.j2"

    @property
    def output(self) -> str:
        return f".claude/skills/{self.name}/SKILL.md"

    def frontmatter(self) -> str:
        description = self.description.replace('"', '\\"')
        lines = ["---", f"name: {self.name}", f'description: "{description}"']
        if self.side_effect:
            lines.append("disable-model-invocation: true")
        lines.append("---")
        return "\n".join(lines) + "\n\n"


_CATALOGUE = [
    SkillMeta("ticket-intake", "Drives a ticket through the eight intake steps (track, dossier, inventory, author, approve, execute, automate, sync). Used whenever a ticket key is handed over to test, verify or automate."),
    SkillMeta("verify-ticket", "Runs the verification loop for an approved ticket: requirements matrix, execution on dev then staging, evidence per case. Used during the execute step of the intake."),
    SkillMeta("gap-analysis", "Compares the acceptance criteria with the existing cases and lists what is not covered. Used before authoring new cases."),
    SkillMeta("sprint-report", "Builds the end-of-sprint AI-usage report from the activity tracker records. Used at the end of a sprint or on demand."),
    SkillMeta("json-schema", "Validates API payloads against their schema and detects silent no-ops. Used when a case asserts on a response body."),
    SkillMeta("fix-tests", "Diagnoses and repairs a failing automated test without weakening the assertion. Used when CI or a local run goes red."),
    SkillMeta("diagnose", "Isolates the cause of an unexpected behaviour with one variable changed per observation. Used when a case fails and the reason is not obvious."),
    SkillMeta("report-bug", "Files a structured, facts-only bug report in the task tracker after a manual reproduction. Used on a failed_scenario verdict.", side_effect=True),
    SkillMeta("handoff-protocol", "Defines the contract every sub-agent dispatch carries and how the result is written back. Used when reconstructing or handing off a ticket in the pipeline."),
    SkillMeta("convention-check", "Checks a test design document or test case against the naming and structure conventions and returns findings by severity. Used after every sub-agent output."),
    SkillMeta("discovery", "Finds what already exists for a ticket in the tracker, the documentation platform and the test repository. Used on a cache miss during cold start."),
    SkillMeta("bdd-writer", "Writes Gherkin scenarios from an approved test design document, one scenario per acceptance criterion. Used by the bdd phase of the pipeline."),
    SkillMeta("comm-broadcast", "Posts QA lifecycle notifications (brief, advisory, escalation, blocker) to the team channel. Used when a phase completes or a blocker appears.", side_effect=True),
    SkillMeta("sql-query", "Runs read-only SQL queries to verify persisted state against the expected outcome. Used when a case asserts on database rows."),
    SkillMeta("nosql-query", "Reads documents or keys from the NoSQL store to verify ingestion and publish events. Used when a case asserts on a document store."),
    SkillMeta("web-ui", "Drives the browser to verify a web flow and capture evidence from a single page load. Used for UI cases."),
    SkillMeta("mobile", "Drives the mobile app through the configured framework and captures evidence per step. Used for iOS and Android cases."),
    SkillMeta("cloud-logs", "Queries the cloud provider logs for the asynchronous side of a flow. Used when a case involves jobs, ingestion or queues."),
    SkillMeta("queue-testing", "Publishes to and consumes from the configured queues in non-production only and verifies the message contract. Used for message-driven flows."),
    SkillMeta("performance", "Designs and runs a load scenario with the configured tool and reads the thresholds. Used for performance cases."),
]

SKILLS: dict[str, SkillMeta] = {s.name: s for s in _CATALOGUE}


def skill(name: str) -> tuple[str, str]:
    """(template, output) pair for the generator."""
    meta = SKILLS[name]
    return meta.template, meta.output
