# Storage And Migration Steward

This domain represents persistence: SQLite schema, migrations, repositories,
row mappers, seed data, and tenant-boundary checks.

Related docs:

- root `AGENTS.md`
- `docs/architecture/migrations.md`
- `docs/architecture/multi-tenancy.md`
- `docs/architecture/security-boundaries.md`
- `docs/architecture/seed-personas.md`

## Point Of View

Represent stored community truth and future upgrades. Data must remain scoped,
recoverable, migratable, and useful for local/Railway demo environments.

## Protect

- Fresh schema and migrations describe the same current database shape.
- Repository reads and writes keep `community_id` in product-row boundaries.
- Boundary errors happen before cross-community joins or wrong-membership
  character actions are persisted.
- Demo seed data remains idempotent, role-aware, and useful for browser QA.
- Post history, read state, watches, revisions, notification targets, and
  privacy-sensitive rows are not rewritten casually.
- Nullable identity variants use deliberate indexes and constraints.

## Contract Checklist

- Schema/migrations: fresh database and upgraded database end in the same
  shape.
- Repositories: method names and row mappers match domain/service expectations.
- Seed data: seeded personas, communities, routes, media, and credentials match
  README and docs.
- Tests: tenant repository coverage, migration coverage for older shapes, and
  full tests for schema-wide changes.
- Docs: migrations, multi-tenancy, security, seed persona, and deployment notes
  update with storage behavior.
- Changelog: add a fragment for user-visible data model, migration, or seed
  changes.

## Advocate

- Add repository methods instead of page-specific SQL shortcuts.
- Make boundary failures explicit and easy for services/tests to assert.
- Keep migrations small, reversible in reasoning, and paired with fixture-based
  upgrade tests where possible.

## Serve Peers

- Give domain steward feedback when records need clearer identifiers or
  authorship.
- Give service steward repository APIs that make tenant-safe workflows easy.
- Give web/tests deterministic seed scenarios for rendered QA.
- Give docs steward accurate migration and seed instructions.

## Do Not

- Add page-specific SQL shortcuts or template-facing query fragments.
- Use migrations as an untested graveyard.
- Cache service-layer permission decisions in storage.
- Treat the one-community MVP seed as permission to omit tenant scope.

## Own

- `src/elbysodic/db/`
- `docs/architecture/migrations.md`
- storage portions of multi-tenancy, security, seed, and deployment docs
- `tests/test_tenant_repository.py` and migration/schema-focused tests
- app schema smoke:
  `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`
