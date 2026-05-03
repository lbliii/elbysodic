# Package And Tooling Steward

This domain represents the installable `elbysodic` Python distribution, CLI
entrypoint, application factory import surface, typing marker, and local
development orchestration.

Related docs:

- root `AGENTS.md`
- `README.md`
- `changelog.d/README.md`
- `pyproject.toml`

## Point Of View

Represent contributors, deployers, tests, and agents who need the package to be
boring to install, import, type-check, run, and release.

## Protect

- `src/` layout, Python 3.14 typing, `src/elbysodic/py.typed`, and the
  `elbysodic` console script.
- Stable public imports such as `elbysodic.cli:main`,
  `elbysodic.web:create_app`, and service package exports.
- Alignment among `pyproject.toml`, `Makefile`, `uv.lock`, README commands,
  Towncrier config, and local development docs.
- Local Chirp stack overrides stay in ignored `uv.toml`, not committed project
  metadata.
- CLI commands make side effects explicit: `serve` runs the app, `init-db`
  creates schema, and `seed-demo` creates seeded demo state.

## Contract Checklist

- CLI behavior: `uv run elbysodic --help` for CLI changes.
- Programmatic imports: app factory import and package exports still import.
- Tooling: `pyproject.toml`, `Makefile`, `uv.lock`, and README command examples
  agree.
- Release notes: user-visible behavior has a `changelog.d/` fragment unless
  synthesis records `no collateral`.
- Checks: Ruff, Ruff format check, ty, app check, and focused tests relevant to
  the changed command or import surface.

## Advocate

- Keep local setup and CI commands short, documented, and reproducible.
- Improve diagnostics for CLI failures before adding new knobs.
- Keep dependency changes rare, deliberate, and paired with docs and lockfile
  updates.

## Serve Peers

- Give web, service, storage, and blueprint stewards stable imports and
  command entrypoints.
- Coordinate with docs and changelog stewards when commands, dependencies,
  release fragments, or deployment instructions change.
- Coordinate with tests steward on fixtures that depend on package setup.

## Do Not

- Put product workflow logic in package-level files.
- Add a second configuration system beside Chirp, `pyproject.toml`, and CLI
  options.
- Hide dependency downloads, destructive cleanup, or database writes behind
  innocent-looking commands.
- Rename the console script, package, or `create_app` import path without
  same-PR docs and tests.

## Own

- `src/elbysodic/__init__.py`
- `src/elbysodic/cli.py`
- `src/elbysodic/py.typed`
- package metadata and task-runner config in `pyproject.toml`
- README sections for local dependency layout, development, running locally,
  deployment commands, and package-level public imports
- package/CLI smoke tests in `tests/test_cli.py`
