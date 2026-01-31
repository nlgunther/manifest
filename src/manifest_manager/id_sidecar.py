"""
ID Sidecar - Fast ID Lookups
=============================

Maintains ID→XPath mapping in a JSON sidecar file for O(1) lookups.

Backend: JSON file (myfile.xml.ids)
Extension Points:
    - SQLite backend for large manifests - see _load() and _save()
    - Redis backend for multi-user - add RedisIDIndex subclass
    - In-memory only mode - set self.persist = False

Performance:
    - Without sidecar: O(n) - full tree traversal per lookup
    - With sidecar: O(1) - hash table lookup
    
Example:
    >>> sidecar = IDSidecar('/path/to/manifest.xml', config)
    >>> sidecar.load()
    >>> xpath = sidecar.get('a3f7b2c1')
    >>> print(xpath)
    "/manifest/project[@id='a3f7b2c1']"
"""

import os
import json
import logging
from typing import Dict, Optional, Set
from lxml import etree

logger = logging.getLogger(__name__)


class IDSidecar:
    """Manages ID→XPath index for fast lookups.
    
    File format: JSON
        {
          "a3f7b2c1": "/manifest/project[@id='a3f7b2c1']",
          "b5e8d9a2": "/manifest/task[@id='b5e8d9a2']"
        }
    """
    
    def __init__(self, manifest_path: str, config):
        """Initialize ID sidecar.
        
        Args:
            manifest_path: Path to manifest file
            config: Config object for behavior settings
        """
        self.manifest_path = manifest_path
        self.sidecar_path = manifest_path + ".ids"
        self.config = config
        self.index: Dict[str, str] = {}  # {id: xpath}
        self.dirty: bool = False
        
        # EXTENSION STUB: Backend selection
        # self.backend = self._select_backend()
        # Backends: 'json' (default), 'sqlite', 'redis', 'memory'
    
    def load(self) -> None:
        """Load sidecar from disk.
        
        EXTENSION POINT: Backend abstraction
        
        To add SQLite backend:
            if self.backend == 'sqlite':
                conn = sqlite3.connect(self.sidecar_path)
                cursor = conn.execute('SELECT id, xpath FROM id_index')
                self.index = dict(cursor.fetchall())
                conn.close()
        """
        if not os.path.exists(self.sidecar_path):
            self.index = {}
            return
        
        try:
            with open(self.sidecar_path, 'r') as f:
                self.index = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load sidecar: {e}")
            self.index = {}
    
    def save(self) -> None:
        """Write sidecar to disk if dirty.
        
        EXTENSION POINT: Backend abstraction
        
        To add SQLite backend:
            if self.backend == 'sqlite':
                conn = sqlite3.connect(self.sidecar_path)
                conn.executemany(
                    'INSERT OR REPLACE INTO id_index (id, xpath) VALUES (?, ?)',
                    self.index.items()
                )
                conn.commit()
                conn.close()
        """
        if not self.dirty:
            return
        
        try:
            with open(self.sidecar_path, 'w') as f:
                json.dump(self.index, f, indent=2, sort_keys=True)
            self.dirty = False
        except IOError as e:
            logger.error(f"Failed to save sidecar: {e}")
    
    def get(self, elem_id: str) -> Optional[str]:
        """Get XPath for an ID.
        
        Args:
            elem_id: Element ID to look up
            
        Returns:
            XPath string or None if not found
        """
        return self.index.get(elem_id)
    
    def exists(self, elem_id: str) -> bool:
        """Check if ID exists in index."""
        return elem_id in self.index
    
    def add(self, elem_id: str, xpath: str) -> None:
        """Add ID mapping.
        
        Args:
            elem_id: Element ID
            xpath: XPath to element
        """
        self.index[elem_id] = xpath
        self.dirty = True
    
    def remove(self, elem_id: str) -> None:
        """Remove ID mapping."""
        if elem_id in self.index:
            del self.index[elem_id]
            self.dirty = True
    
    def all_ids(self) -> Set[str]:
        """Get all IDs in the index."""
        return set(self.index.keys())
    
    def rebuild(self, root: etree._Element) -> None:
        """Rebuild entire index from XML tree.
        
        Args:
            root: Root element of XML tree
        """
        self.index.clear()
        
        for elem in root.iter():
            elem_id = elem.get("id")
            if elem_id:
                xpath = self._build_xpath(elem)
                self.index[elem_id] = xpath
        
        self.dirty = True
        logger.info(f"Rebuilt sidecar with {len(self.index)} IDs")
    
    def verify_and_repair(self, root: etree._Element) -> bool:
        """Verify sidecar integrity and repair if needed.
        
        Args:
            root: Root element to verify against
            
        Returns:
            True if sidecar was valid or repaired, False if user declined repair
        """
        if not self.index:
            return True  # Empty is valid
        
        # Check for corruption
        corrupted = False
        for elem_id, xpath in list(self.index.items()):
            try:
                matches = root.xpath(xpath)
                if not matches or matches[0].get("id") != elem_id:
                    corrupted = True
                    break
            except:
                corrupted = True
                break
        
        if not corrupted:
            return True
        
        # Handle corruption based on config
        handling = self.config.get('sidecar.corruption_handling', 'warn_and_ask')
        
        if handling == 'silent':
            self.rebuild(root)
            self.save()
            return True
        
        elif handling == 'warn_and_proceed':
            logger.warning(f"ID sidecar corrupted for {self.manifest_path}, rebuilding...")
            self.rebuild(root)
            self.save()
            return True
        
        else:  # warn_and_ask
            logger.warning(f"ID sidecar corrupted for {self.manifest_path}")
            
            if self.config.get('sidecar.auto_rebuild', False):
                logger.info("Auto-rebuild enabled, rebuilding...")
                self.rebuild(root)
                self.save()
                return True
            
            # Ask user
            response = input("Rebuild sidecar? [Y/n]: ").strip().lower()
            if response in ('', 'y', 'yes'):
                self.rebuild(root)
                self.save()
                return True
            else:
                logger.warning("Continuing with corrupted sidecar")
                return False
    
    @staticmethod
    def _build_xpath(elem: etree._Element) -> str:
        """Build absolute XPath for an element.
        
        Args:
            elem: Element to build XPath for
            
        Returns:
            Absolute XPath string
            
        Example:
            >>> elem = <task id="abc123" topic="Test"/>
            >>> _build_xpath(elem)
            "/manifest/project[@id='xyz']/task[@id='abc123']"
        """
        parts = []
        current = elem
        
        while current is not None and current.tag != 'manifest':
            tag = current.tag
            elem_id = current.get("id")
            
            if elem_id:
                # Use ID predicate for uniqueness
                tag = f"{tag}[@id='{elem_id}']"
            
            parts.insert(0, tag)
            current = current.getparent()
        
        # Add root
        parts.insert(0, "manifest")
        
        return "/" + "/".join(parts)
    
    # EXTENSION STUB: Multiple backends
    # def _select_backend(self) -> str:
    #     """Select storage backend based on config or manifest size.
    #     
    #     To implement:
    #         1. Check config for explicit backend choice
    #         2. Auto-select based on manifest size:
    #            - < 1000 IDs: JSON (fast, simple)
    #            - < 10000 IDs: SQLite (indexed, transactional)
    #            - > 10000 IDs: Redis (distributed, cached)
    #         3. Return backend name
    #     
    #     Example:
    #         backend = self.config.get('sidecar.backend', 'auto')
    #         if backend == 'auto':
    #             if len(self.index) > 10000:
    #                 return 'sqlite'
    #         return backend
    #     """
    #     return 'json'
    
    # EXTENSION STUB: Differential updates
    # def update_diff(self, added: Set[str], removed: Set[str], modified: Dict[str, str]) -> None:
    #     """Update sidecar with differential changes instead of full rebuild.
    #     
    #     More efficient than rebuild() for incremental updates.
    #     
    #     Args:
    #         added: Set of new IDs to add
    #         removed: Set of IDs to remove
    #         modified: Dict of {id: new_xpath} for changed paths
    #     
    #     To use:
    #         Track changes during operations, then call update_diff()
    #         instead of rebuild()
    #     """
    #     pass
