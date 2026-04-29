"""Service helpers for director-defined claims and application templates."""

from __future__ import annotations

import json
from typing import Protocol

from elbysodic.domain.models import (
    ApplicationFieldValue,
    ApplicationTemplateField,
    Character,
    CharacterApplication,
    CharacterClaim,
    ClaimType,
)
from elbysodic.services.read_models import (
    ApplicationFieldValueView,
    ApplicationTemplateFieldView,
    CharacterClaimView,
    ClaimsDirectory,
    ClaimTypeDirectory,
    ForumView,
)


class ClaimReadRepository(Protocol):
    def list_claim_types(self, community_id: int) -> list[ClaimType]: ...

    def list_character_claims(
        self,
        community_id: int,
        *,
        status: str | None = "claimed",
        claim_type_id: int | None = None,
    ) -> list[CharacterClaim]: ...

    def list_application_template_fields(
        self,
        community_id: int,
    ) -> list[ApplicationTemplateField]: ...

    def get_application_template_field(
        self,
        community_id: int,
        field_id: int,
    ) -> ApplicationTemplateField: ...

    def get_claim_type(self, community_id: int, claim_type_id: int) -> ClaimType: ...

    def get_character(self, community_id: int, character_id: int) -> Character: ...

    def get_character_application(
        self,
        community_id: int,
        application_id: int,
    ) -> CharacterApplication: ...


def application_template_field_view(
    repo: ClaimReadRepository,
    community_id: int,
    field: ApplicationTemplateField,
) -> ApplicationTemplateFieldView:
    mapped_claim_type = (
        repo.get_claim_type(community_id, field.maps_to_claim_type_id)
        if field.maps_to_claim_type_id is not None
        else None
    )
    return ApplicationTemplateFieldView(
        field=field,
        options=_field_options(field),
        mapped_claim_type=mapped_claim_type,
    )


def application_field_value_view(
    repo: ClaimReadRepository,
    community_id: int,
    value: ApplicationFieldValue,
    field: ApplicationTemplateField | None = None,
) -> ApplicationFieldValueView:
    template_field = field or repo.get_application_template_field(
        community_id,
        value.field_id,
    )
    return ApplicationFieldValueView(
        value=value,
        field=application_template_field_view(repo, community_id, template_field),
    )


def claims_directory(repo: ClaimReadRepository, viewer: ForumView) -> ClaimsDirectory:
    fields = [
        application_template_field_view(repo, viewer.community.id, field)
        for field in repo.list_application_template_fields(viewer.community.id)
    ]
    field_claim_type_ids = {
        field.mapped_claim_type.id for field in fields if field.mapped_claim_type is not None
    }
    groups = []
    for claim_type in repo.list_claim_types(viewer.community.id):
        claims = [
            character_claim_view(repo, viewer.community.id, claim, claim_type=claim_type)
            for claim in repo.list_character_claims(
                viewer.community.id,
                status=None,
                claim_type_id=claim_type.id,
            )
        ]
        if (
            claim_type.visibility != "public"
            and not claims
            and claim_type.id not in field_claim_type_ids
        ):
            continue
        groups.append(
            ClaimTypeDirectory(
                claim_type=claim_type,
                claims=claims,
                template_fields=[
                    field
                    for field in fields
                    if field.mapped_claim_type is not None
                    and field.mapped_claim_type.id == claim_type.id
                ],
            )
        )
    return ClaimsDirectory(groups=groups)


def character_claim_view(
    repo: ClaimReadRepository,
    community_id: int,
    claim: CharacterClaim,
    *,
    claim_type: ClaimType | None = None,
) -> CharacterClaimView:
    character = (
        repo.get_character(community_id, claim.character_id)
        if claim.character_id is not None
        else None
    )
    application = (
        repo.get_character_application(community_id, claim.application_id)
        if claim.application_id is not None
        else None
    )
    return CharacterClaimView(
        claim=claim,
        claim_type=claim_type or repo.get_claim_type(community_id, claim.claim_type_id),
        character=character,
        application=application,
    )


def _field_options(field: ApplicationTemplateField) -> list[str]:
    try:
        raw = json.loads(field.options_json)
    except json.JSONDecodeError:
        return []
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if str(item).strip()]
