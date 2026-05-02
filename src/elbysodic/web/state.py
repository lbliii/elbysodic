"""Shared application state for mounted page handlers."""

from __future__ import annotations

from elbysodic.services import AppServices
from elbysodic.web.security import WebSecurityConfig

_services: AppServices | None = None
_dev_tools_enabled = False
_web_security_config: WebSecurityConfig | None = None


def configure_services(
    services: AppServices,
    *,
    dev_tools_enabled: bool = False,
    web_security_config: WebSecurityConfig | None = None,
) -> None:
    global _services
    global _dev_tools_enabled
    global _web_security_config
    _services = services
    _dev_tools_enabled = dev_tools_enabled
    _web_security_config = web_security_config


def get_services(request: object | None = None) -> AppServices:
    if _services is None:
        raise RuntimeError("Elbysodic services have not been configured")
    if request is not None:
        return _services.for_request(request)
    return _services


def dev_tools_enabled() -> bool:
    return _dev_tools_enabled


def get_web_security_config() -> WebSecurityConfig:
    if _web_security_config is None:
        raise RuntimeError("Elbysodic web security has not been configured")
    return _web_security_config
