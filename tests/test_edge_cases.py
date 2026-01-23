"""Additional edge case tests for manifest_core.py"""
import pytest
from lxml import etree
from manifest_core import ManifestRepository, NodeSpec, TaskStatus, Validator


@pytest.fixture
def mock_storage():
    """Mock storage manager."""
    from unittest.mock import MagicMock
    return MagicMock()


@pytest.fixture
def repo(mock_storage):
    """Repository with mocked storage."""
    repository = ManifestRepository()
    repository.storage = mock_storage
    repository.root = etree.Element("manifest")
    repository.tree = etree.ElementTree(repository.root)
    repository.filepath = "test.xml"
    return repository


# =============================================================================
# NO FILE LOADED EDGE CASES
# =============================================================================

class TestNoFileLoaded:
    """Tests for operations when no file is loaded."""
    
    def test_add_node_no_file_loaded(self):
        """Test that add_node fails gracefully when no file loaded."""
        repo = ManifestRepository()  # Fresh, no load() called
        spec = NodeSpec(tag="task")
        
        result = repo.add_node("/*", spec)
        
        assert result.success is False
        assert "No file loaded" in result.message
    
    def test_edit_node_no_file_loaded(self):
        """Test that edit_node fails gracefully when no file loaded."""
        repo = ManifestRepository()
        
        result = repo.edit_node("//task", None, delete=True)
        
        assert result.success is False
        assert "No file loaded" in result.message
    
    def test_search_no_file_loaded(self):
        """Test that search returns empty list when no file loaded."""
        repo = ManifestRepository()
        
        results = repo.search("//task")
        
        assert results == []


# =============================================================================
# UNICODE AND SPECIAL CHARACTERS
# =============================================================================

class TestUnicodeContent:
    """Tests for Unicode and special character handling."""
    
    def test_unicode_in_topic(self, repo):
        """Test that Unicode in topic attribute is preserved."""
        spec = NodeSpec(
            tag="note", 
            topic="日本語タイトル"
        )
        result = repo.add_node("/*", spec)
        assert result.success
        
        node = repo.root[0]
        assert node.get("topic") == "日本語タイトル"
    
    def test_unicode_in_text(self, repo):
        """Test that Unicode in text content is preserved."""
        spec = NodeSpec(
            tag="note",
            text="Ümlauts and émojis 🎉"
        )
        result = repo.add_node("/*", spec)
        assert result.success
        
        node = repo.root[0]
        assert "🎉" in node.text
        assert "Ümlauts" in node.text
    
    def test_special_xml_chars_escaped(self, repo):
        """Test that special XML characters in text are handled."""
        spec = NodeSpec(tag="code", text="if (a < b && c > d)")
        result = repo.add_node("/*", spec)
        assert result.success
        
        # Should not raise, and should roundtrip correctly
        xml_bytes = etree.tostring(repo.root)
        restored = etree.fromstring(xml_bytes)
        
        # Either the text is preserved or XML entities are used
        assert "< b" in restored[0].text or "&lt;" in xml_bytes.decode()


# =============================================================================
# EMPTY MANIFEST EDGE CASES
# =============================================================================

class TestEmptyManifest:
    """Tests for operations on empty manifests."""
    
    def test_wrap_empty_manifest(self, repo):
        """Test that wrapping empty manifest fails gracefully."""
        # repo.root has no children
        result = repo.wrap_content("wrapper")
        
        assert result.success is False
        assert "empty" in result.message.lower()
    
    def test_list_empty_manifest(self, repo):
        """Test that listing empty manifest shows root element."""
        from manifest_core import ManifestView
        nodes = repo.search("/*")
        output = ManifestView.render(nodes, "tree")
        
        # Empty manifest still shows the root element
        assert "<manifest>" in output


# =============================================================================
# MULTIPLE PARENT XPATH
# =============================================================================

class TestMultipleParents:
    """Tests for XPath expressions matching multiple parents."""
    
    def test_add_node_to_multiple_parents(self, repo):
        """Test that adding to multiple parents creates multiple nodes."""
        # Create two projects
        etree.SubElement(repo.root, "project", name="A")
        etree.SubElement(repo.root, "project", name="B")
        
        spec = NodeSpec(tag="task", topic="Shared Task")
        result = repo.add_node("//project", spec)
        
        assert result.success is True
        assert "2 location" in result.message
        assert len(repo.search("//task")) == 2
    
    def test_edit_multiple_nodes(self, repo):
        """Test that editing multiple nodes updates all matches."""
        # Create three tasks
        for i in range(3):
            etree.SubElement(repo.root, "task", status="active")
        
        spec = NodeSpec(tag="ignored", status=TaskStatus.DONE)
        result = repo.edit_node("//task[@status='active']", spec, delete=False)
        
        assert result.success is True
        assert "3 nodes" in result.message
        assert len(repo.search("//task[@status='done']")) == 3


# =============================================================================
# VALIDATOR EDGE CASES
# =============================================================================

