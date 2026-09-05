"""Atomic application-command execution."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol


class CommandSubmission(Protocol):
    @property
    def result_path(self) -> str | None: ...


class CommandRepository(Protocol):
    def transaction(self) -> AbstractContextManager[None]: ...

    def get_command_submission(
        self,
        community_id: int,
        membership_id: int,
        *,
        command_key: str,
        token: str,
    ) -> CommandSubmission | None: ...

    def reserve_command_submission(
        self,
        community_id: int,
        membership_id: int,
        *,
        command_key: str,
        token: str,
    ) -> bool: ...

    def complete_command_submission(
        self,
        community_id: int,
        membership_id: int,
        *,
        command_key: str,
        token: str,
        result_path: str,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class CommandExecution:
    result_path: str
    replayed: bool


class PendingCommandError(ValueError):
    """Raised when an older command reservation has no trustworthy result."""


def execute_command(
    repo: CommandRepository,
    *,
    command_key: str,
    token: str,
    resolve_scope: Callable[[], tuple[int, int]],
    operation: Callable[[], str],
) -> CommandExecution:
    """Commit one command's mutation and replay result as a single unit."""
    with repo.transaction():
        community_id, membership_id = resolve_scope()
        if token:
            submission = repo.get_command_submission(
                community_id,
                membership_id,
                command_key=command_key,
                token=token,
            )
            if submission is not None and submission.result_path is not None:
                return CommandExecution(submission.result_path, replayed=True)
            if submission is not None:
                raise PendingCommandError(
                    "This submission may already have completed, but its result was not "
                    "recorded. Reload the scene before posting again."
                )
            if not repo.reserve_command_submission(
                community_id,
                membership_id,
                command_key=command_key,
                token=token,
            ):
                raise RuntimeError("command token could not be reserved")

        result_path = operation()
        if token:
            repo.complete_command_submission(
                community_id,
                membership_id,
                command_key=command_key,
                token=token,
                result_path=result_path,
            )
    return CommandExecution(result_path, replayed=False)
