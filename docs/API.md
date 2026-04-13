# Manifest Manager API Documentation

**Version**: 3.5.0  
**Last Updated**: March 2026

---

## Table of Contents

1. [Command Reference](#command-reference)
2. [Shortcut System](#shortcut-system)
3. [DataFrame Commands](#dataframe-commands)
4. [Shared Infrastructure](#shared-infrastructure)
5. [Python API](#python-api)
6. [Configuration](#configuration)

---

## Command Reference

### File Commands

#### `load`

Load a manifest file (XML or encrypted 7z). Creates a new file if the path does not exist.

```
load <filename> [--autosc] [--rebuildsc]
```

| Option | Description |
|---|---|
| `--autosc` | Auto-create ID sidecar if missing |
| `--rebuildsc` | Force-rebuild sidecar from XML on load |

```bash
load myproject.xml
load myproject.xml --autosc
load myproject.xml --rebuildsc
load backup.7z                  # Prompts for password
```

---

#### `save`

Save the current manifest. Encrypts automatically when the filename ends in `.7z`.

```
save [filename]
```

```bash
save                    # Overwrite current file
save backup.xml         # Save to new file
save backup.7z          # Save encrypted (prompts for password)
```

---

#### `backup`

Create a backup copy of the current manifest without changing the active file.

```
backup [filename] [--timestamp] [--force] [--no-sidecar]
```

| Option | Description |
|---|---|
| `filename` | Custom backup path (default: `<name>.bkp.<ext>`) |
| `--timestamp`, `-t` | Use timestamp in filename instead of `.bkp` |
| `--force`, `-f` | Overwrite existing backup without prompting |
| `--no-sidecar` | Skip sidecar backup |

```bash
backup                              # → project.bkp.xml
backup --timestamp                  # → project.20260301_143022.xml
backup archive.xml                  # Custom name
backup --timestamp --force          # Overwrite silently
```

---

#### `restore`

Load a backup file into memory. Use `save <original>` afterward to write back.

```
restore <filename>
```

```bash
restore project.bkp.xml
restore project.20260301_143022.xml
```

---

### Node Commands

#### `add`

Add a new node. Supports shortcut syntax (see [Shortcut System](#shortcut-system)).

**Shortcut syntax:**
```
add <shortcut> ["Title"] [options]
```

**Full syntax:**
```
add --tag <name> [options]
```

| Option | Description |
|---|---|
| `--tag <name>` | Tag name (required in full syntax) |
| `--topic <text>` | Topic / title attribute |
| `--status <value>` | Status attribute |
| `--resp <name>` | Responsible party |
| `--due <YYYY-MM-DD>` | Due date |
| `--parent <selector>` | Parent XPath or ID prefix (default: `/*`) |
| `--parent-xpath` | Force XPath interpretation of `--parent` |
| `--parent-id` | Force ID interpretation of `--parent` |
| `--id <value>` | Custom ID |
| `--id False` | Disable auto-ID for this node |
| `-a <key=value>` | Custom attribute (repeatable) |
| `text` | Body text content (positional) |

```bash
# Shortcut
add task "Review PR"
add task "Deploy" --status active --resp alice --due 2026-03-15
add task "Subtask" --parent a3f7
add task "In project" --parent "//project[@topic='Q1']"

# Full syntax
add --tag task --topic "Review PR"
add --tag task --topic "Deploy" --status active --resp alice
add --tag item --topic "Chair" -a colour=blue -a condition=new
```

---

#### `edit`

Modify an existing node. Selector is auto-detected as ID or XPath.

```
edit <selector> [options]
```

| Option | Description |
|---|---|
| `--topic <text>` | Update topic |
| `--status <value>` | Update status |
| `--resp <name>` | Update responsible party |
| `--due <YYYY-MM-DD>` | Update due date |
| `--text <text>` | Update body text |
| `-a <key=value>` | Add / update attribute (repeatable) |
| `--delete` | Delete matched node(s) |
| `--id` | Force ID interpretation of selector |
| `--xpath` | Force XPath interpretation of selector |

```bash
edit a3f7b2c1 --status done
edit a3f --topic "Updated title"        # ID prefix (interactive if multiple)
edit "//task[@status='pending']" --status active
edit a3f --delete                       # Delete via edit
```

---

#### `delete`

Delete a node and all its descendants. Aliases: `del`, `remove`.

```
delete <selector> [--id] [--xpath]
```

```bash
delete a3f7
delete a3f                              # ID prefix (interactive if multiple)
delete "//task[@status='cancelled']"
```

---

#### `show`

Display full details of a single node: all attributes, text, and a tree of children.

```
show <selector> [--id] [--xpath]
```

```bash
show a3f7b2c1
show a3f                                # ID prefix
show "//project[1]"
```

---

### Search & View Commands

#### `find`

Find nodes by ID prefix. Uses the sidecar index (requires `--autosc` on load).

```
find <prefix> [--tree] [--depth N]
```

| Option | Description |
|---|---|
| `prefix` | ID prefix to search |
| `--tree` | Show full subtree for each match |
| `--depth N` | Limit tree depth |

```bash
find a3f
find a3f --tree
find a3f --tree --depth 2
```

---

#### `list`

Display nodes in the manifest.

```
list [selector] [--style tree|table] [--depth N] [--id] [--xpath]
```

| Option | Description |
|---|---|
| `selector` | ID prefix or XPath (default: `/*`) |
| `--style tree` | Hierarchical view (default) |
| `--style table` | Columnar view |
| `--depth N` | Limit display depth |
| `--id` | Force ID interpretation |
| `--xpath` | Force XPath interpretation |

```bash
list
list --style table
list --depth 2
list "//task[@status='active']"
list a3f --style tree
```

---

#### `export-calendar`

Export nodes with `due` attributes to an iCalendar `.ics` file.

```
export-calendar <selector> <output.ics> [--name NAME] [--id] [--xpath]
```

| Option | Description |
|---|---|
| `selector` | XPath, full ID, or ID prefix |
| `output.ics` | Output file path |
| `--name NAME` | Calendar name (default: `"Manifest Tasks"`) |
| `--id` | Force ID interpretation |
| `--xpath` | Force XPath interpretation |

```bash
export-calendar "//task[@due]" tasks.ics
export-calendar "//task[@due][@status='active']" active.ics --name "Active Tasks"
export-calendar a3f my-task.ics         # Export by ID prefix
export-calendar a3f7b2c1 my-task.ics   # Export by full ID
```

---

### Structure Commands

#### `wrap`

Wrap all top-level nodes under a new container element.

```
wrap --root <tag>
```

```bash
wrap --root archive
wrap --root project
```

---

#### `merge`

Merge all nodes from another manifest file into the current one.

```
merge <filename>
```

```bash
merge other.xml
merge backup.7z             # Prompts for password
```

---

### Maintenance Commands

#### `autoid`

Add IDs to elements that lack them.

```
autoid [--overwrite]
```

| Option | Description |
|---|---|
| `--overwrite` | Replace all existing IDs (default: skip elements that already have one) |

```bash
autoid
autoid --overwrite
```

---

#### `rebuild`

Rebuild the ID sidecar index from the current in-memory XML. Use when IDs exist in the XML but the sidecar is missing or stale.

```
rebuild
```

---

#### `cheatsheet`

Print the quick-reference cheatsheet.

---

#### `exit`

Exit the shell. Warns if there are unsaved changes; run `exit` a second time to force quit. `Ctrl+D` also exits.

---

## Shortcut System

Shortcuts let you omit `--tag` and `--topic` for common tag names:

```
add task "Title"
# expands to:
add --tag task --topic "Title"
```

**Rule:** the title must come immediately after the shortcut noun, before any flags.

```bash
# Correct
add task "Title" --status active

# Wrong — "Title" becomes body text, not topic
add task --status active "Title"
```

### Default shortcuts

`task`, `project`, `item`, `note`, `milestone`, `idea`, `location`, `contact`, `reference`, `resource`

### Configuration

**File:** `config/shortcuts.yaml`

```yaml
shortcuts:
  - task
  - project
  - my_custom_tag    # add yours here

reserved_keywords:
  - help
  - exit
  - save
  - list
  - find
  - edit
  - delete
```

Reload the shell after editing the file.

---

## DataFrame Commands

Requires `pandas` (`pip install pandas`). Injected at startup; silently unavailable if pandas is not installed.

#### `to_df`

Convert the loaded manifest (or an XPath subtree) to a DataFrame, with optional CSV export.

```
to_df [xpath] [--save FILE] [--no-text]
```

| Option | Description |
|---|---|
| `xpath` | Optional XPath to select a subtree (default: entire manifest) |
| `--save FILE` | Write CSV instead of printing preview |
| `--no-text` | Omit text column (faster for metadata-only exports) |

```bash
to_df
to_df --save all.csv
to_df "//task[@status='active']" --save active.csv
to_df --no-text --save meta.csv
```

---

#### `find_df`

Execute an XPath query and display or save results as a DataFrame.

```
find_df <xpath> [--save FILE]
```

```bash
find_df "//task[@status='active']"
find_df "//task[@due]" --save due_tasks.csv
```

---

#### `from_df`

Import a CSV (previously exported by `to_df` or `find_df`) back into the manifest.

```
from_df <file> [--parent XPATH] [--dry-run]
```

| Option | Description |
|---|---|
| `file` | CSV file to import |
| `--parent XPATH` | Attach imported nodes under this XPath (default: replace manifest root children) |
| `--dry-run` | Preview without modifying |

```bash
from_df tasks.csv
from_df updated.csv --parent "//project[@id='p1']"
from_df updated.csv --dry-run
```

---

## Shared Infrastructure

### ID Generator — `shared.id_generator`

#### `generate_id(prefix="", length=8)`

Generate a unique hexadecimal ID.

```python
from shared.id_generator import generate_id

generate_id()                    # "a3f7b2c1"
generate_id(prefix="t", length=5)  # "t1a2b3"
```

#### `validate_id(id_str, prefix=None, min_length=3)`

Returns `True` if the string is a valid ID.

#### `extract_prefix(id_str)`

Returns `(prefix, hex_part)` tuple.

---

### Calendar Writer — `shared.calendar.ics_writer`

#### `CalendarEvent` dataclass

Key fields: `uid`, `title`, `start_date`, `description`, `location`, `status`, `categories`.

#### `ICSWriter`

```python
from shared.calendar.ics_writer import CalendarEvent, ICSWriter

writer = ICSWriter("My Tasks")
writer.add_event(CalendarEvent(uid="t1", title="Review", start_date=date(2026, 3, 15)))
writer.write("tasks.ics")
```

---

### File Locking — `shared.locking`

#### `file_lock(filepath, timeout=5)`

Context manager for exclusive file access. Raises `LockTimeout` if the lock cannot be acquired.

```python
from shared.locking import file_lock
from pathlib import Path

with file_lock(Path("data.xml"), timeout=10):
    process_file()
```

#### `check_lock(filepath)`

Returns the PID of the lock holder, or `None`.

---

## Python API

### `ManifestRepository`

Key methods (all return a `Result` object with `.success` and `.message`):

| Method | Description |
|---|---|
| `load(filepath, password, auto_sidecar, rebuild_sidecar)` | Load XML or 7z |
| `save(filepath, password)` | Save XML or 7z |
| `add_node(parent_xpath, spec, auto_id=True)` | Add a node |
| `edit_node(xpath, spec, delete)` | Edit/delete by XPath |
| `edit_node_by_id(elem_id, spec, delete)` | Edit/delete by exact ID |
| `ensure_ids(overwrite=False)` | Auto-generate missing IDs |
| `search(xpath)` | Return list of matching elements |
| `wrap_content(new_root_tag)` | Wrap top-level nodes |
| `merge_from(path, password)` | Merge another file |

### `NodeSpec`

```python
from manifest_manager.manifest_core import NodeSpec

spec = NodeSpec(tag="task", topic="Review PR", status="active",
                resp="alice", due="2026-03-15", attrs={"priority": "high"})

# Or from argparse namespace:
spec = NodeSpec.from_args(args, attributes=extra_attrs)
```

### `dataframe_conversion` module

```python
from manifest_manager.dataframe_conversion import (
    to_dataframe,        # element → DataFrame
    find_to_dataframe,   # XPath search → DataFrame
    from_dataframe,      # DataFrame → element (round-trip)
    preview_dataframe,   # formatted summary string
)
```

`to_dataframe(root, *, include_text=True, generate_ids=False)`  
`find_to_dataframe(tree, xpath, *, wrap_tag="results", include_text=True)`  
`from_dataframe(df, root_tag="root")` — raises `ValueError` if `id`, `parent_id`, or `tag` columns are missing  
`preview_dataframe(df, max_rows=10)`

---

## Configuration

### `pyproject.toml`

```toml
[project]
name = "manifest-manager"
version = "3.5.0"
requires-python = ">=3.8"
dependencies = ["lxml>=4.9.0", "py7zr>=0.20.0", "pyyaml>=6.0"]

[project.scripts]
manifest = "manifest_manager.__main__:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

### `config/shortcuts.yaml`

```yaml
shortcuts:
  - task
  - project
  - item
  - note
  - milestone
  - idea
  - location
  - contact
  - reference
  - resource

reserved_keywords:
  - help
  - exit
  - quit
  - save
  - list
  - search
  - find
  - delete
  - remove
  - edit
  - show
  - export
  - import
```

---

*Last updated: March 2026*
