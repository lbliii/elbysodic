# CLI command surfaces

Elbysodic uses one Milo 0.4 runtime for the root CLI and the nested developer
commands. `elbysodic.cli:main` remains the console entrypoint, and the mature
argv is preserved: a missing command still means `serve`, root server options
still work without spelling `serve`, and existing command and option names are
unchanged.

## Surface allowlist

| Command | Terminal CLI | `--llms-txt` | MCP | Side effect boundary |
| --- | --- | --- | --- | --- |
| `serve` | Yes | Yes | No | Opens a long-running server and database services |
| `init-db` | Yes | Yes | No | Creates or migrates a database schema |
| `seed-demo` | Yes | Yes | No | Writes demo realm data |
| `bootstrap-first-realm` | Yes | Yes | No | Writes the first realm, login, membership, role, and theme |
| `dev preview` | Yes | Yes | No | Seeds local data and opens a long-running server |
| `dev check` | Yes | Yes | No | Launches the repository verification subprocesses |
| `dev db checkpoint` | Yes | Yes | No | Mutates SQLite WAL state |
| `dev db backup` | Yes | Yes | No | Writes an integrity-checked database copy |

The MCP allowlist is intentionally empty. Every current command either opens a
process, handles credentials, or mutates filesystem/database state. Milo's MCP
transport remains enabled and verified so a future read-only diagnostic can be
added deliberately with `surfaces=("cli", "mcp", "llms")`; commands do not
become tools merely because they are registered with the CLI.

Tests pin the empty allowlist and the human-readable discovery surface. Hidden
or excluded commands are uncallable over MCP, matching Milo 0.4's strict
surface contract.

## Host-owned output

Command workflow functions return values for Milo to render. Diagnostics from
developer checks use the injected `Context`, including its `output_sink`, so a
test or host can call a command without replacing process-global terminal
streams:

```python
from io import StringIO

from milo import Context

from elbysodic.cli import cli

diagnostics = StringIO()
cli.call_raw(
    "dev.check",
    ctx=Context(output_sink=diagnostics, color=False),
    quick=True,
)
```

Milo owns option parsing, unknown-argument repair diagnostics, result
formatting, programmatic dispatch, LLM discovery, and MCP dispatch. Run the
cross-surface self-diagnosis with:

```bash
make milo-check
```

The gate imports the CLI, generates all typed schemas, checks the explicit MCP
tool count, validates discovery and MCP Apps projections, and completes the
subprocess JSON-RPC handshake.
