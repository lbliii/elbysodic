"""Chirp hypermedia contract entrypoint for ``chirp check`` / ``chirp diff``.

``create_app()`` returns a :class:`~elbysodic.web.worker_draining.DrainingAwareApp`
ASGI proxy; contract tooling needs the inner :class:`chirp.app.App` instance.
"""

from __future__ import annotations

from chirp.app import App

from elbysodic.web.app import create_app
from elbysodic.web.worker_draining import unwrap_chirp_app

app: App = unwrap_chirp_app(create_app(debug=False, db_path=":memory:"))
