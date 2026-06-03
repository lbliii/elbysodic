from __future__ import annotations

import pytest

from elbysodic.domain import (
    CONTINUITY_AFFECTED_OBJECT_TYPES,
    CONTINUITY_PROPOSAL_STATES,
    CONTINUITY_SOURCE_TYPES,
    ContinuityAffectedObjectDraft,
    ContinuityCanonEntryDraft,
    ContinuityProposalDraft,
    ContinuityReviewEventDraft,
    ContinuitySourceCitationDraft,
    can_transition_continuity_proposal,
)


def test_continuity_vocabularies_name_manual_reviewed_source_links() -> None:
    assert (
        frozenset({"draft", "submitted", "revision_requested", "approved", "rejected", "archived"})
        == CONTINUITY_PROPOSAL_STATES
    )
    assert frozenset({"thread", "post"}) == CONTINUITY_SOURCE_TYPES
    assert {"character", "material", "thread", "wanted_ad"}.issubset(
        CONTINUITY_AFFECTED_OBJECT_TYPES
    )


def test_continuity_proposal_requires_same_community_sources_and_targets() -> None:
    citation = ContinuitySourceCitationDraft(
        community_id=1,
        source_type="post",
        source_id=30,
        source_thread_id=20,
    )
    affected = ContinuityAffectedObjectDraft(
        community_id=1,
        object_type="character",
        object_id=40,
    )

    proposal = ContinuityProposalDraft(
        community_id=1,
        author_membership_id=10,
        author_character_id=11,
        title="Rogue accepts the cost of the rescue",
        summary="A manual scene outcome awaiting review.",
        state="submitted",
        citations=(citation,),
        affected_objects=(affected,),
    )

    assert proposal.is_ready_for_submission is True

    with pytest.raises(ValueError, match="citation belongs to another community"):
        ContinuityProposalDraft(
            community_id=1,
            author_membership_id=10,
            title="Crossed source",
            summary="Wrong tenant source.",
            citations=(
                ContinuitySourceCitationDraft(
                    community_id=2,
                    source_type="thread",
                    source_id=99,
                ),
            ),
        )

    with pytest.raises(ValueError, match="affected object belongs to another community"):
        ContinuityProposalDraft(
            community_id=1,
            author_membership_id=10,
            title="Crossed affected object",
            summary="Wrong tenant target.",
            affected_objects=(
                ContinuityAffectedObjectDraft(
                    community_id=2,
                    object_type="material",
                    object_id=99,
                ),
            ),
        )


def test_submitted_continuity_proposal_requires_citation_and_affected_object() -> None:
    with pytest.raises(ValueError, match="source and affected links"):
        ContinuityProposalDraft(
            community_id=1,
            author_membership_id=10,
            title="Unlinked canon",
            summary="This cannot enter review without explicit provenance.",
            state="submitted",
        )

    with pytest.raises(ValueError, match="post source citations require source_thread_id"):
        ContinuitySourceCitationDraft(
            community_id=1,
            source_type="post",
            source_id=30,
        )


def test_public_continuity_visibility_requires_approval() -> None:
    citation = ContinuitySourceCitationDraft(
        community_id=1,
        source_type="thread",
        source_id=20,
    )
    affected = ContinuityAffectedObjectDraft(
        community_id=1,
        object_type="material",
        object_id=40,
    )

    with pytest.raises(ValueError, match="public continuity visibility requires approved state"):
        ContinuityProposalDraft(
            community_id=1,
            author_membership_id=10,
            title="Too soon",
            summary="Public before approval is forbidden.",
            citations=(citation,),
            affected_objects=(affected,),
            visibility="public",
        )

    approved = ContinuityProposalDraft(
        community_id=1,
        author_membership_id=10,
        title="Approved outcome",
        summary="Reviewed public canon.",
        state="approved",
        citations=(citation,),
        affected_objects=(affected,),
        visibility="public",
    )

    assert approved.visibility == "public"


def test_review_events_keep_staff_actor_membership_separate_from_character_context() -> None:
    event = ContinuityReviewEventDraft(
        community_id=1,
        proposal_id=20,
        actor_membership_id=30,
        actor_character_id=40,
        action="approved",
        note="Reviewed against visible source links.",
    )

    assert event.actor_membership_id == 30
    assert event.actor_character_id == 40


def test_canon_entry_requires_approved_public_contract() -> None:
    entry = ContinuityCanonEntryDraft(
        community_id=1,
        approved_proposal_id=20,
        approved_by_membership_id=30,
        title="Public canon outcome",
        summary="Approved and ready for public canon read models.",
    )

    assert entry.visibility == "public"

    with pytest.raises(ValueError, match="canon entries must use public visibility"):
        ContinuityCanonEntryDraft(
            community_id=1,
            approved_proposal_id=20,
            approved_by_membership_id=30,
            title="Hidden canon",
            summary="Canon entries are public only after approval.",
            visibility="staff",
        )


def test_continuity_lifecycle_distinguishes_author_and_reviewer_transitions() -> None:
    assert can_transition_continuity_proposal("draft", "submitted")
    assert can_transition_continuity_proposal("revision_requested", "submitted")
    assert not can_transition_continuity_proposal("submitted", "approved")
    assert can_transition_continuity_proposal("submitted", "approved", reviewer=True)
    assert can_transition_continuity_proposal(
        "submitted",
        "revision_requested",
        reviewer=True,
    )
    assert not can_transition_continuity_proposal("approved", "submitted", reviewer=True)
