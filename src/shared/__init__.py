"""
Shared Infrastructure Library
==============================

Common utilities for Smart Scheduler and Manifest Manager.
"""

from .calendar.ics_writer import CalendarEvent, ICSWriter
from .id_generator import generate_id, validate_id
from .locking import file_lock, LockTimeout
from .dates import parse_date
from .status_map import to_scheduler_status, to_manifest_status
from .integration_config import load_integration_config, get_scheduler_data_dir, get_manifest_default_dir

__version__ = "2.0.0"

__all__ = [
    "CalendarEvent",
    "ICSWriter",
    "generate_id",
    "validate_id",
    "file_lock",
    "LockTimeout",
    "parse_date",
    "to_scheduler_status",
    "to_manifest_status",
    "load_integration_config",
    "get_scheduler_data_dir",
    "get_manifest_default_dir",
]
