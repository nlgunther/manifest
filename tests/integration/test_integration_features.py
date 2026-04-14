"""
tests/integration/test_integration_features.py
================================================
Tests for the six integration features added in Task Manager 2.0:

  1. shared/status_map.py         — bidirectional status conversion
  2. shared/dates.py              — parse_date now in shared
  3. shared/integration_config.py — config loader
  4. calendar_service refactor    — uses shared.ICSWriter
  5. shared/manifest_bridge.py    — node → task conversion + push
  6. import/export commands       — tested via the bridge layer

Tests are deliberately config-independent: they use a temp integration.yaml
so the production config/integration.yaml state does not affect results.
"""

import pytest
import json
import shutil
import tempfile
from pathlib import Path
from datetime import date, timedelta
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def config_with_mappings(temp_dir):
    """Write a temp integration.yaml with status mappings enabled."""
    import yaml
    cfg = {
        "paths": {
            "scheduler_data_dir": str(temp_dir / "scheduler"),
        },
        "status_mapping": {
            "to_scheduler": {
                "active":    "in_progress",
                "pending":   "todo",
                "blocked":   "waiting",
                "done":      "done",
                "cancelled": "cancelled",
            },
            "to_manifest": {
                "in_progress": "active",
                "todo":        "pending",
                "waiting":     "blocked",
                "done":        "done",
                "cancelled":   "cancelled",
            },
        },
        "export_scheduler": {
            "on_missing_due": "skip",
            "store_manifest_id": True,
            "default_xpath": "",
        },
        "import_manifest": {
            "on_missing_due": "skip",
            "store_manifest_id": True,
            "default_xpath": "",
        },
    }
    config_path = temp_dir / "integration.yaml"
    with open(config_path, "w") as f:
        yaml.dump(cfg, f)
    return config_path


@pytest.fixture
def config_no_mappings(temp_dir):
    """Write a temp integration.yaml with NO status mappings (conservative default)."""
    import yaml
    cfg = {
        "paths": {
            "scheduler_data_dir": str(temp_dir / "scheduler"),
        },
        "status_mapping": {
            "to_scheduler": {},
            "to_manifest": {},
        },
        "export_scheduler": {
            "on_missing_due": "skip",
            "store_manifest_id": True,
            "default_xpath": "",
        },
    }
    config_path = temp_dir / "integration_empty.yaml"
    with open(config_path, "w") as f:
        yaml.dump(cfg, f)
    return config_path


# ---------------------------------------------------------------------------
# 1. Status map — with mappings configured
# ---------------------------------------------------------------------------

