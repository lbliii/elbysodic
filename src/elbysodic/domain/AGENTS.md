# Domain Model Steward

## Steward

Domain model steward for `src/elbysodic/domain/` and the typed records and enum
vocabulary that name Elbysodic's product primitives.

## Protects

- Community, membership, character, board, thread, post, material, wanted,
  plotting, application, claim, reserve, and interaction records remain
  explicit and typed.
- Board kind, sidebar section, and realm vocabulary match navigation and
  product docs.
- Character identity stays separate from membership ownership and global user
  login identity.
- New structured primitives start with tenant scope and intentional authorship.

## Must Not Become

- A persistence layer with SQL, connection handling, or database defaults.
- A service layer with permission decisions or workflow side effects.
- A generic forum ontology that forgets PBP-specific concepts.

## Documentation Ownership

Co-owns `docs/architecture/primitives.md`,
`docs/architecture/multi-tenancy.md`, and product vocabulary references that
depend on core model names.

## Local Checks

- `uv run ty check src/elbysodic/ tests/`
- `uv run pytest tests/test_tenant_repository.py -q --tb=short`
- Add or update focused tests when a model change changes repository rows,
  read models, or rendered pages.

## Public Contracts And Safety

- Do not introduce global characters or user-level staff power.
- Keep `community_id` explicit on product records.
- If a flow can involve both writer and face, model membership for ownership
  and character for public story context.
- Coordinate enum or dataclass renames with repositories, services, templates,
  docs, and tests in the same change.
