# ADR 0001: GitHub issue lifecycle as the work DAG

- **Status:** Accepted
- **Date:** 2026-08-17
- **Plan:** [issue-lifecycle.md](../plan/issue-lifecycle.md)

## Context

Elbysodic already has steward constitutions, Stop And Ask, and GitHub
`type:saga` / `type:epic` / `type:task` labels. Agents still treated
`plans/in-progress/` as a second tracker, re-decided design in chat, and
could not claim a worker-sized unit with owned paths and machine
acceptance.

Orrery freezes the same problem as a saga → epic → design → leaf tree
with a `ready` lease. Dori keeps `plan/` as a live index, not shipped
behavior. Graph-driven development names four graphs (intent, work DAG,
frozen planner subgraph, code knowledge graph). Elbysodic needs the
work DAG on GitHub without standing up a second graph store.

## Decision

1. **Keep the `type:` prefix.** Add `type:design` and `type:leaf`.
   `ready` and `blocked` are gate labels, not types.
2. **Retire `type:task` as the worker unit.** Existing tasks migrate to
   `type:leaf`.
3. **Stop And Ask blocks `ready`.** A leaf that would change a Stop And
   Ask surface cannot carry `ready` until a closed `type:design` issue
   or an ADR exists.
4. **Park July upstream Chirp / Chirp-UI work.** Sagas #214–#218 and
   children stay unbeleafed / `blocked` until a later planning session.
   Do not mint ready leaves under #217 until the adopt-vs-exit design
   issue closes.
5. **Orrery receipts are optional later.** Leaves do not require
   `decision-bind` or `acceptance-bind`. Machine acceptance is a local
   command (pytest, `make check`, contract-diff, documented smoke).
6. **GitHub is the work DAG.** Edge grammar: parent saga/epic, `blocked
   by #N`, design cite, owned-path overlap implies serialize. No
   `.gid/` or `.agraph.yaml` in this wave.
7. **Worker context is the local neighborhood.** Leaf body + cited
   freezes + owned paths + nearest `AGENTS.md`. Not the saga essay, not
   chat history, not the plans pile.
8. **Multiple root sagas are allowed.** `board` reports per saga. Do
   not flatten pillars plus production trust into one evergreen ranking
   file.

## Consequences

- `docs/plan/issue-lifecycle.md` is the process standard.
- `.github/ISSUE_TEMPLATE/` enforces required fields.
- `plans/` is a live index and evidence queue. GitHub issues are
  executable specs.
- `field-guide/` captures agent surprises within a line budget.
- Stewards remain domain constitution. They are not the planner.
  Workers do not spawn steward swarms unless asked.

## Non-goals

- Orrery constellation runtime inside this repo
- GID / AGS files as a second spec store
- Changing tenant, membership, character, privacy, schema, or theme CSS
  as part of adopting this process
