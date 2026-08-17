# Elbysodic Agent Constitution

## North Star

Elbysodic is a roleplay-native play-by-post studio layer. It exists to preserve
character identity, thread continuity, community aesthetic control, and the
emotional safety of pseudonymous writing spaces while making the board-running
work of directors, writers, faces, scenes, locations, events, canon, casting,
claims, reserves, and continuity native to the product.

Directionally, Elbysodic aligns around three product pillars:

- Realm Studio: director and staff workflows for opening, running, shaping,
  reviewing, exporting, and preserving one living PBP realm.
- Writer Network: writer-facing identity, active face, obligations, discovery,
  continuation, wanted hooks, plotting, and cross-realm entry paths.
- Continuity Graph: reviewed, source-linked memory from scenes into canon,
  characters, locations, events, claims, reserves, wanted hooks, and world
  materials after privacy and provenance gates are solid.

The canonical product strategy spine lives in
`docs/product/strategy-spine.md`.

## Non-Negotiables

- This is not a generic forum skin. Use PBP language: face, roster, thread,
  scene, plotter, wanted, claims, reserves, needs reply, waiting, caught up,
  and watching.
- The MVP is one community per install, but the architecture is tenant-aware
  from day one.
- Keep `community_id` explicit in schema, repositories, services, permissions,
  cache keys, exports, and tests.
- Users are global login accounts. `CommunityMembership` is the user's identity
  inside one community. Permissions, roles, names, and default face settings
  belong to membership, not user.
- Characters are public posting identities owned by exactly one membership in
  exactly one community. There are no global characters.
- Store membership for ownership and permissions, and character for public
  authorship or story context when a flow has both.
- Prefer server-rendered Chirp pages and small progressive-enhancement islands.
  Do not turn the app into an SPA.
- Keep Chirp + Kida + HTMX + Alpine. Do not adopt Chirp-UI as the design
  system (ADR 0002). Put Elbysodic primitives and theme tokens in
  `_components/` and `src/elbysodic/web/static/elbysodic-theme.css`.
- Repeated PBP UI concepts belong in
  `src/elbysodic/web/pages/_components/` before they become page-local CSS.
- Prefer repository and service methods over ad hoc SQL in page handlers.

## Architecture Boundaries

- `src/elbysodic/domain/` owns typed product primitives and vocabulary.
- `src/elbysodic/db/` owns SQLite schema, migrations, repositories, and seed
  data. Repository APIs stay tenant-aware.
- `src/elbysodic/services/` owns workflows, policy checks, read models,
  identity resolution, and orchestration.
- `src/elbysodic/web/` owns Chirp app setup, routes/pages/templates/static
  assets, navigation, composer behavior, security wrappers, and rendered
  privacy.
- `src/elbysodic/blueprints/` owns the director-authored Program Blueprint
  import/validation contract.
- `docs/` owns product and architecture decision guides.
- `research/` owns market, user, ecosystem, interview, competitive, outreach,
  and synthesis input. Research is signal, not product doctrine, until
  distilled into `docs/`, `plans/`, or steward guidance.
- `tests/` owns regression proof for repository boundaries, services, policies,
  rendered pages, markup, CLI behavior, and security.
- `plans/` owns a live index and evidence packets, not executable specs.
  GitHub issues are the work DAG. See `docs/plan/issue-lifecycle.md`.
- `changelog.d/` owns user-visible release fragments.
- `field-guide/` owns budgeted agent surprises while building Elbysodic.
- `docs/adr/` owns lasting decisions leaves must cite.

## Work lifecycle

How to work on this repo with agents. **Default:** you talk to the
**orchestrator** (this chat). It reads the board, plans, and **delegates**
planner/worker work to subagents.

