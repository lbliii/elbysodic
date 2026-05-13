"""Database connection provider for repository-scoped work."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from elbysodic.db.repository import ForumRepository
from elbysodic.db.schema import connect, create_schema


class Database:
    """Open initialized SQLite connections for repository operations."""

    def __init__(self, path: str | Path) -> None:
        self.path = path

    def initialize(self) -> None:
        database_path = self.path
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        connection = connect(database_path, check_same_thread=False)
        try:
            create_schema(connection)
        finally:
            connection.close()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = connect(self.path, check_same_thread=False)
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def repository(self) -> Iterator[ForumRepository]:
        with self.connection() as connection:
            yield ForumRepository(connection)
