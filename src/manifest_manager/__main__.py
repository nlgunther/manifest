#!/usr/bin/env python3
"""
Manifest Manager CLI Entry Point
"""

def main():
    """Entry point for manifest command."""
    from manifest_manager.manifest import ManifestShell
    ManifestShell().cmdloop()

if __name__ == '__main__':
    main()
