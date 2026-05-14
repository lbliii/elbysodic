"""Daily director operations console."""

from __future__ import annotations

from chirp.http.request import Request
from chirp.templating.returns import Page

from elbysodic.services.operations import OperationsInspectionConfig
from elbysodic.web.state import get_services, get_web_security_config


def get(request: Request) -> Page:
    services = get_services(request)
    security = get_web_security_config()
    operations = services.director_operations(
        inspection_config=OperationsInspectionConfig(
            environment=security.env,
            secure_cookies=security.secure_cookies,
        )
    )
    return Page.mounted(
        "studio/operations/page.html",
        current_path=request.url,
        viewer=services.viewer(),
        operations=operations,
    )
