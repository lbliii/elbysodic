"""Director Studio content room."""

from chirp.http.request import Request
from chirp.http.response import Redirect
from chirp.templating.returns import Page

from elbysodic.web.pages.studio.page import handle_studio_post, render_studio_room


def get(request: Request) -> Page | Redirect:
    return render_studio_room(request, "content")


async def post(request: Request) -> Page | Redirect:
    return await handle_studio_post(request, "content")
