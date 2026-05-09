"""Tenant-aware request routing helpers."""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Any
from urllib.parse import parse_qsl, urlencode

from chirp.http.request import Request
from chirp.http.response import Redirect, Response

from elbysodic.web.errors import error_response
from elbysodic.web.state import get_services

TENANT_PREFIX = "/c"
TENANT_SLUG_CACHE_KEY = "elbysodic.tenant_slug"
ORIGINAL_PATH_CACHE_KEY = "elbysodic.original_path"

_SCOPED_PATH_PREFIXES = (
    "/",
    "/applications",
    "/boards",
    "/casting",
    "/characters",
    "/claims",
    "/community",
    "/desk",
    "/discover",
    "/interactions",
    "/locations",
    "/mentionables",
    "/members",
    "/my",
    "/notifications",
    "/plotting",
    "/studio",
    "/wanted",
    "/world",
)
_UNSCOPED_PATH_PREFIXES = (
    "/c",
    "/dev",
    "/elbysodic-static",
    "/health",
    "/identity",
    "/login",
    "/logout",
    "/network",
    "/static",
)
_URL_ATTR_RE = re.compile(
    r'(?P<attr>\b(?:href|action|sse-connect|hx-(?:get|post|put|patch|delete))=["\'])'
    r'(?P<url>/[^"\']*)'
)
_FORM_URL_VALUE_RE = re.compile(
    r'(?P<attr><input\b(?=[^>]*\bname=["\'](?:next|redirect|return_to)["\'])'
    r'[^>]*\bvalue=["\'])(?P<url>/[^"\']*)'
)


class TenantPrefixMiddleware:
    """Resolve `/c/{community_slug}` before filesystem page routing."""

    async def __call__(self, request: Request, call_next: Any) -> Any:
        split = split_tenant_path(request.path)
        if split is None:
            return await call_next(request)

        community_slug, local_path = split
        if not _is_scoped_path(local_path):
            return await call_next(request)

        try:
            get_services().repo.get_community_by_slug(community_slug)
        except LookupError:
            return error_response(
                request,
                status=404,
                detail=f"Community not found: {community_slug}",
            )

        scoped_request = replace(request, path=local_path)
        scoped_request._cache[TENANT_SLUG_CACHE_KEY] = community_slug
        scoped_request._cache[ORIGINAL_PATH_CACHE_KEY] = request.path
        response = await call_next(scoped_request)
        return scope_response_urls(response, community_slug)


def split_tenant_path(path: str) -> tuple[str, str] | None:
    """Return `(community_slug, local_path)` for a tenant-prefixed path."""

    if path == TENANT_PREFIX or not path.startswith(TENANT_PREFIX + "/"):
        return None
    remainder = path[len(TENANT_PREFIX) + 1 :]
    slug, separator, rest = remainder.partition("/")
    if not slug:
        return None
    local_path = "/" + rest if separator else "/"
    return slug, local_path


def request_tenant_slug(request: object | None) -> str | None:
    cache = getattr(request, "_cache", None)
    if not isinstance(cache, dict):
        return None
    value = cache.get(TENANT_SLUG_CACHE_KEY)
    return value if isinstance(value, str) and value else None


def request_scoped_path(request: object | None, path: str) -> str:
    """Scope a local community endpoint when the current request is prefixed."""

    tenant_slug = request_tenant_slug(request)
    return scoped_path(tenant_slug, path) if tenant_slug is not None else path


def scoped_path(community_slug: str, path: str) -> str:
    """Return a shared-host canonical path for community-scoped content."""

    if not path.startswith("/"):
        return path
    fragment = ""
    if "#" in path:
        path, fragment = path.split("#", 1)
        fragment = f"#{fragment}"
    query = ""
    if "?" in path:
        path, query = path.split("?", 1)
        query = _scope_query(community_slug, query)
    scoped = _scope_local_path(community_slug, path)
    return f"{scoped}{query}{fragment}"


def scope_response_urls(response: Any, community_slug: str) -> Any:
    """Keep local redirects and rendered links inside the explicit tenant path."""

    if isinstance(response, Redirect):
        return replace(response, url=scoped_path(community_slug, response.url))
    if not isinstance(response, Response):
        return response
    body = _scoped_html_body(response.body, community_slug, response.content_type)
    headers = tuple(
        (
            (name, scoped_path(community_slug, value))
            if name.lower() == "location"
            else (name, value)
        )
        for name, value in response.headers
    )
    if body is response.body and headers == response.headers:
        return response
    return replace(response, body=body, headers=headers)


def _scoped_html_body(body: str | bytes, community_slug: str, content_type: str) -> str | bytes:
    if "text/html" not in content_type:
        return body
    if isinstance(body, bytes):
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            return body
        scoped = _scope_html_links(text, community_slug)
        return scoped.encode("utf-8") if scoped != text else body
    return _scope_html_links(body, community_slug)


def _scope_html_links(html: str, community_slug: str) -> str:
    def replace_match(match: re.Match[str]) -> str:
        url = match.group("url")
        return f"{match.group('attr')}{scoped_path(community_slug, url)}"

    return _FORM_URL_VALUE_RE.sub(replace_match, _URL_ATTR_RE.sub(replace_match, html))


def _scope_query(community_slug: str, query: str) -> str:
    if not query:
        return ""
    pairs = [
        (
            key,
            scoped_path(community_slug, value)
            if key in {"next", "redirect", "return_to"} and value.startswith("/")
            else value,
        )
        for key, value in parse_qsl(query, keep_blank_values=True)
    ]
    return f"?{urlencode(pairs)}" if pairs else f"?{query}"


def _scope_local_path(community_slug: str, path: str) -> str:
    if path == TENANT_PREFIX or path.startswith(TENANT_PREFIX + "/"):
        return path
    if not _is_scoped_path(path):
        return path
    if path == "/":
        return f"{TENANT_PREFIX}/{community_slug}"
    return f"{TENANT_PREFIX}/{community_slug}{path}"


def _is_scoped_path(path: str) -> bool:
    if path in _UNSCOPED_PATH_PREFIXES:
        return False
    if any(path.startswith(prefix + "/") for prefix in _UNSCOPED_PATH_PREFIXES if prefix != "/"):
        return False
    if path == "/":
        return True
    return any(path == prefix or path.startswith(prefix + "/") for prefix in _SCOPED_PATH_PREFIXES)
