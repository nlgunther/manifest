#!/usr/bin/env python3
"""
Test that add command returns the new node's ID
"""
import sys
import os
import tempfile

sys.path.insert(0, '/home/claude/src')

from manifest_manager.manifest_core import ManifestRepository, NodeSpec, Result


def test_result_has_optional_data_field():
    """Test that Result supports optional data field."""
    print("\n1. Testing Result with data field...")
    
    # Test with data
    result1 = Result.ok("Success", data={'id': 'a3f7b2c1', 'count': 1})
    assert result1.success
    assert result1.message == "Success"
    assert result1.data == {'id': 'a3f7b2c1', 'count': 1}
    print("   ✓ Result.ok() with data works")
    
    # Test without data (backward compatibility)
    result2 = Result.ok("Success")
    assert result2.success
    assert result2.message == "Success"
    assert result2.data is None
    print("   ✓ Result.ok() without data works (backward compatible)")
    
    # Test fail with data
    result3 = Result.fail("Error", data={'code': 404})
    assert not result3.success
    assert result3.data == {'code': 404}
    print("   ✓ Result.fail() with data works")
    
    print("   ✅ Result data field test passed")


def test_add_node_returns_id():
    """Test that add_node returns the new node's ID in result.data."""
    print("\n2. Testing add_node returns ID...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        testfile = os.path.join(tmpdir, "test.xml")
        repo = ManifestRepository()
        repo.load(testfile, auto_sidecar=True)
        
        # Test 1: add_node with auto_id=True
        spec = NodeSpec(tag="task", topic="Test task")
        result = repo.add_node("/*", spec, auto_id=True)
        
        assert result.success
        assert result.data is not None, "Result should have data"
        assert 'id' in result.data, "Data should contain 'id'"
        assert 'count' in result.data, "Data should contain 'count'"
        assert len(result.data['id']) == 8, "ID should be 8 characters"
        assert result.data['count'] == 1, "Should add to 1 parent"
        
        created_id = result.data['id']
        print(f"   ✓ Created node with ID: {created_id}")
        
        # Verify the node actually has that ID
        nodes = repo.search(f"//task[@id='{created_id}']")
        assert len(nodes) == 1
        assert nodes[0].get('topic') == "Test task"
        print("   ✓ Node with returned ID exists in manifest")
        
        # Test 2: add_node with auto_id=False and custom ID
        spec2 = NodeSpec(tag="task", topic="Custom ID task")
        spec2.attrs['id'] = 'custom01'
        result2 = repo.add_node("/*", spec2, auto_id=False)
        
        assert result2.success
        assert result2.data is not None
        assert result2.data['id'] == 'custom01'
        print("   ✓ Custom ID returned correctly")
        
        # Test 3: add_node with auto_id=False and NO ID
        spec3 = NodeSpec(tag="task", topic="No ID task")
        result3 = repo.add_node("/*", spec3, auto_id=False)
        
        assert result3.success
        # Should have no data if no ID was created
        assert result3.data is None or result3.data.get('id') is None
        print("   ✓ No ID returned when auto_id=False and no custom ID")
        
        print("   ✅ add_node ID return test passed")


def test_add_node_multiple_parents():
    """Test that add_node returns ID when adding to multiple parents."""
    print("\n3. Testing add_node with multiple parents...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        testfile = os.path.join(tmpdir, "test.xml")
        repo = ManifestRepository()
        repo.load(testfile, auto_sidecar=True)
        
        # Create multiple projects
        for i in range(3):
            proj = NodeSpec(tag="project", topic=f"Project {i+1}")
            repo.add_node("/*", proj, auto_id=True)
        
        # Add task to all projects
        spec = NodeSpec(tag="task", topic="Multi-parent task")
        result = repo.add_node("//project", spec, auto_id=True)
        
        assert result.success
        assert result.data is not None
        assert 'id' in result.data
        assert 'count' in result.data
        assert result.data['count'] == 3, "Should add to 3 parents"
        
        # All tasks should have the SAME ID
        tasks = repo.search("//task")
        assert len(tasks) == 3
        
        created_id = result.data['id']
        for task in tasks:
            assert task.get('id') == created_id
        
        print(f"   ✓ Same ID ({created_id}) used for all {result.data['count']} parents")
        print("   ✅ Multiple parents test passed")


def test_backward_compatibility():
    """Test that old code still works (no breaking changes)."""
    print("\n4. Testing backward compatibility...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        testfile = os.path.join(tmpdir, "test.xml")
        repo = ManifestRepository()
        repo.load(testfile, auto_sidecar=True)
        
        # Old-style code that only uses message
        spec = NodeSpec(tag="task", topic="Old style")
        result = repo.add_node("/*", spec, auto_id=True)
        
        # Old code would do this:
        if result.success:
            message = result.message
            assert "Added node" in message
            print(f"   ✓ Old-style code works: {message}")
        
        # New code can optionally use data
        if result.success and result.data:
            node_id = result.data.get('id')
            if node_id:
                print(f"   ✓ New-style code can access ID: {node_id}")
        
        print("   ✅ Backward compatibility test passed")


def test_cli_would_display_id():
    """Test that CLI would be able to display the ID (simulation)."""
    print("\n5. Testing CLI display logic...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        testfile = os.path.join(tmpdir, "test.xml")
        repo = ManifestRepository()
        repo.load(testfile, auto_sidecar=True)
        
        # Simulate what CLI does
        spec = NodeSpec(
            tag="task",
            topic="Review proposal",
            status="active",
            due="2026-03-15"
        )
        result = repo.add_node("/*", spec, auto_id=True)
        
        # Simulate CLI logic
        if result.success and result.data and result.data.get('id'):
            node_id = result.data['id']
            output = f"✓ Added node with ID: {node_id}"
            print(f"   {output}")
            
            # Would also show attributes
            if spec.topic:
                print(f"     topic: {spec.topic}")
            if spec.status:
                print(f"     status: {spec.status}")
            if spec.due:
                print(f"     due: {spec.due}")
            
            # Verify this is useful
            assert len(node_id) == 8
            print("   ✓ CLI can display ID immediately")
        else:
            print("   ❌ CLI would fall back to old message")
            assert False, "Should have ID in data"
        
        print("   ✅ CLI display test passed")


def run_all_tests():
    """Run all tests for add returns ID feature."""
    print("=" * 70)
    print("ADD RETURNS ID - TEST SUITE")
    print("Testing that add_node returns the new node's ID")
    print("=" * 70)
    
    tests = [
        test_result_has_optional_data_field,
        test_add_node_returns_id,
        test_add_node_multiple_parents,
        test_backward_compatibility,
        test_cli_would_display_id,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n   ❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"\n   ❌ ERROR in {test.__name__}: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nFeatures verified:")
        print("  ✓ Result class has optional data field")
        print("  ✓ add_node returns ID in result.data")
        print("  ✓ Works with auto-generated IDs")
        print("  ✓ Works with custom IDs")
        print("  ✓ Works with multiple parents")
        print("  ✓ Backward compatible with old code")
        print("  ✓ CLI can display ID immediately")
        print("\nNext steps:")
        print("  1. Update CLI in manifest.py to display the ID")
        print("  2. Test the full workflow in the shell")
        print("  3. Enjoy immediate ID feedback! 🎉")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed.")
        print("\nThese tests will pass once you implement:")
        print("  1. Add 'data' field to Result class")
        print("  2. Return ID from add_node() method")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
