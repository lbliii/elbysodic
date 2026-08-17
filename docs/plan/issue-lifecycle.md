# Plan: GitHub issue lifecycle (swarm-ready specs)

- **Status:** Accepted (process freeze)
- **Date:** 2026-08-17
- **ADR:** [0001-issue-lifecycle.md](../adr/0001-issue-lifecycle.md)
- **Templates:** [`.github/ISSUE_TEMPLATE/`](../../.github/ISSUE_TEMPLATE/)
- **Agent stigmergy:** [`field-guide/`](../../field-guide/)

## Why this matters

Large tasks are trees. A planner that also implements fills its context
with leaf detail and drifts. A worker that also designs re-decides
questions already settled elsewhere. GitHub issues are the durable
intent store for Elbysodic; they must be **specs that lower into owned
leaves**, not human tickets that agents reinterpret.

Without a lifecycle freeze:

1. Epics stay prose essays; workers invent schema mid-flight.
2. Two leaves touch the same megafile and thrash.
3. Exit criteria are checkboxes no CI can grade.
4. Design decisions reappear in every subtree (split-brain).
5. `ready` / `blocked` become decoration instead of the lease gate.
6. `plans/in-progress/` becomes a second tracker that goes stale.

**Fix:** Treat the issue graph as the work DAG. Planners own sagas,
epics, and design issues. Workers only claim `type:leaf` + `ready`
issues. Shared ADRs, steward maps, and the field guide carry decisions
and surprises between trajectories.

## Which graph this is

Graph-driven development mixes four graphs. Elbysodic uses **one** of
them as the executable store:

1. **Intent / decision graph** — saga, epic, design, ADRs, minority
   reports. Lives in issue bodies and `docs/adr/`.
2. **Work DAG** — this document. Nodes are issues. Edges are parent,
   blocked-by, design cite, and owned-path overlap.
3. **Frozen planner subgraph** — Orrery constellations. Product SKU,
   not this board.
4. **Code knowledge graph** — GID-style file/call graphs. Not in this
   repo. Owned paths plus the megafile list are the slice.

Do not add `.gid/`, `.agraph.yaml`, or a `specs/` tree beside GitHub.

## Principles

1. **Specs as prompts** — The scarce resource is the right description
   of intent. Issue bodies are the unit of work, not chat history.
2. **Planner never implements; worker never plans** — Design questions
   stay on saga / epic / design issues. Leaves execute frozen
   acceptance.
3. **One decision owner per subtree** — If two leaves would decide the
   same question, collapse it into a design issue or ADR first.
4. **Owned paths** — Every leaf names the paths it may touch. Hotspots
   need explicit carve-outs or a prior split issue.
5. **Machine exit criteria** — Prefer pytest, `make check`,
   contract-diff, or documented smoke over prose-only checkboxes.
   Harness evaluates done; models do not self-certify.
6. **`ready` is the lease** — Workers start only on `ready` leaves.
   Waiting on humans or deps uses `blocked` and does not hold an agent
   lease.
7. **Stop And Ask blocks `ready`** — A leaf that would change a Stop
   And Ask surface cannot be `ready` until a closed `type:design`
   issue or an ADR exists. See root `AGENTS.md`.
8. **Neighborhood context** — A worker reads the leaf, cited freezes,
   owned paths, and the nearest `AGENTS.md`. Not the saga essay, not
   chat, not the plans pile.
9. **Stigmergy over ceremony** — Capture surprise in `field-guide/`
   and lasting decisions in `docs/adr/`.
10. **Multiple root sagas** — Realm Studio, Writer Network, Continuity
    Graph, and production trust may each have a root saga. `board`
    reports per saga. Do not flatten into one evergreen ranking file.
11. **Plans are not specs** — `plans/` is a live index and evidence
    queue. GitHub issues are executable.

## Issue tree

```text
saga (north-star thread)
 └── epic (outcome + exit criteria + child map)
      ├── design (freeze one decision / schema / contract)
      └── leaf (owned paths + machine acceptance)
```

