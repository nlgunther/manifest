"""
test_core.py
============
Tests for ManifestRepository, Validation, and Logic.
"""
import pytest
from unittest.mock import MagicMock, patch
from lxml import etree
from manifest_core import ManifestRepository, NodeSpec, TaskStatus

@pytest.fixture
def mock_storage():
    """Mock storage to avoid disk I/O."""
    return MagicMock()

@pytest.fixture
def repo(mock_storage):
    """Repo with mocked storage and empty in-memory tree."""
    r = ManifestRepository()
    r.storage = mock_storage
    r.root = etree.Element("manifest")
    r.tree = etree.ElementTree(r.root)
    r.filepath = "test.xml"
    return r

def test_add_node_simple(repo):
    spec = NodeSpec(tag="task", topic="Unit Test", status="active")
    res = repo.add_node("/*", spec)
    assert res.success
    assert len(repo.root) == 1
    assert repo.root[0].get("topic") == "Unit Test"

def test_add_node_validation_error(repo):
    """Ensure invalid tags are rejected."""
    spec = NodeSpec(tag="Invalid Tag") 
    with pytest.raises(ValueError):
        repo.add_node("/*", spec)

def test_edit_node_update(repo):
    etree.SubElement(repo.root, "item", topic="Old", id="1")
    spec = NodeSpec("ignored", topic="New", status="done")
    
    res = repo.edit_node("//item", spec, delete=False)
    assert res.success
    assert repo.root[0].get("topic") == "New"
    assert repo.root[0].get("status") == "done"

def test_edit_node_delete(repo):
    etree.SubElement(repo.root, "item", id="1")
    res = repo.edit_node("//item", None, delete=True)
    assert res.success
    assert len(repo.root) == 0

def test_wrap_content(repo):
    etree.SubElement(repo.root, "item1")
    etree.SubElement(repo.root, "item2")
    
    res = repo.wrap_content("archive")
    assert res.success
    assert len(repo.root) == 1
    assert repo.root[0].tag == "archive"
    assert len(repo.root[0]) == 2

def test_merge_from(repo, mock_storage):
    mock_storage.load.return_value = b'<manifest><imported/></manifest>'
    res = repo.merge_from("other.xml")
    assert res.success
    assert len(repo.root) == 1
    assert repo.root[0].tag == "imported"

def test_transaction_rollback(repo):
    """Ensure repo stays clean if an error occurs."""
    etree.SubElement(repo.root, "existing")
    initial_len = len(repo.root)
    
    # Patch internal method to force a crash during add
    # FIX: We must catch the exception because transaction() re-raises it after rollback
    with patch.object(repo, '_safe_xpath', side_effect=Exception("Boom")):
        with pytest.raises(Exception, match="Boom"):
            repo.add_node("//any", NodeSpec("task"))
            
    # Assert state was restored (only 'existing' remains)
    assert len(repo.root) == initial_len
    assert repo.root[0].tag == "existing"