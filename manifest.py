#!/usr/bin/env python3
"""
Manifest Manager CLI v3.3
==========================

Interactive shell for hierarchical XML data management.
Supports plain XML and encrypted 7z archives.

Usage:
    python manifest.py
    
Commands:
    load, save, add, edit, list, find, wrap, merge, autoid, cheatsheet, exit

Example Session:
    (manifest) load myproject --autosc
    (myproject.xml) add --tag task --topic "New feature"
    (myproject.xml) find a3f
    (myproject.xml) edit a3f7b2c1 --status done
    (myproject.xml) save backup.7z

Features:
    - XPath-based querying with CSS selector support
    - Fast ID lookups via sidecar index (O(1))
    - Smart edit: auto-detects ID vs XPath
    - Encrypted backups via 7z with password protection
    - Transaction support with automatic rollback on errors
    - Multiple view formats (tree, table)
    - Configuration files for customization
    - Merge multiple manifest files
    - Wrap top-level nodes under new containers

Security:
    - Password retry with maximum attempt limits
    - Path validation prevents injection attacks
    - XML validation prevents malformed documents
    - Unsaved changes warning on exit
"""

import sys
import cmd
import shlex
import argparse
import getpass
import os

# --- Imports ---
try:
    from manifest_core import ManifestRepository, NodeSpec, ManifestView, Validator
    from storage import PasswordRequired
except ImportError as e:
    print(f"Critical Error: Missing core modules. {e}")
    sys.exit(1)


# --- Helper Functions for v3.3 ---

def _is_id_selector(selector: str, repo) -> bool:
    """Detect if selector is an ID or XPath.
    
    Detection heuristics:
        1. 8-char hex string → ID (our auto-generated format)
        2. Contains XPath syntax (/, [, @, *) → XPath
        3. Exists in sidecar → ID
        4. Default → XPath (safe fallback)
    
    Args:
        selector: User-provided selector string
        repo: Repository to check sidecar
        
    Returns:
        True if selector is likely an ID, False if XPath
        
    Examples:
        >>> _is_id_selector('a3f7b2c1', repo)
        True  # 8-char hex
        >>> _is_id_selector('//task[@status="active"]', repo)
        False  # Has XPath syntax
    """
    # 8-char hex (our auto-generated format)
    if len(selector) == 8 and all(c in '0123456789abcdef' for c in selector):
        return True
    
    # XPath syntax indicators
    if any(c in selector for c in ['/', '[', '@', '*', '=']):
        return False
    
    # Check sidecar (definitive proof)
    if repo.id_sidecar and repo.id_sidecar.exists(selector):
        return True
    
    # Default to XPath for safety (backward compatible)
    return False


# =============================================================================
# COMPREHENSIVE CHEATSHEET
# =============================================================================

CHEATSHEET = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                      MANIFEST MANAGER v3.3 CHEATSHEET                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

FILE OPERATIONS
───────────────
  load <file>           Load XML or 7z file (auto-creates if missing)
  load <file> --autosc  Load and auto-create ID sidecar if missing
  save [file]           Save to current or new file
  merge <file>          Import all nodes from another manifest

