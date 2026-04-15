"""
test_load_aliases.py
====================

Tests for path alias expansion in the load command.

Aliases are defined in the global config (``%APPDATA%\\manifest\\config.yaml``)
under the ``aliases`` key and are expanded by ``do_load`` before the filename
reaches the repository layer.

Covers:
    - Known alias expands to its full path
    - Unknown name passes through unchanged
    - Alias works with --autosc flag
    - Alias works with --rebuildsc flag
    - Expansion is exact-match only (prefix of an alias is not expanded)
    - Empty aliases dict is handled safely
"""

import pytest
from unittest.mock import patch, MagicMock
from manifest_manager.manifest_core import ManifestRepository
from manifest_manager.manifest import ManifestShell


ALIASES = {
    "basic": "g:/my drive/manifests/todo2026",
    "work":  "g:/my drive/manifests/work2026",
}


@pytest.fixture
def shell():
    """Shell instance with config auto-load suppressed."""
    with patch("manifest_manager.manifest.Config") as mock_cfg_class:
        # Suppress startup.default_file auto-load
        instance = mock_cfg_class.return_value
        instance.get.return_value = None
        s = ManifestShell()
    return s


def _patch_aliases(aliases: dict):
    """Return a context manager that injects aliases into do_load's Config call."""
    mock_cfg = MagicMock()
    mock_cfg.get.return_value = aliases
    return patch("manifest_manager.manifest.Config", return_value=mock_cfg)


# ---------------------------------------------------------------------------
# Alias expansion
# ---------------------------------------------------------------------------

def test_known_alias_expands_to_full_path(shell, tmp_path):
    """load basic → loads the full path defined in aliases."""
    target = tmp_path / "todo2026.xml"
    target.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?><manifest/>')

    aliases = {"basic": str(target)}
    with _patch_aliases(aliases):
        shell.onecmd("load basic")

    assert shell.repo.filepath == str(target)


def test_unknown_name_passes_through_unchanged(shell, tmp_path):
    """load myfile → treated as a literal filename when not in aliases."""
    target = tmp_path / "myfile.xml"
    target.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?><manifest/>')

    with _patch_aliases({"basic": "g:/my drive/manifests/todo2026"}):
        shell.onecmd(f'load "{target}"')

    assert shell.repo.filepath == str(target)


def test_alias_with_autosc_flag(shell, tmp_path):
    """load basic --autosc expands alias and passes --autosc through."""
    target = tmp_path / "todo2026.xml"
    target.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?><manifest/>')

    aliases = {"basic": str(target)}
    with _patch_aliases(aliases):
        shell.onecmd("load basic --autosc")

    assert shell.repo.filepath == str(target)
    assert shell.repo.id_sidecar is not None


def test_alias_with_rebuildsc_flag(shell, tmp_path):
    """load basic --rebuildsc expands alias and forces sidecar rebuild."""
    target = tmp_path / "todo2026.xml"
    target.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?><manifest/>')

    aliases = {"basic": str(target)}
    with _patch_aliases(aliases):
        shell.onecmd("load basic --rebuildsc")

    assert shell.repo.filepath == str(target)


def test_alias_prefix_does_not_expand(shell, tmp_path):
    """'bas' is not an alias even if 'basic' is — expansion is exact-match only."""
    target = tmp_path / "bas.xml"
    target.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?><manifest/>')

    aliases = {"basic": "g:/my drive/manifests/todo2026"}
    with _patch_aliases(aliases):
        shell.onecmd(f'load "{target}"')

    # Should load the literal file, not the alias target
    assert shell.repo.filepath == str(target)


def test_empty_aliases_dict_is_safe(shell, tmp_path):
    """load works normally when aliases dict is empty."""
    target = tmp_path / "myfile.xml"
    target.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?><manifest/>')

    with _patch_aliases({}):
        shell.onecmd(f'load "{target}"')

    assert shell.repo.filepath == str(target)


# ---------------------------------------------------------------------------
# Prompt update
# ---------------------------------------------------------------------------

def test_prompt_updates_to_alias_target_basename(shell, tmp_path):
    """After loading via alias, prompt shows the real filename not the alias."""
    target = tmp_path / "todo2026.xml"
    target.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?><manifest/>')

    aliases = {"basic": str(target)}
    with _patch_aliases(aliases):
        shell.onecmd("load basic")

    assert "todo2026.xml" in shell.prompt
    assert "basic" not in shell.prompt
