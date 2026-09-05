# Schema Migrations

Elbysodic supports fresh SQLite database creation and in-place database
upgrades. Fresh databases are created from the current schema in
`src/elbysodic/db/schema.py`. Existing databases are brought forward by the
legacy compatibility helpers in that module and then recorded in the migration
ledger.

## Current Version

The checked-in schema currently creates databases at version `26`. Calling
`create_schema()` creates or upgrades the database, ensures
`schema_migrations` exists, records the current schema as a baseline when no
ledger row exists, and sets SQLite `PRAGMA user_version`.

Version `1` is the historical baseline. Versions `2` and later are ordered
post-baseline migrations in `src/elbysodic/db/migrations.py`. This keeps the
prototype's existing schema bootstrap intact while giving future schema changes
an ordered migration path.

Version `22` adds user-owned passkey credentials and their user/time lookup
index. Version `23` rejects diagnosed legacy tenant-pair drift and then
installs insert/update triggers for every row family covered by the tenant
integrity audit. It also guards community default-theme and identity-accent
roots. The migration never guesses how to repair story-visible or private
rows: it names the affected table and row id, tells the operator to run the
content-free tenant integrity audit, and leaves version `22` recorded until the
row is repaired deliberately.

Version `24` adds community-scoped `role_capabilities` and durable
`staff_audit_events`. It backfills every legacy admin role with the complete
registered capability set, then installs the same role, actor-membership, and
optional actor-face tenant-pair triggers used by fresh databases. It never
infers global staff power or copies an audit actor across communities.

Version `25` adds the allowlisted presentation variant used by world materials.
Existing rows receive the safe `chapter` default; Blueprint apply may then set
`chapter`, `dossier`, `noticeboard`, or `archive` through the validated
material-type mapping without storing CSS or templates.
Version `26` separates scene audience from scene lifecycle by adding
`threads.visibility`. Existing scenes migrate to `members`; legacy scenes whose
status is `private` migrate to `private`. The migration never infers public
publication from an open/active status or a non-private board.

Fresh-schema and upgraded-schema parity is a production-readiness requirement:
new tables, columns, indexes, and constraints must be represented in both the
fresh `create_schema()` path and the ordered migration path. When adding a migration,
include a parity-oriented test if the change affects indexes or constraints
that are easy to omit from one path.

## Adding A Schema Change

When adding a table, column, index, or constraint:

1. Update the fresh schema in `SCHEMA`.
2. Add an ordered migration in `src/elbysodic/db/migrations.py`.
3. Increment `CURRENT_SCHEMA_VERSION` and keep `MIGRATIONS` contiguous.
4. Keep the migration idempotent where possible.
5. Add a test that starts from an older shape and calls `create_schema()`.
6. Include tenant scope in new tables and indexes unless the table is truly
   global infrastructure.

Migration names should describe the product primitive or boundary being
changed, for example `add_character_claims` or `tighten_plotting_participants`.

## Tenant-Safe Migration Rules

New product tables should include `community_id` from their first version.
Tables that join community-scoped objects should either store `community_id`
directly or enforce the community boundary in repository write methods before
inserting rows.

Before adding stricter tenant-pair constraints or triggers, add or expand the
repository integrity diagnostic for the affected row family and prove it with a
corrupt legacy-row test. The migration should then either repair, clear, or
explicitly reject those diagnosed rows before the new constraint is installed.
Use the row-family audit matrix in `docs/architecture/data-integrity.md` to
name the affected tenant pairings, proof group, and approval gate before the
migration slice starts.

Partial unique indexes are preferred when a workflow allows one of several
identity shapes, such as character-backed interest and prospective-character
interest. Do not rely on nullable columns inside a broad unique constraint to
prevent duplicates; SQLite treats `NULL` values as distinct.

## Compatibility Helpers

The helpers in `schema.py` still carry prototype-era upgrades for databases
created before the migration ledger existed. Prefer putting new upgrades in
`migrations.py`. Keep compatibility helpers only for old shapes that need to
reach baseline version `1`.
