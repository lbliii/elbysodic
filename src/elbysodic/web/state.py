"""Shared application state for mounted page handlers."""

from __future__ import annotations

from elbysodic.services import AppServices

_services: AppServices | None = None
_dev_tools_enabled = False


def configure_services(services: AppServices, *, dev_tools_enabled: bool = False) -> None:
    global _services
    global _dev_tools_enabled
    _services = services
    _dev_tools_enabled = dev_tools_enabled


def get_services(request: object | None = None) -> AppServices:
    if _services is None:
        raise RuntimeError("Elbysodic services have not been configured")
    if request is not None:
        return _services.for_request(request)
    return _services


def dev_tools_enabled() -> bool:
    return _dev_tools_enabled
