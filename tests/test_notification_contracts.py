from __future__ import annotations

from dataclasses import replace

import pytest

from elbysodic.db.seed import resolve_seed_persona
from elbysodic.domain.models import Notification
from elbysodic.services import AppServices, create_services
from elbysodic.services.notifications import (
    NOTIFICATION_TARGET_CONTRACTS,
    notification_has_required_target,
    notification_label,
    notification_target_contract,
    notification_target_is_deliverable,
    notify_post_created,
)


def test_notification_target_contracts_are_registered_once() -> None:
    kinds = [contract.kind for contract in NOTIFICATION_TARGET_CONTRACTS]

    assert len(kinds) == len(set(kinds))
    assert set(kinds) == {
        "application_accepted",
        "application_revision_requested",
        "application_submitted",
        "mention",
        "plot_hook_interest",
        "plotting_room_created",
        "plotting_room_threaded",
        "reserve_created",
        "thread_reply",
        "wanted_interest",
        "wanted_reserved",
    }


def test_notification_labels_come_from_target_contracts() -> None:
    for contract in NOTIFICATION_TARGET_CONTRACTS:
        assert notification_label(contract.kind) == contract.label

    assert notification_label("unknown") == "Notification"


def test_notification_target_contracts_name_visibility_rules() -> None:
    expected = {
        "thread_reply": ("thread_post", ("thread_id", "post_id")),
        "mention": ("thread_post", ("thread_id", "post_id")),
        "wanted_interest": ("wanted_interest", ("wanted_ad_id", "wanted_ad_interest_id")),
        "plot_hook_interest": ("plot_hook", ("character_plot_hook_id",)),
        "plotting_room_created": ("plotting_room", ("plotting_room_id",)),
        "application_submitted": ("character_application", ("character_id",)),
    }

    for kind, (target_family, required_fields) in expected.items():
        contract = notification_target_contract(kind)
        assert contract is not None
        assert contract.target_family == target_family
        assert contract.required_fields == required_fields
        assert contract.visibility_rule
        assert contract.redirect_behavior
        assert contract.fallback_behavior


def test_registered_notification_requires_declared_target_fields() -> None:
    notification = _notification(
        kind="thread_reply",
        thread_id=10,
        post_id=20,
    )

    assert notification_has_required_target(notification)
    assert not notification_has_required_target(replace(notification, post_id=None))


def test_unknown_notification_kind_is_inaccessible_to_service_surfaces() -> None:
    notification = _notification(kind="legacy_kind")

    assert notification_target_contract(notification.kind) is None
    assert not notification_has_required_target(notification)


def test_registered_notification_with_missing_target_does_not_render_or_mark_read() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    viewer = services.viewer()
    before_inbox = services.notifications()
    before_ids = {item.notification.id for item in before_inbox.items}
    cursor = repo.connection.execute(
        """
        INSERT INTO notifications (
            community_id,
            membership_id,
            kind,
            actor_membership_id,
            actor_character_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            viewer.community.id,
            viewer.membership.id,
            "thread_reply",
            viewer.membership.id,
            viewer.current_character.id if viewer.current_character is not None else None,
            "2026-01-01T00:00:00+00:00",
        ),
    )
    repo.connection.commit()
    assert cursor.lastrowid is not None
    notification_id = cursor.lastrowid

    inbox = services.notifications()

    assert inbox.unread_count == before_inbox.unread_count
    assert {item.notification.id for item in inbox.items} == before_ids
    with pytest.raises(LookupError, match="notification target not found"):
        services.open_notification(notification_id)
    assert repo.get_notification(viewer.community.id, notification_id).read_at is None

    services.mark_all_notifications_read()

    assert repo.get_notification(viewer.community.id, notification_id).read_at is None


def test_unregistered_notification_kind_does_not_render_count_open_or_mark_read() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    viewer = services.viewer()
    assert viewer.current_character is not None
    notification = repo.create_notification(
        viewer.community.id,
        viewer.membership.id,
        kind="legacy_character",
        character_id=viewer.current_character.id,
        actor_membership_id=viewer.membership.id,
        actor_character_id=viewer.current_character.id,
    )

    inbox = services.notifications()

    assert inbox.unread_count == 0
    assert inbox.items == []
    with pytest.raises(LookupError, match="notification target not found"):
        services.open_notification(notification.id)
    assert repo.get_notification(viewer.community.id, notification.id).read_at is None

    services.mark_all_notifications_read()

    assert repo.get_notification(viewer.community.id, notification.id).read_at is None


def test_post_notification_creation_skips_memberships_that_cannot_view_target() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    writer = services.seed
    staff = resolve_seed_persona(repo, "xmen_staff")
    outsider = resolve_seed_persona(repo, "xmen_outsider")
    assert writer.default_character is not None
    assert staff.character is not None
    private_board = repo.create_board(
        writer.community.id,
        "notification-private-target",
        "Notification Private Target",
        is_private=True,
    )
    private_thread = repo.create_thread(
        writer.community.id,
        private_board.id,
        writer.default_character.id,
        "notification-private-thread",
        "Notification private thread",
    )
    repo.watch_thread(writer.community.id, private_thread.id, outsider.membership.id)
    repo.watch_thread(writer.community.id, private_thread.id, staff.membership.id)
    post = repo.create_post(
        writer.community.id,
        private_thread.id,
        writer.default_character.id,
        "A private reply should notify only viewers who can enter the room.",
    )
    writer_services = AppServices(repo, writer)

    notify_post_created(repo, writer_services.viewer(), private_thread, post)

    outsider_notifications = repo.list_notifications(
        writer.community.id,
        outsider.membership.id,
    )
    staff_notifications = repo.list_notifications(writer.community.id, staff.membership.id)
    assert outsider_notifications == []
    assert [notification.kind for notification in staff_notifications] == ["thread_reply"]


def test_notification_delivery_helper_rejects_inactive_or_malformed_targets() -> None:
    services = create_services(path=":memory:")
    repo = services.repo
    inactive = resolve_seed_persona(repo, "xmen_inactive")
    writer = services.seed
    assert writer.default_character is not None
    board = repo.get_board_by_slug(writer.community.id, "danger-room")
    thread = repo.create_thread(
        writer.community.id,
        board.id,
        writer.default_character.id,
        "notification-delivery-helper",
        "Notification delivery helper",
    )
    post = repo.create_post(
        writer.community.id,
        thread.id,
        writer.default_character.id,
        "A public target with an inactive watcher.",
    )

    assert not notification_target_is_deliverable(
        repo,
        writer.community.id,
        inactive.membership.id,
        kind="thread_reply",
        thread_id=thread.id,
        post_id=post.id,
        actor_membership_id=writer.membership.id,
        actor_character_id=writer.default_character.id,
    )
    assert not notification_target_is_deliverable(
        repo,
        writer.community.id,
        writer.membership.id,
        kind="thread_reply",
        thread_id=thread.id,
        post_id=None,
        actor_membership_id=writer.membership.id,
        actor_character_id=writer.default_character.id,
    )


def _notification(
    *,
    kind: str,
    thread_id: int | None = None,
    post_id: int | None = None,
) -> Notification:
    return Notification(
        id=1,
        community_id=1,
        membership_id=2,
        kind=kind,
        thread_id=thread_id,
        post_id=post_id,
        wanted_ad_id=None,
        wanted_ad_interest_id=None,
        character_plot_hook_id=None,
        plotting_room_id=None,
        character_id=None,
        actor_membership_id=3,
        actor_character_id=None,
        read_at=None,
        created_at="2026-01-01T00:00:00+00:00",
    )
