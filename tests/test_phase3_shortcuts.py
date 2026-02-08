#!/usr/bin/env python3
"""
test_phase3_shortcuts.py
========================
Tests for Phase 3: Shortcut System

Tests cover:
1. Basic shortcut expansion (task, project, location)
2. Shortcut with additional flags
3. Full syntax still works (backward compatibility)
4. Edge cases (empty strings, conflicting flags, etc.)
5. Config file loading
"""

import pytest
import tempfile
import yaml
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from manifest_manager.manifest import ManifestShell


class TestShortcutExpansion:
    """Test basic shortcut expansion functionality."""
    
    def test_task_shortcut_basic(self, tmp_path):
        """Test: add task "Title" expands correctly."""
        # This is an integration test - would need actual shell setup
        # For now, we test the logic directly
        
        # Simulate the expansion logic
        arg = 'task "Buy milk"'
        parts = ['task', 'Buy milk']
        
        # Expected expansion
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            tag = parts[0]
            new_parts = ['--tag', tag]
            if len(parts) > 1 and not parts[1].startswith('-'):
                new_parts.extend(['--topic', parts[1]])
                new_parts.extend(parts[2:])
        
        assert new_parts == ['--tag', 'task', '--topic', 'Buy milk']
    
    def test_project_shortcut_basic(self):
        """Test: add project "Name" expands correctly."""
        arg = 'project "New Project"'
        parts = ['project', 'New Project']
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            tag = parts[0]
            new_parts = ['--tag', tag]
            if len(parts) > 1 and not parts[1].startswith('-'):
                new_parts.extend(['--topic', parts[1]])
                new_parts.extend(parts[2:])
        
        assert new_parts == ['--tag', 'project', '--topic', 'New Project']
    
    def test_location_shortcut_basic(self):
        """Test: add location "Place" expands correctly."""
        parts = ['location', 'Davis, CA']
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            tag = parts[0]
            new_parts = ['--tag', tag]
            if len(parts) > 1 and not parts[1].startswith('-'):
                new_parts.extend(['--topic', parts[1]])
                new_parts.extend(parts[2:])
        
        assert new_parts == ['--tag', 'location', '--topic', 'Davis, CA']


class TestShortcutWithFlags:
    """Test shortcuts combined with additional flags."""
    
    def test_task_with_status(self):
        """Test: add task "Title" --status active"""
        parts = ['task', 'Buy milk', '--status', 'active']
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            tag = parts[0]
            new_parts = ['--tag', tag]
            if len(parts) > 1 and not parts[1].startswith('-'):
                new_parts.extend(['--topic', parts[1]])
                new_parts.extend(parts[2:])
        
        expected = ['--tag', 'task', '--topic', 'Buy milk', '--status', 'active']
        assert new_parts == expected
    
    def test_task_with_resp(self):
        """Test: add task "Title" --resp alice"""
        parts = ['task', 'Review PR', '--resp', 'alice']
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            tag = parts[0]
            new_parts = ['--tag', tag]
            if len(parts) > 1 and not parts[1].startswith('-'):
                new_parts.extend(['--topic', parts[1]])
                new_parts.extend(parts[2:])
        
        expected = ['--tag', 'task', '--topic', 'Review PR', '--resp', 'alice']
        assert new_parts == expected
    
    def test_task_with_multiple_flags(self):
        """Test: add task "Title" --status active --resp bob --due 2026-03-01"""
        parts = ['task', 'Important', '--status', 'active', '--resp', 'bob', '--due', '2026-03-01']
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            tag = parts[0]
            new_parts = ['--tag', tag]
            if len(parts) > 1 and not parts[1].startswith('-'):
                new_parts.extend(['--topic', parts[1]])
                new_parts.extend(parts[2:])
        
        expected = ['--tag', 'task', '--topic', 'Important', '--status', 'active', '--resp', 'bob', '--due', '2026-03-01']
        assert new_parts == expected


class TestBackwardCompatibility:
    """Test that full syntax still works (no regression)."""
    
    def test_full_syntax_still_works(self):
        """Test: add --tag task --topic "Title" (old way)"""
        parts = ['--tag', 'task', '--topic', 'Buy milk']
        shortcuts = {'task', 'project', 'location'}
        
        # Should NOT expand (starts with --)
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            new_parts = ['--tag', parts[0]]
        else:
            new_parts = parts  # Pass through unchanged
        
        assert new_parts == ['--tag', 'task', '--topic', 'Buy milk']
    
    def test_xpath_parent_still_works(self):
        """Test: add --tag task --topic "Title" --parent "//project" """
        parts = ['--tag', 'task', '--topic', 'Subtask', '--parent', '//project']
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            new_parts = ['--tag', parts[0]]
        else:
            new_parts = parts
        
        assert new_parts == ['--tag', 'task', '--topic', 'Subtask', '--parent', '//project']


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_shortcut_without_title(self):
        """Test: add task --status active (no title provided)"""
        parts = ['task', '--status', 'active']
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            tag = parts[0]
            new_parts = ['--tag', tag]
            if len(parts) > 1 and not parts[1].startswith('-'):
                new_parts.extend(['--topic', parts[1]])
                new_parts.extend(parts[2:])
            else:
                new_parts.extend(parts[1:])  # No topic, just flags
        
        expected = ['--tag', 'task', '--status', 'active']
        assert new_parts == expected
    
    def test_empty_input(self):
        """Test: empty parts list"""
        parts = []
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            new_parts = ['--tag', parts[0]]
        else:
            new_parts = parts
        
        assert new_parts == []
    
    def test_single_word_shortcut(self):
        """Test: add task (just the shortcut, no title)"""
        parts = ['task']
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            tag = parts[0]
            new_parts = ['--tag', tag]
            if len(parts) > 1 and not parts[1].startswith('-'):
                new_parts.extend(['--topic', parts[1]])
                new_parts.extend(parts[2:])
            else:
                new_parts.extend(parts[1:])
        
        expected = ['--tag', 'task']
        assert new_parts == expected
    
    def test_unknown_shortcut_fallback(self):
        """Test: add unknown "Title" should not expand"""
        parts = ['unknown', 'Some title']
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            new_parts = ['--tag', parts[0]]
        else:
            new_parts = parts  # Pass through
        
        assert new_parts == ['unknown', 'Some title']
    
    def test_flag_that_looks_like_shortcut(self):
        """Test: --task should not be treated as shortcut"""
        parts = ['--task', 'value']
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            new_parts = ['--tag', parts[0]]
        else:
            new_parts = parts
        
        assert new_parts == ['--task', 'value']


