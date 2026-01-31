#!/usr/bin/env python3
"""
Manifest Manager v3.4 - Package Verification Script
===================================================

Run this script to verify the package is complete and ready to use.

Usage:
    python verify_package.py
"""

import os
import sys
from pathlib import Path

def check_file(filepath, description):
    """Check if file exists."""
    exists = Path(filepath).exists()
    status = "✓" if exists else "✗"
    print(f"  [{status}] {description}: {filepath}")
    return exists

def check_python_syntax(filepath):
    """Check if Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            compile(f.read(), filepath, 'exec')
        return True
    except SyntaxError as e:
        print(f"      ✗ Syntax error: {e}")
        return False

def main():
    print("=" * 70)
    print("MANIFEST MANAGER v3.4 - PACKAGE VERIFICATION")
    print("=" * 70)
    
    all_ok = True
    
    # Core files
    print("\n📄 Core Python Files:")
    core_files = [
        ('manifest.py', 'CLI interface'),
        ('manifest_core.py', 'Business logic'),
        ('config.py', 'Configuration system'),
        ('id_sidecar.py', 'ID sidecar'),
        ('storage.py', 'File I/O'),
    ]
    
    for filepath, desc in core_files:
        if not check_file(filepath, desc):
            all_ok = False
        elif filepath.endswith('.py'):
            if not check_python_syntax(filepath):
                all_ok = False
    
    # Configuration
    print("\n⚙️  Configuration Files:")
    config_files = [
        ('pyproject.toml', 'Package metadata'),
    ]
    
    for filepath, desc in config_files:
        if not check_file(filepath, desc):
            all_ok = False
    
    # Documentation
    print("\n📚 Documentation:")
    doc_files = [
        ('README_v3.4.md', 'Package README'),
        ('CHANGELOG.md', 'Version history'),
        ('INSTALL.md', 'Installation guide'),
        ('INDEX.md', 'Package index'),
    ]
    
    for filepath, desc in doc_files:
        if not check_file(filepath, desc):
            all_ok = False
    
    # Tests
    print("\n🧪 Test Files:")
    test_files = [
        ('tests/test_config.py', 'Config tests'),
        ('tests/test_id_sidecar.py', 'Sidecar tests'),
        ('tests/test_manifest_core_integration.py', 'Integration tests'),
        ('tests/test_integration_v34.py', 'v3.4 tests'),
    ]
    
    for filepath, desc in test_files:
        if not check_file(filepath, desc):
            all_ok = False
        elif filepath.endswith('.py'):
            if not check_python_syntax(filepath):
                all_ok = False
    
    # Documentation (detailed)
    print("\n📖 Detailed Documentation:")
    detailed_docs = [
        ('docs/DOCUMENTATION_PATCHES_v3.4.md', 'API reference'),
        ('docs/IMPLEMENTATION_SUMMARY_v3.4.md', 'Technical details'),
        ('docs/FACTORY_RESP_IMPLEMENTATION.md', 'Design patterns'),
    ]
    
    for filepath, desc in detailed_docs:
        if not check_file(filepath, desc):
            all_ok = False
    
    # Try importing modules
    print("\n🔍 Python Import Tests:")
    try:
        sys.path.insert(0, '.')
        print("  [✓] Testing imports...")
        
        from manifest_core import NodeSpec, ManifestRepository
        print("      ✓ manifest_core imports OK")
        
        from config import Config
        print("      ✓ config imports OK")
        
        from id_sidecar import IDSidecar
        print("      ✓ id_sidecar imports OK")
        
        from storage import StorageManager
        print("      ✓ storage imports OK")
        
    except ImportError as e:
        print(f"      ✗ Import failed: {e}")
        all_ok = False
    
    # Check for critical bugs
    print("\n🐛 Bug Checks:")
    
    # Check for duplicate @dataclass decorator
    with open('manifest_core.py', 'r') as f:
        content = f.read()
        if '@dataclass\n@dataclass' in content:
            print("  [✗] Duplicate @dataclass decorator found!")
            all_ok = False
        else:
            print("  [✓] No duplicate @dataclass")
    
    # Check NodeSpec field ordering
    try:
        from manifest_core import NodeSpec
        spec = NodeSpec(tag="test")
        print("  [✓] NodeSpec dataclass fields ordered correctly")
    except TypeError as e:
        print(f"  [✗] NodeSpec field ordering error: {e}")
        all_ok = False
    
    # Summary
    print("\n" + "=" * 70)
    if all_ok:
        print("✅ VERIFICATION PASSED - Package is ready to use!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. pip install lxml py7zr pyyaml")
        print("  2. pip install -e .")
        print("  3. pytest tests/ -v")
        print("  4. manifest")
        return 0
    else:
        print("❌ VERIFICATION FAILED - Some files are missing or have errors")
        print("=" * 70)
        print("\nPlease check the errors above and fix them before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
