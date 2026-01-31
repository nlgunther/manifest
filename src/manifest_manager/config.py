"""
Configuration Management
========================

Simple YAML configuration with hierarchical defaults.

Extension Points:
    - Additional config backends (JSON, TOML) - see _load_file()
    - Config validation schemas - see _validate()
    - Dynamic config reload - add watch() method
    - Environment variable overrides - see get()

Example:
    >>> config = Config('/path/to/manifest.xml')
    >>> handling = config.get('sidecar.corruption_handling')
    >>> print(handling)
    'warn_and_ask'
"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path


class Config:
    """Simple hierarchical configuration manager.
    
    Priority: per-file > global > defaults
    """
    
    # Default configuration
    DEFAULTS = {
        'sidecar': {
            'corruption_handling': 'warn_and_ask',  # silent | warn_and_proceed | warn_and_ask
            'auto_rebuild': False,
            'enabled': True,
        },
        'display': {
            'show_ids_prominently': True,
            'id_first': True,
        },
        'performance': {
            'cache_xpaths': True,
        },
        # EXTENSION STUB: Add new config sections here
        # 'plugins': {
        #     'enabled': [],
        #     'search_path': ['~/.manifest/plugins'],
        # },
    }
    
    def __init__(self, manifest_path: Optional[str] = None):
        """Initialize config for a manifest file.
        
        Args:
            manifest_path: Path to manifest (for per-file config).
                          If None, only loads global config.
        """
        self.manifest_path = manifest_path
        self.config_path = manifest_path + ".config" if manifest_path else None
        self.global_path = self._get_global_path()
        self.config = self._load_config()
    
    @staticmethod
    def _get_global_path() -> str:
        """Get global config path (XDG-compliant)."""
        if os.name == 'nt':
            base = os.environ.get('APPDATA', os.path.expanduser('~'))
            return os.path.join(base, 'manifest', 'config.yaml')
        else:
            base = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
            return os.path.join(base, 'manifest', 'config.yaml')
    
    def _load_config(self) -> Dict[str, Any]:
        """Load config with priority: per-file > global > defaults."""
        config = self._deep_copy(self.DEFAULTS)
        
        # Load global
        if os.path.exists(self.global_path):
            global_cfg = self._load_file(self.global_path)
            if global_cfg:
                config = self._deep_merge(config, global_cfg)
        
        # Load per-file (overrides global)
        if self.config_path and os.path.exists(self.config_path):
            file_cfg = self._load_file(self.config_path)
            if file_cfg:
                config = self._deep_merge(config, file_cfg)
        
        return config
    
    def _load_file(self, path: str) -> Optional[Dict]:
        """Load config file.
        
        EXTENSION POINT: Add support for other formats
        
        To add JSON support:
            if path.endswith('.json'):
                with open(path) as f:
                    return json.load(f)
        
        To add TOML support:
            if path.endswith('.toml'):
                import tomli
                with open(path, 'rb') as f:
                    return tomli.load(f)
        """
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return None
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get config value using dot-notation.
        
        Args:
            key_path: Dot-separated path (e.g., 'sidecar.enabled')
            default: Fallback value if not found
            
        Returns:
            Config value or default
            
        EXTENSION POINT: Add environment variable overrides
        
        To add env var support:
            env_key = 'MANIFEST_' + key_path.upper().replace('.', '_')
            if env_key in os.environ:
                return os.environ[env_key]
        
        Example:
            >>> config.get('sidecar.enabled')
            True
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key_path: str, value: Any) -> None:
        """Set config value (in-memory only until save()).
        
        Args:
            key_path: Dot-separated path
            value: Value to set
        """
        keys = key_path.split('.')
        current = self.config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def save(self, global_config: bool = False) -> None:
        """Save config to disk.
        
        Args:
            global_config: Save to global config if True, per-file if False
            
        Raises:
            ValueError: If saving per-file without manifest_path
        """
        path = self.global_path if global_config else self.config_path
        
        if not path:
            raise ValueError("Cannot save per-file config without manifest_path")
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # EXTENSION POINT: Format detection
        # Could auto-detect format from extension and call appropriate dumper
        with open(path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, indent=2)
    
    @staticmethod
    def _deep_copy(obj: Dict) -> Dict:
        """Deep copy dictionary."""
        import copy
        return copy.deepcopy(obj)
    
    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        """Recursively merge override into base."""
        result = base.copy()
        for key, value in override.items():
            if (key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    # EXTENSION STUB: Validation
    # def _validate(self, config: Dict) -> None:
    #     """Validate config against schema.
    #     
    #     To implement:
    #         1. Define schema (e.g., using jsonschema)
    #         2. Validate on load
    #         3. Raise ConfigError on invalid
    #     
    #     Example:
    #         schema = {
    #             'sidecar': {
    #                 'corruption_handling': {
    #                     'enum': ['silent', 'warn_and_proceed', 'warn_and_ask']
    #                 }
    #             }
    #         }
    #         # Use jsonschema.validate(config, schema)
    #     """
    #     pass
