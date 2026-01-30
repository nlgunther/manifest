"""
Calendar Export Module for Manifest Manager

Exports tasks with due dates to iCalendar (.ics) format for Google Calendar.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from lxml import etree


class ICSGenerator:
    """Generate iCalendar (.ics) files from manifest tasks."""
    
    @staticmethod
    def generate(elements: List[etree._Element], 
                 calendar_name: str = "Manifest Tasks",
                 timezone: str = "America/Los_Angeles") -> str:
        """Generate ICS file content from elements with due dates.
        
        Args:
            elements: List of XML elements to export
            calendar_name: Name of the calendar
            timezone: Timezone identifier (default: America/Los_Angeles)
            
        Returns:
            ICS file content as string
            
        Example:
            >>> elements = repo.search("//task[@due]")
            >>> ics_content = ICSGenerator.generate(elements)
            >>> with open("tasks.ics", "w") as f:
            ...     f.write(ics_content)
        """
        lines = []
        
        # Calendar header
        lines.append("BEGIN:VCALENDAR")
        lines.append("VERSION:2.0")
        lines.append("PRODID:-//Manifest Manager//Task Export//EN")
        lines.append(f"X-WR-CALNAME:{calendar_name}")
        lines.append("X-WR-TIMEZONE:" + timezone)
        lines.append("CALSCALE:GREGORIAN")
        lines.append("METHOD:PUBLISH")
        
        # Process each element
        events_added = 0
        for elem in elements:
            event = ICSGenerator._element_to_event(elem)
            if event:
                lines.extend(event)
                events_added += 1
        
        # Calendar footer
        lines.append("END:VCALENDAR")
        
        return "\r\n".join(lines) + "\r\n"
    
    @staticmethod
    def _element_to_event(elem: etree._Element) -> Optional[List[str]]:
        """Convert a single element to VEVENT lines.
        
        Args:
            elem: XML element with due date
            
        Returns:
            List of ICS lines for this event, or None if no due date
        """
        due_date = elem.get("due")
        if not due_date:
            return None
        
        # Parse the date
        try:
            due_dt = datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            # Invalid date format, skip
            return None
        
        # Extract event details
        topic = elem.get("topic", elem.tag)
        description = (elem.text or "").strip()
        status = elem.get("status", "")
        resp = elem.get("resp", "")
        uid = elem.get("id", f"{topic}-{due_date}")
        
        # Build description
        desc_lines = []
        if description:
            desc_lines.append(description)
        if status:
            desc_lines.append(f"Status: {status}")
        if resp:
            desc_lines.append(f"Assigned to: {resp}")
        
        # Add parent context if available
        parent = elem.getparent()
        if parent is not None and parent.tag != "manifest":
            parent_topic = parent.get("topic", parent.tag)
            desc_lines.append(f"Project: {parent_topic}")
        
        description_text = "\\n".join(desc_lines).replace(",", "\\,")
        
        # Create timestamps
        now = datetime.now()
        created = now.strftime("%Y%m%dT%H%M%SZ")
        
        # All-day event: use DATE format (not DATETIME)
        due_str = due_dt.strftime("%Y%m%d")
        
        # Build event
        lines = [
            "BEGIN:VEVENT",
            f"UID:{uid}@manifestmanager",
            f"DTSTAMP:{created}",
            f"DTSTART;VALUE=DATE:{due_str}",
            f"SUMMARY:{topic}",
        ]
        
        if description_text:
            lines.append(f"DESCRIPTION:{description_text}")
        
        # Add status mapping
        if status:
            # Map manifest status to iCal status
            ical_status = {
                "done": "COMPLETED",
                "active": "IN-PROCESS",
                "pending": "NEEDS-ACTION",
                "blocked": "NEEDS-ACTION",
                "cancelled": "CANCELLED"
            }.get(status.lower(), "NEEDS-ACTION")
            lines.append(f"STATUS:{ical_status}")
        
        # Add priority based on status
        if status == "active":
            lines.append("PRIORITY:1")  # High priority
        elif status == "pending":
            lines.append("PRIORITY:5")  # Medium priority
        
        # Add categories
        categories = []
        if parent is not None and parent.tag != "manifest":
            categories.append(parent.get("topic", parent.tag))
        if elem.tag:
            categories.append(elem.tag)
        if categories:
            lines.append(f"CATEGORIES:{','.join(categories)}")
        
        lines.append("END:VEVENT")
        
        return lines
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Validate YYYY-MM-DD date format.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False


def export_to_ics(elements: List[etree._Element], 
                  output_file: str,
                  calendar_name: str = "Manifest Tasks") -> int:
    """Export elements with due dates to ICS file.
    
    Args:
        elements: List of XML elements to export
        output_file: Path to output .ics file
        calendar_name: Name of the calendar
        
    Returns:
        Number of events exported
        
    Example:
        >>> tasks = repo.search("//task[@due]")
        >>> count = export_to_ics(tasks, "tasks.ics", "My Tasks")
        >>> print(f"Exported {count} tasks")
    """
    ics_content = ICSGenerator.generate(elements, calendar_name)
    
    # Count events
    event_count = ics_content.count("BEGIN:VEVENT")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(ics_content)
    
    return event_count
