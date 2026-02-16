"""
Tests for DataFrame Conversion Module

Covers:
    - Basic tree to DataFrame conversion
    - Search results to DataFrame
    - DataFrame to tree round-trip
    - Edge cases and error handling
    - CLI command integration
"""

import pytest
import pandas as pd
from lxml import etree
from pathlib import Path

# Import functions to test
from manifest_manager.dataframe_conversion import (
    to_dataframe,
    find_to_dataframe,
    from_dataframe,
    preview_dataframe
)


class TestToDataFrame:
    """Test to_dataframe() function."""
    
    def test_simple_tree(self):
        """Convert simple tree to DataFrame."""
        root = etree.Element('root')
        child = etree.SubElement(root, 'child', id='c1', status='active')
        child.text = 'Child text'
        
        df = to_dataframe(root)
        
        assert len(df) == 2  # root + child
        assert list(df.columns[:4]) == ['id', 'parent_id', 'tag', 'text']
        assert 'status' in df.columns
        
        # Check root row
        root_row = df[df['id'] == df.iloc[0]['id']].iloc[0]
        assert root_row['tag'] == 'root'
        assert root_row['parent_id'] == 'root'
        
        # Check child row
        child_row = df[df['id'] == 'c1'].iloc[0]
        assert child_row['tag'] == 'child'
        assert child_row['status'] == 'active'
        assert child_row['text'] == 'Child text'
    
    def test_hierarchy_preserved(self):
        """Verify parent-child relationships are preserved."""
        root = etree.Element('root', id='r')
        proj = etree.SubElement(root, 'project', id='p1')
        task = etree.SubElement(proj, 'task', id='t1')
        
        df = to_dataframe(root)
        
        # Check parent_id relationships
        assert df[df['id'] == 'r'].iloc[0]['parent_id'] == 'root'
        assert df[df['id'] == 'p1'].iloc[0]['parent_id'] == 'r'
        assert df[df['id'] == 't1'].iloc[0]['parent_id'] == 'p1'
    
    def test_multiple_siblings(self):
        """Handle multiple siblings correctly."""
        root = etree.Element('project', id='p1')
        etree.SubElement(root, 'task', id='t1')
        etree.SubElement(root, 'task', id='t2')
        etree.SubElement(root, 'task', id='t3')
        
        df = to_dataframe(root)
        
        assert len(df) == 4  # project + 3 tasks
        tasks = df[df['tag'] == 'task']
        assert len(tasks) == 3
        assert all(tasks['parent_id'] == 'p1')
    
    def test_no_text_option(self):
        """Test include_text=False option."""
        root = etree.Element('root')
        child = etree.SubElement(root, 'child')
        child.text = 'Should not appear'
        
        df = to_dataframe(root, include_text=False)
        
        assert 'text' not in df.columns
    
    def test_attributes_become_columns(self):
        """All attributes become DataFrame columns."""
        root = etree.Element('task', 
                           id='t1',
                           status='active',
                           priority='high',
                           assignee='alice')
        
        df = to_dataframe(root)
        
        assert 'status' in df.columns
        assert 'priority' in df.columns
        assert 'assignee' in df.columns
        assert df.iloc[0]['status'] == 'active'
    
    def test_empty_tree(self):
        """Handle tree with no children."""
        root = etree.Element('empty')
        df = to_dataframe(root)
        
        assert len(df) == 1  # Just the root
        assert df.iloc[0]['tag'] == 'empty'
    
    def test_generated_ids(self):
        """Auto-generate IDs for nodes without id attribute."""
        root = etree.Element('root')
        etree.SubElement(root, 'child1')
        etree.SubElement(root, 'child2')
        
        df = to_dataframe(root, generate_ids=True)
        
        assert len(df) == 3
        # All nodes should have IDs (generated or otherwise)
        assert all(pd.notna(df['id']))
        # IDs should be unique
        assert len(df['id'].unique()) == 3


