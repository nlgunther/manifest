# Manifest Manager API Documentation

**Version:** 3.4.0  
**Last Updated:** January 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Classes](#core-classes)
4. [Public API](#public-api)
5. [Data Types](#data-types)
6. [Storage Layer](#storage-layer)
7. [Configuration](#configuration)
8. [Error Handling](#error-handling)
9. [Examples](#examples)
10. [Extension Points](#extension-points)

---

## Overview

### Purpose

Manifest Manager provides a programmatic API for managing hierarchical XML data structures with automatic ID generation, fast lookups, and transaction support.

### Design Philosophy

- **Repository Pattern**: Clean abstraction over XML operations
- **Result Type**: Explicit success/failure handling
- **Transaction Support**: ACID guarantees via context managers
- **Type Safety**: Comprehensive type hints throughout

### Installation

```python
from manifest_manager import (
    ManifestRepository,
    NodeSpec,
    Result,
    TaskStatus,
    IDSidecar,
    Config,
    StorageManager
)
```

---

## Architecture

### Layer Diagram

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│  (Your code using the API)              │
└────────────────┬────────────────────────┘
                 │ uses
                 ▼
┌─────────────────────────────────────────┐
│      ManifestRepository (Core API)      │
│  - add_node()                           │
│  - edit_node()                          │
│  - edit_node_by_id()                    │
│  - search()                             │
│  - load() / save()                      │
└────┬──────────────┬─────────────────────┘
     │              │
     ▼              ▼
┌─────────┐  ┌──────────────┐
│ Storage │  │  IDSidecar   │
│ Manager │  │  (Index)     │
└─────────┘  └──────────────┘
```

### Component Responsibilities

| Component | Responsibility | Public API |
|-----------|---------------|------------|
| **ManifestRepository** | Core CRUD operations | Yes |
| **NodeSpec** | Data transfer object | Yes |
| **Result** | Operation outcome | Yes |
| **StorageManager** | File I/O | Limited |
| **IDSidecar** | ID indexing | Limited |
| **Config** | Configuration | Yes |
| **ManifestView** | Rendering | Yes |

---

## Core Classes

### ManifestRepository

**Purpose:** Central API for all manifest operations.

#### Constructor

```python
def __init__(self) -> None:
    """Initialize repository.
    
    Creates empty repository ready to load a manifest.
    Call load() before performing operations.
    """
```

#### Properties

```python
@property
def tree(self) -> Optional[etree._ElementTree]:
    """Current XML tree (read-only)."""

@property
def root(self) -> Optional[etree._Element]:
    """Root element of tree (read-only)."""

@property
def filepath(self) -> Optional[str]:
    """Current file path (read-only)."""

@property
def modified(self) -> bool:
    """True if unsaved changes exist."""

@property
def id_sidecar(self) -> Optional[IDSidecar]:
    """ID index if enabled (read-only)."""
```

#### Core Methods

##### load()

```python
def load(
    self, 
    path: str, 
    password: Optional[str] = None,
    auto_sidecar: bool = False
) -> Result:
    """Load manifest from file.
    
    Args:
        path: File path (.xml or .7z)
        password: Password for encrypted files (optional)
        auto_sidecar: Auto-create ID sidecar if missing
        
    Returns:
        Result with success status and message
        
    Raises:
        PasswordRequired: If encrypted file needs password
        
    Example:
        >>> repo = ManifestRepository()
        >>> result = repo.load("project.xml", auto_sidecar=True)
        >>> if result.success:
        ...     print(result.message)
    """
```

##### save()

```python
def save(self, path: Optional[str] = None, password: Optional[str] = None) -> Result:
    """Save manifest to file.
    
    Args:
        path: File path (uses current if None)
        password: Password for .7z encryption (optional)
        
    Returns:
        Result with success status
        
    Side Effects:
        - Writes XML to disk
        - Syncs ID sidecar if enabled
        - Clears modified flag
        
    Example:
        >>> repo.save()
        >>> repo.save("backup.xml")
        >>> repo.save("encrypted.7z", password="secret")
    """
```

##### add_node()

```python
def add_node(
    self,
    parent_xpath: str,
    spec: NodeSpec,
    auto_id: bool = True
) -> Result:
    """Add new element to manifest.
    
    Args:
        parent_xpath: XPath to parent element(s)
        spec: Node specification (tag, attributes, text)
        auto_id: Generate ID if not in spec.attrs
        
    Returns:
        Result with success status
        
    Side Effects:
        - Modifies XML tree
        - Updates sidecar if enabled
        - Sets modified flag
        
    Example:
        >>> spec = NodeSpec(
        ...     tag="task",
        ...     topic="Review code",
        ...     status="active",
        ...     resp="alice"
        ... )
        >>> result = repo.add_node("/*", spec, auto_id=True)
    """
```

##### edit_node()

```python
def edit_node(
    self,
    xpath: str,
    spec: Optional[NodeSpec],
    delete: bool
) -> Result:
    """Edit or delete elements matching XPath.
    
    Args:
        xpath: XPath expression
        spec: Node updates (None for delete)
        delete: If True, delete matched elements
        
    Returns:
        Result with count of affected elements
        
    Example:
        >>> # Update attributes
        >>> spec = NodeSpec(tag="task", status="done")
        >>> repo.edit_node("//task[@topic='Review']", spec, False)
        
        >>> # Delete elements
        >>> repo.edit_node("//task[@status='cancelled']", None, True)
    """
```

##### edit_node_by_id()

```python
def edit_node_by_id(
    self,
    elem_id: str,
    spec: Optional[NodeSpec],
    delete: bool
) -> Result:
    """Edit or delete element by ID (O(1) lookup via sidecar).
    
    Args:
        elem_id: Element ID (full or prefix)
        spec: Node updates
        delete: If True, delete the element
        
    Returns:
        Result with success status
        
    Requires:
        ID sidecar must be enabled
        
    Example:
        >>> spec = NodeSpec(tag="task", resp="bob")
        >>> repo.edit_node_by_id("a3f7b2c1", spec, False)
    """
```

##### search()

```python
def search(self, xpath: str) -> List[etree._Element]:
    """Execute XPath query.
    
    Args:
        xpath: XPath expression
        
    Returns:
        List of matching elements (empty if none)
        
    Example:
        >>> tasks = repo.search("//task[@status='active']")
        >>> for task in tasks:
        ...     print(task.get("topic"))
    """
```

##### search_by_id_prefix()

```python
def search_by_id_prefix(self, prefix: str) -> Result:
    """Find elements by ID prefix.
    
    Args:
        prefix: ID prefix (3-8 characters)
        
    Returns:
        Result with data=[matched_elements]
        
    Example:
        >>> result = repo.search_by_id_prefix("a3f")
        >>> if result.success:
        ...     for elem in result.data:
        ...         print(elem.get("id"), elem.get("topic"))
    """
```

##### wrap_content()

```python
def wrap_content(self, new_root_tag: str) -> Result:
    """Wrap all top-level children under new container.
    
    Args:
        new_root_tag: Tag name for wrapper element
        
    Returns:
        Result with success status
        
    Example:
        >>> repo.wrap_content("archive")
        # Before: <manifest><task/><task/></manifest>
        # After:  <manifest><archive><task/><task/></archive></manifest>
    """
```

##### merge_from()

```python
def merge_from(self, path: str, password: Optional[str] = None) -> Result:
    """Merge content from another manifest.
    
    Args:
        path: Path to source manifest
        password: Password if encrypted
        
    Returns:
        Result with count of merged elements
        
    Side Effects:
        - Adds source elements to current root
        - Sets modified flag
        
    Example:
        >>> repo.merge_from("team-tasks.xml")
    """
```

##### transaction()

```python
@contextmanager
def transaction(self):
    """Context manager for atomic operations.
    
    Yields:
        None - provides transaction context
        
    Behavior:
        - Snapshots tree before operations
        - Restores snapshot if exception raised
        - Commits changes if successful
        
    Example:
        >>> with repo.transaction():
        ...     repo.add_node("/*", spec1)
        ...     repo.add_node("/*", spec2)
        ...     # If any operation fails, all rolled back
    """
```

##### generate_id()

```python
def generate_id(self, existing: set) -> str:
    """Generate unique 8-character hex ID.
    
    Args:
        existing: Set of existing IDs to avoid collisions
        
    Returns:
        Unique ID string
        
    Algorithm:
        - Uses os.urandom for entropy
        - 8 hex characters = 4 bytes = 2^32 combinations
        - Collision probability negligible for <100k IDs
        
    Example:
        >>> existing = {"a3f7b2c1", "b5e8d9a2"}
        >>> new_id = repo.generate_id(existing)
        >>> print(new_id)  # e.g., "c9d4f1a8"
    """
```

---

## Data Types

### NodeSpec

**Purpose:** Data Transfer Object for node operations.

```python
@dataclass
class NodeSpec:
    """Specification for creating/updating nodes.
    
    Attributes:
        tag: Element tag name (required for add)
        topic: Topic/title attribute (optional)
        status: Status value (optional)
        text: Text content (optional)
        resp: Responsible party (optional)
        attrs: Additional custom attributes (dict)
    """
    tag: str
    topic: Optional[str] = None
    status: Optional[Union[str, TaskStatus]] = None
    text: Optional[str] = None
    resp: Optional[str] = None
    attrs: Dict[str, str] = field(default_factory=dict)
```

#### Methods

##### to_xml_attrs()

```python
def to_xml_attrs(self) -> Dict[str, str]:
    """Convert to XML attributes dictionary.
    
    Returns:
        Dictionary of all attributes for XML element
        
    Example:
        >>> spec = NodeSpec(
        ...     tag="task",
        ...     topic="Review",
        ...     status="active",
        ...     attrs={"priority": "high"}
        ... )
        >>> attrs = spec.to_xml_attrs()
        >>> print(attrs)
        {'topic': 'Review', 'status': 'active', 'priority': 'high'}
    """
```

##### from_args() (Factory Method)

```python
@classmethod
def from_args(
    cls,
    args: argparse.Namespace,
    tag: Optional[str] = None,
    attributes: Optional[Dict] = None
) -> NodeSpec:
    """Create NodeSpec from argparse namespace.
    
    Args:
        args: Parsed command-line arguments
        tag: Override tag (for edit operations)
        attributes: Pre-parsed custom attributes
        
    Returns:
        NodeSpec instance
        
    Example:
        >>> # In CLI handler
        >>> parser = argparse.ArgumentParser()
        >>> # ... add arguments ...
        >>> args = parser.parse_args()
        >>> spec = NodeSpec.from_args(args, attributes=parsed_attrs)
    """
```

### Result

**Purpose:** Standardized return type for operations.

```python
@dataclass
class Result:
    """Operation result with success/failure info.
    
    Attributes:
        success: True if operation succeeded
        message: Human-readable message
        data: Optional data payload
    """
    success: bool
    message: str
    data: Any = None
```

#### Factory Methods

```python
@classmethod
def ok(cls, msg: str, data=None) -> Result:
    """Create success result.
    
    Example:
        >>> return Result.ok("Added 3 nodes", data=new_nodes)
    """

@classmethod
def fail(cls, msg: str) -> Result:
    """Create failure result.
    
    Example:
        >>> return Result.fail("XPath error: invalid syntax")
    """
```

### TaskStatus

**Purpose:** Enumeration of valid task states.

```python
class TaskStatus(str, Enum):
    """Valid status values."""
    ACTIVE = "active"
    DONE = "done"
    PENDING = "pending"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
```

**Usage:**
```python
spec = NodeSpec(tag="task", status=TaskStatus.ACTIVE)
# or
spec = NodeSpec(tag="task", status="active")
```

---

## Storage Layer

### StorageManager

**Purpose:** Abstract file I/O operations.

```python
class StorageManager:
    """Handles XML and 7z archive I/O."""
    
    def load(self, filepath: str, password: Optional[str] = None) -> bytes:
        """Load file contents.
        
        Args:
            filepath: Path to .xml or .7z file
            password: Password for encrypted archives
            
        Returns:
            Raw file contents as bytes
            
        Raises:
            FileNotFoundError: File doesn't exist
            PasswordRequired: Encrypted file needs password
            StorageError: I/O or decompression error
        """
    
    def save(self, filepath: str, data: bytes, password: Optional[str] = None) -> None:
        """Write file contents.
        
        Args:
            filepath: Path to .xml or .7z file
            data: Raw bytes to write
            password: Password for .7z encryption
            
        Raises:
            StorageError: Write failure
        """
```

### IDSidecar

**Purpose:** Manage ID → XPath index.

```python
class IDSidecar:
    """Fast ID lookup index."""
    
    def __init__(self, manifest_path: str, config: Config):
        """Initialize sidecar for manifest."""
    
    def load(self) -> None:
        """Load index from disk (.xml.ids file)."""
    
    def save(self) -> None:
        """Write index to disk if dirty."""
    
    def get(self, elem_id: str) -> Optional[str]:
        """Get XPath for ID (O(1) lookup)."""
    
    def exists(self, elem_id: str) -> bool:
        """Check if ID exists in index."""
    
    def add(self, elem_id: str, xpath: str) -> None:
        """Add ID mapping."""
    
    def remove(self, elem_id: str) -> None:
        """Remove ID mapping."""
    
    def all_ids(self) -> Set[str]:
        """Get all IDs in index."""
    
    def rebuild(self, root: etree._Element) -> None:
        """Rebuild entire index from XML tree (O(n))."""
```

---

## Configuration

### Config Class

```python
class Config:
    """Hierarchical configuration manager."""
    
    def __init__(self, manifest_path: Optional[str] = None):
        """Load configuration.
        
        Args:
            manifest_path: Path for per-file config (optional)
            
        Loads from (in priority order):
            1. Per-file config: <manifest_path>.config
            2. Global config: ~/.config/manifest/config.yaml
            3. Built-in defaults
        """
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Dot-separated key (e.g., "sidecar.enabled")
            default: Default if key not found
            
        Returns:
            Configuration value
            
        Example:
            >>> config = Config()
            >>> auto_id = config.get("auto_id", True)
            >>> max_attempts = config.get("max_password_attempts", 3)
        """
```

### Configuration Schema

```yaml
# Default configuration values

# Auto-generate IDs for new elements
auto_id: true

# Default view style (tree or table)
default_view_style: tree

# Maximum password retry attempts
max_password_attempts: 3

# ID Sidecar settings
sidecar:
  enabled: true
  corruption_handling: warn_and_ask  # silent | warn_and_proceed | warn_and_ask
  auto_rebuild: false

# Display settings
display:
  show_ids: true
  tree_indent: 2
  max_depth: null  # unlimited

# Autosave (experimental)
autosave:
  enabled: false
  interval: 300  # seconds
```

---

## Error Handling

### Exception Hierarchy

```
Exception
├── StorageError              # Base for storage layer
│   ├── PasswordRequired      # Encrypted file needs password
│   └── ArchiveError          # Invalid or multi-file archive
└── ValueError                # Invalid input (tag names, etc.)
```

### Result Pattern

Most operations return `Result` instead of raising exceptions:

```python
result = repo.add_node("/*", spec)
if result.success:
    print(f"✓ {result.message}")
    if result.data:
        process(result.data)
else:
    print(f"✗ {result.message}")
```

### Best Practices

**1. Always check Result.success:**
```python
result = repo.load("project.xml")
if not result.success:
    print(f"Error: {result.message}")
    return
```

**2. Handle PasswordRequired:**
```python
try:
    result = repo.load("backup.7z")
except PasswordRequired:
    password = getpass.getpass("Password: ")
    result = repo.load("backup.7z", password=password)
```

**3. Use transactions for multi-step operations:**
```python
with repo.transaction():
    repo.add_node("/*", spec1)
    repo.add_node("/*", spec2)
    # Rolls back automatically on error
```

---

## Examples

### Example 1: Basic CRUD

```python
from manifest_manager import ManifestRepository, NodeSpec

# Create repository
repo = ManifestRepository()

# Load manifest
result = repo.load("project.xml", auto_sidecar=True)
if not result.success:
    print(f"Error: {result.message}")
    exit(1)

# Add task
spec = NodeSpec(
    tag="task",
    topic="Review documentation",
    status="active",
    resp="alice",
    attrs={"priority": "high"}
)
result = repo.add_node("/*", spec, auto_id=True)
print(f"Added: {result.message}")

# Find by ID prefix
result = repo.search_by_id_prefix("a3f")
if result.success and result.data:
    task = result.data[0]
    print(f"Found: {task.get('topic')}")
    
    # Edit task
    update = NodeSpec(tag="task", status="done")
    result = repo.edit_node_by_id(task.get("id"), update, False)
    print(f"Updated: {result.message}")

# Save
repo.save()
```

### Example 2: Batch Import

```python
from manifest_manager import ManifestRepository, NodeSpec

def import_tasks(repo, tasks_data):
    """Import tasks from external source."""
    
    with repo.transaction():
        for task_data in tasks_data:
            spec = NodeSpec(
                tag="task",
                topic=task_data["title"],
                status=task_data["status"],
                resp=task_data["assignee"],
                text=task_data.get("description", "")
            )
            result = repo.add_node("/*", spec, auto_id=True)
            if not result.success:
                raise Exception(f"Import failed: {result.message}")
    
    print(f"Imported {len(tasks_data)} tasks")

# Usage
repo = ManifestRepository()
repo.load("project.xml", auto_sidecar=True)

tasks = [
    {"title": "Task 1", "status": "active", "assignee": "alice"},
    {"title": "Task 2", "status": "pending", "assignee": "bob"},
]
import_tasks(repo, tasks)

repo.save()
```

### Example 3: Querying and Reporting

```python
from manifest_manager import ManifestRepository
from collections import defaultdict

def generate_report(repo):
    """Generate task report by assignee."""
    
    # Query all tasks
    tasks = repo.search("//task")
    
    # Group by assignee
    by_assignee = defaultdict(lambda: {"active": 0, "done": 0, "pending": 0})
    
    for task in tasks:
        resp = task.get("resp", "unassigned")
        status = task.get("status", "unknown")
        by_assignee[resp][status] += 1
    
    # Print report
    print("\nTask Report by Assignee")
    print("=" * 60)
    for assignee, counts in sorted(by_assignee.items()):
        print(f"\n{assignee}:")
        for status, count in counts.items():
            if count > 0:
                print(f"  {status}: {count}")

# Usage
repo = ManifestRepository()
repo.load("project.xml")
generate_report(repo)
```

### Example 4: Custom Validation

```python
from manifest_manager import ManifestRepository, NodeSpec, Result

class ValidatingRepository(ManifestRepository):
    """Repository with custom validation rules."""
    
    VALID_PRIORITIES = {"low", "medium", "high", "critical"}
    
    def add_node(self, parent_xpath: str, spec: NodeSpec, auto_id: bool = True) -> Result:
        """Add node with validation."""
        
        # Validate priority if present
        if "priority" in spec.attrs:
            if spec.attrs["priority"] not in self.VALID_PRIORITIES:
                return Result.fail(
                    f"Invalid priority: {spec.attrs['priority']}. "
                    f"Must be one of: {', '.join(self.VALID_PRIORITIES)}"
                )
        
        # Validate resp is assigned for active tasks
        if spec.tag == "task" and spec.status == "active" and not spec.resp:
            return Result.fail("Active tasks must have assignee (--resp)")
        
        # Call parent implementation
        return super().add_node(parent_xpath, spec, auto_id)

# Usage
repo = ValidatingRepository()
repo.load("project.xml", auto_sidecar=True)

# This will fail validation
spec = NodeSpec(tag="task", topic="Test", status="active")  # Missing resp
result = repo.add_node("/*", spec)
print(result.message)  # "Active tasks must have assignee"
```

### Example 5: Automated Backups

```python
from manifest_manager import ManifestRepository
from datetime import datetime
import os

class BackupRepository(ManifestRepository):
    """Repository with automatic backup on save."""
    
    def __init__(self, backup_dir: str = "./backups"):
        super().__init__()
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def save(self, path: Optional[str] = None, password: Optional[str] = None) -> Result:
        """Save with automatic backup."""
        
        # Create timestamped backup
        if self.filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            basename = os.path.basename(self.filepath)
            backup_path = os.path.join(
                self.backup_dir,
                f"{basename}.{timestamp}.bak"
            )
            
            # Save backup
            backup_result = super().save(backup_path)
            if not backup_result.success:
                print(f"Warning: Backup failed: {backup_result.message}")
        
        # Save main file
        return super().save(path, password)

# Usage
repo = BackupRepository()
repo.load("project.xml", auto_sidecar=True)
# ... make changes ...
repo.save()  # Automatically creates backup in ./backups/
```

---

## Extension Points

### Custom Backends

The repository abstraction allows for alternative storage backends:

```python
from typing import Protocol

class IManifestRepository(Protocol):
    """Repository interface for dependency injection."""
    
    def load(self, path: str, **kwargs) -> Result: ...
    def save(self, path: Optional[str] = None, **kwargs) -> Result: ...
    def add_node(self, parent: str, spec: NodeSpec, **kwargs) -> Result: ...
    def edit_node(self, xpath: str, spec: NodeSpec, delete: bool) -> Result: ...
    def search(self, xpath: str) -> List: ...

class SQLiteManifestRepository(IManifestRepository):
    """SQLite-backed repository (future implementation)."""
    
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        # ... initialize tables ...
    
    def add_node(self, parent: str, spec: NodeSpec, **kwargs) -> Result:
        """Store node in SQLite instead of XML."""
        # ... SQLite INSERT ...
```

### Custom Sidecar Backends

```python
class RedisSidecar:
    """Redis-backed sidecar for distributed systems."""
    
    def __init__(self, manifest_path: str, redis_url: str):
        import redis
        self.redis = redis.from_url(redis_url)
        self.prefix = f"manifest:{manifest_path}:"
    
    def get(self, elem_id: str) -> Optional[str]:
        """Get XPath from Redis."""
        return self.redis.get(f"{self.prefix}{elem_id}")
    
    def add(self, elem_id: str, xpath: str) -> None:
        """Store ID mapping in Redis."""
        self.redis.set(f"{self.prefix}{elem_id}", xpath)
```

### Custom View Renderers

```python
class JSONRenderer:
    """Render manifest as JSON."""
    
    @staticmethod
    def render(nodes: List[etree._Element]) -> str:
        """Convert nodes to JSON."""
        result = []
        for node in nodes:
            result.append({
                "tag": node.tag,
                "attributes": dict(node.attrib),
                "text": node.text,
                "children": [child.tag for child in node]
            })
        return json.dumps(result, indent=2)

# Usage
repo = ManifestRepository()
repo.load("project.xml")
tasks = repo.search("//task")
print(JSONRenderer.render(tasks))
```

---

## Performance Notes

### Time Complexity

| Operation | Without Sidecar | With Sidecar | Notes |
|-----------|----------------|--------------|-------|
| `load()` | O(n) | O(n) | Parse XML tree |
| `save()` | O(n) | O(n) | Serialize tree |
| `add_node()` | O(log n) | O(log n) + O(1) | XPath + sidecar update |
| `edit_node()` | O(n) | O(n) | XPath traversal |
| `edit_node_by_id()` | N/A | O(1) | Hash lookup |
| `search()` | O(n) | O(n) | XPath traversal |
| `search_by_id_prefix()` | N/A | O(k) | k = matching IDs |
| `rebuild()` | N/A | O(n) | Full tree traversal |

### Space Complexity

- **XML tree**: O(n) where n = number of elements
- **Sidecar index**: O(m) where m = number of IDs
- **Transaction snapshot**: O(n) temporary

### Optimization Tips

1. **Use ID operations when possible** - O(1) vs O(n)
2. **Enable sidecar for large files** - Significant speedup
3. **Use transactions for batch operations** - Reduces overhead
4. **Limit XPath complexity** - Deep predicates are expensive
5. **Use `--depth` parameter** - Limits traversal depth

---

## Thread Safety

**Important:** ManifestRepository is **NOT thread-safe**.

For concurrent access:
1. Use separate repository instances per thread
2. Implement external locking
3. Consider alternative backends (SQLite with WAL mode)

Example with threading:
```python
from threading import Lock
from manifest_manager import ManifestRepository

class ThreadSafeRepository:
    """Thread-safe wrapper."""
    
    def __init__(self):
        self._repo = ManifestRepository()
        self._lock = Lock()
    
    def add_node(self, *args, **kwargs):
        with self._lock:
            return self._repo.add_node(*args, **kwargs)
```

---

## Version Compatibility

### Python Version

- **Required**: Python 3.8+
- **Recommended**: Python 3.10+
- **Tested**: Python 3.8, 3.9, 3.10, 3.11

### Dependency Versions

```
lxml >= 4.6.0
py7zr >= 0.20.0  # Optional, for 7z support
PyYAML >= 5.4    # For configuration
```

### API Stability

- **Stable APIs** (v3.x): All public methods in this document
- **Experimental APIs**: Marked with `# EXPERIMENTAL` in docstrings
- **Deprecated APIs**: None in v3.4

### Migration from v3.3

```python
# v3.3
spec = NodeSpec(tag, topic, status, text, attrs)

# v3.4 (backward compatible, but new factory method preferred)
spec = NodeSpec.from_args(args, attributes=attrs)
```

---

## Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("manifest-core")
```

### Inspect Repository State

```python
# Check if loaded
print(f"Loaded: {repo.tree is not None}")
print(f"File: {repo.filepath}")
print(f"Modified: {repo.modified}")

# Check sidecar
if repo.id_sidecar:
    print(f"IDs in index: {len(repo.id_sidecar.all_ids())}")

# Inspect tree
if repo.root is not None:
    print(f"Root tag: {repo.root.tag}")
    print(f"Children: {len(list(repo.root))}")
```

### Common Issues

**Issue: XPath returns empty**
```python
# Debug XPath
results = repo.search("//task")
print(f"Found {len(results)} tasks")
for task in results:
    print(f"  {task.get('id')} - {task.get('topic')}")
```

**Issue: Sidecar out of sync**
```python
# Force rebuild
if repo.id_sidecar:
    repo.id_sidecar.rebuild(repo.root)
    repo.id_sidecar.save()
```

---

## API Changelog

### v3.4 (Current)

- ✨ Added `NodeSpec.from_args()` factory method
- ✨ Added `resp` attribute support
- ✨ Added `search_by_id_prefix()` for prefix matching
- 🐛 Fixed `_is_id_selector()` detection logic
- 📚 Enhanced docstrings throughout

### v3.3

- ✨ Added `IDSidecar` for O(1) lookups
- ✨ Added `edit_node_by_id()` method
- ✨ Added `Config` class
- ✨ Added smart ID/XPath detection

### v3.2

- ✨ Added transaction support
- ✨ Added 7z encryption
- ✨ Added `wrap_content()` method

### v3.1

- ✨ Initial public release
- ✨ Core CRUD operations
- ✨ XPath queries

---

**End of API Documentation**

For usage examples, see [README.md](README.md)  
For command reference, see [CHEATSHEET.md](CHEATSHEET.md)  
For code review, see [MANIFEST_MANAGER_COMPREHENSIVE_REVIEW.md](MANIFEST_MANAGER_COMPREHENSIVE_REVIEW.md)
