# Productivity Suite CLI Harmonization

**Version**: 3.5.0  
**Status**: Phase 3 Complete  
**Last Updated**: March 2026

---

## Overview

This project harmonizes the command-line interfaces of **Manifest Manager** and **Smart Scheduler**, two complementary productivity tools. The goal is to provide a unified, intuitive user experience while maintaining the unique strengths of each tool.

### The Tools

**Manifest Manager v3.4+**
- Hierarchical XML data management
- Task and project organization
- Flexible schema with arbitrary tags
- XPath querying and ID-based lookups

**Smart Scheduler v2.0** (planned integration)
- Time-based task management
- Natural language date parsing
- Status workflows
- Calendar integration (ICS export)

---

## What's New in v3.5

### 🚀 Phase 3: Shortcut System

**The Problem**: Typing `add --tag task --topic "Buy milk"` is verbose for common operations.

**The Solution**: Shortcuts that expand automatically!

```bash
# New shortcut syntax (70% less typing!)
add task "Buy milk"
add project "Q1 Goals" --status planning
add location "Conference Room A"

# Expands to:
add --tag task --topic "Buy milk"
add --tag project --topic "Q1 Goals" --status planning
add --tag location --topic "Conference Room A"
```

**Features:**
- ✅ Configurable shortcuts (YAML file)
- ✅ Works with all existing flags
- ✅ Backward compatible (old syntax still works)
- ✅ Extensible (add your own shortcuts)

### 🔧 Phase 2: Vocabulary Harmonization

**Consistent flag names** used across commands:

| Attribute | Flag | Notes |
|---|---|---|
| Topic / title | `--topic` | Use for node title in `add` and `edit` |
| Responsible party | `--resp` | Use for assignee in `add` and `edit` |
| Due date | `--due` | Format: `YYYY-MM-DD` |
| Status | `--status` | Common values: `active`, `done`, `pending`, `blocked`, `cancelled` |

### 📦 Phase 1: Shared Infrastructure

**Common libraries** for both tools:

- `shared.id_generator` - Standardized ID creation
- `shared.calendar.ics_writer` - Unified ICS export
- `shared.locking` - File locking for safe concurrent access

---

## Installation

### Prerequisites

- Python 3.8+
- Required packages: `lxml`, `py7zr`, `pyyaml`

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd manifest

# Install in development mode
pip install -e .

# Verify installation
manifest --version
```

### Configuration

The shortcut system uses a configuration file:

**Location**: `config/shortcuts.yaml`

**Default shortcuts**: task, project, item, note, milestone, idea, location, contact, reference

**To add custom shortcuts**, edit the config file:

```yaml
shortcuts:
  - task
  - project
  - location
  - bug        # Add your own!
  - feature
  - meeting
```

---

## Quick Start

### Basic Usage

```bash
# Start the interactive shell
manifest

# Load a manifest file
(manifest) load myproject.xml

# Add items using shortcuts
(myproject.xml) add task "Review PR #42"
(myproject.xml) add project "Website Redesign" --status planning
(myproject.xml) add location "Building A, Room 203"

# Search and edit
(myproject.xml) find task
(myproject.xml) edit a3f7 --status done

# Save your changes
(myproject.xml) save
```

### Shortcut Syntax

**Basic pattern**: `add <shortcut> "Title" [--flags]`

```bash
# Simple
add task "Buy groceries"

# With flags
add task "Important task" --status active --resp alice

# With parent location
add task "Subtask" --parent a3f7

