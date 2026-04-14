"""
tests/smart_scheduler/test_scheduler.py
========================================
Comprehensive tests for Smart Scheduler — models, storage, services, CLI.
Mirrors the style of tests/test_suite.py with updated package imports.
"""
import pytest
import json
import shutil
import tempfile
from pathlib import Path
from datetime import date, timedelta

from smart_scheduler.models import (
    Task, Project, Contact, TaskStatus,
    ModelEncoder, task_from_dict, contact_from_dict, project_from_dict,
)
from smart_scheduler.storage.factory import get_storage_engine
from smart_scheduler.services.task_service import TaskService, parse_date
from smart_scheduler.services.maintenance_service import MaintenanceService
from smart_scheduler.services.calendar_service import CalendarService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(params=["json", "sqlite"])
def storage(request, temp_dir):
    """Runs every storage test against both engines."""
    return get_storage_engine(temp_dir, request.param)


@pytest.fixture
def task_service(storage):
    return TaskService(storage)


@pytest.fixture
def maint_service(storage):
    return MaintenanceService(storage)


@pytest.fixture
def cal_service():
    return CalendarService()


# ---------------------------------------------------------------------------
# 1. Models
# ---------------------------------------------------------------------------

class TestModels:

    def test_task_create_prefix(self):
        """Task IDs must start with 't'."""
        t = Task.create("Do something")
        assert t.id.startswith("t")

    def test_task_create_id_length(self):
        """Task IDs must be prefix + 5 hex chars."""
        t = Task.create("Do something")
        assert len(t.id) == 6  # 't' + 5

    def test_contact_create_prefix(self):
        """Contact IDs must start with 'c'."""
        c = Contact.create("Alice")
        assert c.id.startswith("c")

    def test_contact_create_id_length(self):
        c = Contact.create("Alice")
        assert len(c.id) == 6  # 'c' + 5

    def test_ids_are_unique(self):
        ids = {Task.create("T").id for _ in range(50)}
        assert len(ids) == 50

    def test_task_status_enum_values(self):
        assert TaskStatus.TODO.value == "todo"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.DONE.value == "done"

    def test_task_status_icons(self):
        assert TaskStatus.TODO.icon == "○"
        assert TaskStatus.DONE.icon == "✓"
        assert TaskStatus.CANCELLED.icon == "✗"

    def test_task_is_active(self):
        t = Task.create("T")
        assert t.is_active is True
        t.status = TaskStatus.DONE
        assert t.is_active is False
        t.status = TaskStatus.CANCELLED
        assert t.is_active is False

    def test_task_is_active_waiting(self):
        t = Task.create("T")
        t.status = TaskStatus.WAITING
        assert t.is_active is True

    def test_model_encoder_status(self):
        t = Task.create("T")
        encoded = json.dumps(t, cls=ModelEncoder)
        data = json.loads(encoded)
        assert data["status"] == "todo"

    def test_model_encoder_set(self):
        encoded = json.dumps({"tags": {"a", "b"}}, cls=ModelEncoder)
        data = json.loads(encoded)
        assert sorted(data["tags"]) == ["a", "b"]

    def test_task_from_dict_status_coercion(self):
        t = task_from_dict({"id": "t1", "title": "T", "status": "in_progress"})
        assert t.status == TaskStatus.IN_PROGRESS

    def test_task_from_dict_bad_status_fallback(self):
        t = task_from_dict({"id": "t1", "title": "T", "status": "nonsense"})
        assert t.status == TaskStatus.TODO

    def test_task_from_dict_extra_keys_ignored(self):
        """Extra keys must not raise."""
        t = task_from_dict({"id": "t1", "title": "T", "status": "todo", "unknown_field": "x"})
        assert t.title == "T"

    def test_project_from_dict_round_trip(self):
        p = Project(slug="test", name="Test")
        p.tasks.append(Task.create("T1"))
        p.contacts.append(Contact.create("Alice"))
        data = json.loads(json.dumps(p, cls=ModelEncoder))
        restored = project_from_dict(data)
        assert restored.slug == "test"
        assert len(restored.tasks) == 1
        assert len(restored.contacts) == 1

    def test_project_active_tasks(self):
        p = Project(slug="p", name="P")
        p.tasks.append(Task.create("Active"))
        done = Task.create("Done")
        done.status = TaskStatus.DONE
        p.tasks.append(done)
        assert len(p.active_tasks) == 1


