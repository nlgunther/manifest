"""
Manifest Core - Business Logic Layer
====================================

Contains the domain model, repository pattern implementation,
and view rendering for hierarchical XML data management.

Classes:
    NodeSpec: Data transfer object for node operations
    Result: Standardized operation return type
    TaskStatus: Enumeration of valid task states
    Validator: Tag and content validation utilities
    ManifestRepository: Core CRUD operations on XML tree
    ManifestView: Stateless rendering engine

Example:
    >>> repo = ManifestRepository()
    >>> repo.load("tasks.xml")
    >>> repo.add_node("/*", NodeSpec(tag="task", topic="New Task"))
    >>> repo.save()

Architecture:
    - Repository pattern for data access
    - Transaction support with automatic rollback
    - XPath-based queries with safety wrapper
    - Immutable Result objects for operation outcomes

Security:
    - XML tag name validation (prevents reserved prefixes)
    - Control character sanitization in text content
    - Safe XPath evaluation with error containment
"""

import os
import re
import logging
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
from lxml import etree
from .storage import StorageManager, PasswordRequired

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("manifest-core")

# --- Constants & Types ---
class TaskStatus(str, Enum):
    ACTIVE = "active"
    DONE = "done"
    PENDING = "pending"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    def __str__(self): return self.value

@dataclass
class NodeSpec:
    """Data Transfer Object for Node operations.
    
    Attributes:
        tag: Element tag name
        topic: Topic/title attribute
        status: Status attribute (active, done, pending, blocked, cancelled)
        text: Text content of element
        resp: Responsible party attribute (NEW in v3.4)
        due: Due date in YYYY-MM-DD format (NEW in v3.5)
        attrs: Additional custom attributes (dict)
    """
    tag: str
    topic: Optional[str] = None
    status: Optional[Union[str, TaskStatus]] = None
    text: Optional[str] = None
    resp: Optional[str] = None
    due: Optional[str] = None
    attrs: Dict[str, str] = field(default_factory=dict)

    def to_xml_attrs(self) -> Dict[str, str]:
        """Convert NodeSpec attributes to XML attributes dict."""
        a = self.attrs.copy()
        if self.topic: a['topic'] = self.topic
        if self.status: a['status'] = str(self.status)
        if self.resp: a['resp'] = self.resp
        if self.due: a['due'] = self.due
        return a
    
    @classmethod
    def from_args(cls, args, tag=None, attributes=None):
        """Create NodeSpec from argparse namespace (Factory Method).
        
        Simplifies NodeSpec creation from CLI arguments and provides
        a single source of truth for mapping args to NodeSpec fields.
        
        Args:
            args: Parsed argparse Namespace
            tag: Override tag name (for edit operations where tag is ignored)
            attributes: Pre-parsed attributes dict (from _parse_attrs)
            
        Returns:
            NodeSpec instance
            
        Examples:
            # In add command
            attrs = self._parse_attrs(args.attr)
            spec = NodeSpec.from_args(args, attributes=attrs)
            
            # In edit command (tag is ignored)
            attrs = self._parse_attrs(args.attr)
            spec = NodeSpec.from_args(args, tag="ignored", attributes=attrs)
        
        Note:
            Uses getattr() with None default to handle missing attributes.
            This allows the same factory to work for both add and edit commands.
        """
        return cls(
            tag=tag or getattr(args, 'tag', None),
            topic=getattr(args, 'topic', None),
            status=getattr(args, 'status', None),
            text=getattr(args, 'text', None),
            resp=getattr(args, 'resp', None),
            due=getattr(args, 'due', None),
            attrs=attributes or {}
        )

@dataclass
class Result:
    """Standardized return type for all operations."""
    success: bool
    message: str
    data: Any = None
    @classmethod
    def ok(cls, msg: str, data=None): return cls(True, msg, data)
    @classmethod
    def fail(cls, msg: str): return cls(False, msg)

# --- Logic ---

