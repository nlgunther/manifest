# Manifest Manager v3.0

**Manifest Manager** is a professional-grade, transactional Command Line Interface (CLI) for managing hierarchical data structures. It is designed for developers and power users who need a robust tool for task management, project planning, inventories, or complex configuration management without the overhead of a database server.

It persists data in standard **XML** for portability but adds a layer of safety, encryption, and convenience found in modern applications.

## 🚀 Key Features

### 🛡️ Robust & Safe

* **Atomic Transactions:** Every modification (add, edit, wrap, merge) is wrapped in a transaction. If a command fails or invalidates the schema, the state rolls back instantly. Your data never gets corrupted.
* **Path & Tag Validation:** Rigorous sanitization prevents path injection attacks and ensures generated XML is valid.
* **Zero-Knowledge Encryption:** Native support for **AES-256** encrypted archives (`.7z`). Passwords are never stored on disk.

### ⚡ Powerful Editing

* **Batch Editing:** Use XPath to target multiple nodes at once (e.g., mark all "pending" tasks as "active").
* **Surgical Updates:** specific flags (`--text`, `--topic`, `--status`) let you modify just what you need without rewriting the whole node.

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
   (my_project.xml) add --tag task --parent "//project" --status active "Design Mockups"
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

5. **Secure & Save**
   
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

**License:** MIT
**Version:** 3.0.0
