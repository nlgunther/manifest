# Manifest Manager v3.4 Cheatsheet

**Quick Reference Guide** | Last Updated: January 2026

---

## Quick Start

```bash
# Launch shell
manifest

# Load manifest with ID sidecar
(manifest) load myproject.xml --autosc

# Add task
(myproject.xml) add --tag task --topic "New feature" --status active --resp alice

# Find by ID prefix
(myproject.xml) find a3f

# Edit task
(myproject.xml) edit a3f --status done

# Save
(myproject.xml) save
```

---

## File Operations

### Load Files

```bash
# Create new or load existing
load myproject.xml

# Load with auto-create ID sidecar (recommended)
load myproject.xml --autosc

# Load encrypted file
load backup.7z
# (prompts for password)

# Explicit password
load backup.7z --password mysecret
```

### Save Files

```bash
# Save to current file
save

# Save to new file
save newproject.xml

# Save encrypted backup
save backup.7z
# (prompts for password)

# Check save status
# Prompt shows [*] if unsaved changes
(myproject.xml*) save  # * indicates unsaved
```

### Merge Files

```bash
# Import all nodes from another manifest
merge teamproject.xml

# Merge encrypted file
merge backup.7z
# (prompts for password)
```

---

## Adding Nodes

### Basic Add

```bash
# Minimum: just tag
add --tag note

# With topic
add --tag task --topic "Review documentation"

# With all common attributes
add --tag task --topic "Review PR" --status active --resp alice
```

### Add with Parent

```bash
# Add to all top-level (default)
add --tag task --topic "New task"
# Equivalent to:
add --tag task --topic "New task" --parent "/*"

# Add inside specific project
add --tag task --topic "Subtask" --parent "//project[@topic='Website']"

# Add to first project only
add --tag task --topic "Subtask" --parent "//project[1]"
```

### Custom Attributes

```bash
# Single custom attribute
add --tag task --topic "API work" -a priority=high

# Multiple custom attributes
add --tag task --topic "Bug fix" -a priority=critical -a estimate=4h -a sprint=23

# Custom ID (instead of auto-generated)
add --tag task --topic "Known ID" --id FEATURE-123

# Disable auto-ID
add --tag task --topic "No ID" --id False
```

### With Text Content

```bash
# Text content at end
add --tag note --topic "Meeting notes" "Discussed Q1 roadmap and priorities"

# Multi-line text (use quotes)
add --tag note --topic "Summary" "Line 1
Line 2
Line 3"
```

### Status Values

```bash
# Valid status values
--status active      # Currently being worked on
--status done        # Completed
--status pending     # Waiting to start
--status blocked     # Blocked by dependencies
--status cancelled   # No longer needed
```

---

## Editing Nodes

### Edit by ID Prefix

```bash
# Single match - applies automatically
edit a3f --status done

# Multiple matches - interactive selection
edit a3f --delete
# Shows:
# Multiple IDs match 'a3f':
#   [1] a3f7b2c1 [active] - Review PR
#   [2] a3f8d9e2 [pending] - Deploy
# Select [1-2] or 'c' to cancel:

# Full ID (always exact match)
edit a3f7b2c1 --resp bob
```

### Edit by XPath

```bash
# Single element
edit "//task[@id='a3f7b2c1']" --status done

# Multiple elements
edit "//task[@status='active']" --status pending

# With predicate
edit "//task[contains(@topic,'bug')]" --resp alice
```

### Force Interpretation

```bash
# Force ID interpretation (when ambiguous)
edit --id a3f --status done

# Force XPath interpretation
edit --xpath a3f --delete
# Interprets "a3f" as XPath, not ID
```

### Update Operations

```bash
# Update topic
edit a3f --topic "New title"

# Update status
edit a3f --status done

# Update responsible party
edit a3f --resp bob

# Update text content
edit a3f --text "New description"

# Update custom attribute
edit a3f -a priority=high

# Multiple updates at once
edit a3f --status done --resp alice -a completed=$(date +%Y-%m-%d)
```

### Delete Operations

```bash
# Delete by ID
edit a3f --delete

# Delete by XPath
edit "//task[@status='cancelled']" --delete

# Interactive confirmation on delete
# Shows element details before deleting
```

---

## Searching & Viewing

### Find by ID

```bash
# Find by prefix (shows summary)
find a3f

# Find with full subtree
find a3f --tree

# Find with depth limit
find a3f --tree --depth 2

# Output format:
# Found 2 element(s) matching 'a3f':
# 
#   [1] a3f7b2c1
#       Tag: task
#       Topic: Review PR
#       Status: active
#       Resp: alice
```

### List Elements

