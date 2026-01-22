#!/usr/bin/env python3
"""
Manifest Manager
================
A robust, safe, and extensible CLI for managing hierarchical XML manifests.

Usage:
    python manifest.py
"""

__version__ = "2.2.5"

import cmd
import os
import sys
import shlex
import argparse
import logging
import re
from typing import List, Optional, Dict, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
from lxml import etree

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("manifest")

# --- Models ---

class TaskStatus(str, Enum):
    ACTIVE = "active"
    DONE = "done"
    PENDING = "pending"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    
    def __str__(self): return self.value

@dataclass
class NodeSpec:
    tag: str
    topic: Optional[str] = None
    status: Optional[Union[str, TaskStatus]] = None
    text: Optional[str] = None
    attrs: Dict[str, str] = field(default_factory=dict)

    def to_xml_attrs(self) -> Dict[str, str]:
        final_attrs = self.attrs.copy()
        if self.topic: final_attrs['topic'] = self.topic
        if self.status: final_attrs['status'] = str(self.status)
        return final_attrs

@dataclass
class CommandResult:
    success: bool
    message: str

    @classmethod
    def ok(cls, msg: str): return cls(True, msg)
    @classmethod
    def fail(cls, msg: str): return cls(False, msg)

# --- Validation ---

class Validator:
    TAG_REGEX = re.compile(r'^[a-zA-Z_][\w\-\.]*$')

    @staticmethod
    def validate_tag(tag: str):
        if not tag or not Validator.TAG_REGEX.match(tag):
            raise ValueError(f"Invalid tag '{tag}'. Use alphanumeric/underscores.")
        if tag.lower().startswith('xml'):
            raise ValueError("Tag cannot start with 'xml'.")

    @staticmethod
    def sanitize_text(text: str) -> str:
        if not text: return ""
        return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

# --- Repository (Model) ---

class ManifestRepository:
    def __init__(self):
        self.tree: Optional[etree._ElementTree] = None
        self.root: Optional[etree._Element] = None
        self.filepath: Optional[str] = None
        self.modified: bool = False

    @contextmanager
    def transaction(self):
        if not self.tree: yield; return
        xml_snapshot = etree.tostring(self.root)
        was_modified = self.modified
        try:
            yield
        except Exception as e:
            logger.error(f"Rolling back transaction: {e}")
            self.root = etree.fromstring(xml_snapshot)
            self.tree = etree.ElementTree(self.root)
            self.modified = was_modified
            raise e

    def load(self, filepath: str) -> CommandResult:
        filepath = filepath.strip('"\'')
        if not filepath.lower().endswith('.xml'): filepath += ".xml"
        
        if not os.path.exists(filepath):
            self.root = etree.Element("manifest")
            self.tree = etree.ElementTree(self.root)
            self.filepath = filepath
            self.modified = True
            return CommandResult.ok(f"Created new manifest: {filepath}")

        try:
            parser = etree.XMLParser(remove_blank_text=True)
            self.tree = etree.parse(filepath, parser)
            self.root = self.tree.getroot()
            self.filepath = filepath
            self.modified = False
            return CommandResult.ok(f"Loaded {filepath}")
        except Exception as e:
            return CommandResult.fail(f"Corrupt XML: {e}")

    def save(self, filepath: Optional[str] = None) -> CommandResult:
        target = (filepath or self.filepath or "").strip('"\'')
        if not target: return CommandResult.fail("No file specified.")
        if not target.lower().endswith('.xml'): target += ".xml"

        try:
            self.tree.write(target, pretty_print=True, xml_declaration=True, encoding="UTF-8")
            self.modified = False
            self.filepath = target
            return CommandResult.ok(f"Saved to {target}")
        except Exception as e:
            return CommandResult.fail(f"Save failed: {e}")

    def add_node(self, parent_xpath: str, spec: NodeSpec) -> CommandResult:
        if not self.tree: return CommandResult.fail("No file loaded.")
        with self.transaction():
            Validator.validate_tag(spec.tag)
            try:
                parents = self.root.xpath(parent_xpath)
            except etree.XPathEvalError as e:
                return CommandResult.fail(f"Invalid XPath syntax: {parent_xpath} ({e})")
                
            if not parents: return CommandResult.fail(f"No parent found for XPath: {parent_xpath}")
            
            count = 0
            for p in parents:
                node = etree.SubElement(p, spec.tag, **spec.to_xml_attrs())
                if spec.text: node.text = Validator.sanitize_text(spec.text)
                count += 1
            
            self.modified = True
            return CommandResult.ok(f"Added {count} node(s).")

    def edit_node(self, xpath: str, spec: Optional[NodeSpec] = None, delete: bool = False) -> CommandResult:
        if not self.tree: return CommandResult.fail("No file loaded.")
        with self.transaction():
            try:
                nodes = self.root.xpath(xpath)
            except etree.XPathEvalError as e:
                 return CommandResult.fail(f"Invalid XPath syntax: {xpath} ({e})")

            if not nodes: return CommandResult.fail(f"No matching nodes found for: {xpath}")
            
            if delete:
                for n in nodes:
                    if n.getparent() is not None: n.getparent().remove(n)
                self.modified = True
                return CommandResult.ok(f"Deleted {len(nodes)} node(s).")
            
            # If not deleting, we need a spec
            if spec is None:
                return CommandResult.fail("No changes specified.")

            for n in nodes:
                if spec.text is not None: n.text = Validator.sanitize_text(spec.text)
                for k, v in spec.to_xml_attrs().items(): n.set(k, v)
            
            self.modified = True
            return CommandResult.ok(f"Updated {len(nodes)} node(s).")

    def search(self, xpath: str) -> List[etree._Element]:
        if not self.tree: return []
        try:
            return self.root.xpath(xpath)
        except etree.XPathEvalError:
            return [] 

