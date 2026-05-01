# Package And Tooling Steward

## Steward

Package steward for the installable `elbysodic` distribution, CLI entrypoint,
application factory import surface, and local development orchestration.

## Protects

- The package remains a typed Python 3.14 project with `src/` layout and the
  `elbysodic` console script.
- `elbysodic.cli:main`, `elbysodic.web:create_app`, and `elbysodic.services`
  exports stay boring, importable, and friendly to tests.
- Root tools stay aligned: `pyproject.toml`, `Makefile`, `uv.lock`,
  `changelog.d/`, and README command examples should tell the same story.
- Local dependency overrides keep pointing at the owned Chirp stack described
  in README.

## Must Not Become

- A dumping ground for product logic that belongs in services or repositories.
- A second configuration system beside Chirp, `pyproject.toml`, and the CLI.
- A packaging experiment that makes local setup harder than `make setup`,
  `make install`, and `make ci`.

## Documentation Ownership

Owns README sections for dependency layout, local commands, running the app,
and package-level public imports. Coordinate with `docs/AGENTS.md` when command
or architecture descriptions change.

## Local Checks

- `uv run ruff check .`
- `uv run ruff format . --check`
- `uv run ty check src/elbysodic/ tests/`
- `uv run python -c "from elbysodic.web import create_app; create_app(debug=False, db_path=':memory:').check()"`
- For CLI changes, run a focused smoke such as `uv run elbysodic --help`.

## Public Contracts And Safety

- Do not rename the console script, package, or `create_app` import path without
  updating README, tests, and downstream usage.
- Keep CLI commands side-effect explicit: `serve` runs the app, `init-db`
  creates schema, and `seed-demo` creates seeded demo state.
- Do not hide dependency downloads, destructive cleanup, or database writes
  behind innocuous commands.
