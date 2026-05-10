# Elbysodic Agent Constitution

## North Star

Elbysodic is a roleplay-native play-by-post studio layer. It exists to preserve
character identity, thread continuity, community aesthetic control, and the
emotional safety of pseudonymous writing spaces while making the board-running
work of directors, writers, faces, scenes, locations, events, canon, casting,
claims, reserves, and continuity native to the product.

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
- Use Chirp-UI patterns and token names first. Put Elbysodic theme tokens in
  `src/elbysodic/web/static/elbysodic-theme.css`.
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
- `plans/` owns durable roadmap and steward rollup snapshots, not scratch notes.
- `changelog.d/` owns user-visible release fragments.

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

- Run the relevant local gate: `uv run ruff check .`,
  `uv run ruff format . --check`, `uv run pytest -q --tb=short`,
  `uv run ty check src/elbysodic/ tests/`, and
  `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`.
- For doc-only changes, run the lightest relevant checks and say what was not
  run.
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
