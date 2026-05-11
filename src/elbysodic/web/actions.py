"""Request-scoped action dispatch for rendered form handlers."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Mapping
from typing import cast

from chirp.errors import HTTPError
from chirp.http.forms import FormData
from chirp.http.request import Request

type FormActionHandler[T] = Callable[[Request, FormData], T | Awaitable[T]]


async def dispatch_form_action[T](
    request: Request,
    form: FormData,
    handlers: Mapping[str, FormActionHandler[T]],
    *,
    field: str = "intent",
    default: str = "",
    unknown_detail: str = "unknown form action",
) -> T:
    action = str(form.get(field) or default)
    handler = handlers.get(action)
    if handler is None:
        raise HTTPError(status=400, detail=f"{unknown_detail}: {action}")
    result = handler(request, form)
    if inspect.isawaitable(result):
        return cast(T, await result)
    return result
