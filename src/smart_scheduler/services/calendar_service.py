"""
services/calendar_service.py
Strategy Pattern implementation for Calendar Exports (ICS).

Refactored to delegate to shared.calendar.ics_writer, eliminating
the parallel hand-rolled ICS implementation.
"""
from abc import ABC, abstractmethod
from datetime import datetime, date
from ..models import Task
from shared.calendar.ics_writer import CalendarEvent, ICSWriter


class CalendarExportStrategy(ABC):
    @abstractmethod
    def export(self, task: Task) -> str:
        """Return the string content of the calendar file."""
        pass


class IcsExportStrategy(CalendarExportStrategy):
    def export(self, task: Task) -> str:
        """Generate a complete VCALENDAR string for a single task."""
        if not task.due_date:
            raise ValueError("Task has no due date.")

        year, month, day = (int(p) for p in task.due_date.split("-"))

        desc_parts = []
        if task.notes:
            desc_parts.append(task.notes)
        if task.outcome:
            desc_parts.append(f"Outcome: {task.outcome}")

        event = CalendarEvent(
            uid=f"{task.id}@scheduler.local",
            title=task.title,
            start_date=date(year, month, day),
            description="\n".join(desc_parts) if desc_parts else None,
            all_day=True,
        )

        writer = ICSWriter("Smart Scheduler")
        writer.add_event(event)
        return writer.to_string()


class CalendarService:
    def __init__(self, strategy: CalendarExportStrategy = None):
        self.strategy = strategy or IcsExportStrategy()

    def generate_file_content(self, task: Task) -> str:
        return self.strategy.export(task)
