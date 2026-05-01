# Test Steward

## Steward

Test steward for `tests/`: behavior coverage, tenant-boundary regression tests,
rendered page tests, policy tests, and contract tests for product primitives.

## Protects

- Tests prove user-visible workflows as well as repository boundaries.
- New first-class primitives get tenant, membership, role, and rendered-surface
  coverage proportional to risk.
- Regression tests use PBP vocabulary and realistic seeded workflows instead
  of generic forum placeholders.
- Tests stay fast enough for `make test` and precise enough for local triage.

## Must Not Become

- Snapshot sprawl that blesses accidental markup.
- Only happy-path browser smoke tests.
- A second product spec that contradicts docs or root `AGENTS.md`.

## Documentation Ownership

Co-owns README and AGENTS development-command sections when test commands,
fixtures, or required local services change. Test names should document product
invariants clearly enough to guide future agents.

## Local Checks

- `uv run pytest -q --tb=short`
- `uv run pytest tests/test_tenant_repository.py -q --tb=short`
- `uv run pytest tests/test_forum_slice.py -q --tb=short`
- `uv run pytest tests/test_markup.py tests/test_policies.py tests/test_program_blueprints.py -q --tb=short`

## Public Contracts And Safety

- Boundary tests should seed multiple communities whenever leakage is possible.
- Rendered page tests should cover private rooms, staff desks, notification
  inboxes, and any route that exposes role- or membership-scoped data.
- Avoid depending on incidental HTML structure when a semantic assertion or
  service-level check would be clearer.
