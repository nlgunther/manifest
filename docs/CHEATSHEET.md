# Manifest Manager Cheatsheet

**Version**: 3.5.0 | **Quick Reference Guide**

---

## 🚀 Shortcut Syntax (v3.5+)

### Basic Pattern

```bash
add <shortcut> "Title" [--flags]
```

**Rule**: Title must come immediately after the shortcut noun.

```bash
✅ add task "Title" --status active    # Correct
❌ add task --status active "Title"    # Wrong (title becomes body)
```

### Common Shortcuts

```bash
add task "Buy milk"
add project "Q1 Goals"
add location "Conference Room A"
add note "Remember to..."
add milestone "v1.0 Release"
add idea "Feature: Dark mode"
```

### With Flags

```bash
add task "Review PR" --status active
add task "Deploy" --assignee alice --due 2026-03-15
add project "Website" --status planning --assignee bob
add location "Room 203" --parent "//building[@name='HQ']"
```

---

## 📝 Full Syntax (Always Works)

```bash
# Traditional format
add --tag task --topic "Buy milk"
add --tag project --title "Q1 Goals" --status planning
add --tag item --topic "Chair" --parent a3f7
```

**Note**: Use `--topic` or `--title` (they're aliases)

---

## 🔍 Finding Nodes

### By XPath

```bash
find //task
find "//task[@status='active']"
find "//project[@title='Website']//task"
```

### By ID

```bash
find a3f7b2c1              # Full ID
find a3f7                  # Prefix (shows selection if multiple)
```

### With View Formats

```bash
find //task --view tree    # Hierarchical (default)
find //task --view table   # Tabular
find //task --view compact # Minimal
```

---

## ✏️ Editing Nodes

### By ID

```bash
edit a3f7 --status done
edit a3f7 --status done --assignee charlie
edit a3f7 --clear-due      # Remove attribute
```

### By XPath

```bash
edit "//task[@title='Review']" --status in_progress
```

---

## 📂 File Operations

### Load

```bash
load project.xml
load project.xml --autosc  # Auto-save on changes
load backup.7z             # Encrypted (prompts for password)
```

### Save

```bash
save                       # Save to current file
save backup.xml            # Save as new file
save backup.7z             # Encrypt with password
```

### List

```bash
list                       # Tree view (default)
list --view table          # Table view
list --view compact        # Compact view
```

---

## 🗑️ Deleting

```bash
delete a3f7
delete "//task[@status='cancelled']"
```

---

## 🎯 Common Workflows

### Create Task Hierarchy

```bash
# Create project
add project "Website Redesign" --status planning

# Add tasks (get project ID, e.g., a3f7)
find //project

# Add tasks under project
add task "Design mockups" --parent a3f7 --assignee alice
add task "Implement frontend" --parent a3f7 --assignee bob
add task "Write tests" --parent a3f7 --assignee charlie
```

### Track Progress

```bash
# Find active tasks
find "//task[@status='active']"

# Complete a task
edit a3f7 --status done

# Reassign a task
edit b2c8 --assignee new_person
```

### Add Location Hierarchy

```bash
# Building
add location "Main Office"

# Rooms (get building ID, e.g., d4e9)
add location "Conference Room A" --parent d4e9
add location "Conference Room B" --parent d4e9
add location "Storage" --parent d4e9
```

---

## 🏷️ Attributes Reference

### Standard Attributes

| Attribute     | Shortcut | Full         | Aliases   | Example             |
| ------------- | -------- | ------------ | --------- | ------------------- |
| **Title**     | Yes      | `--topic`    | `--title` | `--topic "My Task"` |
| **Status**    | No       | `--status`   | -         | `--status active`   |
| **Assignee**  | No       | `--assignee` | `--resp`  | `--assignee alice`  |
| **Due Date**  | No       | `--due`      | -         | `--due 2026-03-15`  |
| **Parent**    | No       | `--parent`   | -         | `--parent a3f7`     |
| **Custom ID** | No       | `--id`       | -         | `--id custom123`    |

### Custom Attributes

```bash
# Use -a or --attr (repeatable)
add task "Deploy" -a priority=high -a team=backend
add task "Review" --attr severity=critical --attr platform=web
```

---

## 🔧 ID Shortcuts

### Full ID

```bash
edit a3f7b2c1 --status done    # Exact match
```

### ID Prefix

```bash
edit a3f --status done         # Prefix match
# If multiple matches:
#   [1] a3f7b2c1 - Task: Review PR
#   [2] a3f9d4e2 - Task: Update docs
#   Select: 1
```

### Disable Auto-ID

```bash
add task "No ID" --id False
```

### Custom ID

```bash
add task "Custom" --id my-custom-id
```

---

## 🎨 View Formats

### Tree View (Default)

```bash
list
# Output:
# ├── project: Website
# │   ├── task: Design
# │   └── task: Code
```

### Table View

```bash
list --view table
# Output:
# ID       | Tag     | Title    | Status
# ---------|---------|----------|--------
# a3f7b2c1 | task    | Design   | active
# b8d4e9f2 | task    | Code     | pending
```

### Compact View

```bash
list --view compact
# Output:
# a3f7: task "Design" [active]
# b8d4: task "Code" [pending]
```

---

## 🔒 Advanced Features

### Wrap Nodes

```bash
# Wrap all top-level nodes under new parent
wrap --tag archive --topic "2025 Archive"
```

### Merge Files

```bash
merge other.xml                    # Default: union strategy
merge backup.xml --strategy source_wins
```

### Rebuild Sidecar

```bash
rebuild                            # After manual XML edits
```

### Toggle Auto-ID

```bash
autoid on                          # Enable (default)
autoid off                         # Disable
```

---

## 📋 XPath Quick Reference

### Basic Selectors

```bash
//task                     # All tasks
//project                  # All projects
//*                        # All nodes
```

### Attribute Filters

```bash
//task[@status='active']              # Status equals
//task[@assignee='alice']             # Assignee equals
//project[@title='Website']           # Title equals
```

### Nested Selection

```bash
//project//task                       # Tasks inside projects
//project[@title='Website']//task     # Tasks in specific project
```

### Multiple Conditions

```bash
//task[@status='active'][@assignee='alice']     # AND
//task[@status='active' or @status='pending']   # OR
```

---

## ⚙️ Configuration

### Shortcuts Config

**File**: `config/shortcuts.yaml`

```yaml
shortcuts:
  - task
  - project
  - location
  - your_custom      # Add here!

reserved_keywords:
  - help
  - exit
  # Never add "add"!
```

### Add Custom Shortcut

1. Edit `config/shortcuts.yaml`
2. Add shortcut to list
3. Reload shell: `exit` then `manifest`
4. Use: `add your_custom "Title"`

---

## 🐛 Troubleshooting

### Shortcut Not Working

```bash
# Check config
cat config/shortcuts.yaml

# Verify shortcut is listed
# Reload shell
exit
manifest
```

### Module Not Found

```bash
# Reinstall
pip install -e .
```

### Lock Timeout

```
# Another process is using the file
# Wait or kill the other process
```

### XPath Syntax Error

```bash
# ❌ Wrong (missing quotes)
find //task[@status=active]

# ✅ Correct
find "//task[@status='active']"
```

---

## 💡 Tips & Tricks

### 1. Use ID Prefixes

```bash
# Instead of typing full ID
edit a3f7b2c1

# Just type prefix
edit a3f
```

### 2. Combine Shortcuts with Flags

```bash
# Shortcut + multiple flags
add task "Important" --status active --assignee alice --due 2026-03-15
```

### 3. Use Auto-Save

```bash
# Load with auto-save
load project.xml --autosc

# Every change saves automatically
add task "Auto-saved"
```

### 4. Batch Operations

```bash
# Use shell loops
for name in Alice Bob Charlie; do
    add task "Review for $name" --assignee $name
done
```

### 5. Complex XPath Queries

```bash
# Find all active tasks assigned to Alice
find "//task[@status='active'][@assignee='alice']"

# Find all tasks in Website project
find "//project[@title='Website']//task"
```

---

## 📊 Default Shortcuts

| Shortcut    | Use Case        | Example                    |
| ----------- | --------------- | -------------------------- |
| `task`      | Tasks/todos     | `add task "Review PR"`     |
| `project`   | Projects        | `add project "Q1 Goals"`   |
| `item`      | Generic items   | `add item "Office chair"`  |
| `note`      | Notes/reminders | `add note "Call client"`   |
| `milestone` | Milestones      | `add milestone "v1.0"`     |
| `idea`      | Ideas           | `add idea "Dark mode"`     |
| `location`  | Places          | `add location "Room 203"`  |
| `contact`   | People          | `add contact "John Doe"`   |
| `reference` | Links/docs      | `add reference "API docs"` |

---

## 🎓 Learning Path

### Beginner

1. Load a file: `load test.xml`
2. Add items: `add task "My First Task"`
3. List items: `list`
4. Save: `save`

### Intermediate

1. Use shortcuts with flags: `add task "Task" --status active`
2. Edit by ID prefix: `edit a3f --status done`
3. Find with XPath: `find "//task[@status='active']"`
4. Use custom attributes: `add task "Task" -a priority=high`

### Advanced

1. Complex XPath: `find "//project[@status='planning']//task[@assignee='alice']"`
2. Wrap operations: `wrap --tag archive --topic "Old"`
3. Merge files: `merge backup.xml`
4. Custom shortcuts: Edit `config/shortcuts.yaml`

---

## 📞 Quick Help

### In Shell

```bash
help                    # List all commands
help add                # Help for specific command
cheatsheet              # Show this cheatsheet
```

### Documentation

- `README.md` - Full project documentation
- `API.md` - Complete API reference
- `TEST_PHASE3_GUIDE.md` - Testing guide

---

## 🔑 Keyboard Shortcuts

| Key      | Action                            |
| -------- | --------------------------------- |
| `↑`      | Previous command                  |
| `↓`      | Next command                      |
| `Tab`    | Command completion (if supported) |
| `Ctrl+C` | Cancel current command            |
| `Ctrl+D` | Exit shell                        |

---

## ✅ Checklist for New Users

- [ ] Install: `pip install -e .`
- [ ] Load file: `load test.xml`
- [ ] Try shortcut: `add task "Test"`
- [ ] List items: `list`
- [ ] Edit item: `edit <id> --status done`
- [ ] Save: `save`
- [ ] Add custom shortcut to config
- [ ] Read full docs: `README.md`, `API.md`

---

**Last Updated**: February 2026 | **Version**: 3.5.0

*Print this page for quick reference!*
