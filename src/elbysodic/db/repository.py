"""Tenant-aware SQLite repository for forum-domain operations."""

from __future__ import annotations

from elbysodic.db.repositories.audit import AuditRepositoryMixin


class ForumRepository(
    AuditRepositoryMixin,
):
    """Small repository layer that keeps community scope explicit."""