```bash
# List all top-level elements
list

# List by XPath
list "//task"

# List active tasks
list "//task[@status='active']"

# List by ID prefix (v3.4)
list a3f

# List with different styles
list --style tree    # Hierarchical (default)
list --style table   # Tabular

# Limit depth
list --depth 2       # Only 2 levels deep
list --depth 1       # Top level only

# Combine options
list "//project" --style table --depth 3
```

### View Formats

**Tree View** (default):
```
## Project Alpha

  [ ] (active) @alice **Design mockups**: Create wireframes [id=a3f7b2c1]
  [x] **Research**: Completed [id=b5e8d9a2]
    - **Note**: Found 3 alternatives [id=c9d4e1f7]
```

**Table View**:
```
Topic                | Tag      | Status  | Resp
--------------------|----------|---------|-------
Design mockups      | task     | active  | alice
Research            | task     | done    | -
Note                | note     | -       | -
```

---

## XPath Quick Reference

### Basic Patterns

```bash
# All direct children of root
list "/*"
list "/manifest/*"  # Explicit root

# All elements of type
list "//task"       # All tasks anywhere
list "//project"    # All projects anywhere

# First/last element
list "//task[1]"        # First task
list "//task[last()]"   # Last task
list "//project[2]"     # Second project
```

### Attribute Filters

```bash
# Has attribute
list "//task[@status]"           # Tasks with any status
list "//*[@topic]"                # Any element with topic

# Attribute equals value
list "//task[@status='done']"    # Done tasks
list "//task[@resp='alice']"     # Alice's tasks
list "//*[@id='a3f7b2c1']"       # Specific ID

# Attribute not equals
list "//task[@status!='done']"   # Not done

# Multiple conditions (AND)
list "//task[@status='active'][@resp='alice']"  # Active tasks assigned to Alice
```

### Text Content

```bash
# Contains text
list "//task[contains(@topic,'bug')]"           # Topic contains "bug"
list "//*[contains(@topic,'review')]"           # Any element, topic contains "review"

# Starts with
list "//task[starts-with(@topic,'Fix')]"        # Topic starts with "Fix"

# Text content
list "//note[contains(text(),'important')]"     # Text contains "important"
```

### Hierarchy

```bash
# Direct children
list "//project/task"            # Tasks directly under projects

# Descendants
list "//project//task"           # Tasks anywhere under projects

# Parent
list "//task[@id='a3f']/.."      # Parent of specific task

# Siblings
list "//task[@id='a3f']/following-sibling::*"  # Following siblings
list "//task[@id='a3f']/preceding-sibling::*"  # Preceding siblings
```

### Complex Queries

```bash
# OR conditions
list "//task[@status='active' or @status='pending']"

# AND conditions
list "//task[@status='active' and @resp='alice']"

# Negation
list "//task[not(@status='done')]"               # Not done
list "//task[not(@resp)]"                        # No assignee

# Position
list "//project[position() < 3]"                 # First 2 projects
list "//task[position() > 1]"                    # All but first task

# Count
list "//project[count(task) > 5]"                # Projects with >5 tasks
```

---

## ID Management

### Auto-ID Generation

```bash
# Auto-generate IDs (default)
add --tag task --topic "New task"
# Creates ID like: a3f7b2c1

# Disable auto-ID for specific add
add --tag note --topic "Temp" --id False

# Custom ID
add --tag task --topic "Known" --id FEATURE-123
```

### Add IDs to Existing Elements

```bash
# Add IDs to all elements without them
autoid

# Replace ALL IDs (regenerate)
autoid --overwrite

# Dry run (show what would be added)
autoid --dry-run
```

### Sidecar Management

```bash
# Rebuild sidecar from XML
rebuild

# When to use:
# - After manual XML editing
# - If sidecar out of sync
# - After importing/merging
# - If find/edit by ID not working
```

---

## Structure Operations

### Wrap Content

```bash
# Wrap all top-level nodes under new container
wrap --root archive

# Before:
# <manifest>
#   <task/>
#   <task/>
# </manifest>

# After:
# <manifest>
#   <archive>
#     <task/>
#     <task/>
#   </archive>
# </manifest>

# Use case: Archive old content
wrap --root "archive-2025"
add --tag project --topic "New project for 2026"
```

---

## Configuration

### Configuration Files

**Global**: `~/.config/manifest/config.yaml`
```yaml
auto_id: true
default_view_style: tree
max_password_attempts: 3

sidecar:
  enabled: true
  auto_rebuild: false

display:
  show_ids: true
  tree_indent: 2
```

**Per-file**: `myproject.xml.config`
```yaml
# Overrides global settings for this file
default_view_style: table
display:
  max_depth: 3
```

### Environment Variables

```bash
# Override config directory
export MANIFEST_CONFIG_DIR="$HOME/.manifest"

# Disable sidecar globally
export MANIFEST_NO_SIDECAR=1
```

