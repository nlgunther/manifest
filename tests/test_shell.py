"""
test_shell.py
=============
Tests for the CLI Controller.
"""
import pytest
from unittest.mock import patch
from manifest_manager.manifest import ManifestShell
from manifest_manager.manifest_core import Result, NodeSpec

@pytest.fixture
def shell():
    """Shell with fully mocked Repository."""
    with patch('manifest_manager.manifest.ManifestRepository') as MockRepo:
        sh = ManifestShell()
        sh.repo = MockRepo.return_value
        sh.repo.filepath = "test.xml"
        # Explicitly set password to None so it's not a MagicMock object
        sh.repo.password = None 
        sh.repo.modified = False
        sh.repo.add_node.return_value = Result.ok("Added")
        sh.repo.edit_node.return_value = Result.ok("Edited")
        sh.repo.load.return_value = Result.ok("Loaded")
        sh.repo.save.return_value = Result.ok("Saved")
        sh.repo.wrap_content.return_value = Result.ok("Wrapped")
        return sh

def test_do_add(shell):
    """Test add command parsing."""
    # FIX: Remove 'add ' prefix. do_add receives only arguments.
    shell.do_add('--tag task --topic "My Topic" --status active -a key=val "Text"')
    
    shell.repo.add_node.assert_called_once()
    args, _ = shell.repo.add_node.call_args
    xpath, spec = args
    
    assert xpath == "/*"
    assert spec.tag == "task"
    assert spec.topic == "My Topic"
    assert spec.status == "active"
    assert spec.attrs == {"key": "val"}

def test_do_edit(shell):
    """Test edit command parsing."""
    # FIX: Remove 'edit ' prefix.
    shell.do_edit('--xpath //task --status done --delete')
    
    shell.repo.edit_node.assert_called_once()
    args, _ = shell.repo.edit_node.call_args
    xpath, spec, delete = args
    
    assert xpath == "//task"
    assert delete is True
    assert spec.status == "done"

def test_do_wrap(shell):
    """Test wrap command."""
    # FIX: Remove 'wrap ' prefix.
    shell.do_wrap('--root 2025_archive')
    shell.repo.wrap_content.assert_called_with("2025_archive")

def test_do_save_no_args(shell):
    """Test simple save."""
    # cmd module passes empty string '' when no args are typed
    shell.do_save('')
    
    # repo.save is called with (filename='', password=None)
    shell.repo.save.assert_called_with('', None)

def test_do_load(shell):
    """Test load command."""
    shell.do_load('data.xml')
    shell.repo.load.assert_called()

def test_do_find(shell):
    """Test find command."""
    from lxml import etree
    from manifest_manager.id_sidecar import IDSidecar
    
    # Setup sidecar with mock data
    shell.repo.id_sidecar = IDSidecar("/tmp/test.xml", None)
    shell.repo.root = etree.Element("manifest")
    elem = etree.SubElement(shell.repo.root, "task", id="abc123")
    shell.repo.id_sidecar.add("abc123", "/manifest/task[@id='abc123']")
    
    shell.do_find('abc')
    # Should find the element (captured in stdout)

def test_do_find_tree(shell):
    """Test find command with --tree flag."""
    from lxml import etree
    from manifest_manager.id_sidecar import IDSidecar
    
    # Setup sidecar with mock data
    shell.repo.id_sidecar = IDSidecar("/tmp/test.xml", None)
    shell.repo.root = etree.Element("manifest")
    elem = etree.SubElement(shell.repo.root, "task", id="abc123", topic="Test")
    shell.repo.id_sidecar.add("abc123", "/manifest/task[@id='abc123']")
    
    shell.do_find('abc --tree')
    # Should display tree view

def test_do_find_tree_depth(shell):
    """Test find command with --tree --depth."""
    from lxml import etree
    from manifest_manager.id_sidecar import IDSidecar
    
    # Setup sidecar with mock data
    shell.repo.id_sidecar = IDSidecar("/tmp/test.xml", None)
    shell.repo.root = etree.Element("manifest")
    elem = etree.SubElement(shell.repo.root, "project", id="abc123")
    shell.repo.id_sidecar.add("abc123", "/manifest/project[@id='abc123']")
    
    shell.do_find('abc --tree --depth 2')
    # Should display with depth limit

def test_do_autoid(shell):
    """Test autoid command."""
    from manifest_manager.manifest_core import Result
    shell.repo.ensure_ids.return_value = Result.ok("Added 5 IDs")
    
    shell.do_autoid('')
    shell.repo.ensure_ids.assert_called_with(overwrite=False)
    
    shell.do_autoid('--overwrite')
    shell.repo.ensure_ids.assert_called_with(overwrite=True)