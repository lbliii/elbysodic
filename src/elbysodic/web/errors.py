"""Elbysodic error surfaces for production browser requests."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from http import HTTPStatus
from urllib.parse import quote

from chirp.app import App
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.http.response import Response


@dataclass(frozen=True, slots=True)
class ErrorAction:
    label: str
    href: str
    variant: str = "secondary"


@dataclass(frozen=True, slots=True)
class ErrorScenario:
    title: str
    summary: str
    detail: str
    actions: tuple[ErrorAction, ...]


def register_error_handlers(app: App, *, include_internal: bool) -> None:
    """Register user-facing error pages without replacing debug tracebacks."""

    @app.error(400)
    def bad_request(request: Request, exc: HTTPError) -> Response:
        return error_response(request, status=400, detail=exc.detail)

    @app.error(403)
    def forbidden(request: Request, exc: HTTPError) -> Response:
        return error_response(request, status=403, detail=exc.detail)

    @app.error(404)
    def not_found(request: Request, exc: HTTPError) -> Response:
        return error_response(request, status=404, detail=exc.detail)

    @app.error(405)
    def method_not_allowed(request: Request, exc: HTTPError) -> Response:
        return error_response(request, status=405, detail=exc.detail, headers=exc.headers)

    if include_internal:

        @app.error(500)
        def internal_error(request: Request, _exc: Exception) -> Response:
            return error_response(request, status=500, detail=_request_id_detail(request))


def error_response(
    request: Request,
    *,
    status: int,
    detail: str = "",
    headers: tuple[tuple[str, str], ...] = (),
) -> Response:
    scenario = _scenario(request, status, detail)
    if bool(request.htmx):
        body = _fragment_error(status, scenario)
    else:
        body = _page_error(status, scenario)
    return Response(body=body, status=status, headers=headers)


def _scenario(request: Request, status: int, detail: str) -> ErrorScenario:
    normalized = detail.lower()
    if status == 403:
        if (
            "realm membership role" in normalized
            or "realm membership is no longer available" in normalized
        ):
            return ErrorScenario(
                title="That realm membership needs staff attention.",
                summary=(
                    "Elbysodic stopped before changing your face or realm because that "
                    "membership is missing a valid local role."
                ),
                detail="Your identity did not change. Return to the network and choose another realm.",
                actions=(
                    ErrorAction("Open Studio Network", "/network", "primary"),
                    ErrorAction("Log in again", _login_href(request)),
                ),
            )
        if (
            "login required" in normalized
            or "login is required" in normalized
            or not request.user.is_authenticated
        ):
            return ErrorScenario(
                title="Log in to keep writing.",
                summary=(
                    "This action needs a signed-in account before Elbysodic can resolve "
                    "your realm, membership, and active face."
                ),
                detail="",
                actions=(
                    ErrorAction("Log in", _login_href(request), "primary"),
                    ErrorAction("Open Studio Network", "/network"),
                ),
            )
        if "not active" in normalized:
            return ErrorScenario(
                title="That realm membership is inactive.",
                summary=(
                    "This login knows about the realm, but that membership cannot enter "
                    "or act there right now."
                ),
                detail="Ask the realm staff to reactivate the membership, or choose another program.",
                actions=(
                    ErrorAction("Open Studio Network", "/network", "primary"),
                    ErrorAction("Log in again", _login_href(request)),
                ),
            )
        if "cannot switch" in normalized or "does not belong" in normalized:
            return ErrorScenario(
                title="That realm is not attached to this login.",
                summary=(
                    "The switcher was stopped before it could move you into a membership "
                    "owned by another account."
                ),
                detail="Use the account that owns that realm membership, or return to your network.",
                actions=(
                    ErrorAction("Open Studio Network", "/network", "primary"),
                    ErrorAction("Log in again", _login_href(request)),
                ),
            )

    if status == 404 and request.path.startswith("/c/"):
        slug = request.path.removeprefix("/c/").split("/", 1)[0]
        return ErrorScenario(
            title="We could not find that realm.",
            summary=(f"{slug} is not a program on this studio network, or its address changed."),
            detail="Choose a reachable realm from the network home.",
            actions=(
                ErrorAction("Open Studio Network", "/network", "primary"),
                ErrorAction("Go home", "/"),
            ),
        )

    if status == 500:
        return ErrorScenario(
            title="Something broke backstage.",
            summary=("The request stopped before Elbysodic could finish the page or action."),
            detail=detail,
            actions=(
                ErrorAction("Open Studio Network", "/network", "primary"),
                ErrorAction("Go home", "/"),
            ),
        )

    title, summary, safe_detail = _default_message(status, detail)
    return ErrorScenario(
        title=title,
        summary=summary,
        detail=safe_detail,
        actions=_default_actions(status, request),
    )


def _default_message(status: int, detail: str) -> tuple[str, str, str]:
    match status:
        case 400:
            return (
                "That request could not be read.",
                "Check the form and try the move again.",
                detail,
            )
        case 403:
            return (
                "This door is closed.",
                "Your current login or realm membership cannot use that action.",
                "",
            )
        case 404:
            return (
                "That path is not in this realm.",
                "It may have moved, changed slug, or belonged to another program.",
                "",
            )
        case 405:
            return (
                "That move is not available here.",
                "Use one of the visible page actions instead.",
                "",
            )
        case _:
            return (
                "Something broke while opening this page.",
                "The request was stopped before it could finish.",
                "",
            )


def _default_actions(status: int, request: Request) -> tuple[ErrorAction, ...]:
    if status == 403:
        return (
            ErrorAction("Open Studio Network", "/network", "primary"),
            ErrorAction("Log in again", _login_href(request)),
        )
    if status == 404:
        return (
            ErrorAction("Open Studio Network", "/network", "primary"),
            ErrorAction("Go home", "/"),
        )
    return (
        ErrorAction("Open Studio Network", "/network", "primary"),
        ErrorAction("Go home", "/"),
    )


def _page_error(status: int, scenario: ErrorScenario) -> str:
    status_label = _status_label(status)
    safe_title = escape(scenario.title)
    safe_summary = escape(scenario.summary)
    safe_detail = escape(scenario.detail)
    detail_markup = f'<p class="elbysodic-copy-helper">{safe_detail}</p>' if safe_detail else ""
    actions_markup = "\n".join(
        (
            f'<a class="chirpui-btn chirpui-btn--{escape(action.variant)}" '
            f'href="{escape(action.href, quote=True)}">{escape(action.label)}</a>'
        )
        for action in scenario.actions
    )
    return f"""<!doctype html>
