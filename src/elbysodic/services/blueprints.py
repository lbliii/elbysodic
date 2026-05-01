"""Service boundary for director-authored Program Blueprint previews."""

from __future__ import annotations

from elbysodic.blueprints import ProgramBlueprintPreview, preview_program_blueprint_yaml
from elbysodic.services import policies
from elbysodic.services.read_models import ForumView


def preview_program_blueprint(viewer: ForumView, source: str) -> ProgramBlueprintPreview:
    if not policies.can_manage_world(viewer.membership, viewer.role):
        raise PermissionError(
            f"membership {viewer.membership.id} cannot preview program blueprints"
        )
    return preview_program_blueprint_yaml(source)