---

## Keyboard Shortcuts & Shell Commands

### In Shell

```bash
# Command history
↑ ↓              # Navigate history
Ctrl+R           # Search history

# Line editing
Ctrl+A           # Start of line
Ctrl+E           # End of line
Ctrl+U           # Clear line
Ctrl+W           # Delete word

# Shell commands
help             # List commands
help add         # Help for specific command
cheatsheet       # Show this reference
exit             # Quit (warns if unsaved)
Ctrl+D           # Also exits
```

### Tab Completion

```bash
# Command completion
li<TAB>          # Completes to "list"
ed<TAB>          # Completes to "edit"

# File completion
load pro<TAB>    # Completes filename
```

---

## Common Workflows

### Daily Task Management

```bash
# Morning: load and review
load tasks.xml --autosc
list "//task[@status='active']"

# Add new task
add --tag task --topic "Review PRs" --status active --resp me

# Mark task done
find revi  # Find "Review PRs"
edit <id> --status done

# End of day: save
save
```

### Project Setup

```bash
# Create new project
load project.xml --autosc
add --tag project --topic "Q1 Goals"

# Add tasks to project
add --tag task --topic "Task 1" --parent "//project[@topic='Q1 Goals']"
add --tag task --topic "Task 2" --parent "//project[@topic='Q1 Goals']"

# View structure
list --depth 2

# Save
save
```

### Weekly Review

```bash
# Load project
load project.xml --autosc

# See all active work
list "//task[@status='active']" --style table

# See completed work
list "//task[@status='done']" --style table

# Archive completed
wrap --root "completed-$(date +%Y-W%V)"
save "archive/project-$(date +%Y%m%d).xml"
```

### Team Handoff

```bash
# Reassign tasks
edit "//task[@resp='alice'][@status='active']" --resp bob

# Add notes
add --tag note --topic "Handoff notes" "Bob taking over Alice's tasks"

# Create snapshot
save "handoff-$(date +%Y%m%d).xml"

# Create encrypted backup
save "handoff-$(date +%Y%m%d).7z"
```

### Batch Updates

```bash
# Update all pending to active
edit "//task[@status='pending']" --status active

# Add sprint to all active tasks
edit "//task[@status='active']" -a sprint=23

# Reassign all unassigned
edit "//task[not(@resp)]" --resp unassigned
```

---

## Tips & Tricks

### Efficiency Tips

1. **Use ID prefixes** - Type `a3f` instead of `a3f7b2c1`
2. **Enable sidecar** - Use `--autosc` for O(1) ID lookups
3. **Use find first** - Find ID, then edit: `find desc → edit a3f`
4. **Batch operations** - Edit multiple with XPath
5. **Aliases** - Create shell aliases: `alias m='manifest'`

### Best Practices

1. **Always use --autosc** when loading
2. **Save often** - Especially before risky operations
3. **Use statuses** - Keep tasks organized
4. **Assign responsibilities** - Use `--resp` for accountability
5. **Regular backups** - Use encrypted `.7z` files
6. **Use transactions** - Batch operations are safer

### Power User Tricks

```bash
# Copy task to new project
# (find, copy attributes, add to new parent)
find <id>
add --tag task --topic "Same task" --parent "//project[2]"

# Bulk import from file
# (create script, use shell redirection)
echo "add --tag task --topic 'Task 1'
add --tag task --topic 'Task 2'
save" | manifest

# Template projects
# (save empty structure, merge when needed)
save template-project.xml
# Later: load new.xml → merge template-project.xml

# Query stats
list "//task[@status='done']" | wc -l  # Count done tasks
```

---

## Troubleshooting

### Common Issues

**Problem**: "No file loaded"
```bash
# Solution: Load a file first
load myproject.xml
```

**Problem**: "ID not found: a3f"
```bash
# Solution: Sidecar out of sync
rebuild
find a3f
```

**Problem**: XPath returns nothing
```bash
# Debug: Check structure first
list
# Check attributes
list "/*"
# Verify syntax
list "//task"  # NOT "/task" (missing //)
```

**Problem**: "Multiple IDs match"
```bash
# Solution: Use more characters
edit a3f7 --status done  # Instead of a3f

# Or: Use interactive selection
edit a3f --status done
# Select from menu
```

**Problem**: Can't load encrypted file
```bash
# Solution: Check password, verify file
7z t backup.7z  # Test archive
# If corrupt, restore from earlier backup
```

### Performance Issues

**Slow operations on large files:**
```bash
# Enable sidecar if not already
load large.xml --autosc

# Use ID operations instead of XPath
edit a3f --status done  # Fast (O(1))
# NOT: edit "//task[@id='a3f7b2c1']"  # Slow (O(n))

# Limit depth when listing
list --depth 2

# Consider splitting into multiple files
# Save subprojects separately
```

