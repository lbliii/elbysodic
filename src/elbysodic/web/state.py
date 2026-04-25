"""Shared application state for mounted page handlers."""

from __future__ import annotations

from elbysodic.services import AppServices

_services: AppServices | None = None


def configure_services(services: AppServices) -> None:
    global _services
    _services = services


def get_services() -> AppServices:
    if _services is None:
        raise RuntimeError("Elbysodic services have not been configured")
    return _services