<html lang="en" data-theme="system">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{status_label} · Elbysodic</title>
  <link rel="stylesheet" href="/elbysodic-static/elbysodic-theme.css?v=sidebar-cookie-1">
</head>
<body class="chirpui">
  <main class="elbysodic-error-page" aria-labelledby="elbysodic-error-heading">
    <article class="elbysodic-recovery">
      <p class="elbysodic-section-kicker">{status_label}</p>
      <h1 id="elbysodic-error-heading">{safe_title}</h1>
      <p class="elbysodic-copy-section">{safe_summary}</p>
      {detail_markup}
      <div class="chirpui-cluster elbysodic-error-page__actions">
        {actions_markup}
      </div>
    </article>
  </main>
</body>
</html>"""


def _fragment_error(status: int, scenario: ErrorScenario) -> str:
    action = scenario.actions[0] if scenario.actions else None
    action_markup = (
        f'<a class="chirpui-btn chirpui-btn--{escape(action.variant)}" '
        f'href="{escape(action.href, quote=True)}">{escape(action.label)}</a>'
        if action is not None
        else ""
    )
    return (
        f'<section class="elbysodic-notice elbysodic-notice--error" data-status="{status}">'
        f"<strong>{escape(scenario.title)}</strong>"
        f"<p>{escape(scenario.summary)}</p>"
        f"{action_markup}"
        "</section>"
    )


def _status_label(status: int) -> str:
    try:
        phrase = HTTPStatus(status).phrase
    except ValueError:
        phrase = "Error"
    return f"{status} {phrase}"


def _request_id_detail(request: Request) -> str:
    request_id = getattr(request, "request_id", "")
    if request_id:
        return f"Request id: {request_id}"
    return ""


def _login_href(request: Request) -> str:
    next_url = request.path or "/"
    raw_query = getattr(request.query, "_raw", b"")
    if isinstance(raw_query, bytes) and raw_query:
        next_url = f"{next_url}?{raw_query.decode('latin-1')}"
    return f"/login?next={quote(next_url, safe='/')}"
