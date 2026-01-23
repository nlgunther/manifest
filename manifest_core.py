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
from storage import StorageManager, PasswordRequired

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
    """Data Transfer Object for Node operations."""
    tag: str
    topic: Optional[str] = None
    status: Optional[Union[str, TaskStatus]] = None
    text: Optional[str] = None
    attrs: Dict[str, str] = field(default_factory=dict)

    def to_xml_attrs(self) -> Dict[str, str]:
        a = self.attrs.copy()
        if self.topic: a['topic'] = self.topic
        if self.status: a['status'] = str(self.status)
        return a

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
    """
    def __init__(self):
        self.storage = StorageManager()
        self.tree: Optional[etree._ElementTree] = None
        self.root: Optional[etree._Element] = None
        self.filepath: Optional[str] = None
        self.password: Optional[str] = None
        self.modified: bool = False

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

    def load(self, filepath: str, password: str = None) -> Result:
        path = filepath.strip('"\'')
        if "." not in os.path.basename(path): path += ".xml"
        
        if not os.path.exists(path):
            self.root = etree.Element("manifest")
            self.tree = etree.ElementTree(self.root)
            self.filepath, self.password, self.modified = path, password, True
            return Result.ok(f"Created new: {path}")

        try:
            raw = self.storage.load(path, password)
            self.root = etree.fromstring(raw, etree.XMLParser(remove_blank_text=True))
            self.tree = etree.ElementTree(self.root)
            self.filepath, self.password, self.modified = path, password, False
            return Result.ok(f"Loaded {path}")
        except PasswordRequired: raise
        except Exception as e: return Result.fail(str(e))

    def save(self, filepath: str = None, new_pass: str = None) -> Result:
        target = (filepath or self.filepath or "").strip('"\'')
        if not target: return Result.fail("No file specified.")
        pwd = new_pass if new_pass is not None else self.password

        try:
            xml = etree.tostring(self.root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
            self.storage.save(target, xml, pwd)
            self.filepath, self.password, self.modified = target, pwd, False
            return Result.ok(f"Saved to {target}")
        except Exception as e: return Result.fail(str(e))

    def add_node(self, parent_xpath: str, spec: NodeSpec) -> Result:
        if not self.tree: return Result.fail("No file loaded.")
        with self.transaction():
            Validator.validate_tag(spec.tag)
            ok, parents = self._safe_xpath(parent_xpath)
            if not ok:
                return Result.fail(parents)  # parents contains error message
            if not parents:
                return Result.fail(f"Parent not found: {parent_xpath}")
            
            for p in parents:
                n = etree.SubElement(p, spec.tag, **spec.to_xml_attrs())
                if spec.text: n.text = Validator.sanitize(spec.text)
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
    def render(nodes, style="tree") -> str:
        if not nodes: return "No data."
        if style == "table": return ManifestView._table(nodes)
        return ManifestView._tree(nodes)

    @staticmethod
    def _tree(nodes) -> str:
        lines = []
        def _recurse(node, level, is_root_item):
            tag, topic = node.tag, node.get("topic", "")
            text, status = (node.text or "").strip(), node.get("status")
            
            # Headers
            if is_root_item:
                lines.append(f"\n## {topic if topic else tag.upper()}")
                if not text and not status:
                    for c in node: _recurse(c, level + 1, False)
                    return

            # Items
            indent = "  " * level
            mark = "[x]" if status == "done" else ("[ ]" if status else "-")
            stat_str = f"({status}) " if status and status != "done" else ""
            
            content = f"**{topic}**" if topic else f"<{tag}>"
            if text: content += f": {text}"
            
            ignore = {'topic', 'status'}
            attrs = [f"{k}={v}" for k,v in node.attrib.items() if k not in ignore]
            if attrs: content += f" [{' '.join(attrs)}]"

            lines.append(f"{indent}{mark} {stat_str}{content}")
            for c in node: _recurse(c, level + 1, False)

        for n in nodes:
            is_root = (n.getparent() is not None and n.getparent().tag == "manifest")
            _recurse(n, 0, is_root)
        return "\n".join(lines)

    @staticmethod
    def _table(nodes) -> str:
        rows = []
        def _flat(n, d):
            rows.append({
                "Tag": n.tag, 
                "Topic": ("  "*d) + (n.get("topic") or ""), 
                "Status": n.get("status") or "-"
            })
            for c in n: _flat(c, d+1)
        for n in nodes: _flat(n, 0)
        
        cols = ["Topic", "Tag", "Status"]
        widths = {c: max(len(c), max((len(r[c]) for r in rows), default=0)) for c in cols}
        fmt = " | ".join(f"{{:<{widths[c]}}}" for c in cols)
        
        return "\n".join([fmt.format(**{c:c for c in cols}), "-"*sum(widths.values()), 
                          *[fmt.format(**r) for r in rows]])