"""Shared application state for mounted page handlers."""

from __future__ import annotations

from elbysodic.services import AppServices
from elbysodic.web.security import WebSecurityConfig

_services: AppServices | None = None
_dev_tools_enabled = False
_web_security_config: WebSecurityConfig | None = None
_REQUEST_SERVICES_CACHE_KEY = "elbysodic.request_services"


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
        cache = getattr(request, "_cache", None)
        if isinstance(cache, dict):
            services = cache.get(_REQUEST_SERVICES_CACHE_KEY)
            if isinstance(services, AppServices):
                return services
            services = _services.for_request(request)
            cache[_REQUEST_SERVICES_CACHE_KEY] = services
            return services
        return _services.for_request(request)
    return _services


def close_request_services(request: object) -> None:
    cache = getattr(request, "_cache", None)
    if not isinstance(cache, dict):
        return
    services = cache.pop(_REQUEST_SERVICES_CACHE_KEY, None)
    if isinstance(services, AppServices):
        services.close()


def dev_tools_enabled() -> bool:
    return _dev_tools_enabled


def get_web_security_config() -> WebSecurityConfig:
    if _web_security_config is None:
        raise RuntimeError("Elbysodic web security has not been configured")
    return _web_security_config
