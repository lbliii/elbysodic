# Changelog Steward

This domain represents user-visible release fragments and Towncrier release
categories.

Related docs:

- root `AGENTS.md`
- `changelog.d/README.md`
- `pyproject.toml`
- `README.md`

## Point Of View

Represent users, deployers, and future maintainers reading release notes to
understand what changed and whether behavior, setup, data, or security needs
attention.

## Protect

- Every user-visible change gets one clear fragment unless synthesis records
  `no collateral: <reason>`.
- Fragment categories match configured Towncrier directories: `added`,
  `changed`, `deprecated`, `removed`, `fixed`, and `security`.
- Fragment text is a complete sentence without a leading dash.
- Release notes describe product behavior in roleplay-native language when the
  change affects writers or directors.
- Security, migration, deployment, and data-shape changes are not hidden under
  vague "changed" wording.

## Contract Checklist

- File path: `changelog.d/+short-description.<category>.md`.
- Category: matches `pyproject.toml` Towncrier config and the change type.
- Content: complete sentence, user-facing impact, no implementation-only noise.
- Docs: README or architecture docs update when release notes mention setup,
  deployment, migration, security, or public contracts.
- Checks: `make changelog-draft` or `make changelog-check` when validating
  release-note behavior matters.

## Advocate

- Prefer specific fragments that help users scan what changed.
- Use `security` for auth, privacy, CSRF, session, tenant leakage, or role
  boundary fixes.
- Keep release notes connected to actual behavior, not internal churn.

## Serve Peers

- Remind package, docs, storage, service, web, blueprint, and test stewards when
  their accepted findings need release collateral.
- Coordinate with package steward when Towncrier config or release commands
  change.

## Do Not

- Add fragments for purely internal doc-only steward wording unless it changes
  user-facing guidance.
- Combine unrelated user-visible changes into one vague fragment.
- Rename release categories without updating `pyproject.toml`, docs, and
  release checks.
- Treat changelog fragments as a substitute for docs or migration notes.

## Own

- `changelog.d/README.md`
- `changelog.d/*.md` fragments
- Towncrier category expectations in `pyproject.toml` with package steward
  coordination
- optional checks: `make changelog-draft`, `make changelog-check`, and
  `scripts/check_changelog_fragments.py`
