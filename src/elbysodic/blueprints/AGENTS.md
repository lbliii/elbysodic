# Blueprint Contract Steward

## Steward

Blueprint steward for `src/elbysodic/blueprints/` and the director-authored
program starter packet contract.

## Protects

- Program Blueprints describe PBP hubs in director language: program, roster
  faces, playable boards, materials, wanted hooks, and safe theme tokens.
- Validation errors stay human-readable for directors and import previews.
- Hydration paths go through repository/service boundaries, not ad hoc writes.
- Seed data and future YAML imports remain aligned to one shared shape.

## Must Not Become

- A live state store or replacement for normal staff tools.
- A free-form CSS/theme engine.
- A generic CMS import format without roleplay-specific shape.

## Documentation Ownership

Owns `docs/product/program-blueprints.md` and should update it with any
contract, validation, hydration, or allowed-token change.

## Local Checks

- `uv run pytest tests/test_program_blueprints.py -q --tb=short`
- `uv run pytest tests/test_tenant_repository.py -q --tb=short` when hydration
  touches repositories or tenant boundaries.
- `uv run ty check src/elbysodic/ tests/`

## Public Contracts And Safety

- Do not allow raw CSS, script tags, external font URLs, or layout-breaking
  theme controls in blueprint input.
- Keep created objects scoped to one community and one intentional owner.
- Validate duplicate slugs, missing starter content, unknown board/wanted
  types, invalid theme tokens, and broken material references before hydration.
