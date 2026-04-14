"""
shared/manifest_bridge.py
==========================
Core logic for converting manifest XML nodes into scheduler Task objects
and writing them into the scheduler's storage.

Used by:
  - manifest_manager/manifest.py  → do_export_scheduler()
  - smart_scheduler/cli.py        → cmd_import_manifest()

Neither command contains conversion logic — they both call build_tasks()
and push_tasks_to_scheduler() from here so the behaviour is identical
regardless of which shell the user is in.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from lxml.etree import _Element
    from smart_scheduler.models import Task


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class BridgeResult:
    """Summary returned after a bridge operation."""
    created: int = 0
    skipped: int = 0
    skipped_reasons: List[str] = None

    def __post_init__(self):
        if self.skipped_reasons is None:
            self.skipped_reasons = []

    def __str__(self) -> str:
        lines = [f"✓ Created {self.created} task(s)."]
        if self.skipped:
            lines.append(f"  Skipped {self.skipped} node(s):")
            for r in self.skipped_reasons[:10]:
                lines.append(f"    • {r}")
            if len(self.skipped_reasons) > 10:
                lines.append(f"    … and {len(self.skipped_reasons) - 10} more")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Node → Task conversion
# ---------------------------------------------------------------------------

def _node_to_task(node: "_Element", store_manifest_id: bool) -> Optional["Task"]:
    """Convert a single lxml element to a scheduler Task.

    Returns None and a reason string if conversion cannot proceed.
    """
    from smart_scheduler.models import Task, TaskStatus
    from shared.status_map import to_scheduler_status
    from shared.integration_config import load_integration_config

    cfg = load_integration_config()
    export_cfg = cfg.get("export_scheduler", {})
    on_missing_due = export_cfg.get("on_missing_due", "skip")

    topic = node.get("topic") or node.get("title") or node.text or ""
    topic = topic.strip()
    if not topic:
        return None, f"node <{node.tag}> id={node.get('id','?')} has no topic/title/text"

    due_date = node.get("due")
    if not due_date:
        if on_missing_due == "skip":
            return None, f"{topic!r}: no due date (skipped)"
        elif on_missing_due == "warn":
            print(f"  ⚠ {topic!r}: no due date")

    # Status conversion — None means no mapping configured; caller defaults to TODO
    raw_status = node.get("status")
    scheduler_status_str = to_scheduler_status(raw_status) if raw_status else None

    task = Task.create(
        title=topic,
        assignee=node.get("resp"),
        due_date=due_date,
    )

    if scheduler_status_str:
        try:
            task.status = TaskStatus(scheduler_status_str)
        except ValueError:
            pass  # Bad mapping value — leave as TODO

    # Back-reference
    manifest_id = node.get("id")
    if store_manifest_id and manifest_id:
        task.notes = f"manifest:{manifest_id}"

    return task, None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_tasks(
    nodes: List["_Element"],
) -> tuple[List["Task"], List[str]]:
    """Convert a list of manifest nodes to scheduler Tasks.

    Args:
        nodes: lxml elements selected from the manifest.

    Returns:
        Tuple of (tasks, skip_reasons).
    """
    from shared.integration_config import load_integration_config
    cfg = load_integration_config()
    store_id = cfg.get("export_scheduler", {}).get("store_manifest_id", True)

    tasks, reasons = [], []
    for node in nodes:
        result = _node_to_task(node, store_id)
        task, reason = result
        if task is not None:
            tasks.append(task)
        else:
            reasons.append(reason)

    return tasks, reasons


def push_tasks_to_scheduler(
    tasks: List["Task"],
    project_slug: str,
    project_name: str,
    data_dir: Path,
    storage_engine: str = "json",
) -> BridgeResult:
    """Write tasks into the scheduler's storage under the given project.

    Creates the project if it does not exist.  Uses file_lock on the
    project JSON file to avoid corruption on Google Drive.

    Args:
        tasks:          Tasks produced by build_tasks().
        project_slug:   Slug for the target scheduler project.
        project_name:   Display name (used only when creating a new project).
        data_dir:       Scheduler data directory.
        storage_engine: ``"json"`` (default) or ``"sqlite"``.

    Returns:
        BridgeResult summarising what was created.
    """
    from smart_scheduler.storage.factory import get_storage_engine
    from smart_scheduler.models import Project
    from shared.locking import file_lock

    storage = get_storage_engine(data_dir, storage_engine)

    # Create project if missing
    project = storage.load_project(project_slug)
    if project is None:
        project = Project(slug=project_slug, name=project_name)

    # Lock the project file during write (JSON only; SQLite has its own locking)
    project_file = data_dir / "projects" / f"{project_slug}.json"
    project_file.parent.mkdir(parents=True, exist_ok=True)

    result = BridgeResult()
    with file_lock(project_file, timeout=10):
        # Re-load inside the lock to get latest state
        latest = storage.load_project(project_slug)
        if latest is not None:
            project = latest
        for task in tasks:
            project.tasks.append(task)
            result.created += 1
        storage.save_project(project)

    return result
