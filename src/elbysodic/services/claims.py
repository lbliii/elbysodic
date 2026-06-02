"""Service helpers for director-defined claims and application templates."""

from __future__ import annotations

import json
import re
from typing import Protocol

from elbysodic.domain.models import (
    ApplicationFieldValue,
    ApplicationTemplateField,
    Character,
    CharacterApplication,
    CharacterClaim,
    ClaimType,
)
from elbysodic.services import policies
from elbysodic.services.read_models import (
    ApplicationClaimCheck,
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
    field_view = application_template_field_view(repo, community_id, template_field)
    return ApplicationFieldValueView(
        value=value,
        field=field_view,
        claim_check=_application_claim_check(repo, community_id, value, field_view),
    )


def application_claim_checks(
    repo: ClaimReadRepository,
    community_id: int,
    field_values: dict[int, str],
    *,
    character_id: int | None = None,
    application_id: int | None = None,
) -> dict[int, ApplicationClaimCheck]:
    checks: dict[int, ApplicationClaimCheck] = {}
    for field_id, value in field_values.items():
        field = repo.get_application_template_field(community_id, field_id)
        field_view = application_template_field_view(repo, community_id, field)
        check = _claim_check_for_value(
            repo,
            community_id,
            field_view,
            value,
            character_id=character_id,
            application_id=application_id,
        )
        if check is not None:
            checks[field_id] = check
    return checks


def claims_directory(
    repo: ClaimReadRepository,
    viewer: ForumView,
    *,
    status_filter: str | None = None,
    search_query: str = "",
) -> ClaimsDirectory:
    cleaned_search_query = search_query.strip()
    fields = [
        application_template_field_view(repo, viewer.community.id, field)
        for field in repo.list_application_template_fields(viewer.community.id)
    ]
    field_claim_type_ids = {
        field.mapped_claim_type.id for field in fields if field.mapped_claim_type is not None
    }
    groups = []
    for claim_type in repo.list_claim_types(viewer.community.id):
        all_claims = [
            character_claim_view(repo, viewer.community.id, claim, claim_type=claim_type)
            for claim in repo.list_character_claims(
                viewer.community.id,
                status=None,
                claim_type_id=claim_type.id,
            )
        ]
        visible_claims = (
            [claim for claim in all_claims if claim.claim.status == status_filter]
            if status_filter is not None
            else all_claims
        )
        if cleaned_search_query:
            visible_claims = [
                claim
                for claim in visible_claims
                if _claim_matches_search(claim_type, claim, cleaned_search_query)
            ]
        if (
            claim_type.visibility != "public"
            and not all_claims
            and claim_type.id not in field_claim_type_ids
        ):
            continue
        groups.append(
            ClaimTypeDirectory(
                claim_type=claim_type,
                claims=visible_claims,
                template_fields=[
                    field
                    for field in fields
                    if field.mapped_claim_type is not None
                    and field.mapped_claim_type.id == claim_type.id
                ],
                total_count=len(all_claims),
                claimed_count=_claim_status_count(all_claims, "claimed"),
                reserved_count=_claim_status_count(all_claims, "reserved"),
                available_count=_claim_status_count(all_claims, "available"),
            )
        )
    return ClaimsDirectory(
        groups=groups,
        status_filter=status_filter,
        search_query=cleaned_search_query,
        can_manage=policies.can_manage_applications(viewer.membership, viewer.role),
    )


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


def _application_claim_check(
    repo: ClaimReadRepository,
    community_id: int,
    field_value: ApplicationFieldValue,
    field: ApplicationTemplateFieldView,
) -> ApplicationClaimCheck | None:
    application = repo.get_character_application(community_id, field_value.application_id)
    return _claim_check_for_value(
        repo,
        community_id,
        field,
        field_value.value,
        character_id=application.character_id,
        application_id=field_value.application_id,
    )


def _claim_check_for_value(
    repo: ClaimReadRepository,
    community_id: int,
    field: ApplicationTemplateFieldView,
    value: str,
    *,
    character_id: int | None = None,
    application_id: int | None = None,
) -> ApplicationClaimCheck | None:
    claim_type = field.mapped_claim_type
    if claim_type is None:
        return None
    label = value.strip()
    if not label:
        return ApplicationClaimCheck(
            status="empty",
            label="No claim value",
            variant="muted",
        )
    claim_value = _claim_value_key(label)
    live_claims = [
        claim
        for claim in repo.list_character_claims(
            community_id,
            status=None,
            claim_type_id=claim_type.id,
        )
        if claim.value == claim_value and claim.status in {"claimed", "reserved"}
    ]
    owned_claim = next(
        (
            claim
            for claim in live_claims
            if (application_id is not None and claim.application_id == application_id)
            or (character_id is not None and claim.character_id == character_id)
        ),
        None,
    )
    if owned_claim is not None:
        return ApplicationClaimCheck(
            status="linked",
            label="Already linked",
            variant="info",
            claim=character_claim_view(
                repo,
                community_id,
                owned_claim,
                claim_type=claim_type,
            ),
        )
    conflicting_claim = live_claims[0] if live_claims else None
    if claim_type.is_exclusive and conflicting_claim is not None:
        return ApplicationClaimCheck(
            status="conflict",
            label="Reserved" if conflicting_claim.status == "reserved" else "Already claimed",
            variant="warning",
            claim=character_claim_view(
                repo,
                community_id,
                conflicting_claim,
                claim_type=claim_type,
            ),
        )
    if claim_type.is_exclusive:
        return ApplicationClaimCheck(
            status="available",
            label="Available",
            variant="success",
        )
    return ApplicationClaimCheck(
        status="shared",
        label="Shared lane" if conflicting_claim is not None else "Tracked on accept",
        variant="info",
        claim=(
            character_claim_view(
                repo,
                community_id,
                conflicting_claim,
                claim_type=claim_type,
            )
            if conflicting_claim is not None
            else None
        ),
    )


def _field_options(field: ApplicationTemplateField) -> list[str]:
    try:
        raw = json.loads(field.options_json)
    except json.JSONDecodeError:
        return []
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if str(item).strip()]


def _claim_value_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or value.strip().lower()


def _claim_status_count(claims: list[CharacterClaimView], status: str) -> int:
    return len([claim for claim in claims if claim.claim.status == status])


def _claim_matches_search(
    claim_type: ClaimType,
    claim: CharacterClaimView,
    search_query: str,
) -> bool:
    needle = search_query.casefold()
    searchable = [
        claim_type.name,
        claim_type.claim_kind,
        claim.claim.label,
        claim.claim.value,
        claim.claim.status,
        claim.status_label,
    ]
    if claim.character is not None:
        searchable.extend([claim.character.name, claim.character.slug])
    return any(needle in value.casefold() for value in searchable if value)
