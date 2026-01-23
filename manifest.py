#!/usr/bin/env python3
"""
Manifest Manager CLI
====================

Interactive shell for hierarchical XML data management.
Supports plain XML and encrypted 7z archives.

Usage:
    python manifest.py
    
Commands:
    load, save, add, edit, list, wrap, merge, cheatsheet, exit

Example Session:
    (manifest) load myproject
    (myproject.xml) add --tag task --topic "New feature"
    (myproject.xml) list //task
    (myproject.xml) save backup.7z

Features:
    - XPath-based querying with CSS selector support
    - Encrypted backups via 7z with password protection
    - Transaction support with automatic rollback on errors
    - Multiple view formats (tree, table)
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

# =============================================================================
# COMPREHENSIVE CHEATSHEET
# =============================================================================

CHEATSHEET = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        MANIFEST MANAGER v3.0 CHEATSHEET                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

FILE OPERATIONS
───────────────
  load <file>           Load XML or 7z file (auto-creates if missing)
  save [file]           Save to current or new file
  merge <file>          Import all nodes from another manifest

NODE OPERATIONS
───────────────
  add --tag <name>      Create new node
      --parent <xpath>  Where to add (default: /* = root's children)
      --topic "text"    Set topic attribute  
      --status <s>      Set status: active|done|pending|blocked|cancelled
      -a key=value      Custom attribute (repeatable)
      "body text"       Text content of node

  edit --xpath <query>  Modify or delete nodes
      --text "new"      Update text content
      --topic "new"     Update topic attribute
      --status <s>      Update status
      -a key=value      Add/update attribute
      --delete          Remove matching nodes

VIEWING
───────
  list [xpath]          Display nodes (default: /* = all top-level)
      --style tree      Hierarchical view (default)
      --style table     Tabular view

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

STATUS VALUES
─────────────
  active                In progress
  done                  Completed  
  pending               Not yet started
  blocked               Waiting on dependency
  cancelled             Abandoned

COMMON WORKFLOWS
────────────────
  Daily Task Management:
    1. load tasks.xml
    2. add --tag task --status active "Today's work"
    3. list //task[@status='active']
    4. edit --xpath "//task[1]" --status done
    5. save
  
  Weekly Archive:
    1. load weekly.xml
    2. edit --xpath "//task[@status='done']" --topic "Week-01"
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
  # Start new project
  load myproject
  add --tag project --topic "Q1 Planning"
  add --tag task --parent "//project" --status active "Define roadmap"
  save

  # Complete a task  
  edit --xpath "//task[contains(text(),'roadmap')]" --status done

  # Create encrypted backup
  save archive.7z

  # Reorganize: wrap loose items
  load old_tasks.xml
  wrap --root archive
  save

  # Merge files
  load main.xml  
  merge imported.xml
  save

TIPS
────
  • XPath is case-sensitive: //Task ≠ //task
  • Use quotes around text with spaces: --topic "My Topic"
  • Tab completion works for commands
  • Ctrl+D or 'exit' to quit (warns if unsaved changes)
  • Maximum 3 password attempts for encrypted files
  • Tags cannot start with 'xml' (any case) - XML specification
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
    intro = "Manifest Manager v3.0. Type 'help' or 'cheatsheet' for commands."
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
        """Load a file: load <filename>"""
        if not arg: return print("Usage: load <filename>")
        
        def on_success(result):
            self.prompt = f"({os.path.basename(self.repo.filepath)}) "
        
        self._with_password_retry(self.repo.load, arg, on_success)

    def do_save(self, arg):
        """Save file: save [filename]"""
        pwd = self.repo.password
        if arg and arg.endswith(".7z") and not pwd:
             pwd = self._get_pass(f"Set password for {arg}: ")
        print(self.repo.save(arg, pwd).message)

    def do_add(self, arg):
        """Add node: add --tag task "Desc" """
        p = SafeParser(prog="add", description="Add node")
        p.add_argument("--tag", required=True, help="Tag name")
        p.add_argument("--parent", default="/*", help="Parent XPath")
        p.add_argument("--topic", help="Topic/Title")
        p.add_argument("--status", help="Status")
        p.add_argument("-a", "--attr", action="append", help="k=v attrs")
        p.add_argument("text", nargs="?", help="Body text")

        def _run():
            args = p.parse_args(shlex.split(arg))
            attrs = self._parse_attrs(args.attr)
            spec = NodeSpec(args.tag, args.topic, args.status, args.text, attrs)
            print(self.repo.add_node(args.parent, spec).message)
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

    def do_list(self, arg):
        """View data: list [xpath] [--style tree|table]"""
        p = SafeParser(prog="list")
        p.add_argument("xpath", nargs="?", default="/*")
        p.add_argument("--style", default="tree", choices=["tree", "table"])
        
        def _run():
            args = p.parse_args(shlex.split(arg))
            print(ManifestView.render(self.repo.search(args.xpath), args.style))
        self._exec(_run)

    def do_edit(self, arg):
        """Edit/Delete: edit --xpath <query> [options]"""
        p = SafeParser(prog="edit")
        p.add_argument("--xpath", required=True)
        p.add_argument("--text"); p.add_argument("--status")
        p.add_argument("--topic"); p.add_argument("--delete", action="store_true")
        p.add_argument("-a", "--attr", action="append")

        def _run():
            args = p.parse_args(shlex.split(arg))
            attrs = self._parse_attrs(args.attr)
            spec = NodeSpec("ignored", args.topic, args.status, args.text, attrs)
            print(self.repo.edit_node(args.xpath, spec, args.delete).message)
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

if __name__ == "__main__":
    try: ManifestShell().cmdloop()
    except KeyboardInterrupt: print("\nInterrupted.")