| Kind | Label | Role | Opens when | Closes when |
| --- | --- | --- | --- | --- |
| **Saga** | `type:saga` | Product / strategy thread | A multi-epic north star appears | The thread is obsolete or absorbed |
| **Epic** | `type:epic` | Outcome-sized subtree | Outcome and exit criteria are known | Exit criteria graded true |
| **Design** | `type:design` | Planner-owned decision | Ambiguity would otherwise fork leaves | Decision recorded; ADR linked if lasting |
| **Leaf** | `type:leaf` | Worker-owned unit | Paths + acceptance are frozen | Machine acceptance passes + PR merged |

Bugs use the bug template (still a leaf: owned paths + repro
acceptance). `type:task` is retired; migrate remaining tasks to
`type:leaf`.

## Edge grammar

Every non-root issue names typed edges in the body:

- **Parent saga:** `#N` on every epic
- **Parent epic:** `#N` on every design and leaf (or parent design if
  the leaf only implements that freeze)
- **Blocked by:** `#N` when labeled `blocked`
- **Design cite:** ADR path or design issue number under Decisions
  frozen
- **Owned-path overlap:** if two ready leaves share a megafile or the
  same owned directory, serialize them

`board` flags: orphan epics (no parent saga), leaves missing parent /
owned paths / acceptance, `ready`+`blocked` on the same issue, and
path-overlap pairs that must not run in parallel.

## Required fields by kind

### Saga

- North-star sentence
- Provenance (docs, ADRs, related sagas)
- Workstream / epic list (links, not a fake checklist of code)
- Architectural boundaries and **Not now**
- Success signal (observable, not aspirational)

### Epic

- `**Parent saga:** #N`
- **Outcome** (one paragraph)
- **Scope** / non-goals
- **Decisions already made** (ADR links or “none — see child design
  issues”)
- **Child map** (design + leaf issues, or “to be filed after design”)
- **Exit criteria** (gradable)

### Design

- `**Parent epic:** #N`
- Question being frozen
- Options considered (short)
- Decision + consequences
- What leaves may assume after close
- Link or create ADR when the decision outlives the epic

### Leaf

- `**Parent epic:** #N` (or parent design if the leaf only implements
  that freeze)
- **Outcome** (one sentence)
- **Owned paths** (allowlist of files/dirs the worker may change)
- **Out of scope paths** (optional explicit deny)
- **Decisions frozen** (ADR / design issue cites — do not re-decide)
- **Acceptance** — at least one machine check, for example:
  - `uv run pytest tests/test_foo.py -q`
  - `make check`
  - `make contract-diff`
  - documented HTTP or Railway smoke
- Labels: `type:leaf`, priority, category/pillar when known, and
  exactly one of `ready` or `blocked`

## Label lifecycle

| State | Labels | Meaning |
| --- | --- | --- |
| Planning | `type:design` or `type:epic` without `ready` | Planner work; workers do not claim |
| Blocked | `blocked` (remove `ready`) | Dependency or human gate; no worker lease |
| Ready | `ready` (remove `blocked`) | Leaf may be claimed by a worker |
| In flight | assignee or PR link | One worker owner; do not double-claim |
| Done | issue closed; **remove `ready`** | Acceptance true; PR merged or epic exit graded |

Rules:

1. Never put both `ready` and `blocked` on the same issue.
2. Promoting a leaf to `ready` means its design deps are closed or
   explicitly waived on the issue body, and Stop And Ask does not
   apply (or is already frozen).
3. Epics may carry `blocked` while children proceed only if the epic
   exit still waits on an external gate — prefer blocking the specific
   leaf.
4. Priority (`priority:P0`–`P3`) is scheduling, not readiness.
5. Closing a leaf **must** drop `ready` (and `blocked`). Stale `ready`
   on closed issues poisons orchestrator board counts.
6. Keep existing `pillar:*`, `category:*`, and `wave:*` labels. Do not
   replace them with Orrery bare `saga` / `epic` / `leaf` names.

## Ownership and megafiles

Leaves that would edit any of the following need either a narrow
owned-path carve-out or a prior split/refactor leaf:

