"""Character plot-hook detail page.

Mutations live in ``_actions.py`` (Chirp page actions, dispatched on the
hidden ``_action`` form field). ``post()`` below is only the no-``_action``
fallback that keeps the POST method registered on this path.
"""

from __future__ import annotations

from dataclasses import dataclass

from chirp.contracts import FormContract, contract
from chirp.errors import HTTPError
from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services.plot_hooks import PLOT_HOOK_STATUSES, PLOT_HOOK_TYPES
from elbysodic.web.state import get_services

HOOK_TEMPLATE = "characters/{character_slug}/hooks/{hook_slug}/page.html"


@dataclass(frozen=True, slots=True)
class PlotHookActionForm:
    _action: str
    interest_id: str = ""
    title: str = ""
    hook_type: str = ""
    status: str = ""
    summary: str = ""
    body: str = ""
    facets: str = ""


def get(request: Request, character_slug: str, hook_slug: str) -> Page:
    return _render_hook(request, character_slug, hook_slug)


@contract(form=FormContract(PlotHookActionForm, HOOK_TEMPLATE))
async def post(request: Request, character_slug: str, hook_slug: str) -> Page:
    """Fallback — mutations dispatch via this directory's ``_actions.py``."""
    return _render_hook(request, character_slug, hook_slug)


def _render_hook(request: Request, character_slug: str, hook_slug: str) -> Page:
    services = get_services(request)
    try:
        hook = services.read_plot_hook(character_slug, hook_slug)
    except LookupError as exc:
        raise HTTPError(status=404, detail=str(exc)) from exc
    return Page.mounted(
        HOOK_TEMPLATE,
        current_path=request.url,
        viewer=services.viewer(),
        hook=hook,
        plot_hook_types=PLOT_HOOK_TYPES,
        plot_hook_statuses=PLOT_HOOK_STATUSES,
    )