# ---------------------------------------------------------------------------
# 2. Date Parsing
# ---------------------------------------------------------------------------

class TestDateParsing:

    def test_today(self):
        assert parse_date("today") == date.today().isoformat()

    def test_tomorrow(self):
        assert parse_date("tomorrow") == (date.today() + timedelta(days=1)).isoformat()

    def test_yesterday(self):
        assert parse_date("yesterday") == (date.today() - timedelta(days=1)).isoformat()

    def test_plus_n_days(self):
        assert parse_date("+5") == (date.today() + timedelta(days=5)).isoformat()

    def test_iso_format(self):
        assert parse_date("2026-06-15") == "2026-06-15"

    def test_us_format(self):
        assert parse_date("06/15/2026") == "2026-06-15"

    def test_weekday(self):
        result = parse_date("monday")
        # Result must be a Monday in the future
        assert result is not None
        from datetime import datetime
        d = datetime.strptime(result, "%Y-%m-%d").date()
        assert d.weekday() == 0  # Monday
        assert d > date.today()

    def test_invalid_returns_none(self):
        assert parse_date("not-a-date") is None

    def test_none_input(self):
        assert parse_date(None) is None

    def test_empty_string(self):
        assert parse_date("") is None


# ---------------------------------------------------------------------------
# 3. Storage
# ---------------------------------------------------------------------------

class TestStorage:

    def test_save_and_load_project(self, storage):
        p = Project(slug="work", name="Work")
        t = Task.create("Task A")
        t.notes = "Some notes"
        p.tasks.append(t)
        storage.save_project(p)

        loaded = storage.load_project("work")
        assert loaded is not None
        assert loaded.name == "Work"
        assert loaded.tasks[0].title == "Task A"
        assert loaded.tasks[0].notes == "Some notes"

    def test_load_missing_project_returns_none(self, storage):
        assert storage.load_project("does-not-exist") is None

    def test_list_projects(self, storage):
        storage.save_project(Project(slug="a", name="A"))
        storage.save_project(Project(slug="b", name="B"))
        slugs = storage.list_projects()
        assert "a" in slugs
        assert "b" in slugs

    def test_delete_project(self, storage):
        storage.save_project(Project(slug="tmp", name="Tmp"))
        assert storage.load_project("tmp") is not None
        storage.delete_project("tmp")
        assert storage.load_project("tmp") is None

    def test_rename_project(self, storage):
        p = Project(slug="old", name="Old")
        p.tasks.append(Task.create("T"))
        storage.save_project(p)

        storage.rename_project("old", "new")

        assert storage.load_project("old") is None
        loaded = storage.load_project("new")
        assert loaded is not None
        assert len(loaded.tasks) == 1

    def test_load_all_projects(self, storage):
        storage.save_project(Project(slug="x", name="X"))
        storage.save_project(Project(slug="y", name="Y"))
        all_p = storage.load_all_projects()
        assert len(all_p) == 2

    def test_task_tags_persist(self, storage):
        p = Project(slug="p", name="P")
        t = Task.create("T", tags=["urgent", "bug"])
        p.tasks.append(t)
        storage.save_project(p)

        loaded = storage.load_project("p")
        assert set(loaded.tasks[0].tags) == {"urgent", "bug"}

    def test_contact_persists(self, storage):
        p = Project(slug="crm", name="CRM")
        p.contacts.append(Contact.create("Bob", role="Client"))
        storage.save_project(p)

        loaded = storage.load_project("crm")
        assert loaded.contacts[0].name == "Bob"
        assert loaded.contacts[0].role == "Client"

    def test_overwrite_project(self, storage):
        """Saving a project twice keeps only the latest state."""
        p = Project(slug="p", name="Original")
        storage.save_project(p)
        p.name = "Updated"
        storage.save_project(p)

        assert storage.load_project("p").name == "Updated"


