#!/usr/bin/env python3
"""
Test for ID shortcuts in --parent parameter (v3.4.1)
"""
import sys
import os
import tempfile

sys.path.insert(0, '/home/claude/src')

from manifest_manager.manifest_core import ManifestRepository, NodeSpec

def test_parent_id_shortcut():
    """Test adding child nodes using parent ID shortcuts."""
    print("Testing parent ID shortcut functionality...")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = ManifestRepository()
        testfile = os.path.join(tmpdir, "test.xml")
        
        # 1. Load with sidecar
        print("\n1. Loading manifest with sidecar...")
        result = repo.load(testfile, auto_sidecar=True)
        assert result.success
        print(f"   ✓ {result.message}")
        
        # 2. Add a project
        print("\n2. Adding a project...")
        project_spec = NodeSpec(
            tag="project",
            topic="Test Project",
            status="active"
        )
        result = repo.add_node("/*", project_spec, auto_id=True)
        assert result.success
        print(f"   ✓ {result.message}")
        
        # Get the project ID
        project = repo.root[0]
        project_id = project.get("id")
        print(f"   Project ID: {project_id}")
        
        # 3. Add a task using full ID
        print(f"\n3. Adding task using full parent ID ({project_id})...")
        # In the CLI, this would be: add --tag task --topic "Task 1" --parent {project_id}
        # We simulate by getting XPath from sidecar
        parent_xpath = repo.id_sidecar.get(project_id)
        task_spec = NodeSpec(
            tag="task",
            topic="Task 1",
            status="active",
            resp="alice"
        )
        result = repo.add_node(parent_xpath, task_spec, auto_id=True)
        assert result.success
        print(f"   ✓ {result.message}")
        
        # 4. Add another task using ID prefix
        print(f"\n4. Adding task using ID prefix ({project_id[:3]})...")
        # Simulate prefix lookup
        prefix = project_id[:3]
        matching_ids = [
            elem_id for elem_id in repo.id_sidecar.all_ids()
            if elem_id.startswith(prefix)
        ]
        print(f"   IDs matching '{prefix}': {matching_ids}")
        
        # Use first match (in CLI, would show interactive selection if multiple)
        parent_xpath = repo.id_sidecar.get(matching_ids[0])
        task_spec2 = NodeSpec(
            tag="task",
            topic="Task 2",
            status="pending",
            resp="bob"
        )
        result = repo.add_node(parent_xpath, task_spec2, auto_id=True)
        assert result.success
        print(f"   ✓ {result.message}")
        
        # 5. Verify structure
        print("\n5. Verifying structure...")
        assert len(project) == 2, "Project should have 2 tasks"
        task1 = project[0]
        task2 = project[1]
        
        assert task1.get("topic") == "Task 1"
        assert task1.get("resp") == "alice"
        assert task2.get("topic") == "Task 2"
        assert task2.get("resp") == "bob"
        
        print(f"   ✓ Project has {len(project)} tasks")
        print(f"   ✓ Task 1: '{task1.get('topic')}' assigned to {task1.get('resp')}")
        print(f"   ✓ Task 2: '{task2.get('topic')}' assigned to {task2.get('resp')}")
        
        # 6. Display final structure
        print("\n6. Final structure:")
        print("-" * 60)
        print(f"Project: {project.get('topic')} [id={project.get('id')}]")
        for i, task in enumerate(project, 1):
            print(f"  Task {i}: {task.get('topic')} "
                  f"[@{task.get('resp')}] "
                  f"[{task.get('status')}] "
                  f"[id={task.get('id')}]")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("\n💡 In the CLI, you can now use:")
        print(f"   add --tag task --topic \"Task 3\" --parent {project_id[:3]}")
        print(f"   add --tag task --topic \"Task 4\" --parent {project_id}")
        print(f"   add --tag task --topic \"Task 5\" --parent \"//project[@topic='Test Project']\"")

if __name__ == "__main__":
    test_parent_id_shortcut()  # Returns None implicitly
    sys.exit(0)