# Manifest Manager Cheatsheet

## 📁 File Operations

| Action          | Command               |
|:--------------- |:--------------------- |
| **Open/Create** | `load <filename>`     |
| **Save**        | `save`                |
| **Save As**     | `save <new_filename>` |
| **Exit**        | `exit` or `Ctrl+D`    |

## ➕ Adding Items

*General Syntax:* `add --tag <TAG> --parent <XPATH> [options] "Content"`

| Goal                | Command                                                     |
|:------------------- |:----------------------------------------------------------- |
| **New Project**     | `add --tag project --topic "Work"`                          |
| **Task in Project** | `add --tag task --parent "//*[@topic='Work']" "Send Email"` |
| **With Attributes** | `add --tag item -a priority=high -a cost=50 "Tools"`        |

## ✏️ Editing Items

*General Syntax:* `edit --xpath <XPATH> [options]`

| Goal              | Command                                               |
|:----------------- |:----------------------------------------------------- |
| **Mark Done**     | `edit --xpath "//task[@topic='Email']" --status done` |
| **Change Text**   | `edit --xpath "//item[1]" --text "New Text"`          |
| **Add Attribute** | `edit --xpath "//task" --attr owner=Me`               |
| **Delete**        | `edit --xpath "//item[@status='cancelled']" --delete` |

## 🔍 Viewing Data

| Action            | Command                        |
|:----------------- |:------------------------------ |
| **Show All**      | `list`                         |
| **Show as Table** | `list --style table`           |
| **Filter**        | `list "//*[@status='active']"` |

## 💡 Tips

* **Case Sensitivity:** "Flexspend" is different from "flexspend". Use `list --style table` to see the exact casing stored in the file.
* **Quotes:** Always wrap text with spaces in quotes: `"My Topic"`.
* **Help:** Type `cheatsheet` or `cs` inside the tool.
