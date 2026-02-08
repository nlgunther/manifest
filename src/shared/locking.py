"""
shared/locking.py
"""
import time
import os
from pathlib import Path
from contextlib import contextmanager

class LockTimeout(Exception): pass

def check_lock(filepath: Path) -> bool:
    """Check if a lock exists."""
    lock_path = filepath.with_suffix(filepath.suffix + ".lock")
    return lock_path.exists()

@contextmanager
def file_lock(filepath: Path, timeout: int = 5, stale_threshold: int = None):
    """
    Acquire lock with optional stale lock cleanup.
    """
    lock_path = filepath.with_suffix(filepath.suffix + ".lock")
    start = time.time()
    
    # Check for stale lock first
    if stale_threshold and lock_path.exists():
        try:
            mtime = lock_path.stat().st_mtime
            if time.time() - mtime > stale_threshold:
                try: os.remove(lock_path)
                except OSError: pass
        except OSError:
            pass 

    acquired = False
    try:
        while True:
            try:
                with open(lock_path, 'x'): pass
                acquired = True
                yield
                break
            except FileExistsError:
                if time.time() - start > timeout:
                    raise LockTimeout(f"Locked: {filepath}")
                time.sleep(0.1)
    finally:
        if acquired and lock_path.exists():
            try: os.remove(lock_path)
            except OSError: pass
