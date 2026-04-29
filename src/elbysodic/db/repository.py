"""Tenant-aware SQLite repository for forum-domain operations."""

from __future__ import annotations

from elbysodic.db.repositories.posts import PostRepositoryMixin


class ForumRepository(
    PostRepositoryMixin,
):
    """Small repository layer that keeps community scope explicit."""
