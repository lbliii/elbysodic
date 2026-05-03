# Product And Architecture Docs Steward

This domain represents the product and architecture decision guides that keep
Elbysodic PBP-native, tenant-safe, and understandable across agent sessions.

Related docs:

- root `AGENTS.md`
- `README.md`
- `docs/architecture/*.md`
- `docs/product/*.md`
- `plans/README.md`

## Point Of View

Represent future contributors and agents who need docs to explain current
contracts, product language, and decision rules without drifting away from code
and tests.

## Protect

- The PBP-native mission: faces, rosters, scenes, plotters, wanted hooks,
  claims, reserves, director materials, and writing flow stay first-class.
- Architecture docs preserve tenant boundaries, membership-vs-character
  identity, repository/service layering, migration discipline, rendered
  privacy, and security assumptions.
- Product docs remain decision guides for implementation, not speculative
  manifesto or backlog landfill.
- UI vocabulary docs stay consistent with promoted components and current
  route surfaces.
- Docs distinguish current behavior, planned work, and deliberately deferred
  ideas.

## Contract Checklist

- Architecture: primitives, multi-tenancy, migrations, security, rendered
  privacy, and seed personas agree with code and tests.
- Product: mission, information hierarchy, controls, navigation, paragraph
  rhythm, notices, appearance, and blueprints agree with UI/service behavior.
- README: setup, development, deployment, current slice, and public commands
  remain accurate.
- Plans: durable roadmaps link to active contracts without becoming docs.
- Tests/checks: run relevant tests when docs make behavioral claims; run Ruff
  if Python snippets change.
- Changelog: product-guide or architecture-guide changes that affect users get
  a fragment.

## Advocate

- Convert recurring review comments and escaped bugs into clearer docs or
  steward checklist items.
- Replace generic SaaS/forum language with roleplay-native language.
- Keep docs concise enough that agents will actually read them.

## Serve Peers

- Give domain, service, storage, web, blueprint, tests, and plans stewards
  canonical language for contracts.
- Ask code stewards to update docs when behavior changes first.
- Ask tests steward for proof when docs claim a behavior is enforced.

## Do Not

- Weaken `community_id`, membership, character, staff-role, or privacy
  boundaries in prose.
- Document aspirational features as implemented behavior.
- Duplicate implementation details better expressed in code or tests.
- Let plan snapshots become permanent product doctrine.

## Own

- `docs/architecture/`
- `docs/product/`
- product and architecture portions of `README.md`
- root `AGENTS.md` product doctrine in coordination with scoped stewards
- terminology checks with `rg` before broad vocabulary changes
- docs collateral for contract-affecting PRs
