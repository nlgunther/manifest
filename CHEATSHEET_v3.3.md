# Manifest Manager v3.3 - Quick Reference

## 🆕 New in v3.3

| Feature | Command | Description |
|---------|---------|-------------|
| **Auto-create sidecar** | `load file.xml --autosc` | Create ID index on load |
| **Edit by ID** | `edit a3f7b2c1 --topic "New"` | Fast O(1) lookup |
| **Smart detection** | `edit <id_or_xpath> ...` | Auto-detects ID vs XPath |
| **Prominent IDs** | `find abc` | IDs shown first |
| **Config files** | `myfile.xml.config` | Per-file settings |

---

## 📂 File Management

| Command | Example | Description |
|---------|---------|-------------|
| **load** | `load myfile.xml` | Open or create file |
| **load + sidecar** | `load myfile.xml --autosc` | Create ID index |
| **rebuild sidecar** | `load myfile.xml --rebuildsc` | Force rebuild index |
| **save** | `save` | Save changes |
| **save as** | `save backup.7z` | Save with encryption |
| **merge** | `merge other.xml` | Import from file |

---

## ➕ Adding Items

| Scenario | Command |
|----------|---------|
| **Simple task** | `add --tag task "Description"` |
| **With topic** | `add --tag task --topic "Title" "Body text"` |
| **With status** | `add --tag task --status active --topic "Task"` |
| **Custom ID** | `add --tag task --id BUG-123 --topic "Bug"` |
| **No auto-ID** | `add --tag note --id False "Quick note"` |
| **In project** | `add --tag task --parent "//project[@id='abc']" "Task"` |
| **With attributes** | `add --tag task -a priority=high -a due=2026-02-01 "Task"` |

---

## ✏️ Editing Items

### By ID (NEW in v3.3 - Fast!)

| Command | Description |
|---------|-------------|
| `edit a3f7b2c1 --topic "Updated"` | Auto-detected ID |
| `edit a3f7b2c1 --status done` | Mark as done |
| `edit a3f7b2c1 --text "New body"` | Update text |
| `edit --id BUG-123 --topic "Fixed"` | Custom ID (explicit) |
| `edit a3f7b2c1 --delete` | Delete by ID |

### By XPath (Still works!)

| Command | Description |
|---------|-------------|
| `edit "//task[@topic='Old']" --topic "New"` | By XPath |
| `edit "//*[@status='pending']" --status active` | Batch update |
| `edit --xpath "//task[1]" --delete` | Force XPath mode |

---

## 🔍 Searching & Viewing

### Find by ID

```bash
# Quick lookup (flat)
find abc
  ID: abc123
     Path: /project[@id='abc123']
     Topic: Website
     Status: active

# With tree view
find abc --tree
────────────────────────────────────────
Match 1: /project[@id='abc123']
────────────────────────────────────────
## Website
  - **Design**: Mockups
  - **Development**: Backend

# Limit depth
find abc --tree --depth 2
```

### List

| Command | Description |
|---------|-------------|
| `list` | Show all (tree view) |
| `list --depth 2` | Top 2 levels only |
| `list --style table` | Table view |
| `list "//task"` | Filter by XPath |
| `list "//task[@status='active']"` | Active tasks |

---

## 🆔 ID Management

| Command | Description |
|---------|-------------|
| **find <prefix>** | Search by ID prefix (flat) |
| **find <prefix> --tree** | Show full subtrees |
| **find <prefix> --tree --depth N** | Limit depth |
| **autoid** | Add IDs to elements without them |
| **autoid --overwrite** | Replace all IDs |

**Auto-Generated IDs:**
- Format: 8-char hex (e.g., `a3f7b2c1`)
- Collision risk: ~1 in 4 billion
- Override: `--id CUSTOM` or `--id False`

---

## ⚙️ Configuration

### Config File Locations

```
myfile.xml.config          # Per-file (highest priority)
~/.config/manifest/config.yaml  # Global (Unix)
%APPDATA%\manifest\config.yaml  # Global (Windows)
```

### Common Settings

```yaml
# myfile.xml.config

sidecar:
  corruption_handling: warn_and_ask  # silent | warn_and_proceed | warn_and_ask
  auto_rebuild: false
  enabled: true

display:
  show_ids_prominently: true
  id_first: true
```

---

## 🔍 XPath Examples

| Selector | Meaning |
|----------|---------|
| `/*` | All top-level items |
| `//task` | All tasks anywhere |
| `//project/task` | Tasks directly in projects |
| `//*[@status='active']` | Any active item |
| `//*[@id='a3f7b2c1']` | Element with specific ID |
| `//task[@priority='high']` | High priority tasks |
| `//task[contains(@topic,'urgent')]` | Search by topic |

---

## 🎯 Common Workflows

### Quick Task Management

```bash
# Add task with auto-ID
add --tag task --topic "Fix bug" --status active

# Find it
find <first_3_chars_of_id>

# Edit it
edit <id> --status done

# View all active
list "//*[@status='active']"
```

### Project Organization

```bash
# Create project
add --tag project --topic "Q1 Goals"

# Add tasks to project
add --tag task --parent "//project[@topic='Q1 Goals']" "Task 1"
add --tag task --parent "//project[@topic='Q1 Goals']" "Task 2"

# View project tree
find <project_id> --tree
```

### Batch Updates

```bash
# Mark all pending as active
edit "//*[@status='pending']" --status active

# Delete completed tasks
edit "//*[@status='done']" --delete

# Add priority to all active tasks
edit "//*[@status='active']" -a priority=high
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Sidecar corrupted** | `load file.xml --rebuildsc` |
| **ID not found** | Rebuild: `load file.xml --rebuildsc` |
| **Config not applied** | Check file: `cat myfile.xml.config` |
| **Slow ID lookups** | Create sidecar: `load file.xml --autosc` |

---

## 🔐 Security

| Command | Description |
|---------|-------------|
| `save secure.7z` | Save with password (prompted) |
| `load secure.7z` | Load encrypted (prompted) |
| `save new_backup.7z` | Change password |

**Password Requirements:**
- AES-256 encryption
- Passwords never stored
- Re-prompted on load

---

## ⌨️ Tips & Tricks

1. **Copy IDs easily**: `find abc` shows ID first for copy/paste
2. **Use short prefixes**: `find a3f` instead of full `a3f7b2c1`
3. **Smart editing**: Just type the ID, no XPath needed
4. **Auto-sidecar**: Add `--autosc` to first load, then forget about it
5. **Depth limiting**: Use `--depth 2` for quick overviews
6. **Config once**: Set per-file config for project-specific behavior

---

## 📚 Full Documentation

- **Complete Guide**: `DOCUMENTATION_v3.3.md`
- **API Reference**: `API.md`
- **Architecture**: See code comments and EXTENSION STUB markers
- **Migration**: See DOCUMENTATION_v3.3.md § Migration

---

**Version:** 3.3.0  
**Updated:** January 2026
