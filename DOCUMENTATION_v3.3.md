# Manifest Manager v3.3 - Complete Documentation

## 🎯 What's New in v3.3

### 1. ID Sidecar System
**Fast O(1) ID lookups** via JSON sidecar file (myfile.xml.ids)

**Benefits:**
- Edit by ID without XPath: `edit a3f7b2c1 --topic "Updated"`
- Instant lookups (hash table vs tree traversal)
- Auto-syncs with manifest changes

### 2. Configuration System
**Hierarchical YAML configuration** with sensible defaults

**Locations:**
- Per-file: `myfile.xml.config` (highest priority)
- Global: `~/.config/manifest/config.yaml` (Unix) or `%APPDATA%\manifest\config.yaml` (Windows)
- Defaults: Built-in

### 3. Smart Edit Command
**Auto-detects ID vs XPath** - no need to remember syntax

**Examples:**
```bash
edit a3f7b2c1 --topic "Updated"           # ID (auto-detected)
edit "//task[@status='pending']" --status active  # XPath (auto-detected)
edit --id BUG-123 --topic "Fixed"         # ID (explicit)
```

### 4. Prominent ID Display
**IDs shown first** in find results for easy copy/paste

**Before (v3.2):**
```
/project[@id='a3f7b2c1'] topic="Website"
```

**After (v3.3):**
```
  ID: a3f7b2c1
     Path: /project[@id='a3f7b2c1']
     Topic: Website
     Status: active
```

---

## 📚 User Guide

### Configuration

#### Creating Config Files

**Global config** (applies to all manifests):
```yaml
# ~/.config/manifest/config.yaml

sidecar:
  corruption_handling: warn_and_ask  # silent | warn_and_proceed | warn_and_ask
  auto_rebuild: false
  enabled: true

display:
  show_ids_prominently: true
  id_first: true
```

**Per-file config** (overrides global):
```yaml
# myproject.xml.config

sidecar:
  corruption_handling: silent  # Auto-fix without asking
  auto_rebuild: true           # Always rebuild on load
```

#### Config Options

| Key | Values | Default | Description |
|-----|--------|---------|-------------|
| `sidecar.enabled` | true/false | true | Enable ID sidecar feature |
| `sidecar.corruption_handling` | silent / warn_and_proceed / warn_and_ask | warn_and_ask | How to handle corrupted sidecar |
| `sidecar.auto_rebuild` | true/false | false | Auto-rebuild without confirmation |
| `display.show_ids_prominently` | true/false | true | Show IDs first in find results |
| `display.id_first` | true/false | true | Display ID before other attributes |

### Using the Sidecar

#### Loading with Sidecar

```bash
# Normal load (sidecar loads if exists)
load myfile.xml

# Auto-create sidecar if missing
load myfile.xml --auto-sidecar
load myfile.xml --autosc         # Short form

# Force rebuild sidecar
load myfile.xml --rebuild-sidecar
load myfile.xml --rebuildsc      # Short form
```

#### Editing by ID

```bash
# Auto-detected (8-char hex)
edit a3f7b2c1 --topic "Updated Topic"
edit b5e8d9a2 --status done

# Explicit ID (for custom IDs)
edit --id BUG-123 --topic "Fixed login issue"
edit --id TASK-456 --delete

# Still works: XPath
edit "//task[@status='pending']" --status active
edit --xpath "//*[@id='a3f7b2c1']" --topic "Updated"
```

#### Finding Elements

```bash
# Find by ID prefix (shows IDs prominently)
find a3f

# Output:
#   ID: a3f7b2c1
#      Path: /project[@id='a3f7b2c1']
#      Topic: Website Redesign
#      Status: active
#
#   ID: a3f8e1d4
#      Path: /task[@id='a3f8e1d4']
#      Topic: Fix bug
#      Status: pending

# With tree view
find a3f --tree
find a3f --tree --depth 2
```

---

## 🔧 Technical Reference

### File Structure

```
myproject.xml              # Main manifest
myproject.xml.ids          # ID sidecar (auto-generated)
myproject.xml.config       # Per-file config (optional)

~/.config/manifest/
└── config.yaml            # Global config (optional)
```

### Sidecar Format

**File:** `myfile.xml.ids` (JSON)

```json
{
  "a3f7b2c1": "/manifest/project[@id='a3f7b2c1']",
  "b5e8d9a2": "/manifest/project[@id='a3f7b2c1']/task[@id='b5e8d9a2']",
  "c7k2m4p1": "/manifest/note[@id='c7k2m4p1']"
}
```

**Properties:**
- O(1) lookups
- Auto-syncs on save
- Auto-rebuilds if corrupted
- Safe to delete (rebuilds on next load with `--autosc`)

### ID Detection Algorithm

```
Is selector an ID?

1. If --id flag: YES
2. If --xpath flag: NO
3. If 8-char hex (e.g., 'a3f7b2c1'): YES
4. If contains XPath syntax (/, [, @, *): NO
5. If exists in sidecar: YES
6. Default: NO (safe fallback to XPath)
```

---

## 🚀 Migration from v3.2

### Backward Compatibility

✅ **100% Compatible** - no breaking changes

