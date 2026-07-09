"""Static template validation gate: ``kida check --validate-calls``.

Wraps the stock ``kida check`` CLI so it sees the app's real template
surface instead of a bare Environment:

- Registers the app's template filters (chirp-ui's ``icon``, ``bem``,
  ``html_attrs``, ...) into kida's default filter registry so templates
  that use them compile instead of failing with K-TPL-002.
- Stages a temporary root containing a copy of
  ``src/elbysodic/web/pages`` plus a copy of chirp-ui's packaged
  ``chirpui/`` templates, so ``{% from "chirpui/x.html" import y %}``
  resolves and call sites are validated against the real def
  signatures (the loader's path-traversal guard rejects symlinks that
  escape the root, so a real copy is required).

``--strict`` (explicit ``endif``/``enddef``/... closers) is
intentionally not passed: this app uses kida's unified ``{% end %}``
closer as house style (~1400 sites), so the strict lane can never be
green without rewriting every template.

Reported paths are relative to the staged root and match paths under
``src/elbysodic/web/pages/``.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import chirp_ui
from kida.cli import main as kida_main
from kida.environment.filters import DEFAULT_FILTERS

from elbysodic.web import create_app

REPO_ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = REPO_ROOT / "src" / "elbysodic" / "web" / "pages"
CHIRPUI_TEMPLATES = Path(chirp_ui.__file__).resolve().parent / "templates" / "chirpui"


def run() -> int:
    # The running app is the source of truth for registered filters.
    app = create_app(debug=False, db_path=":memory:")
    DEFAULT_FILTERS.update(app._template_filters)

    with tempfile.TemporaryDirectory(prefix="elbysodic-kida-check-") as tmp:
        root = Path(tmp) / "pages"
        shutil.copytree(PAGES_DIR, root)
        shutil.copytree(CHIRPUI_TEMPLATES, root / "chirpui")
        return kida_main(["check", str(root), "--validate-calls", *sys.argv[1:]])


if __name__ == "__main__":
    sys.exit(run())
