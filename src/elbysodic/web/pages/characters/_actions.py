"""Page actions for /characters — Chirp 0.10 ``_actions.py`` pilot (#249).

Migration recipe (intent dispatch -> Chirp page actions)
=========================================================

Steps
-----
1. Create ``_actions.py`` next to ``page.py``. Write one ``@action("name")``
   function per former intent. Handlers take keyword params resolved by
   Chirp in this priority order: ``request: Request`` > path params >
   cascade/shell context > form fields (by name, as raw ``str``) > service
   providers (by annotation, e.g. ``services: AppServices`` via
   ``app.provide``). Form fields are NOT type-coerced — take ``str`` params
   and normalize inside the handler.
2. Return types:
   - Success: ``FormAction(redirect_url, *fragments, trigger=..., status=...)``.
     Non-htmx POSTs get a redirect (default 303 — pass ``status=302`` to
     preserve a legacy ``Redirect`` status); htmx POSTs get the fragments
     (first = primary swap, rest = OOB) or ``HX-Redirect`` when no fragments.
   - Validation failure (htmx): ``ValidationError(template, block, **ctx)``
     renders the named template block with HTTP 422. Wrap the form region in
     ``{% block form_name %}...{% endblock %}`` and pass EVERY context key the
     block reads — ValidationError context is NOT merged with the layout
     cascade (``upgrade_result`` passes it through untouched).
   - Validation failure (plain POST): htmx never sees a 422 swap, and stock
     htmx 2 does not swap 4xx anyway, so branch on ``request.is_htmx`` and
     return the full ``Page`` re-render (identical to the legacy behavior).
     ``Page`` returned from an action IS upgraded with the layout chain.
3. Templates: add ``<input type="hidden" name="_action" value="name">`` to
   each form (replacing the legacy ``intent`` hidden field). Add ``_action``
   to the route's ``FormContract`` dataclass, otherwise ``app.check()``
   warns about an unknown form field and ``warnings_as_errors`` fails.
4. ``page.py`` MUST keep a ``post()`` fallback: Chirp registers routes only
   for the HTTP-method functions found in ``page.py``, so without ``post()``
   the router 405s before action dispatch runs (Lucky Cat's ``trade/page.py``
   keeps the same stub). The fallback only handles POSTs without ``_action``;
   re-rendering the page (Lucky Cat convention) is enough.
5. Update tests that POST the form to include ``_action=<name>`` — they
   emulate the form, and the form now always submits the hidden field.

Gotchas
-------
- Param-name collisions: cascade/shell context wins over form data, so a
  form param named ``page_title``, ``current_path``, ``viewer``,
  ``breadcrumb_items``/``tab_items``, or any ``_context.py`` key would
  silently receive the context value. Rename the form field if it collides.
- Checkbox fields arrive as ``"on"`` or are absent — keep ``str = ""``
  defaults and compare explicitly.
- ``_actions.py`` is loaded per directory and NOT inherited by
  subdirectories; ``{slug}/page.py`` routes need their own ``_actions.py``.
- Share render helpers by importing from the page module
  (``elbysodic.web.pages.<dir>.page`` — same pattern as the studio pages);
  ``_actions.py`` modules cannot use relative imports.
- ``tests/test_chirp_action_context.py`` pins the framework contract that
  request-scoped providers are only invoked when ``dispatch_action`` gets a
  ``request`` — keep it green when bumping Chirp.
"""

from __future__ import annotations

from chirp.http.request import Request
from chirp.pages.actions import action
from chirp.templating.returns import FormAction, Page, ValidationError

from elbysodic.services import AppServices
from elbysodic.web.pages.characters.page import ROSTER_TEMPLATE, render_roster, roster_context

CREATE_FORM_BLOCK = "character_create_form"


@action("create_character")
async def create_character(
    request: Request,
    services: AppServices,
    name: str = "",
    summary: str = "",
    avatar_url: str = "",
    poster_url: str = "",
    poster_alt: str = "",
    tagline: str = "",
    accent_color: str = "",
    post_profile_variant: str = "bio",
    post_accent_style: str = "soft",
    post_border_style: str = "hairline",
    post_title_style: str = "standard",
    post_density: str = "calm",
    post_style_preset: str = "",
    accent_source: str = "inherit",
    make_default: str = "",
) -> FormAction | ValidationError | Page:
    if accent_source != "custom":
        accent_color = ""
    set_default = make_default == "on"

    try:
        character = services.create_character(
            name=name,
            summary=summary,
            avatar_url=avatar_url,
            poster_url=poster_url,
            poster_alt=poster_alt,
            tagline=tagline,
            accent_color=accent_color,
            post_profile_variant=post_profile_variant,
            post_accent_style=post_accent_style,
            post_border_style=post_border_style,
            post_title_style=post_title_style,
            post_density=post_density,
            post_style_preset=post_style_preset,
            make_default=set_default,
        )
    except ValueError as exc:
        form_state = {
            "error": str(exc),
            "name": name,
            "summary": summary,
            "avatar_url": avatar_url,
            "poster_url": poster_url,
            "poster_alt": poster_alt,
            "tagline": tagline,
            "accent_color": accent_color,
            "post_profile_variant": post_profile_variant,
            "post_accent_style": post_accent_style,
            "post_border_style": post_border_style,
            "post_title_style": post_title_style,
            "post_density": post_density,
            "post_style_preset": post_style_preset,
            "accent_source": accent_source,
            "make_default": set_default,
        }
        if request.is_htmx:
            return ValidationError(
                ROSTER_TEMPLATE,
                CREATE_FORM_BLOCK,
                **roster_context(request, **form_state),
            )
        return render_roster(request, **form_state)

    # status=302 preserves the pre-migration Redirect status for plain POSTs.
    return FormAction(f"/characters/{character.slug}", status=302)