class Validator:
    TAG_REGEX = re.compile(r'^[a-zA-Z_][\w\-\.]*$')
    
    @staticmethod
    def validate_tag(tag: str):
        if not tag or not Validator.TAG_REGEX.match(tag):
            raise ValueError(
                f"Invalid tag '{tag}'. Must start with letter/underscore, "
                "contain only alphanumeric, hyphen, dot."
            )
        if tag.lower().startswith('xml'):
            raise ValueError(
                f"Invalid tag '{tag}'. Tags starting with 'xml' (any case) "
                "are reserved by XML specification."
            )
    
    @staticmethod
    def sanitize(text: str) -> str:
        return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text or "")

class ManifestRepository:
    """
    Core Domain Service.
    Manages the XML Tree state and high-level operations.
    
    EXTENSION POINT: Repository abstraction
    To support multiple backends (SQLite, PostgreSQL):
        1. Extract interface: IManifestRepository (Protocol)
        2. Create XMLManifestRepository (this class)
        3. Create SQLiteManifestRepository (new)
        4. Inject repository into Shell via dependency injection
    
    Example future structure:
        class IManifestRepository(Protocol):
            def load(self, path): ...
            def save(self): ...
            def add_node(self, parent, spec): ...
        
        class XMLManifestRepository(IManifestRepository):
            # Current implementation
        
        class SQLiteManifestRepository(IManifestRepository):
            # New implementation using SQLite
    """
    def __init__(self):
        self.storage = StorageManager()
        self.tree: Optional[etree._ElementTree] = None
        self.root: Optional[etree._Element] = None
        self.filepath: Optional[str] = None
        self.password: Optional[str] = None
        self.modified: bool = False
        
        # NEW: Config and sidecar (v3.3)
        self.config = None
        self.id_sidecar = None

    @contextmanager
    def transaction(self):
        """Context manager that provides automatic rollback on errors.
        
        Creates a snapshot of the XML tree before executing operations.
        If an exception occurs, restores the tree to its original state.
        
        Yields:
            None - just provides context for safe operations
            
        Raises:
            Exception: Re-raises any exception after rollback
            
        Example:
            >>> with repo.transaction():
            ...     repo.add_node("/*", NodeSpec(tag="task"))
            ...     # If error occurs, changes are rolled back
        """
        if self.tree is None: yield; return
        snapshot = etree.tostring(self.root)
        prev_mod = self.modified
        try:
            yield
        except Exception as e:
            self.root = etree.fromstring(snapshot)
            self.tree = etree.ElementTree(self.root)
            self.modified = prev_mod
            raise e

    def _safe_xpath(self, xpath: str) -> tuple[bool, Union[List[etree._Element], str]]:
        """Execute XPath safely, returning (success, results_or_error).
        
        Args:
            xpath: XPath expression to evaluate
            
        Returns:
            (True, list of elements) on success
            (False, error message) on failure
        """
        try:
            return True, self.root.xpath(xpath)
        except etree.XPathEvalError as e:
            return False, f"Invalid XPath expression: {xpath}\nError: {e}"
        except Exception as e:
            return False, f"XPath evaluation failed: {e}"

    def load(self, filepath: str, password: str = None, auto_sidecar: bool = False, 
             rebuild_sidecar: bool = False) -> Result:
        """Load manifest file with optional sidecar management.
        
        Args:
            filepath: Path to manifest file
            password: Optional encryption password
            auto_sidecar: Auto-create sidecar if missing
            rebuild_sidecar: Force rebuild sidecar even if exists
            
        Returns:
            Result indicating success/failure
        """
        path = filepath.strip('"\'')
        if "." not in os.path.basename(path): path += ".xml"
        
        if not os.path.exists(path):
            self.root = etree.Element("manifest")
            self.tree = etree.ElementTree(self.root)
            self.filepath, self.password, self.modified = path, password, True
            
            # NEW: Initialize config and sidecar for new files too (v3.3)
            from .config import Config
            from .id_sidecar import IDSidecar
            
            self.config = Config(self.filepath)
            
            if self.config.get('sidecar.enabled', True):
                self.id_sidecar = IDSidecar(self.filepath, self.config)
                # For new files with auto_sidecar, create empty sidecar
                if auto_sidecar:
                    self.id_sidecar.rebuild(self.root)  # Empty tree, empty sidecar
                    self.id_sidecar.save()
            
            return Result.ok(f"Created new: {path}")

        try:
            raw = self.storage.load(path, password)
            self.root = etree.fromstring(raw, etree.XMLParser(remove_blank_text=True))
            self.tree = etree.ElementTree(self.root)
            self.filepath, self.password, self.modified = path, password, False
            
            # NEW: Load config and sidecar (v3.3)
            from .config import Config
            from .id_sidecar import IDSidecar
            
            self.config = Config(self.filepath)
            
            if self.config.get('sidecar.enabled', True):
                self.id_sidecar = IDSidecar(self.filepath, self.config)
                self.id_sidecar.load()
                
                # Handle sidecar creation/rebuild
                if rebuild_sidecar:
                    logger.info("Force rebuilding sidecar...")
                    self.id_sidecar.rebuild(self.root)
                    self.id_sidecar.save()
                elif not self.id_sidecar.index and auto_sidecar:
                    logger.info("Creating ID sidecar...")
                    self.id_sidecar.rebuild(self.root)
                    self.id_sidecar.save()
                elif self.id_sidecar.index:
                    # Verify and repair if needed
                    self.id_sidecar.verify_and_repair(self.root)
            
            return Result.ok(f"Loaded {path}")
        except PasswordRequired: raise
        except Exception as e: return Result.fail(str(e))

    def save(self, filepath: str = None, password: str = None) -> Result:
        target = (filepath or self.filepath or "").strip('"\'')
        if not target: return Result.fail("No file specified.")
        pwd = password if password is not None else self.password

        try:
            xml = etree.tostring(self.root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
            self.storage.save(target, xml, pwd)
            self.filepath, self.password, self.modified = target, pwd, False
            
            # NEW: Save sidecar if dirty (v3.3)
            if self.id_sidecar:
                self.id_sidecar.save()
            
            return Result.ok(f"Saved to {target}")
        except Exception as e: return Result.fail(str(e))

    def generate_id(self, existing_ids: set = None) -> str:
        """Generate short unique ID (8-char hex).
        
        Uses SHA256 hash of random data for collision resistance.
        Probability of collision: ~1 in 4 billion (2^32).
        
        Args:
            existing_ids: Set of IDs to check for uniqueness (optional)
            
        Returns:
            8-character hex string ID
        """
        import hashlib
        import secrets
        
        while True:
            # Hash random bytes for unpredictability
            random_data = secrets.token_bytes(16)
            hash_digest = hashlib.sha256(random_data).hexdigest()[:8]
            
            # Ensure uniqueness if existing IDs provided
            if existing_ids is None or hash_digest not in existing_ids:
                return hash_digest

    def search_by_id_prefix(self, prefix: str) -> Result:
        """Find all nodes whose ID starts with the given prefix.
        
        Args:
            prefix: Starting characters of ID to search for
            
        Returns:
            Result with list of matching elements
        """
        if not self.tree:
            return Result.fail("No file loaded.")
        
        if not prefix or not prefix.strip():
            return Result.fail("Empty search prefix.")
        
        try:
            # XPath: starts-with(@id, 'prefix')
            # Escape single quotes in prefix for XPath safety
            safe_prefix = prefix.replace("'", "&apos;")
            xpath = f"//*[starts-with(@id, '{safe_prefix}')]"
            matches = self.root.xpath(xpath)
            
            if not matches:
                return Result.fail(f"No IDs starting with '{prefix}'")
            
            return Result.ok(f"Found {len(matches)} match(es)", data=matches)
        except Exception as e:
            return Result.fail(f"Search error: {e}")

    def ensure_ids(self, overwrite: bool = False) -> Result:
        """Walk tree and add IDs to elements that lack them.
        
        Args:
            overwrite: If True, replace existing IDs with new ones
            
        Returns:
            Result with count of IDs added/updated
        """
        if not self.tree:
            return Result.fail("No file loaded.")
        
        with self.transaction():
            count = 0
            existing_ids = set()
            
            # First pass: collect existing IDs
            for elem in self.root.iter():
                elem_id = elem.get("id")
                if elem_id:
                    existing_ids.add(elem_id)
            
            # Second pass: add/update IDs
            for elem in self.root.iter():
                current_id = elem.get("id")
                
                # Skip if has ID and not overwriting
                if current_id and not overwrite:
                    continue
                
                # Generate new unique ID
                new_id = self.generate_id(existing_ids)
                elem.set("id", new_id)
                existing_ids.add(new_id)
                count += 1
            
            if count > 0:
                self.modified = True
            
            return Result.ok(f"Added/updated {count} ID(s)")

    def add_node(self, parent_xpath: str, spec: NodeSpec, auto_id: bool = True) -> Result:
        """Add new node(s) to the tree.
        
        Args:
            parent_xpath: XPath to parent element(s)
            spec: NodeSpec defining the new element
            auto_id: If True and spec has no 'id' in attrs, generate one
            
        Returns:
            Result indicating success/failure
        """
        if not self.tree: return Result.fail("No file loaded.")
        with self.transaction():
            Validator.validate_tag(spec.tag)
            ok, parents = self._safe_xpath(parent_xpath)
            if not ok:
                return Result.fail(parents)  # parents contains error message
            if not parents:
                return Result.fail(f"Parent not found: {parent_xpath}")
            
            # Auto-generate ID if enabled and not explicitly provided
            attrs = spec.to_xml_attrs()
            if auto_id and 'id' not in spec.attrs:
                # Collect existing IDs for uniqueness check
                existing_ids = {elem.get("id") for elem in self.root.iter() if elem.get("id")}
                attrs['id'] = self.generate_id(existing_ids)
            
            for p in parents:
                n = etree.SubElement(p, spec.tag, **attrs)
                if spec.text: n.text = Validator.sanitize(spec.text)
                
                # NEW: Update sidecar with new ID (v3.3)
                if self.id_sidecar and 'id' in attrs:
                    from .id_sidecar import IDSidecar
                    xpath = IDSidecar._build_xpath(n)
                    self.id_sidecar.add(attrs['id'], xpath)
            
            self.modified = True
            return Result.ok(f"Added node to {len(parents)} location(s).")

    def edit_node(self, xpath: str, spec: Optional[NodeSpec], delete: bool) -> Result:
        if not self.tree: return Result.fail("No file loaded.")
        with self.transaction():
            ok, nodes = self._safe_xpath(xpath)
            if not ok:
                return Result.fail(nodes)  # nodes contains error message
            if not nodes:
                return Result.fail("No match found.")
            
            if delete:
                for n in nodes: n.getparent().remove(n)
                self.modified = True
                return Result.ok(f"Deleted {len(nodes)} nodes.")
            
            for n in nodes:
                if spec.text is not None: n.text = Validator.sanitize(spec.text)
                for k, v in spec.to_xml_attrs().items(): n.set(k, v)
            self.modified = True
            return Result.ok(f"Updated {len(nodes)} nodes.")

    def edit_node_by_id(self, elem_id: str, spec: Optional[NodeSpec], delete: bool) -> Result:
        """Edit node by ID using sidecar for fast lookup (NEW in v3.3).
        
        Args:
            elem_id: Element ID to edit
            spec: NodeSpec with updates
            delete: If True, delete the node
            
        Returns:
            Result indicating success/failure
            
        Example:
            >>> repo.edit_node_by_id('a3f7b2c1', NodeSpec(topic="Updated"), False)
            Result(success=True, message="Updated 1 nodes.")
        """
        if not self.id_sidecar:
            return Result.fail("ID sidecar not enabled. Use edit with XPath instead.")
        
        if not self.id_sidecar.exists(elem_id):
            return Result.fail(f"ID not found: {elem_id}")
        
        # Get XPath from sidecar (O(1) lookup!)
        xpath = self.id_sidecar.get(elem_id)
        
        # Delegate to existing edit_node
        return self.edit_node(xpath, spec, delete)

    def wrap_content(self, new_root_tag: str) -> Result:
        """
        NEW FEATURE: Reparents all current top-level nodes under a new container tag.
        """
        if not self.tree: return Result.fail("No file loaded.")
        with self.transaction():
            Validator.validate_tag(new_root_tag)
            
            # 1. Identify current top-level children
            children = list(self.root)
            if not children:
                return Result.fail("Manifest is empty; nothing to wrap.")

            # 2. Create the new wrapper element
            wrapper = etree.Element(new_root_tag)

            # 3. Move children into wrapper
            for child in children:
                self.root.remove(child)
                wrapper.append(child)

            # 4. Append wrapper to main root
            self.root.append(wrapper)
            self.modified = True
            return Result.ok(f"Wrapped {len(children)} items under <{new_root_tag}>.")

    def merge_from(self, path: str, password: str = None) -> Result:
        """Merges external file content into current root."""
        if not self.tree: return Result.fail("No active manifest.")
        try:
            raw = self.storage.load(path, password)
            src_root = etree.fromstring(raw)
        except PasswordRequired: raise
        except Exception as e: return Result.fail(f"Merge error: {e}")

        with self.transaction():
            c = 0
            for child in src_root:
                self.root.append(child)
                c += 1
            self.modified = True
            return Result.ok(f"Merged {c} items.")

    def search(self, xpath: str) -> List[etree._Element]:
        if not self.tree: return []
        ok, results = self._safe_xpath(xpath)
        return results if ok else []

class ManifestView:
    """Stateless rendering engine."""
    @staticmethod
    def render(nodes, style="tree", max_depth: int = None) -> str:
        """Render nodes with optional depth limiting.
        
        Args:
            nodes: List of XML elements to render
            style: "tree" or "table" rendering style
            max_depth: Maximum depth to traverse (None = unlimited)
            
        Returns:
            Formatted string representation
        """
        if not nodes: return "No data."
        if style == "table": return ManifestView._table(nodes, max_depth)
        return ManifestView._tree(nodes, max_depth)

    @staticmethod
    def _tree(nodes, max_depth: int = None) -> str:
        """Tree-style rendering with depth control."""
        lines = []
        def _recurse(node, level, is_root_item, current_depth=0):
            # Check depth limit
            if max_depth is not None and current_depth >= max_depth:
                return
            
            tag, topic = node.tag, node.get("topic", "")
            text, status = (node.text or "").strip(), node.get("status")
            resp = node.get("resp", "")
            
            # Headers
            if is_root_item:
                lines.append(f"\n## {topic if topic else tag.upper()}")
                if not text and not status:
                    for c in node: _recurse(c, level + 1, False, current_depth + 1)
                    return

            # Items
            indent = "  " * level
            mark = "[x]" if status == "done" else ("[ ]" if status else "-")
            stat_str = f"({status}) " if status and status != "done" else ""
            resp_str = f"@{resp} " if resp else ""
            
            content = f"**{topic}**" if topic else f"<{tag}>"
            if text: content += f": {text}"
            
            ignore = {'topic', 'status', 'resp'}
            attrs = [f"{k}={v}" for k,v in node.attrib.items() if k not in ignore]
            if attrs: content += f" [{' '.join(attrs)}]"

            lines.append(f"{indent}{mark} {stat_str}{resp_str}{content}")
            
            # Recurse into children (with depth tracking)
            for c in node: _recurse(c, level + 1, False, current_depth + 1)

        for n in nodes:
            is_root = (n.getparent() is not None and n.getparent().tag == "manifest")
            _recurse(n, 0, is_root, 0)
        return "\n".join(lines)

    @staticmethod
    def _table(nodes, max_depth: int = None) -> str:
        """Table-style rendering with depth control."""
        rows = []
        def _flat(n, d):
            # Check depth limit
            if max_depth is not None and d >= max_depth:
                return
            
            rows.append({
                "ID": n.get("id") or "-",
                "Tag": n.tag, 
                "Topic": ("  "*d) + (n.get("topic") or ""), 
                "Status": n.get("status") or "-",
                "Resp": n.get("resp") or "-"
            })
            for c in n: _flat(c, d+1)
        for n in nodes: _flat(n, 0)
        
        cols = ["ID", "Topic", "Tag", "Status", "Resp"]
        widths = {c: max(len(c), max((len(r[c]) for r in rows), default=0)) for c in cols}
        fmt = " | ".join(f"{{{c}:<{widths[c]}}}" for c in cols)
        
        return "\n".join([fmt.format(**{c:c for c in cols}), "-"*sum(widths.values()), 
                          *[fmt.format(**r) for r in rows]])