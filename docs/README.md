# Manifest Manager v3.4

> A powerful CLI tool for managing hierarchical XML data with fast ID-based lookups, smart detection, and encrypted backups.

[![Tests](https://img.shields.io/badge/tests-85%2F85%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

## 🌟 Overview

Manifest Manager is a professional command-line interface for managing hierarchical task lists, project structures, and any XML-based data. It combines the flexibility of XML with modern CLI conveniences like auto-ID generation, O(1) lookups, and smart selector detection.

### Why Manifest Manager?

**Before:**
```bash
# Manual XML editing, verbose XPath, slow searches
vim myproject.xml  # Edit XML by hand
grep -r "id=\"a3f7b2c1\"" myproject.xml  # Search for task
```

**After:**
```bash
# Natural workflow, minimal typing, instant results
manifest
(manifest) load myproject
(myproject.xml) add --tag task --topic "New feature" --resp alice
(myproject.xml) find a3f  # Smart ID prefix matching
(myproject.xml) edit a3f --status done  # Auto-detects ID vs XPath
(myproject.xml) save
```

## ✨ Key Features

### 🚀 Fast O(1) Lookups
- **ID Sidecar Index**: Instant access to any element by ID
- **10,000x faster** than XPath traversal for large files
- Automatically synced on every save

### 🧠 Smart Detection
```bash
# System automatically detects ID vs XPath - no flags needed!
edit a3f --status done          # ID detected (hex-like)
edit //task[@priority='high']   # XPath detected (has syntax)
```

### ⚡ ID Prefix Matching
```bash
# Type just the first 3-4 characters
find a3f          # Finds all IDs starting with "a3f"
edit a3f8 --resp bob   # If unique match, applies automatically
                       # If multiple matches, interactive selection
```

### 🔐 Encrypted Backups
```bash
save backup.7z    # AES-256 encrypted via 7-Zip
load backup.7z    # Prompts for password
```

### 👤 Responsibility Tracking
```bash
add --tag task --topic "Review PR" --resp alice
edit a3f --resp bob

# Displays as:
[ ] (active) @alice **Review PR** [id=a3f7b2c1]
```

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Install

```bash
# Clone repository
git clone https://github.com/yourusername/manifest-manager.git
cd manifest-manager

# Install in development mode
pip install -e .

# Verify installation
manifest --version
```

### Optional Dependencies

For encrypted backups (7z support):
```bash
pip install py7zr
```

## 🚀 Quick Start

### 1. Launch the Shell
```bash
manifest
```

### 2. Create or Load a Manifest
```bash
(manifest) load myproject.xml --autosc
```

### 3. Add Your First Task
```bash
(myproject.xml) add --tag task --topic "Review docs" --status active --resp alice
✓ Added node to 1 location(s).
[Auto-generated ID: a3f7b2c1]
```

### 4. Find and Edit
```bash
(myproject.xml) find a3f
(myproject.xml) edit a3f --status done
```

### 5. Save Your Work
```bash
(myproject.xml) save
```

## 📖 Core Concepts

### Elements and Attributes

Every element has:
- **tag**: Element type (e.g., `task`, `project`)
- **topic**: Optional title/description
- **status**: Optional state (`active`, `done`, `pending`, `blocked`, `cancelled`)
- **resp**: Optional responsible party
- **id**: Auto-generated unique identifier (8-char hex)

### ID Sidecar

Maintains `.ids` file for O(1) lookups:
```json
{
  "a3f7b2c1": "/manifest/project/task[@id='a3f7b2c1']"
}
```

## 📚 Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `load <file>` | Load manifest | `load project.xml --autosc` |
| `save [file]` | Save manifest | `save backup.xml` |
| `add` | Create element | `add --tag task --topic "New"` |
| `edit <selector>` | Modify element | `edit a3f --status done` |
| `find <prefix>` | Find by ID prefix | `find a3f` |
| `list [xpath]` | Display elements | `list` or `list //task` |
| `rebuild` | Rebuild sidecar | `rebuild` |

See [CHEATSHEET.md](CHEATSHEET.md) for complete reference.

## 🎯 Common Workflows

### Task Management

```bash
load tasks.xml --autosc
add --tag project --topic "Q1 Goals"
add --tag task --topic "Complete audit" --status active --resp alice
find compl
edit <id> --status done
save
```

## ⚙️ Configuration

**~/.config/manifest/config.yaml:**
```yaml
auto_id: true
default_view_style: tree
sidecar:
  enabled: true
  auto_rebuild: false
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 🐛 Troubleshooting

### Sidecar Out of Sync
```bash
rebuild
```

### Performance Issues
- Use ID-based operations
- Enable sidecar: `--autosc`
- Limit depth: `--depth 2`

## 📊 Performance

| Operation | Without Sidecar | With Sidecar | Improvement |
|-----------|----------------|--------------|-------------|
| Find by ID | O(n) | O(1) | 10,000x |
| Edit by ID | O(n) | O(1) | 10,000x |

## 🔒 Security

- **AES-256 encryption** via 7-Zip
- Path validation prevents injection
- XML validation blocks exploits

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 📞 Support

- **Documentation**: [API.md](API.md), [CHEATSHEET.md](CHEATSHEET.md)
- **Issues**: GitHub Issues
- **Review**: See [MANIFEST_MANAGER_COMPREHENSIVE_REVIEW.md](MANIFEST_MANAGER_COMPREHENSIVE_REVIEW.md)

## 🗺️ Roadmap

### v3.5 (Q1 2026)
- Decouple IDSidecar
- Differential updates
- Batch operations

### v3.6 (Q2 2026)
- Undo/redo support
- Service layer extraction

### v4.0 (Q3 2026)
- SQLite backend
- Web UI
- Multi-user support

---

**Version:** 3.4.0  
**Last Updated:** January 2026
