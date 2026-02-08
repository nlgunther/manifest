#!/usr/bin/env python3
"""
revert_to_clean_state.py
Restores manifest.py to the clean state (End of Phase 2).
"""
from pathlib import Path
import shutil
import sys

# Paths
PROJECT_ROOT = Path(__file__).parent
MANIFEST_DIR = PROJECT_ROOT / "src" / "manifest_manager"
MANIFEST_PATH = MANIFEST_DIR / "manifest.py"

def run():
    print("=" * 60)
    print("REVERTING TO CLEAN STATE")
    print("=" * 60)

    # We look for backups created by the Harmonization script (Phase 2)
    # Pattern was: manifest.py.backup_YYYYMMDD_HHMMSS
    # (Phase 3 backups were named .phase3_backup_...)
    
    backups = list(MANIFEST_DIR.glob("manifest.py.backup_*"))
    
    if not backups:
        # Fallback: Try to find the OLDEST phase3 backup (the state before we broke it)
        print("ℹ No Phase 2 backup found. Looking for oldest Phase 3 backup...")
        backups = list(MANIFEST_DIR.glob("manifest.py.phase3_backup_*"))
    
    if not backups:
        print("❌ Error: No backups found! Cannot revert automatically.")
        sys.exit(1)

    # Sort by name (timestamp)
    # We want the LAST "backup_*" (latest good Phase 2) 
    # OR the FIRST "phase3_backup_*" (state before Phase 3 started)
    
    # Let's prioritize the standard backup format
    clean_backups = [b for b in backups if ".phase3_backup" not in b.name]
    phase3_backups = [b for b in backups if ".phase3_backup" in b.name]
    
    target_backup = None
    
    if clean_backups:
        target_backup = sorted(clean_backups)[-1] # Latest clean backup
        print(f"✓ Found Clean Phase 2 Backup: {target_backup.name}")
    elif phase3_backups:
        target_backup = sorted(phase3_backups)[0] # Oldest Phase 3 backup (pre-breakage)
        print(f"✓ Found Pre-Phase 3 Backup: {target_backup.name}")
    
    if not target_backup:
        print("❌ Error: Could not determine a valid backup to restore.")
        sys.exit(1)
        
    # Restore
    try:
        shutil.copy2(target_backup, MANIFEST_PATH)
        print(f"✅ Restored {MANIFEST_PATH.name} from {target_backup.name}")
        print("   The file is now clean. You may proceed to Phase 3.")
    except Exception as e:
        print(f"❌ Restore failed: {e}")

if __name__ == "__main__":
    run()