"""Tests for IDSidecar class."""
import pytest
import os
import tempfile
import json
from lxml import etree
from config import Config
from id_sidecar import IDSidecar


@pytest.fixture
def temp_manifest():
    """Create temporary manifest for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'test.xml')
        root = etree.Element('manifest')
        yield path, root


def test_sidecar_load_empty(temp_manifest):
    """Test loading non-existent sidecar."""
    path, _ = temp_manifest
    config = Config()
    sidecar = IDSidecar(path, config)
    sidecar.load()
    assert sidecar.index == {}


def test_sidecar_add_and_get(temp_manifest):
    """Test adding and retrieving IDs."""
    path, _ = temp_manifest
    config = Config()
    sidecar = IDSidecar(path, config)
    
    sidecar.add('abc123', '/manifest/task[@id="abc123"]')
    assert sidecar.get('abc123') == '/manifest/task[@id="abc123"]'
    assert sidecar.exists('abc123') == True


def test_sidecar_save_and_load(temp_manifest):
    """Test persistence."""
    path, _ = temp_manifest
    config = Config()
    
    # Save
    sidecar1 = IDSidecar(path, config)
    sidecar1.add('abc123', '/manifest/task[@id="abc123"]')
    sidecar1.save()
    
    # Load
    sidecar2 = IDSidecar(path, config)
    sidecar2.load()
    assert sidecar2.get('abc123') == '/manifest/task[@id="abc123"]'


def test_sidecar_rebuild(temp_manifest):
    """Test rebuilding index from XML."""
    path, root = temp_manifest
    config = Config()
    
    # Create tree with IDs
    task1 = etree.SubElement(root, 'task', id='abc123')
    task2 = etree.SubElement(root, 'task', id='def456')
    
    sidecar = IDSidecar(path, config)
    sidecar.rebuild(root)
    
    assert len(sidecar.index) == 2
    assert sidecar.exists('abc123')
    assert sidecar.exists('def456')


def test_sidecar_verify_valid(temp_manifest):
    """Test verification of valid sidecar."""
    path, root = temp_manifest
    config = Config()
    
    task = etree.SubElement(root, 'task', id='abc123')
    
    sidecar = IDSidecar(path, config)
    sidecar.rebuild(root)
    
    # Should verify successfully
    assert sidecar.verify_and_repair(root) == True


def test_sidecar_verify_corrupted(temp_manifest):
    """Test repair of corrupted sidecar."""
    path, root = temp_manifest
    config = Config()
    config.set('sidecar.corruption_handling', 'silent')
    
    task = etree.SubElement(root, 'task', id='abc123')
    
    sidecar = IDSidecar(path, config)
    sidecar.add('abc123', '/manifest/wrong_path')  # Corrupt entry
    
    # Should detect and repair silently
    assert sidecar.verify_and_repair(root) == True
    assert sidecar.get('abc123') != '/manifest/wrong_path'


def test_sidecar_all_ids(temp_manifest):
    """Test getting all IDs."""
    path, root = temp_manifest
    config = Config()
    
    task1 = etree.SubElement(root, 'task', id='abc123')
    task2 = etree.SubElement(root, 'task', id='def456')
    
    sidecar = IDSidecar(path, config)
    sidecar.rebuild(root)
    
    all_ids = sidecar.all_ids()
    assert 'abc123' in all_ids
    assert 'def456' in all_ids
    assert len(all_ids) == 2


def test_sidecar_remove(temp_manifest):
    """Test removing IDs from sidecar."""
    path, _ = temp_manifest
    config = Config()
    sidecar = IDSidecar(path, config)
    
    sidecar.add('abc123', '/manifest/task[@id="abc123"]')
    assert sidecar.exists('abc123')
    
    sidecar.remove('abc123')
    assert not sidecar.exists('abc123')