### Recovery

**Unsaved changes lost:**
```bash
# Prevention: Save often!
# Shell shows [*] when unsaved

# Recovery: Check backups
ls -lt *.xml *.7z
# Look for autosaves (if enabled in config)
```

**Corrupted file:**
```bash
# Try loading with error recovery
load corrupt.xml --force-load

# If fails, restore from backup
load backup-20260120.7z
save recovered.xml
```

---

## Examples by Use Case

### Software Development

```bash
# Bug tracking
add --tag bug --topic "Login fails on Safari" --status active -a severity=high
edit <id> --resp alice -a due=2026-02-01

# Feature planning
add --tag feature --topic "Dark mode" --status pending -a estimate=40h

# Sprint management
edit "//task[@status='pending']" -a sprint=23 --status active
list "//task[@sprint='23'][@status='active']"
```

### Project Management

```bash
# Milestone tracking
add --tag milestone --topic "Beta Release" -a date=2026-03-01
add --tag task --topic "Feature complete" --parent "//milestone[last()]"

# Resource allocation
list "//task[@resp='alice'][@status='active']"
edit "//task[@resp='alice'][1]" --resp bob  # Reassign

# Status reporting
list "//task[@status='done']" --style table
```

### Personal Task Management

```bash
# Daily todos
add --tag todo --topic "Buy groceries" --status pending
add --tag todo --topic "Call dentist" --status active

# Weekly review
list "//todo[@status='done']"
wrap --root "completed-$(date +%V)"

# Recurring tasks (template)
save weekly-template.xml
# Each week: load new.xml → merge weekly-template.xml
```

### Documentation Tracking

```bash
# Documentation tasks
add --tag doc --topic "API Reference" --status active -a pages=50
add --tag doc --topic "User Guide" --status pending

# Track progress
edit <id> -a progress=80%
list "//doc" --style table
```

---

## Glossary

| Term | Definition |
|------|------------|
| **Element** | Node in XML tree (task, project, note, etc.) |
| **Attribute** | Key-value pair on element (topic, status, id, etc.) |
| **ID** | Unique 8-character hex identifier (a3f7b2c1) |
| **Sidecar** | Companion file (.xml.ids) for O(1) ID lookups |
| **XPath** | Query language for XML (//, @, [], etc.) |
| **Prefix** | First 3-8 characters of ID for matching |
| **Repository** | Internal data structure managing XML |
| **Transaction** | Atomic operation with rollback on error |
| **Resp** | Responsible party (assignee) |

---

## Cheat Sheet Summary Card

```
┌─────────────────────────────────────────────────────────────┐
│              MANIFEST MANAGER QUICK REFERENCE                │
├─────────────────────────────────────────────────────────────┤
│ LOAD       load file.xml --autosc                           │
│ SAVE       save                                              │
│ ADD        add --tag task --topic "Title" --status active   │
│ FIND       find a3f                                          │
│ EDIT       edit a3f --status done                           │
│ LIST       list "//task[@status='active']"                  │
│ DELETE     edit a3f --delete                                │
│ REBUILD    rebuild                                           │
│ HELP       help | cheatsheet | exit                         │
├─────────────────────────────────────────────────────────────┤
│ STATUSES   active | done | pending | blocked | cancelled    │
│ ID FORMAT  8-char hex: a3f7b2c1                             │
│ PREFIX     First 3-8 chars: a3f matches a3f7b2c1            │
│ XPATH      //task[@status='active'][@resp='alice']          │
├─────────────────────────────────────────────────────────────┤
│ TIP: Always use --autosc for fast ID lookups                │
│ TIP: Use ID prefixes to save typing                         │
│ TIP: Save often, backup with .7z encryption                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Version History

### v3.4 (Current)
- ✨ ID prefix matching in `list` command
- ✨ `resp` attribute for responsibility tracking
- ✨ Factory method pattern for NodeSpec
- 🐛 Fixed ID detection edge cases

### v3.3
- ✨ ID sidecar for O(1) lookups
- ✨ Smart ID vs XPath detection
- ✨ `find` command with prefix matching

### v3.2
- ✨ Transaction support
- ✨ 7z encryption
- ✨ `wrap` command

---

**Print this page and keep it handy!**

For detailed API documentation, see [API.md](API.md)  
For comprehensive guide, see [README.md](README.md)  
For code review, see [MANIFEST_MANAGER_COMPREHENSIVE_REVIEW.md](MANIFEST_MANAGER_COMPREHENSIVE_REVIEW.md)

**Version:** 3.4.0 | **Updated:** January 2026
