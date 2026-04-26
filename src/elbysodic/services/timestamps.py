"""Timestamp presentation helpers for service read models."""

from __future__ import annotations

from datetime import UTC, datetime


def timestamp_key(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min


def timestamp_label(value: str) -> str:
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError:
        return value
    hour = stamp.hour % 12 or 12
    meridiem = "AM" if stamp.hour < 12 else "PM"
    zone = stamp.tzname() or "UTC"
    return f"{stamp:%b} {stamp.day}, {stamp.year} {hour}:{stamp.minute:02d} {meridiem} {zone}"


def relative_timestamp_label(value: str) -> str:
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError:
        return value
    now = datetime.now(stamp.tzinfo or UTC)
    if stamp.tzinfo is None:
        now = now.replace(tzinfo=None)
    days = (now.date() - stamp.date()).days
    if days == 0:
        return f"Today, {_timestamp_time_label(stamp)}"
    if days == 1:
        return f"Yesterday, {_timestamp_time_label(stamp)}"
    if 1 < days <= 6:
        return f"This week, {stamp:%a}"
    if stamp.year == now.year:
        return f"{stamp:%b} {stamp.day}"
    return f"{stamp:%b} {stamp.day}, {stamp.year}"


def _timestamp_time_label(stamp: datetime) -> str:
    hour = stamp.hour % 12 or 12
    meridiem = "AM" if stamp.hour < 12 else "PM"
    return f"{hour}:{stamp.minute:02d} {meridiem}"
