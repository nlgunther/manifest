# Manifest Manager Cheatsheet

## 📁 File Operations

| Command     | Description                               | Example                    |
|:----------- |:----------------------------------------- |:-------------------------- |
| **load**    | Open or create a file.                    | `load my_data.xml`         |
| **save**    | Save changes.                             | `save`                     |
| **save as** | Save to a new file (supports encryption). | `save secure_backup.7z`    |
| **merge**   | Import items from another file.           | `merge colleague_work.xml` |
| **exit**    | Close the shell.                          | `exit`                     |

---

## 🏗️ Structure & Content

### Adding Nodes

**Syntax:** `add --tag <TAG> [options] "Body Text"`

| Scenario            | Command                                                             |
|:------------------- |:------------------------------------------------------------------- |
| **New Project**     | `add --tag project --topic "Q4 Goals"`                              |
| **Task in Project** | `add --tag task --parent "//project" "Write code"`                  |
| **Detailed Task**   | `add --tag task --status active --topic "Fix Bug" -a priority=high` |
| **Nested Item**     | `add --tag step --parent "//task[@topic='Fix Bug']" "Reproduce it"` |

### Editing Nodes

**Syntax:** `edit --xpath <XPATH> [options]`

| Scenario         | Command                                               |
|:---------------- |:----------------------------------------------------- |
| **Mark Done**    | `edit --xpath "//task[1]" --status done`              |
| **Rename Topic** | `edit --xpath "//project" --topic "Q1 Goals"`         |
| **Delete**       | `edit --xpath "//task[@status='cancelled']" --delete` |
| **Update Text**  | `edit --xpath "//note" --text "Updated content"`      |

### Reorganizing

| Command  | Description                                                                        |
|:-------- |:---------------------------------------------------------------------------------- |
| **wrap** | Moves all current top-level items into a new folder.<br>`wrap --root archive_2025` |

---

## 🔍 XPath Selectors (Querying)

Manifest Manager uses standard **XPath 1.0**.

| Selector                             | Meaning                               |
|:------------------------------------ |:------------------------------------- |
| `/*`                                 | All items at the top level.           |
| `//task`                             | Every `<task>` anywhere in the file.  |
| `//project/task`                     | Only tasks directly inside a project. |
| `//*[@status='active']`              | Any item marked as active.            |
| `//bug[@priority='high']`            | Bugs with high priority attribute.    |
| `//task[contains(@topic, 'Urgent')]` | Search by topic name.                 |

---

## 🚩 Status Flags

The built-in view recognizes these status codes:

* `active`
* `done` (Renders as `[x]`)
* `pending`
* `blocked`
* `cancelled`