| Doc | Role |
| --- | --- |
| [`docs/plan/issue-lifecycle.md`](docs/plan/issue-lifecycle.md) | Saga → epic → design → leaf standard |
| [`docs/adr/0001-issue-lifecycle.md`](docs/adr/0001-issue-lifecycle.md) | Process freeze (labels, DAG, Stop And Ask) |
| [`field-guide/index.md`](field-guide/index.md) | Budgeted surprises |
| [`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/) | Intake forms |
| [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) | PR shape |

**Invariant:** Workers claim only GitHub issues labeled `type:leaf` **and**
`ready`. Planners own `type:saga` / `type:epic` / `type:design`. Do not
re-decide ADRs in a leaf.

### Simple invokes

| You say | Mode | What happens |
| --- | --- | --- |
| **`swarm`** / **`drive`** / **`orchestrate`** | **Orchestrator (default)** | Parent stays in this chat; runs board → plan/unblock → delegate workers via subagents; loops until cap or you stop |
| **`swarm #N`** / **`drive epic #N`** / **`drive saga #N`** | Orchestrator scoped | Same, but only that epic/saga subtree |
| **`board`** / **`status`** | Read-only | Counts + ready list + DAG hygiene; no edits |
| **`burndown`** / **`unblock`** | Planner-only | Unblock queue (no product code); may be a subagent |
| **`plan #N`** | Planner-only | Design/epic freeze; usually a subagent |
| **`claim #N`** / **`work #N`** / **`ship #N`** | Worker escape hatch | Single leaf in-process or one subagent |
| **`triage #N`** | Planner escape hatch | Make one issue swarm-ready |

If you give a goal in plain language (“clear production-trust ready queue”),
treat it as **`swarm`** with that scope.

### Orchestrator mode (default contract)

The parent agent in this chat is the **orchestrator**. It does **not**
implement every leaf itself when parallel work is possible.

1. **Board** — `gh` summary: ready / blocked / open designs; ready count
   **per root saga**. Print DAG hygiene: orphan epics, leaves missing
   parent/owned-paths/acceptance, `ready`+`blocked` collisions, owned-path
   overlap pairs that must serialize.
2. **Plan gate** — If ready queue is empty or leaves lack owned paths, run
   or delegate **planner** work first (`burndown` / `plan #N` / `triage`).
3. **Delegate workers** — For each `type:leaf`+`ready` in scope (respect
   caps), launch a **Task subagent** with the worker contract below. Prefer
   **parallel** subagents when owned paths do not overlap.
4. **Integrate** — Track PRs, merge when asked, close issues, **drop
   `ready` on close**, refresh the board, report status in plain language.
5. **Stop conditions** — Hit the turn/leaf cap, empty ready queue, path
   conflict, or user interrupt. Caps are intentional pauses.

Caps (per orchestrator turn unless the user overrides):

| Knob | Default |
| --- | --- |
| Planner unblocks | ≤5 leaves → `ready`, or ≤2 designs closed |
| Parallel workers | ≤3 subagents (raise only if paths disjoint) |
| Leaves closed this drive | ≤5 unless user says “keep going” / `drive` |
| Megafile conflict | Serialize; do not parallelize overlapping owned paths |

**Plan gate bias:** A closed design/ADR that unblocks many leaves beats
shipping one more half-specified worker.

Status lines before each major step, e.g.:

- `Orchestrator: board — 3 ready, 41 blocked`
- `Orchestrator: planner — unblock #N deps`
- `Orchestrator: worker ×2 — #A, #B`
- `Orchestrator: integrate — PR …`

**Planner subagent** — read-only product code; may edit issues/ADRs/docs:

```text
You are an Elbysodic planner. Read AGENTS.md + docs/plan/issue-lifecycle.md.
No product implementation. Goal: <GOAL>.
Follow the burndown/plan/triage contract. Return: ready now / newly
unblocked / still blocked (why) / ADR paths touched.
```

**Worker subagent** — one leaf only:

```text
You are an Elbysodic worker. Read AGENTS.md + field-guide/index.md.
Claim ONLY GitHub issue #<N> if labels include type:leaf AND ready.
Restate outcome, owned paths, frozen decisions, acceptance.
Implement only owned paths; one PR with PR template; run acceptance.
Before push: `uv run ruff check .`.
If paths/acceptance missing, stop and report triage needed.
Do NOT merge; leave PR open for the orchestrator.
Neighborhood only: leaf body + cited ADR/design + owned paths + nearest
AGENTS.md. Do not ingest the parent saga essay or plans pile.
Return: PR URL, acceptance command + result, ruff clean, files touched.
```

### Mode contracts

**`board` / `status`**

1. `gh issue list` (open) and summarize counts by kind/gate **per root saga**.
2. Print `type:leaf`+`ready` titles (claimable now).
3. Print DAG hygiene: orphan epics, missing parent/owned-paths/acceptance,
   `ready`+`blocked` collisions, path-overlap serialize pairs.
4. Do not edit issues or code unless asked.

**`burndown` / `unblock` (planner)**

1. Read this file + `docs/plan/issue-lifecycle.md` + `field-guide/index.md`.
2. **No product implementation.** Issue/ADR/docs edits OK.
3. For each candidate: missing design / ADR / owned paths / acceptance /
   parent gate → fix, file design, or leave blocked with one-line reason.
4. Never fake-unblock. Cap: ≤5 leaves → `ready`, or ≤2 designs closed.
5. End with: **ready now / newly unblocked / still blocked (why)**.

**`plan #N` (planner)**

1. Fetch issue `#N`. If it is a leaf, stop and suggest `claim` or `triage`.
2. Freeze the decision; link or write ADR when it outlives the epic.
3. File or update child **leaves** with owned paths + machine acceptance.
4. Set `ready` only when deps are actually clear and Stop And Ask does not
   apply (or is already frozen); otherwise `blocked`.

**`claim #N` / `work #N` / `ship #N` (worker)**

1. Fetch `#N`. Abort unless labels include `type:leaf` and `ready`.
2. Restate: outcome, owned paths, frozen decisions, acceptance command.
3. If owned paths or machine acceptance are missing → stop; suggest
   `triage #N`.
4. Touch **only** owned paths.
5. Do not invent schema/policy; open a design issue or comment instead.
6. One PR using the PR template; run the acceptance command; report results.
7. **Before push:** `uv run ruff check .` must be clean.
8. Optional: one field-guide line for a true surprise (respect line budget).
9. Do not merge unless the user pinned `ship #N` with merge intent.

**Integrate hygiene** — when a leaf PR merges and the issue closes:

1. Remove `ready` (and `blocked` if somehow still present).
2. Confirm the board’s `type:leaf`+`ready` list no longer includes it.
3. If the merge unblocks dependents, either flip them to `ready` or leave a
   one-line comment on why they stay `blocked`.

**`triage #N` (planner)** — rewrite or comment so `#N` matches the
leaf/design template. Add `type:leaf` / `ready` / `blocked` correctly. No
feature code in this mode.

### Intelligence tiers

Frontier models belong on planner/design work and on intentional breakage.
Inexpensive models belong on explicit ready leaves.

## Stakes

When this repo regresses, writers can post as the wrong face, private/staff data
can leak across communities, directors can lose structured board-running
material, seeded demos can misrepresent the product, rendered pages can break
long-form writing flow, and future agents can drift into generic forum or SaaS
decisions that erase the culture the platform is meant to protect.

## Stop And Ask

Check in with a human before:

- public API, CLI, route, import path, blueprint, or release-protocol changes
- new runtime dependencies or dependency-source changes
- config, build, deployment, Railway, or release-surface changes
- data model, schema, migration, seed, or irreversible data changes
- irreversible operations or destructive filesystem/git actions
- security, auth, CSRF, session, role, permission, or privacy-boundary changes
- concurrency, lifecycle, startup, request-context, or persistence changes
- test/code disagreement where the intended product behavior is unclear
- unreproduced bugs or fixes based only on speculation

A leaf that would change a Stop And Ask surface cannot carry `ready` until a
closed `type:design` issue or an ADR exists. See
`docs/plan/issue-lifecycle.md` and `docs/adr/0001-issue-lifecycle.md`.

## Anti-Patterns

- Global characters, user-level staff power, or role checks detached from
  membership.
- Page handlers with one-off SQL for product rows.
- Structured board-running material forced into threads when it deserves its
  own primitive.
- Generic tags replacing director-defined facets.
- UI that hides writing context, active face, preview, drafts, or control
  affordances roleplayers need during long sessions.
- Theme or Blueprint inputs that accept raw CSS, script tags, external font
  URLs, or layout-breaking controls.
- Docs or tests that describe a different tenant, identity, navigation, or
  product vocabulary contract than the code implements.

## Steward System

Agents read this root constitution plus the closest scoped `AGENTS.md` before
making product or architecture decisions. Root is the constitution and routing
guide. Scoped files are domain stewards: they own local invariants, refusal
patterns, docs, tests, examples, fixtures, and checks.

Each steward uses this operating model:

- Point of View: who or what the domain represents
- Protect: invariants, contracts, quality bars, and failure modes
- Contract Checklist: concrete surfaces to inspect when this domain changes
- Advocate: features, fixes, and investments the domain should push for
- Serve Peers: upstream/downstream domains that need clearer contracts,
  diagnostics, docs, tests, or ergonomics
- Do Not: local anti-patterns
- Own: tests, docs, examples, fixtures, maintenance checks

Cross-boundary PRs should include short **Steward Notes** naming consulted
stewards, accepted/deferred findings, proof, collateral updates, and remaining
risks.

## Surface Contract Steward

The Surface Contract Steward is a cross-cutting steward for View Contract
Architecture. It coordinates the service, web, docs, and tests stewards when a
page or route needs a named contract between workflow state and rendered UI.

Consult it when work changes or creates a rendered surface, page-level read
model, discovery/search slice, shell/sidebar count, public preview, member
dashboard, staff queue, character posting surface, or director workflow room.

Surface contract review asks:

- Who is the audience: public visitor, member, owner, character-backed writer,
  staff, director, inactive member, or cross-tenant recovery visitor?
- Which service method owns the page state, and which read model does the
  template render?
- Which tenant, membership, character, staff, and publication boundaries are
  enforced before rendering?
- Which filtering, sorting, ranking, lifecycle, or discovery decisions are
  service-owned rather than template-owned?
- Which repeated PBP card, lane, queue, or action shape should become a shared
  read model or `_components/` pattern?
- Which rendered tests prove the contract, and which docs or privacy matrix
  rows need to move with it?

The Surface Contract Steward does not replace local stewards. It creates
tension across them so public, member, character, and staff state do not blur
inside templates or page handlers.

## Contract Checklist

For cross-surface changes:

- Identify every surface that should agree: CLI/API, programmatic use,
  protocol, schema/types, UI, docs, examples, scaffold/templates, tests,
  benchmarks, and changelog.
- Every accepted finding must name required proof and collateral updates, or
  explicitly say `no collateral: <reason>`.
- Docs, examples, and scaffold/templates move in the same PR as user-facing
  behavior unless synthesis records why they are unaffected.
- Contract-affecting PRs include a parity matrix when behavior spans multiple
  entrypoints.

## Steward Signal Format

Steward findings should be contract-oriented, evidence-backed, and
collateral-aware.

Use this format:

- Steward:
- Area:
- Severity: P0/P1/P2/P3
- Invariant:
- Evidence:
- User Impact:
- Required Fix:
- Required Proof:
- Collateral:
- Confidence:

## Steward Swarms

When the user asks for `ask stewards`, `bugbash`, `review swarm`, or
`steward synthesis`, and delegation is available:

- spawn independent steward agents for affected domains
- each steward reads root plus its closest scoped `AGENTS.md`
- each steward advocates only for that domain's interests
- each steward returns findings in the Steward Signal Format
- implementing agent owns synthesis and final decisions
- stewards advise and create useful tension; they do not own the integrated
  implementation
- keep PR scope bounded to accepted findings and their proof/collateral
- defer unrelated steward suggestions to not-now/follow-up

For backlog, roadmap, or prioritization work, consult all scoped stewards and
produce raw steward signals, confidence, dependencies, risks, convergence,
minority reports, ranked backlog, and not-now items.

## Steward Feedback Loop

- Steward miss: when a bug escapes an applicable steward, update the checklist,
  a regression test, a docs/snippet check, a routing rule, or record why the
  miss should not become policy.
- Steward overreach: when a steward repeatedly pulls unrelated work into PRs,
  narrow the checklist, split the steward, or move the concern to follow-up.
- Repeated high-quality findings should become checklist items.
- Repeated noisy findings should be pruned or clarified.
- Steward guidance evolves from evidence: escaped bugs, late collateral
  updates, CI/review misses, and recurring review comments.

## When To Consult

- Proactively consult stewards for cross-boundary, public-facing,
  hard-to-reverse, performance-sensitive, concurrency-sensitive,
  security-sensitive, or contract-affecting work.
- Consult the Surface Contract Steward for new or changed rendered surfaces,
  page-level read models, public catalog/search behavior, shell counts, staff
  queues, and any template currently making product, privacy, or ranking
  decisions.
- For UX, onboarding, navigation, writing-flow, Studio, Appearance Studio,
  wanted/backstage, application, claim, reserve, or public discovery changes,
  consult the user panel in `docs/product/user-personas-panel.md` in addition
  to affected technical stewards.
- Use the nearest steward for local work.
- Use multiple stewards when ownership lines cross.
- Parallelize steward consultation only when questions are independent.
- Keep final synthesis and implementation accountability with the implementing
  agent.

## User Panel

The user panel is a product-research complement to stewards. It represents
active writers, new face applicants, hook hunters, directors, staff moderators,
safety-boundary writers, and returning regulars. Use it to evaluate user jobs,
expectations, anxieties, flow clarity, and PBP vocabulary. It does not override
tenant, membership, character, staff, security, privacy, or architecture
contracts.

When the user asks for a user-panel review and delegation is available, spawn
independent panel agents from `docs/product/user-personas-panel.md`. Each
panelist should return findings in the User Panel Signal Format, and the
implementing agent owns synthesis, accepted/deferred decisions, proof, and
collateral.

## Ask Stewards

Trigger phrase: `ask stewards`.

For implementation work, consult affected stewards and return synthesis before
or during the change. Include accepted/deferred findings, merged duplicates,
minority reports, required proof, collateral updates, and not-now items.

For multi-surface work, include a parity matrix like:

| Contract | API/CLI | Programmatic | Protocol | Schema/Types | Docs | Examples | Tests |
|---|---|---|---|---|---|---|---|

For backlog, roadmap, or product sequencing work, consult all scoped stewards.
Favor convergence, dependency order, blast-radius reduction, public-contract
risk, user-visible correctness, risk reduction, and reversibility. Preserve
minority reports when a steward sees a real risk the majority downweights.

## Extension Routing

Elbysodic does not currently expose a general plugin system. The extension-like
contract is Program Blueprints:

- Blueprint parser and validation: `src/elbysodic/blueprints/`
- Blueprint hydration and workflow logic: `src/elbysodic/services/blueprints.py`
- Blueprint product contract: `docs/product/program-blueprints.md`
- Blueprint tests: `tests/test_program_blueprints.py`

## Done Criteria

- Agent work that implements a feature starts from a `type:leaf` + `ready`
  GitHub issue with owned paths and a machine acceptance command.
- Run the relevant local gate: `uv run ruff check .`,
  `uv run ruff format . --check`, `uv run pytest -q --tb=short`,
  `uv run ty check src/elbysodic/ tests/`, and
  `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`.
- For doc-only changes, run the lightest relevant checks and say what was not
  run. Run the leaf's named acceptance command when one exists.
- Update docs, changelog fragments, migration notes, examples, scaffold, or
  templates when user-facing behavior or public contracts change.
- Add performance, concurrency, security, or privacy notes when relevant.
- Every accepted steward finding has test/docs/example/benchmark proof or an
  explicit no-impact note.

## Review Notes

Flag these in commits, PRs, or final handoff when they appear:

- weird tests or brittle assertions
- unused public names or dead code
- suppressions and why they remain justified
- benchmark gaps for performance-sensitive changes
- free-threading, request-lifecycle, or SQLite persistence assumptions
- steward disagreement, minority reports, and deferred/not-now findings
- product-code/docs/tests/changelog drift