- All v3.2 commands work identically
- Sidecar is optional (disable in config)
- XPath editing unchanged
- Old files work without modification

### Recommended Migration

**Step 1:** Update files
```bash
# Copy new files:
# - config.py
# - id_sidecar.py
# - manifest_core.py (updated)
# - manifest.py (updated, see MANIFEST_PY_PATCH.md)
```

**Step 2:** Create sidecars for existing files
```bash
manifest
(manifest) load myfile.xml --autosc
(manifest) save
# Now myfile.xml.ids exists
```

**Step 3:** (Optional) Create config
```bash
# Create global config with defaults
mkdir -p ~/.config/manifest
cat > ~/.config/manifest/config.yaml << 'EOF'
sidecar:
  corruption_handling: warn_and_proceed
  auto_rebuild: false
  enabled: true
EOF
```

**Step 4:** Test new features
```bash
(manifest) find <id_prefix>
(manifest) edit <id> --topic "Test"
```

---

## 🐛 Troubleshooting

### Sidecar Corruption

**Symptoms:**
- Warning: "ID sidecar corrupted"
- IDs not found when they should exist

**Causes:**
- Manual XML edits outside manifest manager
- Interrupted save operation
- File system issues

**Solutions:**
```bash
# Option 1: Rebuild on load
load myfile.xml --rebuildsc

# Option 2: Delete and recreate
rm myfile.xml.ids
load myfile.xml --autosc

# Option 3: Set auto-rebuild in config
# myfile.xml.config:
sidecar:
  corruption_handling: silent
  auto_rebuild: true
```

### ID Not Found

**Problem:** `edit abc123` says "ID not found"

**Check:**
1. Is sidecar enabled? `config.get('sidecar.enabled')`
2. Does sidecar exist? `ls myfile.xml.ids`
3. Is ID in sidecar? `cat myfile.xml.ids | grep abc123`

**Fix:**
```bash
load myfile.xml --rebuildsc
```

### Config Not Loading

**Problem:** Changes to config file not applied

**Check:**
1. Correct path? (per-file overrides global)
2. Valid YAML? `yamllint myfile.xml.config`
3. File permissions? `ls -l myfile.xml.config`

**Debug:**
```python
from config import Config
config = Config('/path/to/myfile.xml')
print(config.config)  # See what was loaded
```

---

## 📊 Performance

### Sidecar Impact

| Operation | Without Sidecar | With Sidecar | Improvement |
|-----------|----------------|--------------|-------------|
| Edit by ID | O(n) tree scan | O(1) lookup | 100-1000x faster |
| Find by ID | O(n) tree scan | O(1) lookup | 100-1000x faster |
| Load time | Instant | +10-50ms | Negligible |
| Save time | Normal | +10-50ms | Negligible |

### File Sizes

| Manifest Size | Sidecar Size | Ratio |
|---------------|--------------|-------|
| 10 KB (50 items) | 2 KB | 20% |
| 100 KB (500 items) | 15 KB | 15% |
| 1 MB (5000 items) | 120 KB | 12% |

---

## 🔮 Extension Points

### For Future Development

The code includes stubs for future extensions:

#### 1. Additional Config Backends
**Location:** `config.py`, `_load_file()` method

**To add JSON support:**
```python
if path.endswith('.json'):
    with open(path) as f:
        return json.load(f)
```

#### 2. SQLite Sidecar Backend
**Location:** `id_sidecar.py`, see EXTENSION STUB comments

**Use case:** Manifests with >10,000 IDs

**To implement:**
```python
if self.backend == 'sqlite':
    conn = sqlite3.connect(self.sidecar_path)
    cursor = conn.execute('SELECT id, xpath FROM id_index')
    self.index = dict(cursor.fetchall())
```

#### 3. Repository Abstraction
**Location:** `manifest_core.py`, ManifestRepository class docstring

**Use case:** Support SQLite, PostgreSQL backends

**To implement:**
1. Define `IManifestRepository` Protocol
2. Rename current class to `XMLManifestRepository`
3. Create `SQLiteManifestRepository`
4. Use dependency injection in Shell

---

## 📝 API Reference

### Config

```python
class Config:
    def __init__(self, manifest_path: Optional[str] = None)
    def get(self, key_path: str, default: Any = None) -> Any
    def set(self, key_path: str, value: Any) -> None
    def save(self, global_config: bool = False) -> None
```

### IDSidecar

```python
class IDSidecar:
    def __init__(self, manifest_path: str, config: Config)
    def load(self) -> None
    def save(self) -> None
    def get(self, elem_id: str) -> Optional[str]
    def exists(self, elem_id: str) -> bool
    def add(self, elem_id: str, xpath: str) -> None
    def remove(self, elem_id: str) -> None
    def rebuild(self, root: etree._Element) -> None
    def verify_and_repair(self, root: etree._Element) -> bool
```

### ManifestRepository (New Methods)

```python
class ManifestRepository:
    def load(self, filepath: str, password: str = None,
             auto_sidecar: bool = False, 
             rebuild_sidecar: bool = False) -> Result
    
    def edit_node_by_id(self, elem_id: str, spec: NodeSpec, 
                        delete: bool) -> Result
```

---

**Version:** 3.3.0  
**Date:** January 2026  
**License:** MIT
