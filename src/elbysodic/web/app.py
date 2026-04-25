"""Chirp application factory for Elbysodic."""

from __future__ import annotations

from pathlib import Path

from chirp.app import App
from chirp.config import AppConfig
from chirp.ext.chirp_ui import use_chirp_ui
from chirp.middleware.static import StaticFiles

from elbysodic.services import AppServices, create_services
from elbysodic.web.state import configure_services

PAGES_DIR = Path(__file__).parent / "pages"
STATIC_DIR = Path(__file__).parent / "static"


def create_app(
    *,
    debug: bool = True,
    services: AppServices | None = None,
    db_path: str | Path | None = None,
) -> App:
    config = AppConfig(template_dir=PAGES_DIR, debug=debug)
    app = App(config=config)

    configure_services(services or create_services(db_path))
    use_chirp_ui(app)
    app.add_middleware(StaticFiles(directory=str(STATIC_DIR), prefix="/elbysodic-static"))
    app.mount_pages(str(PAGES_DIR))

    return app
