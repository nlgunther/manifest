#!/usr/bin/env python3
"""
Comprehensive integration test for v3.4
Tests factory method, resp attribute, and all integrations
"""
import sys
import os
import tempfile

# Add parent directory to path
sys.path.insert(0, '/mnt/user-data/outputs')

from manifest_manager.manifest_core import ManifestRepository, NodeSpec, Result
from manifest_manager.config import Config
from manifest_manager.id_sidecar import IDSidecar

def test_factory_method():
    """Test NodeSpec.from_args factory method."""
    print("Testing factory method...")
    
    # Mock argparse namespace
    class MockArgs:
        tag = "task"
        topic = "Test Task"
        status = "active"
        text = "Test text"
        resp = "alice"
    
    args = MockArgs()
    attrs = {"priority": "high"}
    
    # Create via factory
    spec = NodeSpec.from_args(args, attributes=attrs)
    
    assert spec.tag == "task"
    assert spec.topic == "Test Task"
    assert spec.status == "active"
    assert spec.text == "Test text"
    assert spec.resp == "alice"
    assert spec.attrs == {"priority": "high"}
    
    print("✓ Factory method works")

def test_resp_attribute():
    """Test resp attribute in add/edit/display."""
    print("\nTesting resp attribute...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = ManifestRepository()
        testfile = os.path.join(tmpdir, "test.xml")
        
        # Load with sidecar
        repo.load(testfile, auto_sidecar=True)
        
        # Add node with resp
        spec = NodeSpec(
            tag="task",
            topic="Review PR",
            status="active",
            resp="alice"
        )
        result = repo.add_node("/*", spec, auto_id=True)
        assert result.success, f"Add failed: {result.message}"
        
        # Verify resp in XML
        task = repo.root[0]
        assert task.get("resp") == "alice", "resp not in XML"
        
        # Edit resp
        spec2 = NodeSpec(tag="task", resp="bob")
        task_id = task.get("id")
        result = repo.edit_node_by_id(task_id, spec2, delete=False)
        assert result.success, f"Edit failed: {result.message}"
        assert task.get("resp") == "bob", "resp not updated"
        
        print("✓ Resp attribute works in add/edit")

def test_factory_with_missing_attrs():
    """Test factory handles missing attributes gracefully."""
    print("\nTesting factory with missing attributes...")
    
    class MinimalArgs:
        tag = "note"
        # No topic, status, text, resp
    
    args = MinimalArgs()
    spec = NodeSpec.from_args(args, attributes={})
    
    assert spec.tag == "note"
    assert spec.topic is None
    assert spec.status is None
    assert spec.text is None
    assert spec.resp is None
    assert spec.attrs == {}
    
    print("✓ Factory handles missing attrs")

def test_factory_tag_override():
    """Test factory tag override for edit."""
    print("\nTesting factory tag override...")
    
    class EditArgs:
        # No tag attribute (edit doesn't have --tag)
        topic = "Updated"
        status = "done"
        resp = "carol"
    
    args = EditArgs()
    spec = NodeSpec.from_args(args, tag="ignored", attributes={})
    
    assert spec.tag == "ignored"
    assert spec.topic == "Updated"
    assert spec.resp == "carol"
    
    print("✓ Factory tag override works")

def test_to_xml_attrs_includes_resp():
    """Test to_xml_attrs includes resp."""
    print("\nTesting to_xml_attrs...")
    
    spec = NodeSpec(
        tag="task",
        topic="Test",
        status="active",
        resp="diana",
        attrs={"custom": "value"}
    )
    
    xml_attrs = spec.to_xml_attrs()
    
    assert xml_attrs["topic"] == "Test"
    assert xml_attrs["status"] == "active"
    assert xml_attrs["resp"] == "diana"
    assert xml_attrs["custom"] == "value"
    
    print("✓ to_xml_attrs includes resp")

def test_complete_workflow():
    """Test complete workflow: add with resp, find, edit."""
    print("\nTesting complete workflow...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = ManifestRepository()
        testfile = os.path.join(tmpdir, "workflow.xml")
        
        # Load
        repo.load(testfile, auto_sidecar=True)
        
        # Add multiple tasks with different resp
        for name, resp in [("Alice's task", "alice"), ("Bob's task", "bob")]:
            spec = NodeSpec(tag="task", topic=name, status="active", resp=resp)
            result = repo.add_node("/*", spec, auto_id=True)
            assert result.success
        
        # Search by prefix
        result = repo.search_by_id_prefix(repo.root[0].get("id")[:3])
        assert result.success
        assert len(result.data) >= 1
        
        # Edit via ID
        first_id = repo.root[0].get("id")
        spec = NodeSpec(tag="task", resp="carol", status="done")
        result = repo.edit_node_by_id(first_id, spec, delete=False)
        assert result.success
        
        # Verify
        assert repo.root[0].get("resp") == "carol"
        assert repo.root[0].get("status") == "done"
        
        print("✓ Complete workflow works")

def test_sidecar_integration():
    """Test sidecar updates when using factory."""
    print("\nTesting sidecar integration...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = ManifestRepository()
        testfile = os.path.join(tmpdir, "sidecar.xml")
        
        repo.load(testfile, auto_sidecar=True)
        
        # Add via factory-created spec
        class AddArgs:
            tag = "task"
            topic = "Sidecar Test"
            status = "active"
            resp = "eve"
            text = None
        
        spec = NodeSpec.from_args(AddArgs(), attributes={})
        result = repo.add_node("/*", spec, auto_id=True)
        assert result.success
        
        # Verify sidecar has the ID
        task_id = repo.root[0].get("id")
        assert repo.id_sidecar.exists(task_id), "ID not in sidecar"
        
        print("✓ Sidecar integration works")

def main():
    """Run all tests."""
    print("=" * 60)
    print("COMPREHENSIVE v3.4 INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        test_factory_method()
        test_resp_attribute()
        test_factory_with_missing_attrs()
        test_factory_tag_override()
        test_to_xml_attrs_includes_resp()
        test_complete_workflow()
        test_sidecar_integration()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