class TestStatusMapWithConfig:

    def test_active_to_in_progress(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.status_map import to_scheduler_status
            assert to_scheduler_status("active") == "in_progress"

    def test_pending_to_todo(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.status_map import to_scheduler_status
            assert to_scheduler_status("pending") == "todo"

    def test_blocked_to_waiting(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.status_map import to_scheduler_status
            assert to_scheduler_status("blocked") == "waiting"

    def test_done_to_done(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.status_map import to_scheduler_status
            assert to_scheduler_status("done") == "done"

    def test_cancelled_to_cancelled(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.status_map import to_scheduler_status
            assert to_scheduler_status("cancelled") == "cancelled"

    def test_in_progress_to_active(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.status_map import to_manifest_status
            assert to_manifest_status("in_progress") == "active"

    def test_waiting_to_blocked(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.status_map import to_manifest_status
            assert to_manifest_status("waiting") == "blocked"

    def test_enum_accepted(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.status_map import to_manifest_status
            from smart_scheduler.models import TaskStatus
            assert to_manifest_status(TaskStatus.IN_PROGRESS) == "active"

    def test_case_insensitive(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.status_map import to_scheduler_status
            assert to_scheduler_status("ACTIVE") == "in_progress"
            assert to_scheduler_status("Active") == "in_progress"


class TestStatusMapNoConfig:
    """With no mappings configured, everything returns None."""

    def test_no_mapping_returns_none(self, config_no_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_no_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.status_map import to_scheduler_status
            assert to_scheduler_status("active") is None
            assert to_scheduler_status("pending") is None
            assert to_scheduler_status("done") is None

    def test_to_manifest_no_mapping_returns_none(self, config_no_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_no_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.status_map import to_manifest_status
            assert to_manifest_status("in_progress") is None

    def test_none_input_returns_none(self, config_no_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_no_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.status_map import to_scheduler_status, to_manifest_status
            assert to_scheduler_status(None) is None
            assert to_manifest_status(None) is None


# ---------------------------------------------------------------------------
# 2. Shared date parser
# ---------------------------------------------------------------------------

class TestSharedDateParser:

    def test_today(self):
        from shared.dates import parse_date
        assert parse_date("today") == date.today().isoformat()

    def test_tomorrow(self):
        from shared.dates import parse_date
        assert parse_date("tomorrow") == (date.today() + timedelta(days=1)).isoformat()

    def test_yesterday(self):
        from shared.dates import parse_date
        assert parse_date("yesterday") == (date.today() - timedelta(days=1)).isoformat()

    def test_plus_n(self):
        from shared.dates import parse_date
        assert parse_date("+7") == (date.today() + timedelta(days=7)).isoformat()

    def test_iso_passthrough(self):
        from shared.dates import parse_date
        assert parse_date("2026-12-25") == "2026-12-25"

    def test_us_format(self):
        from shared.dates import parse_date
        assert parse_date("12/25/2026") == "2026-12-25"

    def test_weekday_is_future(self):
        from shared.dates import parse_date
        result = parse_date("monday")
        assert result is not None
        d = date.fromisoformat(result)
        assert d.weekday() == 0
        assert d > date.today()

    def test_weekday_never_today(self):
        """Even if today is Monday, result should be next Monday."""
        from shared.dates import parse_date
        from unittest.mock import patch
        import datetime as dt
        # Force today to be a Monday
        a_monday = date(2026, 4, 13)
        with patch("shared.dates.datetime") as mock_dt:
            mock_dt.now.return_value.date.return_value = a_monday
            result = parse_date("monday")
        d = date.fromisoformat(result)
        assert d > a_monday

    def test_invalid_returns_none(self):
        from shared.dates import parse_date
        assert parse_date("not-a-date") is None
        assert parse_date("") is None
        assert parse_date(None) is None

    def test_scheduler_still_uses_shared(self):
        """task_service.parse_date must be the shared version."""
        from smart_scheduler.services import task_service as ts
        from shared.dates import parse_date
        assert ts.parse_date is parse_date


# ---------------------------------------------------------------------------
# 3. Integration config loader
# ---------------------------------------------------------------------------

class TestIntegrationConfig:

    def test_loads_from_env(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            cfg = integration_config.load_integration_config()
            assert "status_mapping" in cfg

    def test_missing_file_returns_empty(self, temp_dir):
        from shared import integration_config
        with patch.object(integration_config, "_find_config_path", return_value=None):
            integration_config._cache = None
            cfg = integration_config.load_integration_config(force_reload=True)
            assert cfg == {}

    def test_get_scheduler_data_dir_from_config(self, config_with_mappings, temp_dir):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            d = integration_config.get_scheduler_data_dir()
            assert d == temp_dir / "scheduler"

    def test_get_scheduler_data_dir_from_env(self, temp_dir):
        target = str(temp_dir / "sched")
        from shared import integration_config
        with patch.object(integration_config, "_find_config_path", return_value=None):
            with patch.dict("os.environ", {"SCHEDULER_DATA_DIR": target}):
                integration_config._cache = None
                result = integration_config.get_scheduler_data_dir()
                assert result == Path(target)

    def test_cache_is_reused(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            cfg1 = integration_config.load_integration_config()
            cfg2 = integration_config.load_integration_config()
            assert cfg1 is cfg2


# ---------------------------------------------------------------------------
# 4. CalendarService uses shared ICSWriter
# ---------------------------------------------------------------------------

class TestCalendarServiceRefactor:

    def test_output_is_valid_ics(self):
        from smart_scheduler.services.calendar_service import CalendarService
        from smart_scheduler.models import Task
        t = Task.create("Dentist", due_date="2026-09-01")
        content = CalendarService().generate_file_content(t)
        assert "BEGIN:VCALENDAR" in content
        assert "END:VCALENDAR" in content
        assert "BEGIN:VEVENT" in content
        assert "END:VEVENT" in content

    def test_uid_contains_task_id(self):
        from smart_scheduler.services.calendar_service import CalendarService
        from smart_scheduler.models import Task
        t = Task.create("T", due_date="2026-09-01")
        content = CalendarService().generate_file_content(t)
        assert t.id in content

    def test_summary_is_task_title(self):
        from smart_scheduler.services.calendar_service import CalendarService
        from smart_scheduler.models import Task
        t = Task.create("Annual review", due_date="2026-09-01")
        content = CalendarService().generate_file_content(t)
        assert "SUMMARY:Annual review" in content

    def test_date_format(self):
        from smart_scheduler.services.calendar_service import CalendarService
        from smart_scheduler.models import Task
        t = Task.create("T", due_date="2026-07-04")
        content = CalendarService().generate_file_content(t)
        assert "DTSTART;VALUE=DATE:20260704" in content

    def test_notes_in_description(self):
        from smart_scheduler.services.calendar_service import CalendarService
        from smart_scheduler.models import Task
        t = Task.create("T", due_date="2026-09-01")
        t.notes = "Bring passport"
        content = CalendarService().generate_file_content(t)
        assert "Bring passport" in content

    def test_no_due_date_raises(self):
        from smart_scheduler.services.calendar_service import CalendarService
        from smart_scheduler.models import Task
        t = Task.create("No due date")
        with pytest.raises(ValueError):
            CalendarService().generate_file_content(t)

    def test_uses_shared_ics_writer(self):
        """Confirm calendar_service imports from shared, not a local implementation."""
        import inspect
        from smart_scheduler.services import calendar_service as cs
        source = inspect.getsource(cs)
        assert "from shared.calendar.ics_writer import" in source
        assert "BEGIN:VCALENDAR" not in source  # no hand-rolled ICS strings


# ---------------------------------------------------------------------------
# 5. Manifest bridge — build_tasks
# ---------------------------------------------------------------------------

class TestManifestBridge:

    def _make_node(self, tag="task", **attrs):
        from lxml import etree
        node = etree.Element(tag)
        for k, v in attrs.items():
            node.set(k, v)
        return node

    def test_basic_conversion(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.manifest_bridge import build_tasks
            node = self._make_node(topic="Deploy website", due="2026-06-01", id="a3f7b2c1")
            tasks, skipped = build_tasks([node])
            assert len(tasks) == 1
            assert tasks[0].title == "Deploy website"
            assert tasks[0].due_date == "2026-06-01"

    def test_status_mapped(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.manifest_bridge import build_tasks
            from smart_scheduler.models import TaskStatus
            node = self._make_node(topic="T", due="2026-06-01", status="active")
            tasks, _ = build_tasks([node])
            assert tasks[0].status == TaskStatus.IN_PROGRESS

    def test_status_not_mapped_defaults_to_todo(self, config_no_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_no_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.manifest_bridge import build_tasks
            from smart_scheduler.models import TaskStatus
            node = self._make_node(topic="T", due="2026-06-01", status="active")
            tasks, _ = build_tasks([node])
            assert tasks[0].status == TaskStatus.TODO

    def test_manifest_id_stored_in_notes(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.manifest_bridge import build_tasks
            node = self._make_node(topic="T", due="2026-06-01", id="a3f7b2c1")
            tasks, _ = build_tasks([node])
            assert tasks[0].notes == "manifest:a3f7b2c1"

    def test_node_without_due_is_skipped(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.manifest_bridge import build_tasks
            node = self._make_node(topic="No due date")
            tasks, skipped = build_tasks([node])
            assert len(tasks) == 0
            assert len(skipped) == 1

    def test_node_without_topic_is_skipped(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.manifest_bridge import build_tasks
            node = self._make_node(due="2026-06-01")  # no topic
            tasks, skipped = build_tasks([node])
            assert len(tasks) == 0
            assert len(skipped) == 1

    def test_multiple_nodes_mixed(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.manifest_bridge import build_tasks
            nodes = [
                self._make_node(topic="A", due="2026-06-01"),
                self._make_node(topic="B"),              # no due — skipped
                self._make_node(topic="C", due="2026-07-01"),
            ]
            tasks, skipped = build_tasks(nodes)
            assert len(tasks) == 2
            assert len(skipped) == 1

    def test_resp_becomes_assignee(self, config_with_mappings):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.manifest_bridge import build_tasks
            node = self._make_node(topic="T", due="2026-06-01", resp="alice")
            tasks, _ = build_tasks([node])
            assert tasks[0].assignee == "alice"


# ---------------------------------------------------------------------------
# 6. Bridge push_tasks_to_scheduler
# ---------------------------------------------------------------------------

class TestBridgePush:

    def test_creates_project_if_missing(self, config_with_mappings, temp_dir):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.manifest_bridge import push_tasks_to_scheduler
            from smart_scheduler.models import Task
            data_dir = temp_dir / "sched"
            t = Task.create("T", due_date="2026-06-01")
            result = push_tasks_to_scheduler([t], "newproj", "New Project", data_dir)
            assert result.created == 1
            from smart_scheduler.storage.factory import get_storage_engine
            p = get_storage_engine(data_dir, "json").load_project("newproj")
            assert p is not None
            assert len(p.tasks) == 1

    def test_appends_to_existing_project(self, config_with_mappings, temp_dir):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.manifest_bridge import push_tasks_to_scheduler
            from smart_scheduler.models import Task, Project
            from smart_scheduler.storage.factory import get_storage_engine
            data_dir = temp_dir / "sched2"
            storage = get_storage_engine(data_dir, "json")
            storage.save_project(Project(slug="existing", name="Existing"))
            t = Task.create("New task", due_date="2026-06-01")
            push_tasks_to_scheduler([t], "existing", "Existing", data_dir)
            p = storage.load_project("existing")
            assert len(p.tasks) == 1

    def test_empty_task_list_is_noop(self, config_with_mappings, temp_dir):
        with patch.dict("os.environ", {"TASK_MANAGER_CONFIG": str(config_with_mappings)}):
            from shared import integration_config
            integration_config._cache = None
            from shared.manifest_bridge import push_tasks_to_scheduler
            data_dir = temp_dir / "sched3"
            result = push_tasks_to_scheduler([], "proj", "Proj", data_dir)
            assert result.created == 0
