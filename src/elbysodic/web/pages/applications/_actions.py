"""Chirp page actions for the applications desk."""

from __future__ import annotations

from collections.abc import Callable

from chirp.errors import HTTPError
from chirp.pages.actions import action
from chirp.templating.returns import FormAction

from elbysodic.services import AppServices


def _run_application_action(
    operation: Callable[..., object], *args: object, **kwargs: object
) -> FormAction:
    try:
        operation(*args, **kwargs)
    except PermissionError as exc:
        raise HTTPError(status=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPError(status=400, detail=str(exc)) from exc
    return FormAction("/applications", status=302)


@action("submit_application")
async def submit_application(services: AppServices, character_slug: str) -> FormAction:
    return _run_application_action(services.submit_character_application, character_slug)


@action("accept_application")
async def accept_application(services: AppServices, character_slug: str) -> FormAction:
    return _run_application_action(services.accept_character_application, character_slug)


@action("request_revision")
async def request_revision(
    services: AppServices, character_slug: str, revision_note: str = ""
) -> FormAction:
    return _run_application_action(
        services.request_character_application_revision,
        character_slug,
        note=revision_note,
    )
