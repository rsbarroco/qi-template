# Architecture decision records — QI-template

Decisions about **this repository**, not about the projects it generates. A generated
project gets its own `docs/decisions/`, rendered from `qi/templates/decisions/`; this
folder is the template eating its own food.

One file per decision, MADR style, numbered without gaps. The **Confirmation** section
says how the decision is checked: a test, a CI job, a script. A decision with no
confirmation is a wish.

Status flow: `proposed` → `accepted` → `deprecated` or `superseded by [ADR](...)`.
Never edit an accepted decision's Decision section; supersede it.
