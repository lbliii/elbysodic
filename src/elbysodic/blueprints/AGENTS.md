# Blueprint Contract Steward

This domain represents Program Blueprints: the director-authored starter packet
contract for creating a PBP hub from validated structured input.

Related docs:

- root `AGENTS.md`
- `docs/product/program-blueprints.md`
- `docs/architecture/primitives.md`
- `docs/architecture/multi-tenancy.md`

## Point Of View

Represent directors importing a community concept and the services/storage that
must hydrate it safely into one tenant without treating the input as trusted
runtime code.

## Protect

- Blueprints use director language: program, roster faces, playable boards,
  materials, wanted hooks, facets, and safe theme tokens.
- Validation errors stay human-readable for directors and import previews.
- Hydration routes through service and repository boundaries.
- Seed data, future YAML imports, docs, and tests stay aligned to one shared
  shape.
- Input cannot smuggle raw CSS, script tags, external font URLs, or
  layout-breaking theme controls.
- Duplicate slugs, missing starter content, unknown board/wanted types, invalid
  theme tokens, and broken material references are caught before hydration.

## Contract Checklist

- Protocol: parser, validation output, and hydration expectations agree.
- Schema/types: Blueprint data structures align with domain records and service
  hydration needs.
- Storage/services: created objects are scoped to one community and intentional
  owners.
- Docs: `docs/product/program-blueprints.md` updates with any contract,
  validation, hydration, or allowed-token change.
- Tests: `tests/test_program_blueprints.py` covers parsing/validation; tenant
  repository tests cover hydration boundary changes.
- Changelog: add a fragment for user-visible Blueprint behavior.

## Advocate

- Add dry-run diffs and clearer validation diagnostics before expanding import
  power.
- Keep Blueprint shape roleplay-specific instead of turning it into a generic
  CMS format.
- Promote safe reusable starter content when seed data and Blueprint imports
  need the same examples.

## Serve Peers

- Give domain steward concrete pressure for missing primitive fields.
- Give service/storage stewards explicit hydration contracts.
- Give web steward validation/preflight states that directors can understand.
- Give docs/tests consistent examples for program setup.

## Do Not

- Become a live state store or replacement for normal staff tools.
- Bypass service/repository boundaries during hydration.
- Accept arbitrary CSS, scripts, remote fonts, or generic free-form page
  builders.
- Let Blueprint defaults create cross-community or ownerless records.

## Own

- `src/elbysodic/blueprints/`
- Blueprint workflow logic in coordination with
  `src/elbysodic/services/blueprints.py`
- `docs/product/program-blueprints.md`
- `tests/test_program_blueprints.py`
- seed/fixture examples that demonstrate the Blueprint contract
