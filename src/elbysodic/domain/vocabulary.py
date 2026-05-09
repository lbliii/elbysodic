"""Shared PBP vocabulary for typed story and director materials."""

from __future__ import annotations

MATERIAL_TYPE_LABELS: dict[str, str] = {
    "premise": "Premise",
    "guide": "Guide",
    "factions": "Factions",
    "application": "Application",
    "event": "Event",
}
MATERIAL_TYPES: frozenset[str] = frozenset(MATERIAL_TYPE_LABELS)

WANTED_TYPE_LABELS: dict[str, str] = {
    "canon": "Canon",
    "connection": "Connection",
    "event_role": "Event Role",
    "faction_need": "Faction Need",
    "plot_role": "Plot Role",
    "relationship": "Relationship",
    "rival": "Rival",
}
WANTED_TYPES: frozenset[str] = frozenset(WANTED_TYPE_LABELS)

PLOT_HOOK_TYPE_LABELS: dict[str, str] = {
    "scene": "Scene",
    "relationship": "Relationship",
    "connection": "Connection",
    "event": "Event",
    "other": "Other",
}
PLOT_HOOK_TYPES: frozenset[str] = frozenset(PLOT_HOOK_TYPE_LABELS)


def vocabulary_label(value: str, labels: dict[str, str]) -> str:
    return labels.get(value, value.replace("_", " ").title())


def material_type_label(material_type: str) -> str:
    return vocabulary_label(material_type, MATERIAL_TYPE_LABELS)


def wanted_type_label(wanted_type: str) -> str:
    return vocabulary_label(wanted_type, WANTED_TYPE_LABELS)


def plot_hook_type_label(hook_type: str) -> str:
    return vocabulary_label(hook_type, PLOT_HOOK_TYPE_LABELS)
