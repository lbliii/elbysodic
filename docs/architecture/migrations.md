# Schema Migrations

Elbysodic supports fresh SQLite database creation and in-place database
upgrades. Fresh databases are created from the current schema in
`src/elbysodic/db/schema.py`. Existing databases are brought forward by the
legacy compatibility helpers in that module and then recorded in the migration
ledger.

## Current Baseline

The current checked-in schema is baseline version `1`. Calling `create_schema()`
creates or upgrades the database, ensures `schema_migrations` exists, records
the baseline when no ledger row exists, and sets SQLite `PRAGMA user_version`.

This baseline keeps the prototype's existing schema bootstrap intact while
giving future schema changes an ordered migration path.

## Adding A Schema Change

When adding a table, column, index, or constraint:

1. Update the fresh schema in `SCHEMA`.
2. Add an ordered migration in `src/elbysodic/db/migrations.py`.
3. Keep the migration idempotent where possible.
4. Add a test that starts from an older shape and calls `create_schema()`.
5. Include tenant scope in new tables and indexes unless the table is truly
   global infrastructure.

Migration names should describe the product primitive or boundary being
changed, for example `add_character_claims` or `tighten_plotting_participants`.

## Tenant-Safe Migration Rules

New product tables should include `community_id` from their first version.
Tables that join community-scoped objects should either store `community_id`
directly or enforce the community boundary in repository write methods before
inserting rows.

Partial unique indexes are preferred when a workflow allows one of several
identity shapes, such as character-backed interest and prospective-character
interest. Do not rely on nullable columns inside a broad unique constraint to
prevent duplicates; SQLite treats `NULL` values as distinct.

## Compatibility Helpers

The helpers in `schema.py` still carry prototype-era upgrades for databases
created before the migration ledger existed. Prefer putting new upgrades in
`migrations.py`. Keep compatibility helpers only for old shapes that need to
reach baseline version `1`.
