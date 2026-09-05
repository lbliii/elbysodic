# Program Blueprint Hydration Plan


## Archival Note

Lifecycle: Superseded

Archived 2026-08-17. Apply/hydration work moved to GitHub (closed epic #85 and related). Residual apply policy is a GitHub design issue if still open.

Status: implementation complete on the issue #85 branch; archive after merge
Owner: Blueprint, service, storage, and test stewardship  
Created: 2026-05-02  
Last updated: 2026-07-20
Review by: 2026-05-30
Closure criteria: split into PRs for dry-run diffs, service-layer hydration,
rollback tests, tenant coverage, and Studio apply controls; archive once apply
is implemented or superseded.

## 2026-07-20 Closure Update

The typed current-realm diff and Studio apply workflow are implemented with
create-only, skip-existing, explicit-update, and dry-run modes. Apply rechecks
the accepted fingerprint and named capability before reserving a
fingerprint-and-mode command key. Hydrated primitives and the accepted audit
event commit in one repository transaction; deterministic late failures prove
row and command-reservation rollback, and durable failed events use sanitized
reasons.

Coverage now includes every supported primitive, same-slug rows in a second
community, writer ownership limits, repeated command rejection, v25 material
variant migration, rendered preview/stale/apply state, and unsafe input
validation. The implementation deliberately targets only the resolved current
realm; opening a new hosted realm remains a separate privileged workflow.

## 2026-05-09 Verification Update

Studio intake remains correctly dry-run-only. The Blueprint steward identified
the next production work as typed diff rows, unknown-key diagnostics, collision
semantics, stale-preview fingerprinting, transaction-backed apply, rollback
proof, idempotency, and ordinary-member denial. Seed hydration already mutates
demo data through a privileged path; future YAML apply should either share the
same planning semantics or explicitly document why seed remains privileged.

## Purpose

Studio intake parses and validates Program Blueprint YAML, shows exactly what
would be created, updated, skipped, or blocked, then applies only the accepted
current-realm fingerprint and collision mode. This plan records why the Apply
button follows that service-owned hydrator contract instead of bypassing it.

Program Blueprints are starter packets for PBP hubs: program identity, director
role, starter faces, playable boards, world materials, wanted hooks, safe theme
tokens, board media, and appearance vocabulary. Hydration must preserve that
director language while using normal repository and service boundaries.

## Steward Rollup

| Steward | Priority | Confidence | Evidence | Risk |
| --- | --- | --- | --- | --- |
| Root constitution | Keep new program material community-scoped and PBP-native. | High | Blueprints create communities, memberships, faces, boards, materials, wanted hooks, and theme context. | A generic import path could bypass the studio layer and tenant model. |
| Blueprint contract | Hydrate only after validation and human-readable preview. | High | `ProgramBlueprintPreview` already validates counts, unsafe theme keys, board media, and references. | An apply path without a diff makes duplicate and update behavior surprising. |
| Service layer | Put orchestration in `services/blueprints.py`, not page handlers. | High | Preview already routes through the service boundary and policy helper. | Page-local hydration would spread permission and rollback decisions. |
| Storage | Reuse repository methods and keep created rows tenant-scoped. | High | Existing repos already enforce community ids for boards, materials, wanted, characters, themes, and claims. | Cross-community references or partial writes would be hard to unwind. |
| Tests | Prove dry-run and mutation behavior with tenant fixtures. | High | Existing tests cover preview without hydration. | A happy-path import test alone would miss slug collisions and rollback leaks. |

## Product Decision

Hydration should be an explicit two-step Studio flow:

1. **Preview diff**: parse, validate, resolve collisions, and show create,
   update, skip, and blocked actions without writing.
2. **Apply previewed diff**: execute the exact accepted plan inside one
   service-layer transaction.

The preview diff is the product contract. Directors should see board, face,
material, wanted, and appearance changes in board-running language before they
commit.

## Hydration Contract

The first supported apply path should hydrate into a new or existing community
identified by blueprint program slug.

Rules:

- Existing community, role, character, board, material, wanted, and theme rows
  are matched by slug inside the target community.
- Missing rows are created.
- Existing board, material, and theme rows can be updated from the packet.
- Existing characters and wanted hooks should default to skip unless an
  explicit update mode is added, because writers may have edited live roster or
  casting language.
- Board media hydrates only after URL, alt text, treatment, focal point, and
  overlay validation.
- Appearance payloads hydrate only through approved token and variant fields.
- Raw CSS, scripts, external fonts, and template/layout overrides remain
  invalid input.
- Every created character and wanted hook gets an intentional owner membership,
  starting with the importing director membership unless the contract adds
  named owners later.

## Transaction And Rollback

Apply should run as a single transaction. If any planned action fails, the
entire hydration attempt should roll back and return a director-readable error.

Implementation shape:

- Add repository transaction helper if the current connection wrapper does not
  expose one cleanly.
- Resolve all target ids during diff planning where possible.
- Re-resolve during apply to avoid stale preview assumptions.
- Refuse apply when the submitted diff token no longer matches the current
  database state.
- Keep idempotency tests for applying the same packet twice.

## PR Sequence

1. **Hydration diff model**: add typed diff rows such as create, update, skip,
   blocked, and warning; keep preview read-only.
2. **Resolver service**: build `plan_program_blueprint_hydration()` in
   `services/blueprints.py` with policy checks and duplicate handling.
3. **Transaction-backed apply**: add `apply_program_blueprint_hydration()` with
   repository transaction support and rollback tests.
4. **Studio apply UI**: show grouped diff rows and enable Apply only for a
   valid, current diff.
5. **Tenant and privacy tests**: prove cross-community collisions do not attach
   rows to the wrong community and ordinary members cannot preview or apply.
6. **Docs update**: refresh `docs/product/program-blueprints.md` with the
   implemented duplicate and update semantics.

## Acceptance Checks

- Previewing a valid blueprint still writes no rows.
- Applying a valid blueprint creates or updates only the intended community.
- Applying the same blueprint twice is idempotent for create-on-missing rows.
- Slug collisions are shown as update, skip, or blocked before apply.
- A forced mid-apply failure leaves no partial program changes.
- Ordinary members cannot preview or apply.
- Board media and appearance fields cannot bypass validation.
- `uv run pytest tests/test_program_blueprints.py tests/test_tenant_repository.py tests/test_forum_slice.py -q --tb=short`
- `uv run ty check src/elbysodic/ tests/`

## Not Now

- Hosted public community creation.
- Background import jobs.
- File upload storage.
- Blueprint marketplace or theme packs.
- Per-row owner mapping UI beyond the importing director.
- Export round trip for boards and themes before import apply is stable.

## Resolved Questions

- Existing rows change only in explicit-update mode; create-only rejects live
  content collisions and skip-existing preserves them.
- Starter faces are created as importing-membership faces. Future applicant
  staging remains a separate onboarding design.
- Imported wanted hooks are created open and owned by the importing membership.
- The apply token hashes the source plus current typed diff rows and is paired
  with the selected mode in the command ledger.