# ---------------------------------------------------------------------------
# 4. Task Service
# ---------------------------------------------------------------------------

class TestTaskService:

    def test_create_project(self, task_service):
        p = task_service.create_project("dev", "Dev")
        assert p.slug == "dev"
        assert task_service.storage.load_project("dev") is not None

    def test_create_duplicate_slug_raises(self, task_service):
        task_service.create_project("dev", "Dev")
        with pytest.raises(ValueError):
            task_service.create_project("dev", "Dev 2")

    def test_add_task(self, task_service):
        task_service.create_project("dev", "Dev")
        t = task_service.add_task("dev", "Fix bug")
        assert t.title == "Fix bug"
        assert t.id.startswith("t")

    def test_add_task_with_due_date(self, task_service):
        task_service.create_project("dev", "Dev")
        t = task_service.add_task("dev", "Release", due="tomorrow")
        expected = (date.today() + timedelta(days=1)).isoformat()
        assert t.due_date == expected

    def test_add_task_to_missing_project_raises(self, task_service):
        with pytest.raises(ValueError):
            task_service.add_task("ghost", "Task")

    def test_update_task_status(self, task_service):
        task_service.create_project("dev", "Dev")
        t = task_service.add_task("dev", "T")
        updated = task_service.update_task("dev", t.id, status="in_progress")
        assert updated.status == TaskStatus.IN_PROGRESS

    def test_update_task_notes_and_tags(self, task_service):
        task_service.create_project("dev", "Dev")
        t = task_service.add_task("dev", "T")
        updated = task_service.update_task("dev", t.id, notes="Note", tags=["v1"])
        assert updated.notes == "Note"
        assert "v1" in updated.tags

    def test_update_task_due_date_parsing(self, task_service):
        task_service.create_project("dev", "Dev")
        t = task_service.add_task("dev", "T")
        updated = task_service.update_task("dev", t.id, due_date="+3")
        expected = (date.today() + timedelta(days=3)).isoformat()
        assert updated.due_date == expected

    def test_add_contact(self, task_service):
        task_service.create_project("crm", "CRM")
        c = task_service.add_contact("crm", "Alice", role="PM", note="Key contact")
        assert c.name == "Alice"
        assert c.id.startswith("c")
        loaded = task_service.storage.load_project("crm")
        assert loaded.contacts[0].notes == "Key contact"

    def test_find_task_by_id_across_projects(self, task_service):
        task_service.create_project("a", "A")
        task_service.create_project("b", "B")
        task_service.add_task("a", "Task in A")
        t = task_service.add_task("b", "Task in B")

        result = task_service.find_task_by_id(t.id)
        assert result is not None
        project, task = result
        assert project.slug == "b"
        assert task.title == "Task in B"

    def test_find_task_by_id_prefix(self, task_service):
        task_service.create_project("p", "P")
        t = task_service.add_task("p", "T")

        result = task_service.find_task_by_id(t.id[:3])
        assert result is not None

    def test_find_task_by_id_not_found(self, task_service):
        assert task_service.find_task_by_id("tfffff") is None

    def test_delete_task_by_id(self, task_service):
        task_service.create_project("p", "P")
        t = task_service.add_task("p", "To delete")

        deleted = task_service.delete_task_by_id(t.id)
        assert deleted is True

        p = task_service.storage.load_project("p")
        assert all(x.id != t.id for x in p.tasks)

    def test_delete_task_by_id_not_found(self, task_service):
        assert task_service.delete_task_by_id("tfffff") is False

    def test_find_contact_by_id(self, task_service):
        task_service.create_project("crm", "CRM")
        c = task_service.add_contact("crm", "Bob")

        result = task_service.find_contact_by_id(c.id)
        assert result is not None
        _, contact = result
        assert contact.name == "Bob"

    def test_delete_contact_by_id(self, task_service):
        task_service.create_project("crm", "CRM")
        c = task_service.add_contact("crm", "Bob")

        assert task_service.delete_contact_by_id(c.id) is True
        p = task_service.storage.load_project("crm")
        assert len(p.contacts) == 0

    def test_update_project_name_and_desc(self, task_service):
        task_service.create_project("p", "Original")
        updated = task_service.update_project("p", name="Renamed", desc="New desc")
        assert updated.name == "Renamed"
        assert updated.description == "New desc"

    def test_delete_project(self, task_service):
        task_service.create_project("p", "P")
        assert task_service.delete_project("p") is True
        assert task_service.storage.load_project("p") is None

    def test_get_summary(self, task_service):
        task_service.create_project("a", "A")
        task_service.add_task("a", "T1")
        task_service.add_task("a", "T2")
        done = task_service.add_task("a", "T3")
        task_service.update_task("a", done.id, status="done")

        summary = task_service.get_summary()
        assert summary["total_projects"] == 1
        assert summary["total_active"] == 2


