"""
tests/test_move_node.py
=======================
Tests for ManifestRepository.move_node().
"""
import pytest
import tempfile
import os
from manifest_manager.manifest_core import ManifestRepository, NodeSpec


@pytest.fixture
def repo():
    """Fresh repo with a simple two-project tree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        r = ManifestRepository()
        path = os.path.join(tmpdir, "test.xml")
        r.load(path, auto_sidecar=True)

        # Build:  <manifest>
        #           <project id="p1" topic="Alpha">
        #             <task id="t1" topic="Do it"/>
        #           </project>
        #           <project id="p2" topic="Beta"/>
        #         </manifest>
        r.add_node("/*", NodeSpec(tag="project", topic="Alpha", attrs={"id": "p1"}), auto_id=False)
        r.add_node("//project[@id='p1']", NodeSpec(tag="task", topic="Do it", attrs={"id": "t1"}), auto_id=False)
        r.add_node("/*", NodeSpec(tag="project", topic="Beta", attrs={"id": "p2"}), auto_id=False)
        yield r


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

def test_move_by_xpath(repo):
    """Move a node using full XPath selectors."""
    result = repo.move_node("//task[@id='t1']", "//project[@id='p2']")
    assert result.success
    # task is now under p2
    p2 = repo.root.find(".//project[@id='p2']")
    assert p2.find("task[@id='t1']") is not None
    # task is gone from p1
    p1 = repo.root.find(".//project[@id='p1']")
    assert p1.find("task") is None


def test_move_by_id(repo):
    """Move a node using bare ID strings."""
    result = repo.move_node("t1", "p2")
    assert result.success
    p2 = repo.root.find(".//project[@id='p2']")
    assert p2.find("task[@id='t1']") is not None


def test_subtree_moves_with_node(repo):
    """Child nodes travel with their parent."""
    # Add a grandchild under t1
    repo.add_node("//task[@id='t1']", NodeSpec(tag="note", topic="detail", attrs={"id": "n1"}), auto_id=False)

    result = repo.move_node("t1", "p2")
    assert result.success

    p2 = repo.root.find(".//project[@id='p2']")
    task = p2.find("task[@id='t1']")
    assert task is not None
    assert task.find("note[@id='n1']") is not None  # grandchild came along


def test_sidecar_updated_after_move(repo):
    """Sidecar XPaths are refreshed for moved node and its descendants."""
    repo.add_node("//task[@id='t1']", NodeSpec(tag="note", topic="x", attrs={"id": "n1"}), auto_id=False)
    repo.move_node("t1", "p2")

    # Sidecar entries must reflect new positions
    t1_xpath = repo.id_sidecar.get("t1")
    assert "p2" in t1_xpath, f"Expected p2 in xpath, got: {t1_xpath}"

    n1_xpath = repo.id_sidecar.get("n1")
    assert "p2" in n1_xpath, f"Expected p2 in xpath, got: {n1_xpath}"


# ---------------------------------------------------------------------------
# Error / guard tests
# ---------------------------------------------------------------------------

def test_move_source_not_found(repo):
    result = repo.move_node("//task[@id='NOPE']", "//project[@id='p2']")
    assert not result.success
    assert "not found" in result.message.lower()


def test_move_dest_not_found(repo):
    result = repo.move_node("//task[@id='t1']", "//project[@id='NOPE']")
    assert not result.success
    assert "not found" in result.message.lower()


def test_move_src_is_dest(repo):
    result = repo.move_node("//project[@id='p1']", "//project[@id='p1']")
    assert not result.success
    assert "same node" in result.message.lower()


def test_move_dest_is_descendant_of_src(repo):
    """Moving a node into its own subtree must be rejected."""
    result = repo.move_node("//project[@id='p1']", "//task[@id='t1']")
    assert not result.success
    assert "descendant" in result.message.lower()


def test_move_no_file_loaded():
    r = ManifestRepository()
    result = r.move_node("//a", "//b")
    assert not result.success
    assert "no file" in result.message.lower()


def test_move_tree_unchanged_on_error(repo):
    """Failed move must not mutate the tree (transaction rollback)."""
    from lxml import etree
    before = etree.tostring(repo.root)
    repo.move_node("//project[@id='p1']", "//task[@id='t1']")  # cycle — must fail
    after = etree.tostring(repo.root)
    assert before == after
