"""
conftest.py
===========

Pytest configuration to make 'shared' module importable in tests.
Place this file in the project root directory.
"""

import sys
from pathlib import Path

# Add src/ to Python path so tests can import from shared.*
project_root = Path(__file__).parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))