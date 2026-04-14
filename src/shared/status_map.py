"""
shared/status_map.py
====================
Canonical bidirectional mapping between Manifest Manager status vocabulary
and Smart Scheduler status vocabulary.

Both tools import from here so the mapping is a single source of truth.
The mapping is driven by config/integration.yaml — until the user sets
explicit mappings there, conversion returns None (no mapping applied).

See config/integration.yaml for the configurable defaults.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from smart_scheduler.models import TaskStatus


# ---------------------------------------------------------------------------
# Vocabulary reference (informational, not used for conversion logic)
# ---------------------------------------------------------------------------

#: All valid manifest status values.
MANIFEST_STATUSES = frozenset({"active", "done", "pending", "blocked", "cancelled"})

#: All valid scheduler status values.
SCHEDULER_STATUSES = frozenset({"todo", "in_progress", "waiting", "done", "cancelled"})


# ---------------------------------------------------------------------------
# Config-driven conversion
# ---------------------------------------------------------------------------

def _load_mapping(direction: str) -> dict[str, str]:
    """Read the integration.yaml status mapping for a given direction.

    Args:
        direction: ``"to_scheduler"`` or ``"to_manifest"``

    Returns:
        Dict of {source_value: target_value}. Empty dict if config is absent
        or the mapping section has no entries.
    """
    from shared.integration_config import load_integration_config
    cfg = load_integration_config()
    return cfg.get("status_mapping", {}).get(direction, {})


def to_scheduler_status(manifest_status: Optional[str]) -> Optional[str]:
    """Convert a manifest status string to its scheduler equivalent.

    Returns ``None`` if:
    - ``manifest_status`` is None or empty
    - No mapping is configured in ``config/integration.yaml``

    The caller decides what to do with ``None`` (e.g. default to ``"todo"``,
    skip the field, or warn the user).

    Args:
        manifest_status: A manifest status value such as ``"active"``.

    Returns:
        A scheduler status string such as ``"in_progress"``, or ``None``.

    Example::

        status = to_scheduler_status("active")
        task_status = TaskStatus(status) if status else TaskStatus.TODO
    """
    if not manifest_status:
        return None
    mapping = _load_mapping("to_scheduler")
    return mapping.get(manifest_status.lower())


def to_manifest_status(scheduler_status) -> Optional[str]:
    """Convert a scheduler ``TaskStatus`` (or its string value) to a manifest
    status string.

    Returns ``None`` if no mapping is configured.

    Args:
        scheduler_status: A ``TaskStatus`` enum member or its ``.value`` string.

    Returns:
        A manifest status string such as ``"active"``, or ``None``.

    Example::

        manifest_val = to_manifest_status(TaskStatus.IN_PROGRESS)
        node_status = manifest_val or "active"
    """
    if scheduler_status is None:
        return None
    # Accept both enum and plain string
    value = getattr(scheduler_status, "value", str(scheduler_status)).lower()
    mapping = _load_mapping("to_manifest")
    return mapping.get(value)
