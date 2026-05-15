"""Tenant-aware SQLite repository for forum-domain operations."""

from __future__ import annotations

from elbysodic.db.repositories.discovery import DiscoveryRepositoryMixin


class ForumRepository(
    DiscoveryRepositoryMixin,
):
    """Small repository layer that keeps community scope explicit."""