# --- View (Formatters) ---

class ManifestView:
    _formatters = {}
    @classmethod
    def register(cls, name):
        def dec(f): cls._formatters[name] = f; return f
        return dec
    @classmethod
    def render(cls, nodes, style="tree"):
        return cls._formatters.get(style, cls._formatters['tree'])(nodes)

@ManifestView.register("tree")
def render_tree(nodes):
    lines = []
    def _recurse(node, level):
        indent = "  " * level
        tag, topic = node.tag, node.get("topic", "")
        text, status = (node.text or "").strip(), node.get("status")
        
        # Format based on standard conventions
        if tag == "project":
            lines.append(f"\n{'#' * (level+1)} {topic}")
        else:
            check = "[x]" if status == "done" else "[ ]"
            stat_txt = f"({status}) " if status and status != "done" else ""
            content = f"**{topic}**" if topic else f"<{tag}>"
            if text: content += f": {text}"
            
            ignore = {'topic', 'status'}
            attrs = [f"{k}={v}" for k,v in node.attrib.items() if k not in ignore]
            if attrs: content += f" [{' '.join(attrs)}]"

            lines.append(f"{indent}- {check} {stat_txt}{content}")
        
        for child in node: _recurse(child, level + 1)
    
    if not nodes: return "No data."
    for n in nodes: _recurse(n, 0)
    return "\n".join(lines)

@ManifestView.register("table")
def render_table(nodes):
    rows = []
    def _flatten(node, depth):
        rows.append({
            "Topic": ("  " * depth) + (node.get("topic") or node.tag),
            "Tag": node.tag,
            "Status": node.get("status") or "-",
            "Content": (node.text or "").strip()
        })
        for c in node: _flatten(c, depth + 1)
    
    if not nodes: return "No data."
    for n in nodes: _flatten(n, 0)
    
    cols = ["Topic", "Tag", "Status", "Content"]
    widths = {c: max(len(c), max(len(r[c]) for r in rows)) for c in cols}
    
    header = " | ".join(f"{c:<{widths[c]}}" for c in cols)
    sep = "-+-".join("-" * widths[c] for c in cols)
    lines = [header, sep]
    for r in rows:
        lines.append(" | ".join(f"{r[c]:<{widths[c]}}" for c in cols))
    return "\n".join(lines)

# --- Controller (Shell) ---

class ParserControl(Exception): pass

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"Error: {message}\n")
        self.print_help()
        raise ParserControl()
    
    def exit(self, status=0, message=None):
        if message: print(message)
        raise ParserControl()

