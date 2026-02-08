# Manifest Manager API Documentation

**Version**: 3.5.0  
**Last Updated**: February 2026

---

## Table of Contents

1. [Command Reference](#command-reference)
2. [Shortcut System](#shortcut-system)
3. [Shared Infrastructure](#shared-infrastructure)
4. [Python API](#python-api)
5. [Configuration](#configuration)
6. [Advanced Usage](#advanced-usage)

---

## Command Reference

### Core Commands

#### `load`

Load a manifest file (XML or encrypted 7z).

**Syntax:**
```bash
load <filename> [--autosc] [--autoid]
```

**Options:**
- `--autosc` - Auto-save on changes
- `--autoid` - Enable automatic ID generation

**Examples:**
```bash
load project.xml
load project.xml --autosc
load backup.7z  # Prompts for password
```

---

#### `add`

Add a new node to the manifest.

**Shortcut Syntax** (v3.5+):
```bash
add <shortcut> "Title" [--flags]
```

**Full Syntax**:
```bash
add --tag <tag> [--topic "Title"] [--flags]
```

**Options:**
- `--tag <name>` - Node tag name (required in full syntax)
- `--topic <text>` - Topic/title text
- `--title <text>` - Alias for --topic (v3.4+)
- `--status <value>` - Status value
- `--resp <name>` - Responsible party (legacy)
- `--assignee <name>` - Assignee (v3.4+, alias for --resp)
- `--due <date>` - Due date (YYYY-MM-DD)
- `--parent <selector>` - Parent location (XPath or ID)
- `--id <value>` - Custom ID (default: auto-generated)
- `--id False` - Disable auto-ID
- `-a, --attr <k=v>` - Additional attributes (repeatable)
- `text` - Body text content

**Shortcut Examples:**
```bash
# Basic
add task "Buy groceries"

# With status
add task "Review PR" --status active

# With assignee
add task "Deploy" --assignee alice

# With due date
add task "Submit report" --due 2026-03-15

# With parent (using ID)
add task "Subtask" --parent a3f7

# With parent (using XPath)
add task "Feature task" --parent "//project[@title='Website']"

# Multiple flags
add project "Q1 Goals" --status planning --assignee bob --due 2026-03-31

# Custom attributes
add task "Database migration" -a priority=high -a team=backend
```

**Full Syntax Examples:**
```bash
# Traditional syntax (still works)
add --tag task --topic "Buy groceries"
add --tag project --title "Q1 Goals" --status planning
add --tag item --topic "Office supplies" --parent "//location[@title='Storage']"
```

**Parent Selector Detection:**
- Contains `/` → XPath
- Hex-like (3-8 chars) → ID prefix
- Exact match in sidecar → Full ID

---

#### `edit`

Modify an existing node.

**Syntax:**
```bash
edit <selector> [--flags]
```

**Selector Types:**
- Full ID: `a3f7b2c1`
- ID prefix: `a3f7` (shows selection if multiple matches)
- XPath: `//task[@status='active']`

**Options:**
- Same as `add` command (except --tag)
- `--clear-<attr>` - Remove an attribute

**Examples:**
```bash
# Edit by full ID
edit a3f7b2c1 --status done

# Edit by ID prefix
edit a3f --status in_progress

# Edit by XPath
edit "//task[@title='Review PR']" --assignee charlie

# Clear an attribute
edit a3f7 --clear-due

# Multiple changes
edit a3f7 --status done --resp alice --topic "Updated title"
```

---

#### `find`

Search for nodes using XPath or ID.

**Syntax:**
```bash
find <selector> [--view <format>]
```

**Selector Types:**
- XPath: `//task[@status='active']`
- ID: `a3f7b2c1`
- ID prefix: `a3f`

**View Formats:**
- `tree` (default) - Hierarchical tree view
- `table` - Tabular view
- `compact` - Minimal output

**Examples:**
```bash
# Find by tag
find //task

# Find by attribute
find "//task[@status='active']"

# Find by ID prefix
find a3f

# Complex XPath
find "//project[@status='planning']//task[@assignee='alice']"

# With view format
find //task --view table
find //project --view compact
```

---

#### `list`

List all nodes in the manifest.

**Syntax:**
```bash
list [--view <format>]
```

**View Formats:**
- `tree` (default)
- `table`
- `compact`

**Examples:**
```bash
list
list --view table
list --view compact
```

---

#### `save`

Save the current manifest.

**Syntax:**
```bash
save [filename] [--encrypt]
```

**Options:**
- `filename` - Save as different file
- `--encrypt` - Save as encrypted 7z

**Examples:**
```bash
save                    # Save to current file
save backup.xml         # Save as new file
save backup.7z          # Save as encrypted 7z (prompts for password)
```

---

#### `delete`

Delete a node.

**Syntax:**
```bash
delete <selector>
```

**Examples:**
```bash
delete a3f7
delete "//task[@status='cancelled']"
```

---

#### `wrap`

Wrap top-level nodes under a new parent.

**Syntax:**
```bash
wrap --tag <tag> --topic "Title"
```

**Examples:**
```bash
wrap --tag project --topic "Archive 2025"
```

---

#### `merge`

Merge another manifest file into the current one.

**Syntax:**
```bash
merge <filename> [--strategy <strategy>]
```

**Strategies:**
- `union` - Combine all (default)
- `source_wins` - Source wins conflicts
- `target_wins` - Target wins conflicts

**Examples:**
```bash
merge other.xml
merge backup.xml --strategy source_wins
```

---

### Utility Commands

#### `rebuild`

Rebuild the ID sidecar index.

**Syntax:**
```bash
rebuild
```

**When to use:**
- After manual XML edits
- After merge operations
- To verify sidecar consistency

---

#### `autoid`

Configure automatic ID generation.

**Syntax:**
```bash
autoid [on|off]
```

**Examples:**
```bash
autoid on
autoid off
```

---

#### `cheatsheet`

Display quick reference guide.

**Syntax:**
```bash
cheatsheet
```

---

#### `exit`

Exit the shell (with unsaved changes warning).

**Syntax:**
```bash
exit
```

---

## Shortcut System

### Overview

Shortcuts allow you to type less for common operations:

```bash
# Shortcut (v3.5+)
add task "Title"

# Expands to:
add --tag task --topic "Title"
```

### How It Works

**Detection Logic:**
1. First word is a known shortcut?
2. First word doesn't start with `--`?
3. → Expand to full syntax

**Expansion Rules:**
```
add <shortcut> "Title" [--flags]
  ↓
add --tag <shortcut> --topic "Title" [--flags]
```

### Default Shortcuts

| Shortcut | Description | Example |
|----------|-------------|---------|
| `task` | Task items | `add task "Review PR"` |
| `project` | Projects | `add project "Q1 Goals"` |
| `item` | Generic items | `add item "Office chair"` |
| `note` | Notes/reminders | `add note "Remember to..."` |
| `milestone` | Milestones | `add milestone "v1.0 Release"` |
| `idea` | Ideas | `add idea "Feature: Dark mode"` |
| `location` | Locations | `add location "Conference Room A"` |
| `contact` | Contacts | `add contact "John Doe"` |
| `reference` | References | `add reference "Documentation link"` |

### Configuration

**File**: `config/shortcuts.yaml`

```yaml
shortcuts:
  - task
  - project
  - location
  - your_custom_shortcut  # Add here!

reserved_keywords:
  - help
  - exit
  # Don't add "add" here!
```

### Adding Custom Shortcuts

1. Edit `config/shortcuts.yaml`
2. Add your shortcut to the list
3. Reload the shell
4. Use it: `add your_shortcut "Title"`

### Reserved Keywords

These words **cannot** be shortcuts:
- `help`, `exit`, `quit`
- `save`, `load`
- `list`, `find`, `edit`, `delete`

**Note**: `add` is NOT reserved (it's the command itself).

---

## Shared Infrastructure

### ID Generator

**Module**: `shared.id_generator`

#### `generate_id(prefix="", length=8)`

Generate a unique hexadecimal ID.

**Parameters:**
- `prefix` (str): Optional prefix (e.g., "t" for task)
- `length` (int): Length of hex part (default: 8)

**Returns:** String ID

**Examples:**
```python
from shared.id_generator import generate_id

# Default
id = generate_id()  # "a3f7b2c1"

# With prefix
task_id = generate_id(prefix="t", length=5)  # "t12345"

# Custom length
short_id = generate_id(length=4)  # "a3f7"
```

#### `validate_id(id_str, prefix=None, min_length=3)`

Validate ID format.

**Parameters:**
- `id_str` (str): ID to validate
- `prefix` (str, optional): Expected prefix
- `min_length` (int): Minimum length (default: 3)

**Returns:** bool

**Examples:**
```python
from shared.id_generator import validate_id

validate_id("a3f7b2c1")  # True
validate_id("t12345", prefix="t")  # True
validate_id("xyz")  # False
validate_id("12", min_length=3)  # False
```

#### `extract_prefix(id_str)`

Split ID into prefix and hex parts.

**Returns:** tuple[str, str]

**Examples:**
```python
from shared.id_generator import extract_prefix

extract_prefix("t12345")  # ("t", "12345")
extract_prefix("a3f7b2c1")  # ("", "a3f7b2c1")
```

---

### Calendar Writer

**Module**: `shared.calendar.ics_writer`

#### `CalendarEvent`

Dataclass representing a calendar event.

**Attributes:**
- `uid` (str): Unique identifier
- `title` (str): Event title
- `start_date` (datetime|date): Start date/time
- `end_date` (datetime|date, optional): End date/time
- `description` (str, optional): Description
- `location` (str, optional): Location
- `status` (str, optional): CONFIRMED, TENTATIVE, CANCELLED
- `all_day` (bool): True for all-day events
- `categories` (list[str]): Category tags
- `url` (str, optional): Associated URL

**Example:**
```python
from shared.calendar.ics_writer import CalendarEvent
from datetime import date

event = CalendarEvent(
    uid="task123",
    title="Team Meeting",
    start_date=date(2026, 3, 15),
    description="Weekly sync",
    location="Conference Room A"
)
```

#### `ICSWriter`

Writer for iCalendar (.ics) files.

**Constructor:**
```python
ICSWriter(calendar_name="Exported Calendar", timezone_str="UTC", description=None)
```

**Methods:**

##### `add_event(event: CalendarEvent)`

Add an event to the calendar.

##### `write(filepath: str)`

Write calendar to .ics file.

##### `to_string() -> str`

Generate ICS content as string.

**Example:**
```python
from shared.calendar.ics_writer import CalendarEvent, ICSWriter
from datetime import date

# Create writer
writer = ICSWriter("My Tasks")

# Add events
writer.add_event(CalendarEvent(
    uid="task1",
    title="Review PR",
    start_date=date(2026, 3, 15)
))

writer.add_event(CalendarEvent(
    uid="task2",
    title="Deploy",
    start_date=date(2026, 3, 20)
))

# Write to file
writer.write("tasks.ics")
```

---

### File Locking

**Module**: `shared.locking`

#### `file_lock(filepath, timeout=5)`

Context manager for exclusive file access.

**Parameters:**
- `filepath` (Path): File to lock
- `timeout` (int): Seconds to wait (default: 5)
- `poll_interval` (float): Retry interval (default: 0.1)
- `stale_threshold` (int): Stale lock age in seconds (default: 300)

**Raises:**
- `LockTimeout`: If lock cannot be acquired

**Example:**
```python
from shared.locking import file_lock
from pathlib import Path

with file_lock(Path("data.xml"), timeout=10):
    # Exclusive access guaranteed
    data = load_data()
    modify(data)
    save_data()
```

#### `check_lock(filepath) -> Optional[str]`

Check if file is currently locked.

**Returns:** PID of lock holder, or None

**Example:**
```python
from shared.locking import check_lock
from pathlib import Path

holder = check_lock(Path("data.xml"))
if holder:
    print(f"File locked by process {holder}")
```

---

## Python API

### ManifestRepository

**Module**: `manifest_manager.manifest_core`

#### Core Methods

##### `add_node(parent_xpath, spec, auto_id=True)`

Add a node to the manifest.

**Parameters:**
- `parent_xpath` (str): Parent XPath
- `spec` (NodeSpec): Node specification
- `auto_id` (bool): Auto-generate ID

**Returns:** Result object

**Example:**
```python
from manifest_manager import ManifestRepository, NodeSpec

repo = ManifestRepository("project.xml")
spec = NodeSpec(
    tag="task",
    topic="Review PR",
    attributes={"status": "active"}
)

result = repo.add_node("/*", spec, auto_id=True)
if result.success:
    print(f"Added: {result.data['id']}")
```

##### `find_nodes(xpath, view=ManifestView.TREE)`

Find nodes by XPath.

**Parameters:**
- `xpath` (str): XPath query
- `view` (ManifestView): Output format

**Returns:** List of nodes

##### `edit_node(selector, updates)`

Edit a node.

**Parameters:**
- `selector` (str): XPath or ID
- `updates` (dict): Attributes to update

**Returns:** Result object

##### `delete_node(selector)`

Delete a node.

**Returns:** Result object

---

### NodeSpec

**Module**: `manifest_manager.manifest_core`

Factory for creating node specifications.

#### `NodeSpec.from_args(args, attributes=None)`

Create spec from argparse namespace.

**Example:**
```python
from manifest_manager import NodeSpec

# From parsed args
spec = NodeSpec.from_args(args, attributes={"custom": "value"})

# Manual creation
spec = NodeSpec(
    tag="task",
    topic="My Task",
    status="active",
    resp="alice",
    attributes={"priority": "high"}
)
```

---

## Configuration

### pyproject.toml

```toml
[project]
name = "manifest-manager"
version = "3.5.0"
requires-python = ">=3.8"
dependencies = [
    "lxml>=4.9.0",
    "py7zr>=0.20.0",
    "pyyaml>=6.0",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
pythonpath = ["src"]
```

### shortcuts.yaml

```yaml
shortcuts:
  - task
  - project
  - item
  # ... add more

reserved_keywords:
  - help
  - exit
  # ... add more (but NOT "add"!)
```

---

## Advanced Usage

### Batch Operations

```bash
# Add multiple tasks
for title in "Task 1" "Task 2" "Task 3"; do
    manifest add task "$title" --status active
done
```

### Scripting

```python
from manifest_manager import ManifestRepository, NodeSpec

# Programmatic usage
repo = ManifestRepository("project.xml")

tasks = [
    ("Review PR", "active"),
    ("Deploy", "planning"),
    ("Test", "active")
]

for title, status in tasks:
    spec = NodeSpec(tag="task", topic=title, status=status)
    repo.add_node("/*", spec, auto_id=True)

repo.save()
```

### Custom Shortcuts

```yaml
# Domain-specific shortcuts
shortcuts:
  - bug          # add bug "Fix crash"
  - feature      # add feature "Dark mode"
  - meeting      # add meeting "Team sync"
  - document     # add document "Requirements"
```

### Parent Resolution

```bash
# By ID
add task "Subtask" --parent a3f7

# By XPath
add task "Feature" --parent "//project[@title='Website']"

# Nested
add task "Detail" --parent "//project//milestone[@title='v1.0']"
```

---

## Error Handling

### Common Errors

**ModuleNotFoundError**:
```bash
# Solution
pip install -e .
```

**LockTimeout**:
```python
# Another process is using the file
# Wait or use longer timeout
with file_lock(path, timeout=30):
    ...
```

**XPath Syntax Error**:
```bash
# Invalid
find //task[@status=active]  # Missing quotes

# Valid
find "//task[@status='active']"
```

**Shortcut Not Found**:
```bash
# Check config
cat config/shortcuts.yaml

# Reload shell
exit
manifest
```

---

## See Also

- [README.md](README.md) - Project overview
- [CHEATSHEET.md](CHEATSHEET.md) - Quick reference
- [TEST_PHASE3_GUIDE.md](TEST_PHASE3_GUIDE.md) - Testing guide

---

*Last updated: February 2026*