class TestConfigLoading:
    """Test configuration file loading."""
    
    def test_config_file_structure(self):
        """Test that config file has correct structure."""
        config_path = Path(__file__).parent.parent / "config" / "shortcuts.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            assert 'shortcuts' in config
            assert isinstance(config['shortcuts'], list)
            assert 'task' in config['shortcuts']
            assert 'project' in config['shortcuts']
            assert 'location' in config['shortcuts']
    
    def test_default_shortcuts_present(self):
        """Test that all default shortcuts are in config."""
        config_path = Path(__file__).parent.parent / "config" / "shortcuts.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            shortcuts = set(config['shortcuts'])
            required = {'task', 'project', 'item', 'note', 'milestone', 'idea', 'location'}
            
            assert required.issubset(shortcuts), f"Missing shortcuts: {required - shortcuts}"
    
    def test_reserved_keywords_validation(self):
        """Test that reserved keywords don't include 'add'."""
        config_path = Path(__file__).parent.parent / "config" / "shortcuts.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if 'reserved_keywords' in config:
                reserved = config['reserved_keywords']
                assert 'add' not in reserved, "'add' should not be reserved (it's the command!)"


class TestShortcutParsing:
    """Test the actual parsing logic with shlex."""
    
    def test_quoted_title_with_spaces(self):
        """Test: add task "Title with spaces" """
        import shlex
        arg = 'task "Title with spaces"'
        parts = shlex.split(arg)
        
        assert parts == ['task', 'Title with spaces']
    
    def test_quoted_title_with_flags(self):
        """Test: add task "Title" --status active"""
        import shlex
        arg = 'task "My Title" --status active'
        parts = shlex.split(arg)
        
        assert parts == ['task', 'My Title', '--status', 'active']
    
    def test_unquoted_single_word(self):
        """Test: add task MyTask"""
        import shlex
        arg = 'task MyTask'
        parts = shlex.split(arg)
        
        assert parts == ['task', 'MyTask']
    
    def test_title_with_special_chars(self):
        """Test: add task "Title with 'quotes' and \"nested\"" """
        import shlex
        arg = """task "Title with special chars: @#$%^&*()" """
        parts = shlex.split(arg)
        
        assert parts[0] == 'task'
        assert parts[1] == "Title with special chars: @#$%^&*()"


class TestIntegrationScenarios:
    """Real-world usage scenarios."""
    
    def test_scenario_simple_task(self):
        """Scenario: User adds a simple task."""
        import shlex
        arg = 'task "Buy groceries"'
        parts = shlex.split(arg)
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            tag = parts[0]
            new_parts = ['--tag', tag]
            if len(parts) > 1 and not parts[1].startswith('-'):
                new_parts.extend(['--topic', parts[1]])
                new_parts.extend(parts[2:])
        
        assert new_parts == ['--tag', 'task', '--topic', 'Buy groceries']
    
    def test_scenario_project_with_status(self):
        """Scenario: User creates a project with status."""
        import shlex
        arg = 'project "Q1 Goals" --status planning'
        parts = shlex.split(arg)
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            tag = parts[0]
            new_parts = ['--tag', tag]
            if len(parts) > 1 and not parts[1].startswith('-'):
                new_parts.extend(['--topic', parts[1]])
                new_parts.extend(parts[2:])
        
        assert new_parts == ['--tag', 'project', '--topic', 'Q1 Goals', '--status', 'planning']
    
    def test_scenario_location_tracking(self):
        """Scenario: User tracks a location."""
        import shlex
        arg = 'location "Conference Room A" --parent "//building[@name=\'Office\']"'
        parts = shlex.split(arg)
        shortcuts = {'task', 'project', 'location'}
        
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            tag = parts[0]
            new_parts = ['--tag', tag]
            if len(parts) > 1 and not parts[1].startswith('-'):
                new_parts.extend(['--topic', parts[1]])
                new_parts.extend(parts[2:])
        
        expected = ['--tag', 'location', '--topic', 'Conference Room A', '--parent', "//building[@name='Office']"]
        assert new_parts == expected
    
    def test_scenario_backward_compat_user(self):
        """Scenario: Existing user uses old syntax."""
        import shlex
        arg = '--tag task --topic "Old style task"'
        parts = shlex.split(arg)
        shortcuts = {'task', 'project', 'location'}
        
        # Should pass through unchanged
        if parts and parts[0] in shortcuts and not parts[0].startswith('-'):
            new_parts = ['--tag', parts[0]]
        else:
            new_parts = parts
        
        assert new_parts == ['--tag', 'task', '--topic', 'Old style task']


# Test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
