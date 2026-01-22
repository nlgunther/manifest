import pytest
from lxml import etree
from manifest import ManifestRepository, NodeSpec, Validator, TaskStatus

# --- Fixtures (Setup) ---

@pytest.fixture
def repo():
    """Returns a repository with a clean, in-memory XML tree."""
    r = ManifestRepository()
    # Loading a non-existent file creates a new in-memory tree
    r.load("test_memory.xml") 
    return r

@pytest.fixture
def populated_repo(repo):
    """Returns a repo pre-filled with a project and task."""
    repo.add_node("/*", NodeSpec(tag="project", topic="Work"))
    repo.add_node("//project[@topic='Work']", 
                  NodeSpec(tag="task", topic="Report", status="active", text="Write it"))
    return repo

# --- Validation Tests ---

def test_validator_rejects_bad_tags():
    """Validator should crash on invalid tag names."""
    with pytest.raises(ValueError):
        Validator.validate_tag("123NumberStart")
    with pytest.raises(ValueError):
        Validator.validate_tag("Has Spaces")
    with pytest.raises(ValueError):
        Validator.validate_tag("xmlReserved")

def test_sanitization():
    """Validator should strip control characters but keep structure."""
    dirty_text = "Hello\x00World"
    clean = Validator.sanitize_text(dirty_text)
    assert clean == "HelloWorld"

# --- CRUD Tests (Create, Read, Update, Delete) ---

def test_add_node(repo):
    """Test creating a new node."""
    spec = NodeSpec(tag="item", topic="Milk", status="pending")
    result = repo.add_node("/*", spec)
    
    assert result.success
    assert "Added 1" in result.message
    
    # Verify via search
    nodes = repo.search("//item")
    assert len(nodes) == 1
    assert nodes[0].get("topic") == "Milk"
    assert nodes[0].get("status") == "pending"

def test_edit_node_text_and_status(populated_repo):
    """Test modifying an existing node."""
    # Find the task created in the fixture
    xpath = "//task[@topic='Report']"
    
    # Change text and status
    new_spec = NodeSpec(tag="ignored", text="Updated Report", status="done")
    result = populated_repo.edit_node(xpath, new_spec)
    
    assert result.success
    
    # Verify changes
    node = populated_repo.search(xpath)[0]
    assert node.text == "Updated Report"
    assert node.get("status") == "done"

def test_delete_node(populated_repo):
    """Test deleting a node."""
    xpath = "//task[@topic='Report']"
    
    # Verify it exists first
    assert len(populated_repo.search(xpath)) == 1
    
    # Delete it
    result = populated_repo.edit_node(xpath, delete=True)
    assert result.success
    assert "Deleted 1" in result.message
    
    # Verify it's gone
    assert len(populated_repo.search(xpath)) == 0

def test_transaction_safety(repo):
    """Ensure operations are atomic (all-or-nothing)."""
    # 1. Add a safe node
    repo.add_node("/*", NodeSpec(tag="project", topic="Safe"))
    
    # 2. Try to add a node that causes a crash (simulated)
    # We manually simulate a crash inside a transaction to test rollback
    try:
        with repo.transaction():
            # This would technically succeed...
            repo.add_node("//project", NodeSpec(tag="task", topic="Ghost"))
            # ... but then we hit an error!
            raise RuntimeError("Database Crash!")
    except RuntimeError:
        pass # We expect this crash
    
    # 3. Verify Rollback
    # The 'Safe' project should be there
    assert len(repo.search("//project[@topic='Safe']")) == 1
    # The 'Ghost' task should NOT be there because the transaction failed
    assert len(repo.search("//task[@topic='Ghost']")) == 0