class ManifestShell(cmd.Cmd):
    intro = f"Manifest Manager v{__version__}. Type 'cheatsheet' (or 'cs') for help."
    prompt = "(manifest) "

    def __init__(self):
        super().__init__()
        self.repo = ManifestRepository()
        self._confirm_exit = False

    def _exec(self, func: Callable):
        try: 
            func()
        except ParserControl: pass
        except ValueError as e: print(f"Error: {e}")
        except Exception as e: print(f"Unexpected Error: {e}")

    def _parse_attrs(self, items: Optional[List[str]]) -> Dict[str, str]:
        if not items: return {}
        res = {}
        for i in items:
            if "=" in i: k, v = i.split("=", 1); res[k] = v
            else: print(f"Ignored invalid attr '{i}' (use key=value)")
        return res

    def postcmd(self, stop, line):
        if line.strip() not in ['exit', 'quit', 'EOF']:
            self._confirm_exit = False
        return stop

    # --- Commands ---

    def do_cheatsheet(self, _):
        """Show quick reference."""
        print("""
[CHEATSHEET]
1. load file.xml
2. add --tag project --topic "My Project"
3. add --tag task --parent "//*[@topic='My Project']" "Do Work"
4. edit --xpath "//task" --status done
5. list --style table
6. save
""")
    
    def do_cs(self, arg): self.do_cheatsheet(arg)

    def do_load(self, arg):
        """Load file: load filename"""
        res = self.repo.load(arg)
        print(res.message)
        if res.success: self.prompt = f"({os.path.basename(self.repo.filepath)}) "

    def do_save(self, arg):
        """Save file: save [filename]"""
        print(self.repo.save(arg).message)

    def do_add(self, arg):
        """Add node: add --tag task --attr priority=high "Content" """
        parser = ArgumentParser(prog="add", description="Add a new node.")
        parser.add_argument("--tag", required=True, help="XML Tag")
        parser.add_argument("--parent", default="/*", help="Parent XPath")
        parser.add_argument("--topic", help="Topic")
        parser.add_argument("--status", help="Status")
        parser.add_argument("--attr", "-a", action="append", help="Attributes (key=value)")
        parser.add_argument("text", nargs="?", help="Content")

        def _action():
            args = parser.parse_args(shlex.split(arg))
            spec = NodeSpec(args.tag, args.topic, args.status, args.text, self._parse_attrs(args.attr))
            print(self.repo.add_node(args.parent, spec).message)
        self._exec(_action)

    def do_edit(self, arg):
        """Edit node: edit --xpath //task --attr priority=low"""
        parser = ArgumentParser(prog="edit", description="Edit nodes.")
        parser.add_argument("--xpath", required=True, help="Target XPath")
        parser.add_argument("--text", help="New text")
        parser.add_argument("--status", help="New status")
        parser.add_argument("--topic", help="New topic")
        parser.add_argument("--attr", "-a", action="append", help="Attributes (key=value)")
        parser.add_argument("--delete", action="store_true", help="Delete node")

        def _action():
            args = parser.parse_args(shlex.split(arg))
            spec = NodeSpec("ignored", args.topic, args.status, args.text, self._parse_attrs(args.attr))
            print(self.repo.edit_node(args.xpath, spec, delete=args.delete).message)
        self._exec(_action)

    def do_list(self, arg):
        """List contents: list [xpath] [--style table]"""
        parser = ArgumentParser(prog="list")
        parser.add_argument("xpath", nargs="?", default="/*", help="Filter")
        parser.add_argument("--style", choices=["tree", "table"], default="tree")
        
        def _action():
            args = parser.parse_args(shlex.split(arg))
            print(ManifestView.render(self.repo.search(args.xpath), args.style))
        self._exec(_action)

    def do_exit(self, _):
        """Exit app."""
        if self.repo.modified and not self._confirm_exit:
            print("Unsaved changes! Type 'save' to save, or 'exit' again to discard.")
            self._confirm_exit = True
            return False
        print("Goodbye.")
        return True
    
    def do_EOF(self, _):
        print() 
        return self.do_exit(_)

def main():
    try: ManifestShell().cmdloop()
    except KeyboardInterrupt: print("\nInterrupted.")

if __name__ == "__main__":
    main()