# Multiple attributes
add project "Q1 Goals" --status planning --resp bob --due 2026-03-31
```

### Full Syntax (Still Works!)

```bash
# Old way (backward compatible)
add --tag task --topic "Buy groceries"
add --tag project --topic "Q1 Goals" --status planning
```

---

## Architecture

### Directory Structure

```
manifest/
├── config/
│   └── shortcuts.yaml          # Shortcut configuration
├── src/
│   ├── shared/                 # Shared infrastructure
│   │   ├── __init__.py
│   │   ├── id_generator.py     # ID generation
│   │   ├── locking.py          # File locking
│   │   └── calendar/
│   │       ├── __init__.py
│   │       └── ics_writer.py   # ICS export
│   └── manifest_manager/       # Manifest Manager package
│       ├── __init__.py
│       ├── manifest.py                 # CLI shell
│       ├── manifest_core.py            # Core logic
│       ├── storage.py                  # Storage layer
│       ├── calendar.py                 # Calendar export helpers
│       ├── config.py                   # Per-file config
│       ├── id_sidecar.py               # ID sidecar index
│       ├── dataframe_conversion.py     # XML ↔ DataFrame (v3.5)
│       └── dataframe_commands.py       # to_df / find_df / from_df (v3.5)
├── tests/
│   ├── shared/                 # Tests for shared code
│   │   ├── test_id_generator.py
│   │   ├── test_ics_writer.py
│   │   └── test_locking.py
│   │   ├── test_phase3_shortcuts.py
│   ├── test_dataframe_conversion.py
│   ├── test_export_calendar_ids.py
│   └── ... (see tests/ directory)
├── docs/
│   ├── API.md                  # API documentation
│   ├── CHEATSHEET.md           # Quick reference
│   └── PHASE_1_REFLECTION.md   # Implementation notes
├── pyproject.toml              # Project configuration
└── README.md                   # This file
```

### Package Layout

```python
# The "src layout" pattern
src/
├── shared/              # Shared between tools
│   └── ...
└── manifest_manager/    # Manifest Manager
    └── ...

# Install makes both importable:
from shared import generate_id
from manifest_manager import ManifestRepository
```

---

## Features

### Shortcut System (v3.5)

**Automatic expansion** of common commands:

```bash
add task "Title"
# ↓ Expands to:
add --tag task --topic "Title"
```

**Configurable** via YAML:
- Add domain-specific shortcuts
- Reserved keyword protection
- Easy team customization

### Smart ID Matching (v3.4)

**Prefix matching** for IDs:

```bash
# Full ID: a3f7b2c1
edit a3f                    # Matches prefix
edit a3f7b2c1               # Exact match

# Multiple matches? Interactive selection:
edit a3
  [1] a3f7b2c1 - Task: Review PR
  [2] a3a9c4d2 - Task: Update docs
  Select: 1
```

### Flexible Selectors

**XPath or ID** - use what's natural:

```bash
# XPath (precise)
find "//task[@status='active']"

# ID (fast)
find a3f7

# ID prefix (convenient)
find a3f
```

### File Locking (Phase 5)

**Prevents corruption** from concurrent access:

```python
from shared.locking import file_lock

with file_lock(Path("data.xml"), timeout=5):
    # Exclusive access guaranteed
    modify_data()
```

---

## Testing

### Run All Tests

```bash
# All tests
pytest

# Specific module
pytest tests/shared/ -v
pytest tests/test_phase3_shortcuts.py -v

# With coverage
pytest --cov=manifest_manager --cov=shared --cov-report=html
```

### Test Coverage

**Phase 1 (Shared Infrastructure):**
- ✅ ID generation (8 tests)
- ✅ ICS export (6 tests)
- ✅ File locking (5 tests)

**Phase 3 (Shortcuts):**
- ✅ Basic expansion (3 tests)
- ✅ Shortcuts with flags (3 tests)
- ✅ Backward compatibility (2 tests)
- ✅ Edge cases (5 tests)
- ✅ Config loading (3 tests)
- ✅ Integration scenarios (4 tests)

**Total**: 39+ tests passing

---

## Configuration

### shortcuts.yaml

```yaml
# Shortcut configuration
shortcuts:
  - task          # add task "Title"
  - project       # add project "Name"
  - item          # add item "Thing"
  - note          # add note "Reminder"
  - milestone     # add milestone "v1.0"
  - idea          # add idea "Feature"
  - location      # add location "Place"
  - contact       # add contact "Person"
  - reference     # add reference "Doc"