# ---------------------------------------------------------------------------
# 5. Calendar Service
# ---------------------------------------------------------------------------

class TestCalendarService:

    def test_ics_output_structure(self, cal_service):
        t = Task.create("Dentist", due_date="2026-07-10")
        t.id = "t00001"
        content = cal_service.generate_file_content(t)
        assert "BEGIN:VCALENDAR" in content
        assert "END:VCALENDAR" in content
        assert "BEGIN:VEVENT" in content
        assert "SUMMARY:Dentist" in content

    def test_ics_date_format(self, cal_service):
        t = Task.create("T", due_date="2026-07-10")
        content = cal_service.generate_file_content(t)
        assert "DTSTART;VALUE=DATE:20260710" in content

    def test_ics_includes_notes(self, cal_service):
        t = Task.create("T", due_date="2026-07-10")
        t.notes = "Bring documents"
        content = cal_service.generate_file_content(t)
        assert "DESCRIPTION:Bring documents" in content

    def test_ics_includes_outcome(self, cal_service):
        t = Task.create("T", due_date="2026-07-10")
        t.outcome = "Rescheduled"
        content = cal_service.generate_file_content(t)
        assert "Outcome: Rescheduled" in content

    def test_ics_no_due_date_raises(self, cal_service):
        t = Task.create("No due date")
        with pytest.raises(ValueError):
            cal_service.generate_file_content(t)

    def test_ics_special_chars_escaped(self, cal_service):
        t = Task.create("T", due_date="2026-07-10")
        t.notes = "Call client; confirm slot, then proceed"
        content = cal_service.generate_file_content(t)
        assert "\\;" in content
        assert "\\," in content


# ---------------------------------------------------------------------------
# 6. Maintenance Service
# ---------------------------------------------------------------------------

class TestMaintenanceService:

    def test_backup_creates_directory(self, maint_service, task_service, temp_dir):
        task_service.create_project("main", "Main")
        task_service.add_task("main", "Critical task")

        backup_path = maint_service.backup(str(temp_dir / "snap"))
        assert backup_path.exists()

    def test_backup_compressed_creates_zip(self, maint_service, task_service, temp_dir):
        task_service.create_project("main", "Main")
        backup_path = maint_service.backup(str(temp_dir / "snap"), compress=True)
        assert backup_path.suffix == ".zip"
        assert backup_path.exists()

    def test_restore_from_zip(self, maint_service, task_service):
        task_service.create_project("main", "Main")
        task_service.add_task("main", "Critical task")

        # Backup must live outside data_dir — use a dedicated sibling temp dir
        # so restore's rename of data_dir doesn't take the zip with it.
        backup_dir = Path(tempfile.mkdtemp())
        try:
            backup_path = maint_service.backup(str(backup_dir / "snap"), compress=True)

            task_service.storage.delete_project("main")
            assert task_service.storage.load_project("main") is None

            maint_service.restore(str(backup_path))

            restored = task_service.storage.load_project("main")
            assert restored is not None
            assert restored.tasks[0].title == "Critical task"
        finally:
            shutil.rmtree(backup_dir, ignore_errors=True)

    def test_restore_missing_source_raises(self, maint_service):
        with pytest.raises(FileNotFoundError):
            maint_service.restore("/nonexistent/path/backup.zip")
