"""
Tests for shared.locking module.
"""
import pytest
import time
from pathlib import Path
from shared.locking import file_lock, LockTimeout, check_lock


def test_basic_locking(tmp_path):
    """Test basic lock acquisition and release."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("data")
    
    with file_lock(test_file):
        assert check_lock(test_file) is not None
    
    assert not check_lock(test_file)


def test_concurrent_lock(tmp_path):
    """Test that concurrent locks are prevented."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("data")
    
    with file_lock(test_file, timeout=1):
        with pytest.raises(LockTimeout):
            with file_lock(test_file, timeout=1):
                pass


def test_stale_lock_cleanup(tmp_path):
    """Test stale lock cleanup."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("data")
    lock_file = test_file.with_suffix(".txt.lock")
    
    lock_file.write_text("12345")
    
    old_time = time.time() - 400
    import os
    os.utime(lock_file, (old_time, old_time))
    
    with file_lock(test_file, stale_threshold=300):
        pass
    
    assert not lock_file.exists()