NODE OPERATIONS
───────────────
  add --tag <n>      Create new node
      --parent <xpath>  Where to add (default: /* = root's children)
      --topic "text"    Set topic attribute  
      --status <s>      Set status: active|done|pending|blocked|cancelled
      --id <value>      Custom ID (or 'False' to disable auto-ID)
      -a key=value      Custom attribute (repeatable)
      "body text"       Text content of node

  edit <id_or_xpath>    Modify or delete nodes (auto-detects ID vs XPath)
      --text "new"      Update text content
      --topic "new"     Update topic attribute
      --status <s>      Update status
      -a key=value      Add/update attribute
      --delete          Remove matching nodes
      --id              Force ID interpretation
      --xpath           Force XPath interpretation

SEARCHING & VIEWING
───────────────────
  find <prefix>         Find by ID prefix (fast sidecar lookup)
      --tree            Show full subtrees for matches
      --depth N         Limit tree depth

  list [xpath]          Display nodes (default: /* = all top-level)
      --style tree      Hierarchical view (default)
      --style table     Tabular view
      --depth N         Limit tree depth

  autoid                Add IDs to elements that lack them
      --overwrite       Replace ALL existing IDs

STRUCTURE
─────────
  wrap --root <tag>     Wrap all top-level nodes under new container

XPATH QUICK REFERENCE
─────────────────────
  /*                    All direct children of root
  /manifest/*           Same as above (explicit root)
  //task                All <task> elements anywhere
  //task[@status]       Tasks that have a status attribute
  //task[@status='done'] Tasks with status="done"  
  //*[@topic]           Any element with topic attribute
  //project/task        Tasks directly inside projects
  //task[1]             First task element
  //task[last()]        Last task element
  //task[contains(@topic,'bug')]  Tasks with 'bug' in topic

v3.3 NEW FEATURES
─────────────────
  ID Sidecar:
    - Fast O(1) ID lookups
    - Auto-syncs on save
    - Created with --autosc flag

  Smart Edit:
    - edit a3f7b2c1 --topic "New"     # By ID (auto-detected)
    - edit //task --status active      # By XPath (auto-detected)
    - edit --id BUG-123 --topic "Fix"  # Custom ID (explicit)

  Prominent IDs:
    - find command shows IDs first
    - Easy copy/paste workflow

  Configuration:
    - Per-file: myfile.xml.config
    - Global: ~/.config/manifest/config.yaml

STATUS VALUES
─────────────
  active                In progress
  done                  Completed  
  pending               Not yet started
  blocked               Waiting on dependency
  cancelled             Abandoned

COMMON WORKFLOWS
────────────────
  Quick Task Management with IDs:
    1. load tasks.xml --autosc
    2. add --tag task --status active "Today's work"
    3. find <first_3_chars_of_id>
    4. edit <id> --status done
    5. save
  
  Weekly Archive:
    1. load weekly.xml
    2. edit "//task[@status='done']" --topic "Week-01"
    3. wrap --root "archive_2026_w01"
    4. save archive_2026_w01.7z
  
  Merge Team Updates:
    1. load main.xml
    2. merge alice.xml
    3. merge bob.xml
    4. list //task --style table
    5. save team_combined.xml

EXAMPLES
────────
  # Start new project with sidecar
  load myproject --autosc
  add --tag project --topic "Q1 Planning"
  add --tag task --parent "//project" --status active "Define roadmap"
  save

  # Edit by ID (fast!)
  find def
  edit def456ab --status done

  # Edit by XPath (still works!)
  edit "//task[contains(text(),'roadmap')]" --status done

  # Create encrypted backup
  save archive.7z

  # Reorganize: wrap loose items
  load old_tasks.xml
  wrap --root archive
  save

  # Force rebuild sidecar
  load myfile.xml --rebuildsc

TIPS
────
  • IDs shown first in find results for easy copy/paste
  • Use ID prefixes: 'find a3f' instead of full 'find a3f7b2c1'
  • XPath is case-sensitive: //Task ≠ //task
  • Use quotes around text with spaces: --topic "My Topic"
  • Tab completion works for commands
  • Ctrl+D or 'exit' to quit (warns if unsaved changes)
  • Maximum 3 password attempts for encrypted files
  • Tags cannot start with 'xml' (any case) - XML specification
  • Config files: see DOCUMENTATION_v3.3.md for full guide
"""

class ParserControl(Exception): pass

class SafeParser(argparse.ArgumentParser):
    """Prevents argparse from killing the shell on error."""
    def error(self, message):
        print(f"ArgError: {message}\n")
        self.print_help()
        raise ParserControl()
    def exit(self, status=0, message=None):
        if message: print(message)
        raise ParserControl()

class ManifestShell(cmd.Cmd):
    intro = "Manifest Manager v3.3. Type 'help' or 'cheatsheet' for commands."
    prompt = "(manifest) "

    def __init__(self):
        super().__init__()
        self.repo = ManifestRepository()
        self._confirm_exit = False

    def _exec(self, func):
        """Safe execution wrapper."""
        try: func()
        except ParserControl: pass
        except ValueError as e: print(f"Input Error: {e}")
        except Exception as e: print(f"System Error: {e}")

    def _get_pass(self, prompt="Password: "):
        try: return getpass.getpass(prompt)
        except KeyboardInterrupt: return None

    def _with_password_retry(self, operation, filepath, success_callback=None):
        """Execute operation with password retry loop.
        
        Args:
            operation: Callable(filepath, password) -> Result
            filepath: Path to pass to operation
            success_callback: Optional callable(result) on success
        
        Returns:
            Result object from operation, or None if cancelled
        """
        pwd = None
        max_attempts = 3
        attempts = 0
        
        while attempts < max_attempts:
            try:
                result = operation(filepath, pwd)
                print(result.message)
                if result.success:
                    if success_callback:
                        success_callback(result)
                    return result
                else:
                    # Operation failed for non-password reason
                    return result
            except PasswordRequired:
                attempts += 1
                if attempts >= max_attempts:
                    print(f"Maximum password attempts ({max_attempts}) exceeded.")
                    return None
                pwd = self._get_pass(f"Enter password for {filepath} (attempt {attempts}/{max_attempts}): ")
                if pwd is None:
                    return None

    @staticmethod
    def _parse_attrs(attr_list: list | None) -> dict:
        """Parse attribute list into dictionary.
        
        Args:
            attr_list: List like ['-a', 'k=v', '-a', 'k2=v2']
            
        Returns:
            Dict like {'k': 'v', 'k2': 'v2'}
            
        Note:
            - Items without '=' are silently ignored
            - Later values override earlier for same key
            - Uses split("=", 1) to allow '=' in values
        """
        if not attr_list:
            return {}
        
        attrs = {}
        for item in attr_list:
            if "=" not in item:
                continue  # Skip malformed items
            key, value = item.split("=", 1)
            attrs[key] = value
        
        return attrs

    # --- Commands ---

    def do_load(self, arg):
        """Load manifest: load <file> [--auto-sidecar] [--rebuild-sidecar]
        
        Examples:
            load myfile.xml
            load myfile.xml --autosc          # Create sidecar if missing
            load myfile.xml --rebuildsc       # Force rebuild sidecar
        """
        p = SafeParser(prog="load")
        p.add_argument("filename")
        p.add_argument("--auto-sidecar", "--autosc", action="store_true",
                       help="Auto-create sidecar if missing")
        p.add_argument("--rebuild-sidecar", "--rebuildsc", action="store_true",
                       help="Force rebuild sidecar")
        
        def _run():
            args = p.parse_args(shlex.split(arg))
            
            def on_success(result):
                self.prompt = f"({os.path.basename(self.repo.filepath)}) "
            
            # Call load with sidecar flags
            def load_with_flags(filepath, password):
                return self.repo.load(
                    filepath,
                    password,
                    auto_sidecar=args.auto_sidecar,
                    rebuild_sidecar=args.rebuild_sidecar
                )
            
            self._with_password_retry(load_with_flags, args.filename, on_success)
        
        self._exec(_run)

    def do_save(self, arg):
        """Save file: save [filename]"""
        pwd = self.repo.password
        if arg and arg.endswith(".7z") and not pwd:
             pwd = self._get_pass(f"Set password for {arg}: ")
        print(self.repo.save(arg, pwd).message)

    def do_add(self, arg):
        """Add node: add --tag task "Desc"
        
        Options:
          --id <value>     Custom ID (default: auto-generated 8-char hex)
          --id False       Disable auto-ID generation
        """
        p = SafeParser(prog="add", description="Add node")
        p.add_argument("--tag", required=True, help="Tag name")
        p.add_argument("--parent", default="/*", help="Parent XPath")
        p.add_argument("--topic", help="Topic/Title")
        p.add_argument("--status", help="Status")
        p.add_argument("--id", dest="node_id", help="ID (or 'False' to disable auto-ID)")
        p.add_argument("-a", "--attr", action="append", help="k=v attrs")
        p.add_argument("text", nargs="?", help="Body text")

        def _run():
            args = p.parse_args(shlex.split(arg))
            attrs = self._parse_attrs(args.attr)
            
            # Handle --id parameter
            auto_id = True
            if args.node_id:
                if args.node_id.lower() in ('false', 'no', 'off', '0'):
                    auto_id = False  # Explicitly disable
                else:
                    attrs['id'] = args.node_id  # Custom ID
                    auto_id = False  # Don't auto-generate if custom provided
            
            spec = NodeSpec(args.tag, args.topic, args.status, args.text, attrs)
            print(self.repo.add_node(args.parent, spec, auto_id=auto_id).message)
        self._exec(_run)

    def do_wrap(self, arg):
        """
        Wrap all top-level items under a new root tag.
        Usage: wrap --root <new_tag_name>
        """
        p = SafeParser(prog="wrap", description="Reparent top items")
        p.add_argument("--root", default="root", help="New root tag name")
        
        def _run():
            args = p.parse_args(shlex.split(arg))
            print(self.repo.wrap_content(args.root).message)
        self._exec(_run)

    def do_merge(self, arg):
        """Merge external file: merge <filename>"""
        if not arg: return print("Usage: merge <filename>")
        self._with_password_retry(self.repo.merge_from, arg)

    def do_find(self, arg):
        """Find nodes by ID prefix: find <prefix> [--tree] [--depth N]
        
        Examples:
          find a3f              # Find IDs starting with 'a3f' (flat view)
          find a3f --tree       # Show full subtrees
          find a3f --tree --depth 2  # Limit depth
        """
        p = SafeParser(prog="find")
        p.add_argument("prefix", help="ID prefix to search")
        p.add_argument("--tree", action="store_true", help="Show tree view")
        p.add_argument("--depth", type=int, help="Limit tree depth")
        
        def _run():
            args = p.parse_args(shlex.split(arg))
            result = self.repo.search_by_id_prefix(args.prefix)
            
            if not result.success:
                print(f"Error: {result.message}")
                return
            
            print(f"\n{result.message}")
            
            if args.tree:
                # Tree view - show full subtrees
                for i, elem in enumerate(result.data, 1):
                    if i > 1:
                        print("\n" + "─" * 60)
                    print(f"Match {i}: {self._build_xpath(elem)}")
                    print("─" * 60)
                    print(ManifestView.render([elem], "tree", max_depth=args.depth))
            else:
                # Flat view - show IDs prominently (v3.3)
                for elem in result.data:
                    # Build XPath
                    xpath = self._build_xpath(elem)
                    
                    # Display with ID first and prominent
                    elem_id = elem.get("id", "")
                    topic = elem.get("topic", "")
                    status = elem.get("status", "")
                    
                    print()  # Blank line before each result
                    if elem_id:
                        print(f"  ID: {elem_id}")  # ID first, easy to copy
                    print(f"     Path: {xpath}")
                    if topic:
                        print(f"     Topic: {topic}")
                    if status:
                        print(f"     Status: {status}")
        
        self._exec(_run)

    @staticmethod
    def _build_xpath(elem) -> str:
        """Build XPath for an element."""
        path_parts = []
        current = elem
        while current is not None and current.tag != "manifest":
            tag = current.tag
            elem_id = current.get("id", "")
            if elem_id:
                tag = f"{tag}[@id='{elem_id}']"
            path_parts.insert(0, tag)
            current = current.getparent()
        
        return "/" + "/".join(path_parts) if path_parts else f"/{elem.tag}"

    def do_autoid(self, arg):
        """Auto-generate IDs for elements that lack them.
        
        Usage: 
          autoid              # Add IDs to elements without them
          autoid --overwrite  # Replace ALL IDs with new ones
        
        Examples:
          autoid              # Safe: only adds missing IDs
          autoid --overwrite  # Caution: replaces existing IDs
        """
        p = SafeParser(prog="autoid", description="Add IDs to elements")
        p.add_argument("--overwrite", action="store_true", 
                      help="Replace existing IDs (default: skip elements with IDs)")
        
        def _run():
            args = p.parse_args(shlex.split(arg))
            result = self.repo.ensure_ids(overwrite=args.overwrite)
            print(result.message)
            if result.success and not args.overwrite:
                print("Tip: Use 'autoid --overwrite' to replace existing IDs")
        self._exec(_run)

    def do_list(self, arg):
        """View data: list [xpath] [--style tree|table] [--depth N]"""
        p = SafeParser(prog="list")
        p.add_argument("xpath", nargs="?", default="/*")
        p.add_argument("--style", default="tree", choices=["tree", "table"])
        p.add_argument("--depth", type=int, help="Limit tree depth")
        
        def _run():
            args = p.parse_args(shlex.split(arg))
            print(ManifestView.render(
                self.repo.search(args.xpath), 
                args.style, 
                max_depth=args.depth
            ))
        self._exec(_run)

    def do_edit(self, arg):
        """Edit/Delete: edit <id_or_xpath> [options]
        
        Smart detection:
            - 8-char hex (e.g., 'a3f7b2c1') → Treated as ID
            - XPath syntax (e.g., '//task') → Treated as XPath
            - Exists in sidecar → Treated as ID
            - Use --xpath to force XPath, --id to force ID
        
        Examples:
            edit a3f7b2c1 --topic "Updated"           # By ID (auto-detected)
            edit --id BUG-123 --topic "Fixed"         # By ID (explicit)
            edit "//task[@status='pending']" --status active  # By XPath
        """
        p = SafeParser(prog="edit")
        p.add_argument("selector", help="Element ID or XPath")
        p.add_argument("--xpath", dest="force_xpath", action="store_true",
                       help="Force XPath interpretation")
        p.add_argument("--id", dest="force_id", action="store_true",
                       help="Force ID interpretation")
        p.add_argument("--topic", help="New topic")
        p.add_argument("--status", help="New status")
        p.add_argument("--text", help="New body text")
        p.add_argument("-a", "--attr", action="append", help="k=v attributes")
        p.add_argument("--delete", action="store_true", help="Delete node")
        
        def _run():
            args = p.parse_args(shlex.split(arg))
            
            # Determine if selector is ID or XPath
            if args.force_id:
                is_id = True
            elif args.force_xpath:
                is_id = False
            else:
                is_id = _is_id_selector(args.selector, self.repo)
            
            # Build NodeSpec
            attrs = self._parse_attrs(args.attr)
            spec = NodeSpec("ignored", args.topic, args.status, args.text, attrs)
            
            # Edit by ID or XPath
            if is_id:
                result = self.repo.edit_node_by_id(args.selector, spec, args.delete)
            else:
                result = self.repo.edit_node(args.selector, spec, args.delete)
            
            print(result.message)
        
        self._exec(_run)

    def do_cheatsheet(self, _):
        """Display comprehensive command reference."""
        print(CHEATSHEET)
    
    def do_exit(self, _):
        if self.repo.modified and not self._confirm_exit:
            print("Unsaved changes! Type 'save' or 'exit' again.")
            self._confirm_exit = True
            return False
        return True
    def do_EOF(self, _): return self.do_exit(_)


def main():
    """Entry point for pip-installed command."""
    try:
        ManifestShell().cmdloop()
    except KeyboardInterrupt:
        print("\nInterrupted.")


if __name__ == "__main__":
    main()