- `src/elbysodic/web/app.py`
- `src/elbysodic/web/pages/_layout.html`
- `src/elbysodic/web/static/elbysodic-theme.css` and
  `src/elbysodic/web/static/elbysodic-theme/`
- `src/elbysodic/web/surface_contracts.py`
- shared seed modules under `src/elbysodic/db/`

Prefer “touch only this page + its tests + the matching docs” shaped
leaves.

## Planner vs worker operating loop

```text
1. Planner opens / updates epic (outcome + exit).
2. Planner files design issues for contested decisions.
3. Design closes → ADR or in-body decision freeze.
4. Planner files leaves with owned paths + machine acceptance.
5. Planner flips leaves to ready when deps close.
6. Worker claims one ready leaf; implements only owned paths.
7. Worker runs acceptance and `uv run ruff check .` before push.
8. Worker opens PR citing issue number + acceptance commands
   (does not merge).
9. Orchestrator integrates: CI green → merge → close issue →
   drop `ready`.
10. On surprise, update field-guide/ (budgeted) or open a design
    issue — do not silently expand leaf scope.
```

Frontier models belong on steps 1–5 and on intentional breakage that
needs a new decision. Inexpensive models belong on step 6 when the
leaf is explicit.

## Intentional breakage

If a leaf must change a core contract outside its owned paths:

1. Stop and open or resume a **design** issue (or ADR).
2. Or, if urgency is justified, land a focused patch with an issue
   comment that states *why*, then file follow-up leaves for
   dependents.

## Review lenses (stacked)

| Lens | Cheap signal |
| --- | --- |
| CI ruff / format / ty | First-fail hygiene |
| `make check` | Template and app gates |
| Named pytest / contract-diff | Leaf-local grade |
| Steward swarm | Only when asked (`ask stewards`) |
| Human / planner | New ADR, auth, schema, or product direction |

No single lens is enough; prefer stacking cheap ones over one
expensive reread of the full transcript.

## Field guide

[`field-guide/`](../../field-guide/) is agent-curated shared context
for building Elbysodic. `field-guide/index.md` is the inject point.

Constraints:

- Line budget enforced in the index header
- Capture **surprises** and durable gotchas, not restatements of ADRs
- Prefer links to ADRs / ops docs over pasting large specs
- Humans may prune; agents may edit within budget

## Templates and scripts

| Asset | Purpose |
| --- | --- |
| [`AGENTS.md`](../../AGENTS.md) | Simple invokes: `board`, `burndown`, `claim #N`, … |
| `.github/ISSUE_TEMPLATE/*.yml` | Form-enforced required fields |
| `.github/PULL_REQUEST_TEMPLATE.md` | Cite leaf, paths, acceptance |
| `docs/adr/` | Lasting decisions leaves must cite |
| Steward `AGENTS.md` maps | Domain constitution, not the planner |

## Adoption checklist

- [ ] New work uses the saga / epic / design / leaf templates
- [ ] Open leaves that an agent could start have `type:leaf` + `ready`
      or `blocked`
- [ ] Each ready leaf lists owned paths and a machine acceptance
      command
- [ ] Epics link parent saga and child issues
- [ ] Design decisions that outlive an epic land an ADR
- [ ] PRs fill the PR template and name the acceptance command run
- [ ] Workers run `uv run ruff check .` before push
- [ ] Closed leaves no longer carry `ready`
- [ ] Surprises go to `field-guide/` within budget
- [ ] `plans/` is an index, not a second issue tracker

## Non-goals

- Replacing GitHub with another tracker
- Building an in-house swarm VCS or merge reconciler
- Hosting Orrery constellations or receipts as required process
- Mandatory story points, sprint ceremonies, or SLA theater
- A code knowledge graph or AGS YAML export (later, only if this DAG
  proves insufficient)

## Success signal

A frontier planner can decompose an epic into ready leaves; a cheaper
worker can complete a leaf using only the issue body + cited ADRs +
owned paths; CI grades acceptance without re-reading chat.
