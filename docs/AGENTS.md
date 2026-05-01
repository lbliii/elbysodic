# Product And Architecture Steward

## Steward

Product and architecture steward for `docs/architecture/`, `docs/product/`, and
the README/AGENTS narrative when it explains Elbysodic's direction.

## Protects

- The PBP-native mission: faces, rosters, scenes, plotters, wanted hooks,
  claims, reserves, director materials, and writing flow stay first-class.
- Architecture docs preserve tenant boundaries, membership-vs-character
  identity, repository/service layering, and migration discipline.
- Product docs remain decision guides for agents, not aspirational clutter.
- UI vocabulary docs stay consistent with promoted components and current
  route surfaces.

## Must Not Become

- A backlog landfill or speculative manifesto detached from code.
- Generic SaaS language that erases roleplay culture.
- A duplicate of implementation details better expressed in tests or code.

## Documentation Ownership

Owns `docs/architecture/*.md`, `docs/product/*.md`, README architecture/product
sections, and root `AGENTS.md` product doctrine. When code changes alter a
primitive, control pattern, navigation rule, or migration boundary, update the
relevant doc in the same PR.

## Local Checks

- `rg` for conflicting terms before changing product vocabulary.
- `uv run ruff check .` when doc examples include Python snippets.
- `uv run pytest -q --tb=short` when documentation claims are backed by tests.

## Public Contracts And Safety

- Do not weaken `community_id`, membership, character, or staff-role
  boundaries in prose.
- Keep examples in PBP language and make clear whether a feature is current,
  planned, or deliberately deferred.
- Cross-cutting docs changes should include Steward Notes naming affected code
  domains and tests that prove the claim.
