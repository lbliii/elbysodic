from __future__ import annotations

import re
import sqlite3
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager

_LITERAL_RE = re.compile(r"'[^']*'|\b\d+\b")
_WRITE_PREFIXES = ("INSERT", "UPDATE", "DELETE", "REPLACE", "BEGIN", "COMMIT", "ROLLBACK")


def normalize_sql(sql: str) -> str:
    compact = " ".join(sql.strip().split())
    return _LITERAL_RE.sub("?", compact)


def sql_kind(sql: str) -> str:
    compact = " ".join(sql.strip().split())
    if not compact:
        return ""
    return compact.split(" ", 1)[0].upper()


def is_write_sql(sql: str) -> bool:
    return sql_kind(sql) in _WRITE_PREFIXES


class SqlTrace:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def __call__(self, statement: str) -> None:
        self.statements.append(statement)

    @property
    def count(self) -> int:
        return len(self.statements)

    @property
    def writes(self) -> list[str]:
        return [statement for statement in self.statements if is_write_sql(statement)]

    def normalized_counts(self) -> Counter[str]:
        return Counter(normalize_sql(statement) for statement in self.statements)


@contextmanager
def trace_sql(connection: sqlite3.Connection) -> Iterator[SqlTrace]:
    trace = SqlTrace()
    connection.set_trace_callback(trace)
    try:
        yield trace
    finally:
        connection.set_trace_callback(None)
