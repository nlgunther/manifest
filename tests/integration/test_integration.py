"""
tests/integration/test_integration.py
=======================================
Cross-package integration tests verifying that smart_scheduler and
manifest_manager coexist correctly under the task-manager monorepo,
and that shared infrastructure is used consistently by both.
"""
import pytest
import json
import shutil
import tempfile
from pathlib import Path

from shared import generate_id, validate_id, file_lock, LockTimeout
from smart_scheduler.models import Task, Contact


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# 1. Shared library is importable from both packages in the same process
# ---------------------------------------------------------------------------

class TestSharedImports:

    def test_shared_importable(self):
        from shared import generate_id, validate_id, file_lock, LockTimeout
        assert callable(generate_id)
        assert callable(validate_id)

    def test_shared_calendar_importable(self):
        from shared.calendar.ics_writer import CalendarEvent, ICSWriter
        assert CalendarEvent is not None
        assert ICSWriter is not None

    def test_scheduler_importable(self):
        from smart_scheduler.models import Task, Project, TaskStatus
        assert Task is not None

    def test_manifest_importable(self):
        from manifest_manager.manifest_core import ManifestRepository
        assert ManifestRepository is not None

    def test_both_packages_import_in_same_process(self):
        """Neither package must pollute the other's namespace."""
        from smart_scheduler.models import Task
        from manifest_manager.manifest_core import ManifestRepository
        # Instantiate both to confirm no import-time side effects collide
        t = Task.create("Test task")
        assert t.id.startswith("t")

    def test_shared_not_shadowed_by_scheduler(self):
        """smart_scheduler.models must use shared.generate_id, not uuid4."""
        import smart_scheduler.models as sm
        import inspect
        source = inspect.getsource(sm)
        assert "uuid4" not in source
        assert "generate_id" in source

    def test_shared_not_shadowed_by_stdlib(self):
        """
        Python stdlib has a 'calendar' module; our shared.calendar must
        not be masked by it.
        """
        from shared.calendar.ics_writer import ICSWriter
        assert ICSWriter is not None


# ---------------------------------------------------------------------------
# 2. ID consistency — scheduler IDs pass shared validation
# ---------------------------------------------------------------------------

class TestIDConsistency:

    def test_task_id_passes_validate_id(self):
        t = Task.create("T")
        assert validate_id(t.id, prefix="t")

    def test_contact_id_passes_validate_id(self):
        c = Contact.create("Alice")
        assert validate_id(c.id, prefix="c")

    def test_task_id_hex_payload(self):
        t = Task.create("T")
        hex_part = t.id[1:]  # strip 't' prefix
        assert len(hex_part) == 5
        int(hex_part, 16)   # raises ValueError if not valid hex

    def test_contact_id_hex_payload(self):
        c = Contact.create("Alice")
        hex_part = c.id[1:]
        assert len(hex_part) == 5
        int(hex_part, 16)

    def test_bulk_task_ids_all_valid(self):
        ids = [Task.create("T").id for _ in range(100)]
        assert all(validate_id(i, prefix="t") for i in ids)
        assert len(set(ids)) == 100  # all unique

    def test_generate_id_prefix_t(self):
        """generate_id with prefix='t' produces IDs that match Task.create format."""
        generated = generate_id(prefix="t", length=5)
        assert validate_id(generated, prefix="t")

    def test_generate_id_prefix_c(self):
        generated = generate_id(prefix="c", length=5)
        assert validate_id(generated, prefix="c")


# ---------------------------------------------------------------------------
# 3. Shared file locking works for scheduler JSON files
# ---------------------------------------------------------------------------

class TestFileLockingIntegration:

    def test_lock_acquired_and_released(self, temp_dir):
        target = temp_dir / "data.json"
        target.write_text("{}")
        with file_lock(target):
            lock_file = target.with_suffix(".json.lock")
            assert lock_file.exists()
        assert not lock_file.exists()

    def test_lock_prevents_concurrent_access(self, temp_dir):
        target = temp_dir / "data.json"
        target.write_text("{}")
        with file_lock(target, timeout=1):
            with pytest.raises(LockTimeout):
                with file_lock(target, timeout=0.1):
                    pass

    def test_lock_cleanup_on_exception(self, temp_dir):
        target = temp_dir / "data.json"
        target.write_text("{}")
        lock_file = target.with_suffix(".json.lock")
        try:
            with file_lock(target):
                raise RuntimeError("simulated error")
        except RuntimeError:
            pass
        assert not lock_file.exists()


# ---------------------------------------------------------------------------
# 4. Shared ICS writer produces output consistent with scheduler service
# ---------------------------------------------------------------------------

class TestICSConsistency:

    def test_shared_ics_writer_and_calendar_service_same_uid_format(self):
        """
        The scheduler's CalendarService uses task.id as the UID.
        The shared ICSWriter also accepts a uid directly.
        Both must produce parseable VEVENT blocks.
        """
        from shared.calendar.ics_writer import CalendarEvent, ICSWriter
        from smart_scheduler.services.calendar_service import CalendarService
        from datetime import date

        t = Task.create("Annual review", due_date="2026-09-01")

        # Via scheduler service
        svc_content = CalendarService().generate_file_content(t)
        assert "BEGIN:VEVENT" in svc_content
        assert t.id in svc_content  # UID contains task ID

        # Via shared ICSWriter
        event = CalendarEvent(
            uid=t.id,
            title=t.title,
            start_date=date(2026, 9, 1),
            all_day=True,
        )
        writer = ICSWriter("Test")
        writer.add_event(event)
        writer_content = writer.to_string()
        assert f"UID:{t.id}" in writer_content
        assert "SUMMARY:Annual review" in writer_content
