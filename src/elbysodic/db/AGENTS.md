# Storage And Migration Steward

## Steward

Storage steward for `src/elbysodic/db/`: SQLite schema, migrations,
repositories, seed data, and tenant-boundary persistence checks.

## Protects

- Fresh schema and migrations describe the same current database shape.
- Repository methods keep `community_id` in reads and writes for product rows.
- Boundary errors are raised before cross-community joins or wrong-membership
  character actions are persisted.
- Demo seed data remains idempotent and useful for browser QA.

## Must Not Become

- A collection of page-specific SQL shortcuts.
- A migration graveyard with non-idempotent or untested upgrades.
- A cache for service-layer decisions that should remain explicit workflows.

## Documentation Ownership

Owns `docs/architecture/migrations.md` with the docs steward, and co-owns
tenant and security-boundary docs when schema or repository behavior changes.

## Local Checks

- `uv run pytest tests/test_tenant_repository.py -q --tb=short`
- `uv run pytest -q --tb=short` for schema changes.
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`
- Add migration tests that start from an older shape when changing schema.

## Public Contracts And Safety

- New product tables need `community_id` unless truly global infrastructure.
- Prefer partial unique indexes for nullable identity variants.
- Do not rewrite post history, read state, watches, revisions, or notification
  targets during thread lifecycle changes.
- Keep repository APIs tenant-aware even while the MVP seeds one community.
