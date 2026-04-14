"""
shared/integration_config.py
=============================
Loader for config/integration.yaml.

Both tools and the shared library use this to read cross-tool settings
(status mappings, data paths, export defaults) without hardcoding them.

Config file resolution order
-----------------------------
1. ``TASK_MANAGER_CONFIG`` environment variable (full path to yaml file)
2. ``config/integration.yaml`` relative to the installed package root
   (i.e. the ``manifest/`` repo directory)
3. Falls back to an empty dict — all features that depend on config
   behave conservatively (no mappings applied, no paths assumed).
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Any

_cache: dict[str, Any] | None = None


def _find_config_path() -> Path | None:
    """Locate integration.yaml using the resolution order above."""
    # 1. Explicit environment override
    env = os.environ.get("TASK_MANAGER_CONFIG")
    if env:
        p = Path(env)
        if p.exists():
            return p

    # 2. Relative to this file: src/shared/ → ../../config/integration.yaml
    candidate = Path(__file__).parent.parent.parent / "config" / "integration.yaml"
    if candidate.exists():
        return candidate

    return None


def load_integration_config(force_reload: bool = False) -> dict[str, Any]:
    """Load and cache integration.yaml.

    Args:
        force_reload: Bypass the cache and re-read from disk.

    Returns:
        Parsed config dict, or empty dict if the file is absent or unreadable.
    """
    global _cache
    if _cache is not None and not force_reload:
        return _cache

    path = _find_config_path()
    if path is None:
        _cache = {}
        return _cache

    try:
        import yaml
        with open(path, encoding="utf-8") as f:
            _cache = yaml.safe_load(f) or {}
    except Exception:
        _cache = {}

    return _cache


def get_scheduler_data_dir() -> Path | None:
    """Return the configured scheduler data directory, or None if not set."""
    cfg = load_integration_config()
    raw = cfg.get("paths", {}).get("scheduler_data_dir")
    if raw:
        return Path(raw).expanduser()
    env = os.environ.get("SCHEDULER_DATA_DIR")
    if env:
        return Path(env)
    return None


def get_manifest_default_dir() -> Path | None:
    """Return the configured default manifest directory, or None if not set."""
    cfg = load_integration_config()
    raw = cfg.get("paths", {}).get("manifest_default_dir")
    if raw:
        return Path(raw).expanduser()
    env = os.environ.get("MANIFEST_DIR")
    if env:
        return Path(env)
    return None
