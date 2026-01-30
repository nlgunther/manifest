#!/usr/bin/env python3
"""
Test --due option as first-class attribute
"""
import sys
import os
import tempfile

sys.path.insert(0, '/home/claude/src')

from manifest_manager.manifest_core import ManifestRepository, NodeSpec


def test_nodespec_due_attribute():
    """Test NodeSpec has due as first-class attribute."""
    print("\n1. Testing NodeSpec with due attribute...")
    
    spec = NodeSpec(
        tag="task",
        topic="Review proposal",
        status="active",
        due="2026-03-15"
    )
    
    assert spec.due == "2026-03-15"
    print("   ✓ NodeSpec accepts due parameter")
    
    # Test to_xml_attrs includes due
    attrs = spec.to_xml_attrs()
    assert 'due' in attrs
    assert attrs['due'] == "2026-03-15"
    print("   ✓ to_xml_attrs() includes due")
    
    print("   ✅ NodeSpec due attribute test passed")


def test_nodespec_from_args():
    """Test from_args factory includes due."""
    print("\n2. Testing NodeSpec.from_args() with due...")
    
    from argparse import Namespace
    
    args = Namespace(
        tag='task',
        topic='Test task',
        status='active',
        resp='alice',
        due='2026-03-20',
        text='Description'
    )
    
    spec = NodeSpec.from_args(args)
    
    assert spec.due == '2026-03-20'
    print("   ✓ from_args() preserves due")
    
    attrs = spec.to_xml_attrs()
    assert attrs['due'] == '2026-03-20'
    print("   ✓ Converted to XML attributes")
    
    print("   ✅ from_args() test passed")


def test_add_node_with_due():
    """Test adding node with due date via NodeSpec."""
    print("\n3. Testing add_node() with due...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = ManifestRepository()
        testfile = os.path.join(tmpdir, "test.xml")
        repo.load(testfile, auto_sidecar=True)
        
        spec = NodeSpec(
            tag="task",
            topic="Complete report",
            status="active",
            due="2026-03-15",
            text="Quarterly report"
        )
        
        result = repo.add_node("/*", spec, auto_id=True)
        assert result.success
        
        # Verify the due attribute was added
        task = repo.search("//task")[0]
        assert task.get("due") == "2026-03-15"
        assert task.get("topic") == "Complete report"
        
        print("   ✓ Node created with due attribute")
        print(f"   ✓ Due date: {task.get('due')}")
        print("   ✅ add_node() with due test passed")


def test_edit_node_with_due():
    """Test editing node to add/change due date."""
    print("\n4. Testing edit_node() with due...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = ManifestRepository()
        testfile = os.path.join(tmpdir, "test.xml")
        repo.load(testfile, auto_sidecar=True)
        
        # Add task without due date
        spec1 = NodeSpec(tag="task", topic="Task 1")
        repo.add_node("/*", spec1, auto_id=True)
        task_id = list(repo.root)[0].get("id")
        
        # Edit to add due date
        spec2 = NodeSpec(tag="task", due="2026-03-15")
        result = repo.edit_node_by_id(task_id, spec2, delete=False)
        assert result.success
        
        # Verify due date was added
        task = repo.search(f"//task[@id='{task_id}']")[0]
        assert task.get("due") == "2026-03-15"
        print("   ✓ Due date added via edit")
        
        # Edit to change due date
        spec3 = NodeSpec(tag="task", due="2026-04-01")
        result = repo.edit_node_by_id(task_id, spec3, delete=False)
        assert result.success
        
        task = repo.search(f"//task[@id='{task_id}']")[0]
        assert task.get("due") == "2026-04-01"
        print("   ✓ Due date changed via edit")
        
        print("   ✅ edit_node() with due test passed")


def test_calendar_export_with_due():
    """Test calendar export uses due dates."""
    print("\n5. Testing calendar export with --due...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = ManifestRepository()
        testfile = os.path.join(tmpdir, "test.xml")
        repo.load(testfile, auto_sidecar=True)
        
        # Add tasks with due dates
        for i in range(3):
            spec = NodeSpec(
                tag="task",
                topic=f"Task {i+1}",
                status="active",
                due=f"2026-03-{15+i:02d}"
            )
            repo.add_node("/*", spec, auto_id=True)
        
        # Get tasks with due dates
        tasks = repo.search("//task[@due]")
        assert len(tasks) == 3
        
        # Export to calendar
        from manifest_manager.calendar import export_to_ics
        
        ics_file = os.path.join(tmpdir, "tasks.ics")
        count = export_to_ics(tasks, ics_file)
        
        assert count == 3
        assert os.path.exists(ics_file)
        
        # Verify ICS content
        with open(ics_file, 'r') as f:
            content = f.read()
        
        assert "20260315" in content
        assert "20260316" in content
        assert "20260317" in content
        
        print(f"   ✓ Exported {count} tasks with due dates")
        print("   ✓ All dates present in ICS")
        print("   ✅ Calendar export test passed")


def test_nodespec_without_due():
    """Test NodeSpec still works without due (backward compatibility)."""
    print("\n6. Testing backward compatibility (no due)...")
    
    spec = NodeSpec(
        tag="task",
        topic="No due date",
        status="pending"
    )
    
    assert spec.due is None
    print("   ✓ NodeSpec without due works")
    
    attrs = spec.to_xml_attrs()
    assert 'due' not in attrs
    print("   ✓ to_xml_attrs() excludes None due")
    
    print("   ✅ Backward compatibility test passed")


def run_all_tests():
    """Run all --due option tests."""
    print("=" * 70)
    print("DUE DATE AS FIRST-CLASS ATTRIBUTE TEST SUITE")
    print("Testing --due option in CLI")
    print("=" * 70)
    
    tests = [
        test_nodespec_due_attribute,
        test_nodespec_from_args,
        test_add_node_with_due,
        test_edit_node_with_due,
        test_calendar_export_with_due,
        test_nodespec_without_due,
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
        print("\n🎉 ALL DUE DATE TESTS PASSED!")
        print("\nFeatures verified:")
        print("  ✓ NodeSpec has due as first-class attribute")
        print("  ✓ from_args() factory includes due")
        print("  ✓ add command works with --due")
        print("  ✓ edit command works with --due")
        print("  ✓ Calendar export uses due dates")
        print("  ✓ Backward compatible (due is optional)")
        print("\nCLI Usage:")
        print("  add --tag task --topic 'Review' --due 2026-03-15")
        print("  edit a3f --due 2026-03-20")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
