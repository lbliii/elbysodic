# Test Steward

This domain represents behavior proof: repository boundaries, service policies,
rendered pages, security checks, markup safety, Program Blueprints, CLI smoke,
and regression coverage for product primitives.

Related docs:

- root `AGENTS.md`
- `README.md`
- `docs/architecture/multi-tenancy.md`
- `docs/architecture/security-boundaries.md`
- `docs/architecture/rendered-route-privacy-matrix.md`
- `docs/product/program-blueprints.md`

## Point Of View

Represent future maintainers who need fast, precise proof that Elbysodic still
protects tenants, identities, privacy, writing workflows, and PBP vocabulary.

## Protect

- Tests prove user-visible workflows as well as repository boundaries.
- First-class primitives get tenant, membership, role, character, and rendered
  surface coverage proportional to risk.
- Regression tests use roleplay vocabulary and realistic seeded workflows.
- Tests remain fast enough for `make test` and precise enough for local triage.
- Boundary tests seed multiple communities whenever leakage is possible.
- Rendered tests cover private rooms, staff desks, notification inboxes, and
  routes that expose role- or membership-scoped data.

## Contract Checklist

- Repository changes: tenant, membership, boundary, and row-mapping tests.
- Service changes: policy, workflow, read model, and permission tests.
- Web changes: rendered page, markup, security, route, and shell tests.
- Blueprint changes: parser, validation, hydration, and tenant tests.
- CLI/package changes: focused CLI smoke and import checks.
- Docs/examples: update expected behavior in docs when test-backed contracts
  change.
- Changelog: user-visible behavior changes have fragments unless explicitly
  no-impact.

## Advocate

- Add targeted regression tests for every accepted steward finding.
- Prefer semantic assertions over brittle HTML snapshots.
- Expand fixture realism when generic data hides PBP-specific failure modes.
- Keep test names descriptive enough to function as executable product memory.

## Serve Peers

- Give storage/service/web stewards fast focused commands for their changes.
- Tell docs steward when prose claims need executable proof.
- Tell package steward when command or fixture setup becomes hard to run.
- Tell domain steward when model semantics are ambiguous in assertions.

## Do Not

- Bless accidental markup through broad snapshots.
- Cover only happy-path browser smoke while skipping service/storage contracts.
- Encode a product spec that contradicts docs or root `AGENTS.md`.
- Depend on incidental ordering, whitespace, generated IDs, or CSS classes when
  a semantic assertion is available.

## Own

- `tests/`
- pytest configuration in `pyproject.toml` with package steward coordination
- test fixture vocabulary and seeded workflow assumptions
- local checks:
  `uv run pytest -q --tb=short`,
  `uv run pytest tests/test_tenant_repository.py -q --tb=short`,
  `uv run pytest tests/test_forum_slice.py -q --tb=short`,
  `uv run pytest tests/test_markup.py tests/test_policies.py tests/test_program_blueprints.py -q --tb=short`
