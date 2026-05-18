"""Tenant-aware SQLite repository for forum-domain operations."""

from __future__ import annotations

from elbysodic.db.repositories.gateway import GatewayRepositoryMixin


class ForumRepository(
    GatewayRepositoryMixin,
):
    """Small repository layer that keeps community scope explicit."""