class TestValidatorEdgeCases:
    """Tests for Validator edge cases."""
    
    def test_sanitize_removes_control_chars(self):
        """Test that sanitize removes dangerous control characters."""
        dirty = "Hello\x00World\x01Test\x1F!"
        clean = Validator.sanitize(dirty)
        
        assert clean == "HelloWorldTest!"
        assert '\x00' not in clean
        assert '\x01' not in clean
    
    def test_sanitize_preserves_newlines_tabs(self):
        """Test that sanitize keeps valid whitespace."""
        text = "Line1\nLine2\tTabbed  Spaced"
        clean = Validator.sanitize(text)
        
        assert clean == text
    
    def test_sanitize_none_input(self):
        """Test that sanitize handles None gracefully."""
        assert Validator.sanitize(None) == ""
    
    def test_sanitize_empty_string(self):
        """Test that sanitize handles empty string."""
        assert Validator.sanitize("") == ""
    
    def test_validate_tag_leading_underscore(self):
        """Test that leading underscore is allowed."""
        Validator.validate_tag("_private")  # Should not raise
    
    def test_validate_tag_with_dots(self):
        """Test that dots in tag names are allowed."""
        Validator.validate_tag("tag.with.dots")  # Should not raise
    
    def test_validate_tag_with_hyphens(self):
        """Test that hyphens in tag names are allowed."""
        Validator.validate_tag("tag-with-hyphens")  # Should not raise
    
    def test_validate_tag_xml_prefix_mixed_case(self):
        """Test that XML prefix is rejected in any case."""
        for variant in ["xml", "XML", "Xml", "xMl", "XmL"]:
            with pytest.raises(ValueError, match="reserved"):
                Validator.validate_tag(f"{variant}Tag")
    
    def test_validate_tag_starts_with_number(self):
        """Test that tags starting with numbers are rejected."""
        with pytest.raises(ValueError, match="Invalid tag"):
            Validator.validate_tag("123tag")
    
    def test_validate_tag_special_chars(self):
        """Test that special characters are rejected."""
        for char in ["<", ">", "&", "'", '"', " ", "\t", "\n"]:
            with pytest.raises(ValueError, match="Invalid tag"):
                Validator.validate_tag(f"tag{char}name")


# =============================================================================
# XPATH EDGE CASES
# =============================================================================

class TestXPathEdgeCases:
    """Tests for XPath handling edge cases."""
    
    def test_xpath_with_special_chars(self, repo):
        """Test XPath with special characters in attribute values."""
        # Add node with special chars in topic
        spec = NodeSpec(tag="task", topic="Task & Info")
        repo.add_node("/*", spec)
        
        # Search for it (XPath handles escaping)
        nodes = repo.search("//task")
        assert len(nodes) == 1
        assert nodes[0].get("topic") == "Task & Info"
    
    def test_malformed_xpath_graceful_failure(self, repo):
        """Test that malformed XPath returns error instead of crashing."""
        result = repo.add_node("//Bad[XPath", NodeSpec(tag="task"))
        
        assert result.success is False
        assert "Invalid XPath" in result.message
    
    def test_empty_xpath_result(self, repo):
        """Test that XPath matching nothing fails gracefully."""
        result = repo.add_node("//nonexistent", NodeSpec(tag="task"))
        
        assert result.success is False
        assert "Parent not found" in result.message


# =============================================================================
# TRANSACTION ROLLBACK
# =============================================================================

class TestTransactionRollback:
    """Tests for transaction rollback behavior."""
    
    def test_transaction_rollback_on_validation_error(self, repo):
        """Test that transaction rolls back on validation error."""
        initial_xml = etree.tostring(repo.root)
        
        # Attempt to add node with invalid tag
        with pytest.raises(ValueError):
            with repo.transaction():
                # Add a valid node first
                etree.SubElement(repo.root, "valid")
                # Then trigger validation error
                Validator.validate_tag("Invalid Tag")
        
        # Verify rollback: tree should be unchanged
        current_xml = etree.tostring(repo.root)
        assert current_xml == initial_xml
    
    def test_transaction_commit_on_success(self, repo):
        """Test that successful transaction commits changes."""
        with repo.transaction():
            etree.SubElement(repo.root, "committed_node")
        
        # Changes should persist
        assert len(repo.root) == 1
        assert repo.root[0].tag == "committed_node"


# =============================================================================
# WRAP CONTENT EDGE CASES  
# =============================================================================

class TestWrapContent:
    """Tests for wrap_content edge cases."""
    
    def test_wrap_single_node(self, repo):
        """Test wrapping a single top-level node."""
        etree.SubElement(repo.root, "item")
        
        result = repo.wrap_content("wrapper")
        assert result.success
        assert len(repo.root) == 1
        assert repo.root[0].tag == "wrapper"
        assert len(repo.root[0]) == 1
    
    def test_wrap_preserves_attributes(self, repo):
        """Test that wrap preserves node attributes."""
        etree.SubElement(repo.root, "item", id="1", status="active")
        
        result = repo.wrap_content("wrapper")
        assert result.success
        
        wrapped_item = repo.root[0][0]
        assert wrapped_item.get("id") == "1"
        assert wrapped_item.get("status") == "active"
    
    def test_wrap_preserves_text(self, repo):
        """Test that wrap preserves node text content."""
        item = etree.SubElement(repo.root, "item")
        item.text = "Important text"
        
        result = repo.wrap_content("wrapper")
        assert result.success
        
        wrapped_item = repo.root[0][0]
        assert wrapped_item.text == "Important text"


# =============================================================================
# MERGE EDGE CASES
# =============================================================================

class TestMergeEdgeCases:
    """Tests for merge_from edge cases."""
    
    def test_merge_empty_manifest(self, repo, mock_storage):
        """Test merging an empty manifest."""
        mock_storage.load.return_value = b'<manifest></manifest>'
        
        result = repo.merge_from("empty.xml")
        
        assert result.success
        assert "0 items" in result.message
    
    def test_merge_preserves_existing(self, repo, mock_storage):
        """Test that merge doesn't remove existing nodes."""
        # Add existing node
        etree.SubElement(repo.root, "existing")
        
        # Merge new content
        mock_storage.load.return_value = b'<manifest><new_item /></manifest>'
        result = repo.merge_from("other.xml")
        
        assert result.success
        assert len(repo.root) == 2  # existing + new_item
        assert repo.root[0].tag == "existing"
        assert repo.root[1].tag == "new_item"
