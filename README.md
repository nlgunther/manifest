# Manifest Manager v3.0

**Manifest Manager** is a professional-grade, transactional Command Line Interface (CLI) for managing hierarchical data structures. It is designed for developers and power users who need a robust tool for task management, project planning, inventories, or complex configuration management without the overhead of a database server.

It persists data in standard **XML** for portability but adds a layer of safety, encryption, and convenience found in modern applications.

## 🚀 Key Features

### 🛡️ Robust & Safe

* **Atomic Transactions:** Every modification (add, edit, wrap, merge) is wrapped in a transaction. If a command fails or invalidates the schema, the state rolls back instantly. Your data never gets corrupted.
* **Path & Tag Validation:** Rigorous sanitization prevents path injection attacks and ensures generated XML is valid.
* **Zero-Knowledge Encryption:** Native support for **AES-256** encrypted archives (`.7z`). Passwords are never stored on disk.
* **Auto-Generated IDs:** Every new element gets a unique 8-character ID (e.g., `a3f7b2c1`) for easy reference. Override with `--id custom` or disable with `--id False`.

### ⚡ Powerful Editing

* **Batch Editing:** Use XPath to target multiple nodes at once (e.g., mark all "pending" tasks as "active").
* **Surgical Updates:** specific flags (`--text`, `--topic`, `--status`) let you modify just what you need without rewriting the whole node.
* **ID-Based Search:** Find elements by ID prefix with `find abc` command.

### 🔗 Merge Capabilities

* **Import External Data:** Merge nodes from other files into your workspace.
* **Non-Destructive:** The merge strategy is **append-only**. No existing data is ever overwritten or deleted during a merge.

---

## 🏃‍♂️ Quick Start Guide

Once inside the `(manifest)` shell:

1. **Create a New File**
   
   ```text
   (manifest) load my_project
   ```

2. **Add Data**
   
   ```text
   (my_project.xml) add --tag project --topic "Website Redesign"
   Added node to 1 location(s).
   # Auto-generated ID: <project id="a3f7b2c1" topic="Website Redesign"/>
   
   (my_project.xml) add --tag task --parent "//project" --status active "Design Mockups"
   Added node to 1 location(s).
   # Auto-generated ID: <task id="b5e8d9a2" status="active">Design Mockups</task>
   
   # Use custom ID
   (my_project.xml) add --tag task --id BUG-123 --topic "Fix login bug"
   # Result: <task id="BUG-123" topic="Fix login bug"/>
   
   # Disable auto-ID
   (my_project.xml) add --tag note --id False "Quick note"
   # Result: <note>Quick note</note>
   ```

3. **Edit Data**
   
   * *Update Status:*
     
     ```text
     (my_project.xml) edit --xpath "//task[@status='active']" --status done
     ```
   
   * *Change Text:*
     
     ```text
     (my_project.xml) edit --xpath "//project" --topic "Global Redesign 2026"
     ```
   
   * *Delete Items:*
     
     ```text
     (my_project.xml) edit --xpath "//task[@status='cancelled']" --delete
     ```

4. **View Your Data**
   
   ```text
   (my_project.xml) list
   ```

5. **Search by ID**
   
   ```text
   (my_project.xml) find a3f
   Found 2 match(es)
     /project[@id='a3f7b2c1'] topic="Website Redesign"
     /task[@id='a3f8e1d4'] topic="Another task"
   
   # Add IDs to existing elements that lack them
   (my_project.xml) autoid
   Added/updated 15 ID(s)
   ```

6. **Secure & Save**
   
   ```text
   (my_project.xml) save secret_plans.7z
   Enter password for secret_plans.7z: *******
   ```

---

## 🤝 Merge Conventions

The `merge` command (`merge filename.xml`) follows a **Strict Append Strategy**:

1. **Scope:** It imports all **top-level children** from the source file's root.
2. **No Overwriting:** Existing nodes in your current file are **never** modified, replaced, or deleted.
3. **Duplicates:** Because it is an append operation, if the source file contains data identical to your current file, you will end up with duplicates.
   * *Recommendation:* Use `wrap` before merging to isolate imported data into its own container (e.g., `wrap --root existing_data` -> `merge new_data.xml`).

---

## 🆕 What's New in v3.3

### ID Sidecar for Fast Lookups

```text
(manifest) load myfile.xml --autosc
Creating ID sidecar...
```

Creates `myfile.xml.ids` for O(1) ID lookups.

### Smart Edit by ID

```text
(manifest) edit a3f7b2c1 --topic "Updated"
```

Auto-detects ID vs XPath - no XPath syntax needed!

### Configuration Files

Create `myfile.xml.config` or `~/.config/manifest/config.yaml` to customize behavior.

See DOCUMENTATION_v3.3.md for complete guide.

---

**License:** MIT
**Version:** 3.0.0
