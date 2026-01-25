"""Integration tests for manifest_core with sidecar."""
import pytest
import tempfile
import os
from manifest_core import ManifestRepository, NodeSpec


@pytest.fixture
def temp_repo():
    """Create temporary repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = ManifestRepository()
        path = os.path.join(tmpdir, 'test.xml')
        repo.load(path, auto_sidecar=True)
        yield repo


def test_add_node_updates_sidecar(temp_repo):
    """Test that adding a node updates the sidecar."""
    repo = temp_repo
    
    # Add node with auto-generated ID
    spec = NodeSpec(tag='task', topic='Test')
    result = repo.add_node('/*', spec, auto_id=True)
    
    assert result.success
    
    # Check sidecar was updated
    task_id = repo.root[0].get('id')
    assert repo.id_sidecar.exists(task_id)


def test_edit_node_by_id(temp_repo):
    """Test editing by ID."""
    repo = temp_repo
    
    # Add node
    spec = NodeSpec(tag='task', topic='Original')
    repo.add_node('/*', spec, auto_id=True)
    task_id = repo.root[0].get('id')
    
    # Edit by ID
    update_spec = NodeSpec(tag='task', topic='Updated')
    result = repo.edit_node_by_id(task_id, update_spec, delete=False)
    
    assert result.success
    assert repo.root[0].get('topic') == 'Updated'


def test_edit_node_by_invalid_id(temp_repo):
    """Test editing with non-existent ID."""
    repo = temp_repo
    
    spec = NodeSpec(tag='task', topic='Test')
    result = repo.edit_node_by_id('invalid123', spec, delete=False)
    
    assert not result.success
    assert 'not found' in result.message.lower()


def test_sidecar_persistence(temp_repo):
    """Test that sidecar persists across save/load."""
    repo = temp_repo
    path = repo.filepath
    
    # Add node with ID
    spec = NodeSpec(tag='task', topic='Test')
    repo.add_node('/*', spec, auto_id=True)
    task_id = repo.root[0].get('id')
    repo.save()
    
    # Reload
    repo2 = ManifestRepository()
    repo2.load(path, auto_sidecar=True)
    
    # Sidecar should have the ID
    assert repo2.id_sidecar.exists(task_id)


def test_load_without_sidecar_flag(temp_repo):
    """Test that load without --autosc doesn't create sidecar."""
    repo = temp_repo
    path = repo.filepath
    
    # Add node
    spec = NodeSpec(tag='task', topic='Test')
    repo.add_node('/*', spec, auto_id=True)
    repo.save()
    
    # Remove sidecar
    sidecar_path = path + '.ids'
    if os.path.exists(sidecar_path):
        os.remove(sidecar_path)
    
    # Reload without --autosc
    repo2 = ManifestRepository()
    repo2.load(path, auto_sidecar=False)
    
    # Sidecar should not exist
    assert not os.path.exists(sidecar_path)


def test_rebuild_sidecar_flag(temp_repo):
    """Test --rebuild-sidecar flag."""
    repo = temp_repo
    path = repo.filepath
    
    # Add node
    spec = NodeSpec(tag='task', topic='Test')
    repo.add_node('/*', spec, auto_id=True)
    task_id = repo.root[0].get('id')
    repo.save()
    
    # Corrupt sidecar manually
    sidecar_path = path + '.ids'
    with open(sidecar_path, 'w') as f:
        f.write('{"corrupt": "data"}')
    
    # Reload with rebuild flag
    repo2 = ManifestRepository()
    repo2.load(path, rebuild_sidecar=True)
    
    # Should have valid sidecar with correct ID
    assert repo2.id_sidecar.exists(task_id)