# Reserved keywords (cannot be shortcuts)
reserved_keywords:
  - help
  - exit
  - save
  - list
  - edit
  - find
  - delete
```

### pyproject.toml

```toml
[project]
name = "manifest-manager"
version = "3.5.0"
dependencies = [
    "lxml>=4.9.0",
    "py7zr>=0.20.0",
    "pyyaml>=6.0",
]

[tool.setuptools.packages.find]
where = ["src"]  # Auto-discovers packages

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

---

## Roadmap

### ✅ Completed

- [x] **Phase 1**: Shared infrastructure library
- [x] **Phase 2**: Vocabulary harmonization
- [x] **Phase 3**: Shortcut system

### 🔜 Upcoming

- [ ] **Phase 4**: Integrate shared components into both tools
  - Replace ID generation with `shared.id_generator`
  - Replace ICS export with `shared.calendar.ics_writer`
  - Comprehensive compatibility testing

- [ ] **Phase 5**: File locking integration
  - Add locking to save operations
  - Add locking to database writes
  - Test concurrent access scenarios

### 📅 Future

- [ ] **Phase 6**: Smart Scheduler integration
  - Apply shortcut system to Scheduler
  - Unified CLI patterns
  - Cross-tool compatibility

---

## Contributing

### Adding New Shortcuts

1. Edit `config/shortcuts.yaml`:
   ```yaml
   shortcuts:
     - your_shortcut  # Add here
   ```

2. Test it:
   ```bash
   manifest
   (manifest) load test
   (test.xml) add your_shortcut "Test"
   ```

3. Verify expansion:
   ```bash
   # Should create node with tag="your_shortcut"
   (test.xml) list
   ```

### Reporting Issues

**Bug reports** should include:
- Command that failed
- Expected behavior
- Actual behavior
- Manifest Manager version
- Python version

### Development Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests before committing
pytest

# Check code style
flake8 src/

# Run type checker (if using)
mypy src/
```

---

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'shared'`

**Solution**:
```bash
# Ensure package is installed
pip install -e .

# Check pythonpath in pyproject.toml
pythonpath = ["src"]
```

### Shortcut Not Working

**Problem**: `add task "Title"` not expanding

**Solution**:
1. Check `config/shortcuts.yaml` exists
2. Verify "task" is in shortcuts list
3. Ensure "task" not in reserved keywords
4. Reload the shell

### Tests Failing

**Problem**: Import errors in tests

**Solution**:
```bash
# Ensure conftest.py exists in project root
# It should contain:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
```

---

## FAQ

### Q: Can I use both shortcut and full syntax?

**A**: Yes! They work identically:
```bash
add task "Title"              # Shortcut
add --tag task --topic "Title"  # Full syntax
```

### Q: How do I add a custom shortcut?

**A**: Edit `config/shortcuts.yaml` and add your shortcut to the list.

### Q: Will shortcuts break existing scripts?

**A**: No. Scripts using full syntax continue to work unchanged.

### Q: Can I disable shortcuts?

**A**: Yes. Use the full `--tag` syntax, which bypasses shortcut expansion.

### Q: What if my shortcut conflicts with a flag?

**A**: Shortcuts must not start with `--`. The parser detects flags first.

### Q: How do I see all available shortcuts?

**A**: Check `config/shortcuts.yaml` or run:
```bash
cat config/shortcuts.yaml
```

---

## License

[Your License Here]

---

## Credits

**Design & Implementation**: CLI Harmonization Project (2026)  
**Tools**: Manifest Manager v3.4+, Smart Scheduler v2.0  
**Technology**: Python 3.8+, lxml, pytest

---

## Support

**Documentation**: See `docs/` directory
- `API.md` - Complete API reference
- `CHEATSHEET.md` - Quick command reference
- `PHASE_1_REFLECTION.md` - Implementation notes

**Issues**: [GitHub Issues]  
**Discussions**: [GitHub Discussions]

---

*Last updated: February 2026*
