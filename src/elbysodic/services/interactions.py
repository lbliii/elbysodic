"""Service helpers for realm quizzes, polls, and surveys."""

from __future__ import annotations

from collections.abc import Mapping

from elbysodic.db import ForumRepository
from elbysodic.domain.models import RealmInteraction
from elbysodic.services.read_models import (
    ForumView,
    RealmInteractionDetail,
    RealmInteractionHub,
    RealmInteractionOptionView,
    RealmInteractionQuestionView,
    RealmInteractionSummary,
)


def realm_interaction_summary(
    repo: ForumRepository,
    viewer: ForumView,
    interaction: RealmInteraction,
) -> RealmInteractionSummary:
    return RealmInteractionSummary(
        interaction=interaction,
        response_count=repo.count_realm_interaction_responses(
            viewer.community.id,
            interaction.id,
        ),
        has_response=repo.get_realm_interaction_response_for_membership(
            viewer.community.id,
            interaction.id,
            viewer.membership.id,
        )
        is not None,
    )


def realm_interaction_hub(repo: ForumRepository, viewer: ForumView) -> RealmInteractionHub:
    return RealmInteractionHub(
        interactions=[
            realm_interaction_summary(repo, viewer, interaction)
            for interaction in repo.list_realm_interactions(viewer.community.id)
        ]
    )


def read_realm_interaction(
    repo: ForumRepository,
    viewer: ForumView,
    slug: str,
) -> RealmInteractionDetail:
    interaction = repo.get_realm_interaction_by_slug(viewer.community.id, slug)
    response = repo.get_realm_interaction_response_for_membership(
        viewer.community.id,
        interaction.id,
        viewer.membership.id,
    )
    answers = (
        repo.list_realm_interaction_answers(viewer.community.id, response.id)
        if response is not None
        else []
    )
    selected_option_ids = {answer.option_id for answer in answers if answer.option_id is not None}
    option_counts = repo.realm_interaction_option_counts(viewer.community.id, interaction.id)
    questions = [
        RealmInteractionQuestionView(
            question=question,
            options=[
                RealmInteractionOptionView(
                    option=option,
                    response_count=option_counts.get(option.id, 0),
                    is_selected=option.id in selected_option_ids,
                )
                for option in repo.list_realm_interaction_options(
                    viewer.community.id,
                    question.id,
                )
            ],
        )
        for question in repo.list_realm_interaction_questions(viewer.community.id, interaction.id)
    ]
    return RealmInteractionDetail(
        summary=realm_interaction_summary(repo, viewer, interaction),
        questions=questions,
        response=response,
        answers=answers,
    )


def submit_realm_interaction(
    repo: ForumRepository,
    viewer: ForumView,
    slug: str,
    selected_option_ids: Mapping[int, int],
) -> RealmInteractionDetail:
    interaction = repo.get_realm_interaction_by_slug(viewer.community.id, slug)
    if interaction.status != "open":
        raise ValueError("this realm artifact is not accepting responses")
    repo.submit_realm_interaction_response(
        viewer.community.id,
        interaction.id,
        viewer.membership.id,
        character_id=viewer.current_character.id if viewer.current_character is not None else None,
        selected_option_ids=selected_option_ids,
    )
    return read_realm_interaction(repo, viewer, slug)
