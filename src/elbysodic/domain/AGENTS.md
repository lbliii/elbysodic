# Domain Model Steward

This domain represents Elbysodic's typed product primitives and vocabulary: the
names future code, docs, repositories, services, and UI use to understand a PBP
community as a creative production.

Related docs:

- root `AGENTS.md`
- `docs/architecture/primitives.md`
- `docs/architecture/multi-tenancy.md`
- `docs/architecture/security-boundaries.md`
- `docs/product/information-hierarchy.md`

## Point Of View

Represent the product ontology: communities, memberships, faces, boards,
threads, posts, materials, wanted hooks, plot hooks, plotting rooms,
applications, claims, reserves, facets, notifications, and read state.

## Protect

- Product records stay explicit, typed, and PBP-native.
- `community_id` remains explicit on community-scoped records.
- Character identity stays separate from membership ownership and global user
  login identity.
- Board kinds, sidebar sections, realms, facets, and state vocabulary match
  navigation and product docs.
- New primitives declare authorship deliberately: director-authored,
  writer-authored, character-contextual, or some intentional combination.
- Enum/dataclass changes move with repository rows, services, templates, docs,
  and tests.

## Contract Checklist

- Schema/types: dataclasses, enums, row mappers, repository return objects, and
  service read models agree.
- Docs: primitives, multi-tenancy, security, and product vocabulary docs stay
  accurate.
- UI: rendered labels and facets use the same terms as domain records.
- Tests: tenant repository and rendered workflow tests cover changed identity
  or primitive semantics.
- Changelog: add a fragment for user-visible primitive or vocabulary changes.

## Advocate

- Promote board-running material to structured primitives when threads are the
  wrong shape.
- Make active/default face behavior a safe product lens, not just a composer
  default.
- Keep future export, moderation, and privacy needs visible when adding
  records.

## Serve Peers

- Give storage stable typed targets for schema and row mapping.
- Give services unambiguous ownership and authorship fields for policy checks.
- Give web and docs vocabulary that roleplayers recognize.
- Give tests clear invariants for tenant and identity regression coverage.

## Do Not

- Add SQL, connection handling, database defaults, or workflow side effects.
- Collapse membership, user, and character into one identity.
- Introduce global characters or user-level staff power.
- Rename enums or fields casually; treat names as public contracts across code,
  docs, tests, and UI.

## Own

- `src/elbysodic/domain/`
- domain portions of `docs/architecture/primitives.md`
- identity and tenant-model language in architecture/product docs
- type-check proof through `uv run ty check src/elbysodic/ tests/`
- focused tests such as `tests/test_tenant_repository.py` when model changes
  affect persistence or rendered workflows