class TestFindToDataFrame:
    """Test find_to_dataframe() function."""
    
    def create_test_tree(self):
        """Create tree for testing."""
        root = etree.Element('root')
        
        p1 = etree.SubElement(root, 'project', id='p1', status='active')
        etree.SubElement(p1, 'task', id='t1', status='active', priority='high')
        etree.SubElement(p1, 'task', id='t2', status='done', priority='low')
        
        p2 = etree.SubElement(root, 'project', id='p2', status='planning')
        etree.SubElement(p2, 'task', id='t3', status='active', priority='high')
        
        return root
    
    def test_find_active_tasks(self):
        """Find all active tasks."""
        tree = self.create_test_tree()
        
        df = find_to_dataframe(tree, "//task[@status='active']")
        
        assert len(df) == 3  # results wrapper + 2 tasks
        tasks = df[df['tag'] == 'task']
        assert len(tasks) == 2
        assert all(tasks['status'] == 'active')
    
    def test_find_high_priority(self):
        """Find high priority items."""
        tree = self.create_test_tree()
        
        df = find_to_dataframe(tree, "//task[@priority='high']")
        
        tasks = df[df['tag'] == 'task']
        assert len(tasks) == 2
        assert all(tasks['priority'] == 'high')
    
    def test_no_matches(self):
        """Handle XPath with no matches."""
        tree = self.create_test_tree()
        
        df = find_to_dataframe(tree, "//nonexistent")
        
        assert df.empty or len(df) == 0
    
    def test_custom_wrapper(self):
        """Use custom wrapper tag."""
        tree = self.create_test_tree()
        
        df = find_to_dataframe(tree, "//project", wrap_tag='search_results')
        
        # First row should be the wrapper
        assert df.iloc[0]['tag'] == 'search_results'
    
    def test_original_tree_unchanged(self):
        """Verify original tree is not modified."""
        tree = self.create_test_tree()
        original_children = len(tree)
        
        df = find_to_dataframe(tree, "//task")
        
        # Original tree should be unchanged
        assert len(tree) == original_children


class TestFromDataFrame:
    """Test from_dataframe() function."""
    
    def test_simple_round_trip(self):
        """Convert tree → DataFrame → tree."""
        # Create original tree
        root = etree.Element('root')
        proj = etree.SubElement(root, 'project', id='p1', status='active')
        task = etree.SubElement(proj, 'task', id='t1', priority='high')
        task.text = 'Task description'
        
        # Convert to DataFrame
        df = to_dataframe(root)
        
        # Convert back to tree
        reconstructed = from_dataframe(df)
        
        # Verify structure
        assert reconstructed.tag == 'root'
        assert len(reconstructed) == 1
        
        proj_elem = reconstructed[0]
        assert proj_elem.tag == 'project'
        assert proj_elem.get('id') == 'p1'
        assert proj_elem.get('status') == 'active'
        
        task_elem = proj_elem[0]
        assert task_elem.tag == 'task'
        assert task_elem.get('id') == 't1'
        assert task_elem.get('priority') == 'high'
        assert task_elem.text == 'Task description'
    
    def test_attributes_preserved(self):
        """All DataFrame columns become attributes."""
        df = pd.DataFrame([
            {'id': 'n1', 'parent_id': 'root', 'tag': 'node', 
             'attr1': 'value1', 'attr2': 'value2'}
        ])
        
        tree = from_dataframe(df)
        
        # When first row has parent_id='root', it becomes the root
        # So the tree itself is the node, not tree[0]
        assert tree.tag == 'node'
        assert tree.get('attr1') == 'value1'
        assert tree.get('attr2') == 'value2'
    
    def test_missing_columns(self):
        """Raise error if required columns missing."""
        df = pd.DataFrame([
            {'id': 'n1', 'tag': 'node'}  # Missing parent_id
        ])
        
        with pytest.raises(ValueError, match="missing required columns"):
            from_dataframe(df)
    
    def test_nan_handling(self):
        """Handle NaN values gracefully."""
        df = pd.DataFrame([
            {'id': 'root_node', 'parent_id': 'root', 'tag': 'root_tag', 
             'optional': None, 'text': None},
            {'id': 'n1', 'parent_id': 'root_node', 'tag': 'node',
             'optional': None, 'text': None}
        ])
        
        tree = from_dataframe(df)
        
        # Should not crash, NaN values skipped
        # Tree root should be first row
        assert tree.tag == 'root_tag'
        assert tree.get('id') == 'root_node'
        
        # Child node should exist
        node = tree[0]
        assert node.tag == 'node'
        assert 'optional' not in node.attrib  # NaN was skipped


