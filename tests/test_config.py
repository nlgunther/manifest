"""Tests for Config class."""
import pytest
import os
import tempfile
import yaml
from manifest_manager.config import Config


def test_config_defaults():
    """Test that defaults are loaded correctly."""
    config = Config()
    assert config.get('sidecar.enabled') == True
    assert config.get('sidecar.corruption_handling') == 'warn_and_ask'


def test_config_dot_notation():
    """Test dot-notation key access."""
    config = Config()
    assert config.get('sidecar.corruption_handling') == 'warn_and_ask'
    assert config.get('display.show_ids_prominently') == True


def test_config_nonexistent_key():
    """Test default value for missing keys."""
    config = Config()
    assert config.get('nonexistent.key', 'default') == 'default'


def test_config_merge():
    """Test that per-file config overrides global."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, 'test.xml')
        config_path = manifest_path + '.config'
        
        # Create per-file config
        with open(config_path, 'w') as f:
            yaml.dump({'sidecar': {'enabled': False}}, f)
        
        config = Config(manifest_path)
        assert config.get('sidecar.enabled') == False  # Overridden
        assert config.get('sidecar.corruption_handling') == 'warn_and_ask'  # Still default


def test_config_set_and_get():
    """Test setting and getting values."""
    config = Config()
    config.set('sidecar.auto_rebuild', True)
    assert config.get('sidecar.auto_rebuild') == True
