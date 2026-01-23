import pytest
from unittest.mock import MagicMock, ANY
from lxml import etree
from manifest_core import ManifestRepository, NodeSpec, TaskStatus, Result

# --- Fixtures ---

@pytest.fixture
def mock_storage():
    """Creates a mock storage manager."""
    return MagicMock()

@pytest.fixture
def repo(mock_storage):
    """
    Initializes a ManifestRepository with:
    1. A mocked storage layer (no disk I/O).
    2. An in-memory XML tree ready for testing.
    """
    repository = ManifestRepository()
    repository.storage = mock_storage
    
    # Setup standard starting state
    repository.root = etree.Element("manifest")
    repository.tree = etree.ElementTree(repository.root)
    repository.filepath = "test.xml"
    
    return repository

@pytest.fixture
def populated_repo(repo):
    """Returns a repo pre-filled with some data."""
    # Add a project
    project = etree.SubElement(repo.root, "project", topic="Alpha")
    # Add a task inside project
    etree.SubElement(project, "task", topic="Report", status="active")
    return repo

# --- Tests ---

def test_add_node_success(repo):
    """Test adding a valid node."""
    spec = NodeSpec(tag="task", topic="Test Task", status=TaskStatus.ACTIVE)
    result = repo.add_node("/*", spec)
    
    assert result.success is True
    assert len(repo.root) == 1
    
    node = repo.root[0]
    assert node.tag == "task"
    assert node.get("topic") == "Test Task"
    assert node.get("status") == "active"

def test_add_node_invalid_xpath(repo):
    """Test that bad XPath handles gracefully."""
    spec = NodeSpec(tag="task")
    result = repo.add_node("//Bad[XPath", spec) # Malformed syntax
    
    assert result.success is False
    assert "Invalid XPath" in result.message

def test_add_node_no_parent(repo):
    """Test adding to a non-existent parent."""
    spec = NodeSpec(tag="task")
    result = repo.add_node("//ghost", spec)
    
    assert result.success is False
    assert "Parent not found" in result.message

def test_edit_node_update(populated_repo):
    """Test updating an existing node's text and attributes."""
    xpath = "//task[@topic='Report']"
    
    # Change status to done and add text
    spec = NodeSpec(tag="ignored", status=TaskStatus.DONE, text="Finished it")
    result = populated_repo.edit_node(xpath, spec, delete=False)
    
    assert result.success is True
    
    # Verify XML structure
    node = populated_repo.root.xpath(xpath)[0]
    assert node.get("status") == "done"
    assert node.text == "Finished it"

def test_edit_node_delete(populated_repo):
    """Test deleting a node."""
    xpath = "//task[@topic='Report']"
    
    # Verify it exists first
    assert len(populated_repo.search(xpath)) == 1
    
    # Delete it
    result = populated_repo.edit_node(xpath, spec=None, delete=True)
    
    assert result.success is True
    assert len(populated_repo.search(xpath)) == 0

def test_wrap_content(repo):
    """Test wrapping top-level items into a new container."""
    # 1. Setup: Add 3 loose items
    for i in range(3):
        etree.SubElement(repo.root, "item", id=str(i))
    
    assert len(repo.root) == 3

    # 2. Action: Wrap them
    result = repo.wrap_content("archive")
    
    assert result.success is True
    
    # 3. Verify: Root should now have 1 child (the wrapper)
    assert len(repo.root) == 1
    wrapper = repo.root[0]
    assert wrapper.tag == "archive"
    
    # 4. Verify: Wrapper should contain the 3 items
    assert len(wrapper) == 3
    assert wrapper[0].get("id") == "0"

def test_merge_from_external(repo, mock_storage):
    """Test merging content from another file."""
    # Mock the return value of storage.load to simulate reading a file
    mock_storage.load.return_value = b'<manifest><imported_item topic="New" /></manifest>'
    
    result = repo.merge_from("other_file.xml")
    
    assert result.success is True
    assert "Merged 1 items" in result.message
    
    # Verify the item is now in our root
    assert len(repo.search("//imported_item")) == 1

def test_transaction_rollback(repo):
    """Ensure the tree state is restored if an error occurs during an operation."""
    initial_structure = etree.tostring(repo.root)
    
    # Attempt an operation that we force to fail logic validation
    # (NodeSpec validation runs inside the transaction)
    with pytest.raises(ValueError):
        # Invalid tag name (contains space)
        bad_spec = NodeSpec(tag="Invalid Tag Name")
        repo.add_node("/*", bad_spec)
        
    # Verify the tree is exactly as it was before
    current_structure = etree.tostring(repo.root)
    assert current_structure == initial_structure

@pytest.mark.parametrize("input_tag,expected_valid", [
    ("task", True),
    ("my_tag", True),
    ("Tag123", True),
    ("Invalid Tag", False), # Spaces not allowed
    ("xmlTag", False),      # Cannot start with xml
    ("XMLTag", False),      # Cannot start with xml (any case)
    ("123Tag", False),      # Cannot start with number
    ("!", False),           # Special chars
])
def test_tag_validation(repo, input_tag, expected_valid):
    """Data-driven test for tag naming rules."""
    spec = NodeSpec(tag=input_tag)
    
    if expected_valid:
        result = repo.add_node("/*", spec)
        assert result.success, f"Valid tag '{input_tag}' was rejected: {result.message}"
    else:
        with pytest.raises(ValueError, match="Invalid tag"):
            repo.add_node("/*", spec)