class TestPreviewDataFrame:
    """Test preview_dataframe() function."""
    
    def test_preview_format(self):
        """Test preview output format."""
        df = pd.DataFrame([
            {'id': 't1', 'tag': 'task', 'status': 'active'},
            {'id': 't2', 'tag': 'task', 'status': 'done'},
            {'id': 'm1', 'tag': 'milestone', 'status': 'planning'},
        ])
        
        preview = preview_dataframe(df)
        
        assert 'DataFrame: 3 rows' in preview
        assert 'Columns:' in preview
        assert 'Tags: task(2), milestone(1)' in preview
        assert 'Preview:' in preview
    
    def test_empty_dataframe(self):
        """Handle empty DataFrame."""
        df = pd.DataFrame()
        preview = preview_dataframe(df)
        
        assert preview == "Empty DataFrame"


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_search_transform_save_workflow(self, tmp_path):
        """Complete workflow: search → DataFrame → transform → save."""
        # Create test tree
        root = etree.Element('root')
        proj = etree.SubElement(root, 'project', id='p1')
        etree.SubElement(proj, 'task', id='t1', status='pending')
        etree.SubElement(proj, 'task', id='t2', status='pending')
        
        # Find pending tasks
        df = find_to_dataframe(root, "//task[@status='pending']")
        
        # Transform (simulate user pandas pipeline)
        df_tasks = df[df['tag'] == 'task'].copy()
        df_tasks['status'] = 'in_progress'
        
        # Save
        csv_path = tmp_path / 'tasks.csv'
        df_tasks.to_csv(csv_path, index=False)
        
        # Verify file
        assert csv_path.exists()
        
        # Load and verify
        loaded = pd.read_csv(csv_path)
        assert len(loaded) == 2
        assert all(loaded['status'] == 'in_progress')
    
    def test_export_edit_import_workflow(self, tmp_path):
        """Full round-trip workflow."""
        # Create tree
        root = etree.Element('root')
        proj = etree.SubElement(root, 'project', id='p1', status='active')
        etree.SubElement(proj, 'task', id='t1', status='pending')
        
        # Export
        df = to_dataframe(root)
        csv_path = tmp_path / 'export.csv'
        df.to_csv(csv_path, index=False)
        
        # Edit (simulate external modification)
        df_edited = pd.read_csv(csv_path)
        df_edited.loc[df_edited['id'] == 't1', 'status'] = 'done'
        df_edited.to_csv(csv_path, index=False)
        
        # Import back
        df_imported = pd.read_csv(csv_path)
        tree_imported = from_dataframe(df_imported)
        
        # Verify change applied
        task = tree_imported.xpath("//task[@id='t1']")[0]
        assert task.get('status') == 'done'


# Test fixtures
@pytest.fixture
def sample_tree():
    """Create sample tree for testing."""
    root = etree.Element('manifest')
    
    p1 = etree.SubElement(root, 'project', id='p1', title='Website')
    m1 = etree.SubElement(p1, 'milestone', id='m1', title='Design')
    etree.SubElement(m1, 'task', id='t1', title='Mockups', status='active')
    etree.SubElement(m1, 'task', id='t2', title='Review', status='pending')
    
    p2 = etree.SubElement(root, 'project', id='p2', title='Mobile App')
    etree.SubElement(p2, 'task', id='t3', title='Setup', status='active')
    
    return root


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for testing."""
    return pd.DataFrame([
        {'id': 'p1', 'parent_id': 'root', 'tag': 'project', 'title': 'Website'},
        {'id': 'm1', 'parent_id': 'p1', 'tag': 'milestone', 'title': 'Design'},
        {'id': 't1', 'parent_id': 'm1', 'tag': 'task', 'title': 'Mockups', 'status': 'active'},
        {'id': 't2', 'parent_id': 'm1', 'tag': 'task', 'title': 'Review', 'status': 'pending'},
    ])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
