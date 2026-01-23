# Manifest Manager API Reference

The project follows a **Layered Architecture**:

1. **Presentation Layer (`manifest.py`):** CLI and User Input.
2. **Domain Layer (`manifest_core.py`):** Business Logic, Models, Validation.
3. **Data Layer (`storage.py`):** File I/O, Encryption, Compression.

---

## 1. Domain Layer (`manifest_core.py`)

### `ManifestRepository`

The primary entry point for manipulating the data tree.

* **`load(filepath, password=None) -> Result`**
  
  * Orchestrates loading data from storage and parsing it into `lxml.etree`.

* **`save(filepath=None, new_pass=None) -> Result`**
  
  * Serializes the DOM to bytes and delegates to `StorageManager`.

* **`add_node(parent_xpath, spec: NodeSpec) -> Result`**
  
  * **Transactional.** Adds a child element defined by `NodeSpec`.
  * Validates tag names against regex `^[a-zA-Z_][\w\-\.]*$`.

* **`edit_node(xpath, spec: NodeSpec, delete: bool) -> Result`**
  
  * **Transactional.** Targets nodes matching `xpath`.
  * **Update Mode (`delete=False`):** Applies non-null fields from `spec` (topic, status, text, attributes) to *all* matching nodes. Existing attributes not mentioned in `spec` are preserved.
  * **Delete Mode (`delete=True`):** Removes *all* matching nodes from the tree.

* **`wrap_content(new_root_tag) -> Result`**
  
  * **Transactional.** Moves all current root children into a new wrapper element.

* **`merge_from(path, password=None) -> Result`**
  
  * **Transactional.** Loads an external file and appends its root children to the current tree.
  * **Convention:** Append-Only (Shallow Merge).
  * **Conflict Resolution:** None. Duplicates are allowed.

### `NodeSpec` (Data Class)

A standard transfer object used to pass data from the CLI to the Core.

* `tag` (str): XML tag name.
* `topic` (str): Primary label/title.
* `status` (str): Workflow state (`active`, `done`, etc.).
* `text` (str): Body content.
* `attrs` (dict): Custom key-value attributes.

---

## 2. Data Layer (`storage.py`)

### `StorageManager`

A decoupled adapter that abstracts away the file system.

* **Security:**
  * **Path Validation:** Rejects null bytes, control characters, and empty paths.
  * **Temp Extraction:** Uses `tempfile.TemporaryDirectory` for safe 7-Zip extraction, ensuring compatibility with all `py7zr` versions.
* **`load(filepath, password) -> bytes`**
  * Detects `.7z` extension automatically.
  * Returns raw bytes.
* **`save(filepath, data, password) -> None`**
  * Writes bytes.
  * Uses LZMA2 compression for `.7z` files.

---

## 3. Presentation Layer (`manifest.py`)

### `ManifestShell`

Extends Python's `cmd.Cmd`.

* **Safe Execution:** Wraps all commands in `_exec` to catch `argparse` exit signals.
* **Password Retry:** Implements a retry loop (max 3 attempts) for encrypted operations.
