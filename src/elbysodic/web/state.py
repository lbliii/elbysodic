"""Shared application state for mounted page handlers."""

from __future__ import annotations

from elbysodic.services import AppServices

_services: AppServices | None = None


def configure_services(services: AppServices) -> None:
    global _services
    _services = services


def get_services(request: object | None = None) -> AppServices:
    if _services is None:
        raise RuntimeError("Elbysodic services have not been configured")
    if request is not None:
        return _services.for_request(request)
    return _services
