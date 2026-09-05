"""Tenant-scoped manual Continuity Graph persistence."""

from __future__ import annotations

from collections.abc import Iterable

from elbysodic.db.repositories.base import (
    TenantBoundaryError,
    _last_id,
    _next_update_stamp,
    _utc_now,
)
from elbysodic.db.repositories.gateway import GatewayRepositoryMixin
from elbysodic.db.repositories.rows import (
    _continuity_affected_object_from_row,
    _continuity_canon_entry_from_row,
    _continuity_proposal_from_row,
    _continuity_review_event_from_row,
    _continuity_source_citation_from_row,
)
from elbysodic.domain.continuity import (
    CONTINUITY_PROPOSAL_STATES,
    CONTINUITY_REVIEW_ACTIONS,
    CONTINUITY_VISIBILITIES,
    ContinuityAffectedObject,
    ContinuityAffectedObjectDraft,
    ContinuityCanonEntry,
    ContinuityProposal,
    ContinuityProposalState,
    ContinuityReviewAction,
    ContinuityReviewEvent,
    ContinuitySourceCitation,
    ContinuitySourceCitationDraft,
    ContinuityVisibility,
)


class ContinuityRepositoryMixin(GatewayRepositoryMixin):
    def create_continuity_proposal(
        self,
        community_id: int,
        author_membership_id: int,
        *,
        title: str,
        summary: str = "",
        author_character_id: int | None = None,
        citations: Iterable[ContinuitySourceCitationDraft] = (),
        affected_objects: Iterable[ContinuityAffectedObjectDraft] = (),
    ) -> ContinuityProposal:
        cleaned_title = title.strip()
        if not cleaned_title:
            raise ValueError("continuity proposal title is required")
        citation_rows = tuple(citations)
        affected_rows = tuple(affected_objects)
        with self.transaction():
            membership = self.get_membership(community_id, author_membership_id)
            if not membership.is_active:
                raise PermissionError("continuity proposal authors must be active members")
            if author_character_id is not None:
                character = self.get_character(community_id, author_character_id)
                if character.membership_id != membership.id:
                    raise TenantBoundaryError("continuity proposal face must belong to its author")
            now = _utc_now()
            cursor = self.connection.execute(
                """
                INSERT INTO continuity_proposals (
                    community_id, author_membership_id, author_character_id,
                    title, summary, state, visibility, revision_note,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 'draft', 'private', '', ?, ?)
                """,
                (
                    community_id,
                    membership.id,
                    author_character_id,
                    cleaned_title,
                    summary.strip(),
                    now,
                    now,
                ),
            )
            proposal_id = _last_id(cursor)
            for citation in citation_rows:
                self._create_continuity_citation(community_id, proposal_id, citation, now)
            for affected in affected_rows:
                self._create_continuity_affected_object(
                    community_id,
                    proposal_id,
                    affected,
                    now,
                )
        return self.get_continuity_proposal(community_id, proposal_id)

    def get_continuity_proposal(
        self,
        community_id: int,
        proposal_id: int,
    ) -> ContinuityProposal:
        row = self.connection.execute(
            """
            SELECT id, community_id, author_membership_id, author_character_id,
                   title, summary, state, visibility, revision_note, created_at, updated_at
            FROM continuity_proposals
            WHERE community_id = ? AND id = ?
            """,
            (community_id, proposal_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"continuity proposal not found in community {community_id}: {proposal_id}"
            )
        return _continuity_proposal_from_row(row)

    def list_continuity_proposals(
        self,
        community_id: int,
        *,
        states: Iterable[ContinuityProposalState] | None = None,
        author_membership_id: int | None = None,
    ) -> list[ContinuityProposal]:
        self.get_community(community_id)
        clauses = ["community_id = ?"]
        values: list[object] = [community_id]
        if states is not None:
            selected = tuple(dict.fromkeys(states))
            unknown = set(selected) - CONTINUITY_PROPOSAL_STATES
            if unknown:
                raise ValueError(f"unknown continuity states: {', '.join(sorted(unknown))}")
            if not selected:
                return []
            clauses.append(f"state IN ({','.join('?' for _ in selected)})")
            values.extend(selected)
        if author_membership_id is not None:
            self.get_membership(community_id, author_membership_id)
            clauses.append("author_membership_id = ?")
            values.append(author_membership_id)
        rows = self.connection.execute(
            f"""
            SELECT id, community_id, author_membership_id, author_character_id,
                   title, summary, state, visibility, revision_note, created_at, updated_at
            FROM continuity_proposals
            WHERE {" AND ".join(clauses)}
            ORDER BY updated_at DESC, id DESC
            """,  # noqa: S608 - clauses are fixed and placeholders bind values.
            tuple(values),
        ).fetchall()
        return [_continuity_proposal_from_row(row) for row in rows]

    def list_continuity_source_citations(
        self,
        community_id: int,
        proposal_id: int,
    ) -> list[ContinuitySourceCitation]:
        self.get_continuity_proposal(community_id, proposal_id)
        rows = self.connection.execute(
            """
            SELECT id, community_id, proposal_id, source_type, source_id,
                   source_thread_id, created_at
            FROM continuity_source_citations
            WHERE community_id = ? AND proposal_id = ?
            ORDER BY id
            """,
            (community_id, proposal_id),
        ).fetchall()
        return [_continuity_source_citation_from_row(row) for row in rows]

    def list_continuity_affected_objects(
        self,
        community_id: int,
        proposal_id: int,
    ) -> list[ContinuityAffectedObject]:
        self.get_continuity_proposal(community_id, proposal_id)
        rows = self.connection.execute(
            """
            SELECT id, community_id, proposal_id, object_type, object_id, created_at
            FROM continuity_affected_objects
            WHERE community_id = ? AND proposal_id = ?
            ORDER BY id
            """,
            (community_id, proposal_id),
        ).fetchall()
        return [_continuity_affected_object_from_row(row) for row in rows]

    def update_continuity_proposal_state(
        self,
        community_id: int,
        proposal_id: int,
        *,
        state: ContinuityProposalState,
        visibility: ContinuityVisibility,
        revision_note: str = "",
    ) -> ContinuityProposal:
        proposal = self.get_continuity_proposal(community_id, proposal_id)
        if state not in CONTINUITY_PROPOSAL_STATES:
            raise ValueError(f"unknown continuity state: {state}")
        if visibility not in CONTINUITY_VISIBILITIES:
            raise ValueError(f"unknown continuity visibility: {visibility}")
        self.connection.execute(
            """
            UPDATE continuity_proposals
            SET state = ?, visibility = ?, revision_note = ?, updated_at = ?
            WHERE community_id = ? AND id = ?
            """,
            (
                state,
                visibility,
                revision_note.strip(),
                _next_update_stamp(proposal.updated_at),
                community_id,
                proposal.id,
            ),
        )
        self._commit()
        return self.get_continuity_proposal(community_id, proposal.id)

    def create_continuity_review_event(
        self,
        community_id: int,
        proposal_id: int,
        actor_membership_id: int,
        *,
        action: ContinuityReviewAction,
        actor_character_id: int | None = None,
        note: str = "",
    ) -> ContinuityReviewEvent:
        self.get_continuity_proposal(community_id, proposal_id)
        membership = self.get_membership(community_id, actor_membership_id)
        if action not in CONTINUITY_REVIEW_ACTIONS:
            raise ValueError(f"unknown continuity review action: {action}")
        if actor_character_id is not None:
            character = self.get_character(community_id, actor_character_id)
            if character.membership_id != membership.id:
                raise TenantBoundaryError("continuity review face must belong to its actor")
        cursor = self.connection.execute(
            """
            INSERT INTO continuity_review_events (
                community_id, proposal_id, actor_membership_id,
                actor_character_id, action, note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                proposal_id,
                actor_membership_id,
                actor_character_id,
                action,
                note.strip(),
                _utc_now(),
            ),
        )
        self._commit()
        return self.get_continuity_review_event(community_id, _last_id(cursor))

    def get_continuity_review_event(
        self,
        community_id: int,
        event_id: int,
    ) -> ContinuityReviewEvent:
        row = self.connection.execute(
            """
            SELECT id, community_id, proposal_id, actor_membership_id,
                   actor_character_id, action, note, created_at
            FROM continuity_review_events
            WHERE community_id = ? AND id = ?
            """,
            (community_id, event_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"continuity review event not found in community {community_id}: {event_id}"
            )
        return _continuity_review_event_from_row(row)

    def list_continuity_review_events(
        self,
        community_id: int,
        proposal_id: int,
    ) -> list[ContinuityReviewEvent]:
        self.get_continuity_proposal(community_id, proposal_id)
        rows = self.connection.execute(
            """
            SELECT id, community_id, proposal_id, actor_membership_id,
                   actor_character_id, action, note, created_at
            FROM continuity_review_events
            WHERE community_id = ? AND proposal_id = ?
            ORDER BY created_at, id
            """,
            (community_id, proposal_id),
        ).fetchall()
        return [_continuity_review_event_from_row(row) for row in rows]

    def create_continuity_canon_entry(
        self,
        community_id: int,
        approved_proposal_id: int,
        approved_by_membership_id: int,
        *,
        title: str,
        summary: str,
    ) -> ContinuityCanonEntry:
        proposal = self.get_continuity_proposal(community_id, approved_proposal_id)
        if proposal.state != "approved" or proposal.visibility != "public":
            raise ValueError("canon entries require an approved public continuity proposal")
        self.get_membership(community_id, approved_by_membership_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO canon_entries (
                community_id, approved_proposal_id, approved_by_membership_id,
                title, summary, visibility, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'public', ?, ?)
            """,
            (
                community_id,
                proposal.id,
                approved_by_membership_id,
                title.strip(),
                summary.strip(),
                now,
                now,
            ),
        )
        self._commit()
        return self.get_continuity_canon_entry(community_id, _last_id(cursor))

    def get_continuity_canon_entry(
        self,
        community_id: int,
        entry_id: int,
    ) -> ContinuityCanonEntry:
        row = self.connection.execute(
            """
            SELECT id, community_id, approved_proposal_id, approved_by_membership_id,
                   title, summary, visibility, created_at, updated_at
            FROM canon_entries
            WHERE community_id = ? AND id = ?
            """,
            (community_id, entry_id),
        ).fetchone()
        if row is None:
            raise LookupError(f"canon entry not found in community {community_id}: {entry_id}")
        return _continuity_canon_entry_from_row(row)

    def get_continuity_canon_entry_for_proposal(
        self,
        community_id: int,
        proposal_id: int,
    ) -> ContinuityCanonEntry | None:
        row = self.connection.execute(
            """
            SELECT id, community_id, approved_proposal_id, approved_by_membership_id,
                   title, summary, visibility, created_at, updated_at
            FROM canon_entries
            WHERE community_id = ? AND approved_proposal_id = ?
            """,
            (community_id, proposal_id),
        ).fetchone()
        return None if row is None else _continuity_canon_entry_from_row(row)

    def list_continuity_canon_entries(self, community_id: int) -> list[ContinuityCanonEntry]:
        self.get_community(community_id)
        rows = self.connection.execute(
            """
            SELECT id, community_id, approved_proposal_id, approved_by_membership_id,
                   title, summary, visibility, created_at, updated_at
            FROM canon_entries
            WHERE community_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (community_id,),
        ).fetchall()
        return [_continuity_canon_entry_from_row(row) for row in rows]

    def _create_continuity_citation(
        self,
        community_id: int,
        proposal_id: int,
        citation: ContinuitySourceCitationDraft,
        created_at: str,
    ) -> None:
        if citation.community_id != community_id:
            raise TenantBoundaryError("continuity citation belongs to another community")
        if citation.source_type == "thread":
            thread = self.get_thread(community_id, citation.source_id)
            source_thread_id = thread.id
        else:
            if citation.source_thread_id is None:
                raise ValueError("post continuity citations require a source thread")
            thread = self.get_thread(community_id, citation.source_thread_id)
            post = self.get_post(community_id, citation.source_id)
            if post.thread_id != thread.id:
                raise TenantBoundaryError("continuity post citation does not belong to its thread")
            source_thread_id = thread.id
        self.connection.execute(
            """
            INSERT INTO continuity_source_citations (
                community_id, proposal_id, source_type, source_id,
                source_thread_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                proposal_id,
                citation.source_type,
                citation.source_id,
                source_thread_id,
                created_at,
            ),
        )

    def _create_continuity_affected_object(
        self,
        community_id: int,
        proposal_id: int,
        affected: ContinuityAffectedObjectDraft,
        created_at: str,
    ) -> None:
        if affected.community_id != community_id:
            raise TenantBoundaryError("continuity affected object belongs to another community")
        match affected.object_type:
            case "board":
                self.get_board(community_id, affected.object_id)
            case "character":
                self.get_character(community_id, affected.object_id)
            case "claim":
                self.get_character_claim(community_id, affected.object_id)
            case "material":
                self.get_material(community_id, affected.object_id)
            case "plot_hook":
                self.get_character_plot_hook(community_id, affected.object_id)
            case "reserve":
                self.get_character_reserve(community_id, affected.object_id)
            case "thread":
                self.get_thread(community_id, affected.object_id)
            case "wanted_ad":
                self.get_wanted_ad(community_id, affected.object_id)
        self.connection.execute(
            """
            INSERT INTO continuity_affected_objects (
                community_id, proposal_id, object_type, object_id, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                community_id,
                proposal_id,
                affected.object_type,
                affected.object_id,
                created_at,
            ),
        )
