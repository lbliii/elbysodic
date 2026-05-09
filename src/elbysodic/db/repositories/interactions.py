"""Realm quiz, poll, and survey repository methods."""

from __future__ import annotations

from collections.abc import Mapping

from elbysodic.db.repositories.base import (
    TenantBoundaryError,
    _last_id,
    _next_update_stamp,
    _utc_now,
)
from elbysodic.db.repositories.rows import (
    _realm_interaction_answer_from_row,
    _realm_interaction_from_row,
    _realm_interaction_option_from_row,
    _realm_interaction_question_from_row,
    _realm_interaction_response_from_row,
)
from elbysodic.db.repositories.threads import ThreadRepositoryMixin
from elbysodic.domain.models import (
    RealmInteraction,
    RealmInteractionAnswer,
    RealmInteractionOption,
    RealmInteractionQuestion,
    RealmInteractionResponse,
)


class InteractionRepositoryMixin(ThreadRepositoryMixin):
    def create_realm_interaction(
        self,
        community_id: int,
        slug: str,
        title: str,
        *,
        interaction_type: str = "quiz",
        placement: str = "general",
        summary: str = "",
        body: str = "",
        status: str = "open",
        result_mode: str = "confirmation",
        sort_order: int = 0,
    ) -> RealmInteraction:
        self.get_community(community_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO realm_interactions (
                community_id,
                slug,
                title,
                interaction_type,
                placement,
                summary,
                body,
                status,
                result_mode,
                sort_order,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                slug,
                title,
                interaction_type,
                placement,
                summary,
                body,
                status,
                result_mode,
                sort_order,
                now,
                now,
            ),
        )
        self._commit()
        return self.get_realm_interaction(community_id, _last_id(cursor))

    def get_realm_interaction(
        self,
        community_id: int,
        interaction_id: int,
    ) -> RealmInteraction:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                title,
                interaction_type,
                placement,
                summary,
                body,
                status,
                result_mode,
                sort_order,
                created_at,
                updated_at
            FROM realm_interactions
            WHERE community_id = ? AND id = ?
            """,
            (community_id, interaction_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"realm interaction not found in community {community_id}: {interaction_id}"
            )
        return _realm_interaction_from_row(row)

    def get_realm_interaction_by_slug(
        self,
        community_id: int,
        slug: str,
    ) -> RealmInteraction:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                slug,
                title,
                interaction_type,
                placement,
                summary,
                body,
                status,
                result_mode,
                sort_order,
                created_at,
                updated_at
            FROM realm_interactions
            WHERE community_id = ? AND slug = ?
            """,
            (community_id, slug),
        ).fetchone()
        if row is None:
            raise LookupError(f"realm interaction not found in community {community_id}: {slug}")
        return _realm_interaction_from_row(row)

    def list_realm_interactions(
        self,
        community_id: int,
        *,
        status: str | None = "open",
        placement: str | None = None,
    ) -> list[RealmInteraction]:
        clauses = ["community_id = ?"]
        params: list[object] = [community_id]
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if placement is not None:
            clauses.append("placement = ?")
            params.append(placement)
        where = " AND ".join(clauses)
        if where == "community_id = ?":
            query = """
                SELECT
                    id,
                    community_id,
                    slug,
                    title,
                    interaction_type,
                    placement,
                    summary,
                    body,
                    status,
                    result_mode,
                    sort_order,
                    created_at,
                    updated_at
                FROM realm_interactions
                WHERE community_id = ?
                ORDER BY sort_order, title, id
                """
        elif where == "community_id = ? AND status = ?":
            query = """
                SELECT
                    id,
                    community_id,
                    slug,
                    title,
                    interaction_type,
                    placement,
                    summary,
                    body,
                    status,
                    result_mode,
                    sort_order,
                    created_at,
                    updated_at
                FROM realm_interactions
                WHERE community_id = ? AND status = ?
                ORDER BY sort_order, title, id
                """
        elif where == "community_id = ? AND placement = ?":
            query = """
                SELECT
                    id,
                    community_id,
                    slug,
                    title,
                    interaction_type,
                    placement,
                    summary,
                    body,
                    status,
                    result_mode,
                    sort_order,
                    created_at,
                    updated_at
                FROM realm_interactions
                WHERE community_id = ? AND placement = ?
                ORDER BY sort_order, title, id
                """
        else:
            query = """
                SELECT
                    id,
                    community_id,
                    slug,
                    title,
                    interaction_type,
                    placement,
                    summary,
                    body,
                    status,
                    result_mode,
                    sort_order,
                    created_at,
                    updated_at
                FROM realm_interactions
                WHERE community_id = ? AND status = ? AND placement = ?
                ORDER BY sort_order, title, id
                """
        rows = self.connection.execute(
            query,
            tuple(params),
        ).fetchall()
        return [_realm_interaction_from_row(row) for row in rows]

    def create_realm_interaction_question(
        self,
        community_id: int,
        interaction_id: int,
        prompt: str,
        *,
        help_text: str = "",
        question_type: str = "single_choice",
        is_required: bool = True,
        sort_order: int = 0,
    ) -> RealmInteractionQuestion:
        self.get_realm_interaction(community_id, interaction_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO realm_interaction_questions (
                community_id,
                interaction_id,
                prompt,
                help_text,
                question_type,
                is_required,
                sort_order,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                interaction_id,
                prompt,
                help_text,
                question_type,
                int(is_required),
                sort_order,
                now,
                now,
            ),
        )
        self._commit()
        return self.get_realm_interaction_question(community_id, _last_id(cursor))

    def get_realm_interaction_question(
        self,
        community_id: int,
        question_id: int,
    ) -> RealmInteractionQuestion:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                interaction_id,
                prompt,
                help_text,
                question_type,
                is_required,
                sort_order,
                created_at,
                updated_at
            FROM realm_interaction_questions
            WHERE community_id = ? AND id = ?
            """,
            (community_id, question_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"realm interaction question not found in community {community_id}: {question_id}"
            )
        return _realm_interaction_question_from_row(row)

    def list_realm_interaction_questions(
        self,
        community_id: int,
        interaction_id: int,
    ) -> list[RealmInteractionQuestion]:
        self.get_realm_interaction(community_id, interaction_id)
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                interaction_id,
                prompt,
                help_text,
                question_type,
                is_required,
                sort_order,
                created_at,
                updated_at
            FROM realm_interaction_questions
            WHERE community_id = ? AND interaction_id = ?
            ORDER BY sort_order, id
            """,
            (community_id, interaction_id),
        ).fetchall()
        return [_realm_interaction_question_from_row(row) for row in rows]

    def create_realm_interaction_option(
        self,
        community_id: int,
        question_id: int,
        slug: str,
        label: str,
        *,
        description: str = "",
        result_key: str = "",
        score: int = 0,
        sort_order: int = 0,
    ) -> RealmInteractionOption:
        self.get_realm_interaction_question(community_id, question_id)
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO realm_interaction_options (
                community_id,
                question_id,
                slug,
                label,
                description,
                result_key,
                score,
                sort_order,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                community_id,
                question_id,
                slug,
                label,
                description,
                result_key,
                score,
                sort_order,
                now,
                now,
            ),
        )
        self._commit()
        return self.get_realm_interaction_option(community_id, _last_id(cursor))

    def get_realm_interaction_option(
        self,
        community_id: int,
        option_id: int,
    ) -> RealmInteractionOption:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                question_id,
                slug,
                label,
                description,
                result_key,
                score,
                sort_order,
                created_at,
                updated_at
            FROM realm_interaction_options
            WHERE community_id = ? AND id = ?
            """,
            (community_id, option_id),
        ).fetchone()
        if row is None:
            raise LookupError(
                f"realm interaction option not found in community {community_id}: {option_id}"
            )
        return _realm_interaction_option_from_row(row)

    def list_realm_interaction_options(
        self,
        community_id: int,
        question_id: int,
    ) -> list[RealmInteractionOption]:
        self.get_realm_interaction_question(community_id, question_id)
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                question_id,
                slug,
                label,
                description,
                result_key,
                score,
                sort_order,
                created_at,
                updated_at
            FROM realm_interaction_options
            WHERE community_id = ? AND question_id = ?
            ORDER BY sort_order, id
            """,
            (community_id, question_id),
        ).fetchall()
        return [_realm_interaction_option_from_row(row) for row in rows]

    def get_realm_interaction_response_for_membership(
        self,
        community_id: int,
        interaction_id: int,
        membership_id: int,
    ) -> RealmInteractionResponse | None:
        row = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                interaction_id,
                membership_id,
                character_id,
                created_at,
                updated_at
            FROM realm_interaction_responses
            WHERE community_id = ? AND interaction_id = ? AND membership_id = ?
            """,
            (community_id, interaction_id, membership_id),
        ).fetchone()
        if row is None:
            return None
        return _realm_interaction_response_from_row(row)

    def list_realm_interaction_answers(
        self,
        community_id: int,
        response_id: int,
    ) -> list[RealmInteractionAnswer]:
        rows = self.connection.execute(
            """
            SELECT
                id,
                community_id,
                response_id,
                question_id,
                option_id,
                text_answer,
                created_at
            FROM realm_interaction_answers
            WHERE community_id = ? AND response_id = ?
            ORDER BY id
            """,
            (community_id, response_id),
        ).fetchall()
        return [_realm_interaction_answer_from_row(row) for row in rows]

    def submit_realm_interaction_response(
        self,
        community_id: int,
        interaction_id: int,
        membership_id: int,
        *,
        selected_option_ids: Mapping[int, int],
        character_id: int | None = None,
    ) -> RealmInteractionResponse:
        interaction = self.get_realm_interaction(community_id, interaction_id)
        membership = self.get_membership(community_id, membership_id)
        if membership.community_id != interaction.community_id:
            raise TenantBoundaryError("membership must belong to the interaction community")
        if character_id is not None:
            character = self.get_character(community_id, character_id)
            if character.membership_id != membership.id:
                raise TenantBoundaryError("character must belong to the responding membership")

        questions = {
            question.id: question
            for question in self.list_realm_interaction_questions(community_id, interaction.id)
        }
        option_questions: dict[int, int] = {}
        for question_id, option_id in selected_option_ids.items():
            question = questions.get(question_id)
            if question is None:
                raise TenantBoundaryError("answer question must belong to the interaction")
            option = self.get_realm_interaction_option(community_id, option_id)
            if option.question_id != question.id:
                raise TenantBoundaryError("answer option must belong to its question")
            option_questions[question_id] = option_id

        missing_required = [
            question.prompt
            for question in questions.values()
            if question.is_required and question.id not in option_questions
        ]
        if missing_required:
            raise ValueError("choose an answer for every required question")

        now = _utc_now()
        existing = self.get_realm_interaction_response_for_membership(
            community_id,
            interaction.id,
            membership.id,
        )
        if existing is None:
            cursor = self.connection.execute(
                """
                INSERT INTO realm_interaction_responses (
                    community_id,
                    interaction_id,
                    membership_id,
                    character_id,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (community_id, interaction.id, membership.id, character_id, now, now),
            )
            response_id = _last_id(cursor)
        else:
            response_id = existing.id
            self.connection.execute(
                """
                UPDATE realm_interaction_responses
                SET character_id = ?, updated_at = ?
                WHERE community_id = ? AND id = ?
                """,
                (
                    character_id,
                    _next_update_stamp(existing.updated_at),
                    community_id,
                    existing.id,
                ),
            )
            self.connection.execute(
                """
                DELETE FROM realm_interaction_answers
                WHERE community_id = ? AND response_id = ?
                """,
                (community_id, existing.id),
            )

        for question_id, option_id in option_questions.items():
            self.connection.execute(
                """
                INSERT INTO realm_interaction_answers (
                    community_id,
                    response_id,
                    question_id,
                    option_id,
                    text_answer,
                    created_at
                )
                VALUES (?, ?, ?, ?, '', ?)
                """,
                (community_id, response_id, question_id, option_id, now),
            )
        self._commit()
        response = self.get_realm_interaction_response_for_membership(
            community_id,
            interaction.id,
            membership.id,
        )
        if response is None:
            raise RuntimeError("realm interaction response was not persisted")
        return response

    def count_realm_interaction_responses(self, community_id: int, interaction_id: int) -> int:
        row = self.connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM realm_interaction_responses
            WHERE community_id = ? AND interaction_id = ?
            """,
            (community_id, interaction_id),
        ).fetchone()
        return int(row["count"] if row is not None else 0)

    def realm_interaction_option_counts(
        self,
        community_id: int,
        interaction_id: int,
    ) -> dict[int, int]:
        rows = self.connection.execute(
            """
            SELECT answers.option_id, COUNT(*) AS count
            FROM realm_interaction_answers AS answers
            JOIN realm_interaction_questions AS questions
              ON questions.id = answers.question_id
             AND questions.community_id = answers.community_id
            WHERE answers.community_id = ?
              AND questions.interaction_id = ?
              AND answers.option_id IS NOT NULL
            GROUP BY answers.option_id
            """,
            (community_id, interaction_id),
        ).fetchall()
        return {int(row["option_id"]): int(row["count"]) for row in rows}
