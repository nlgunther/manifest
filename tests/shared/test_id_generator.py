"""
Tests for shared.id_generator module.
"""
import pytest
from shared.id_generator import (
    generate_id,
    validate_id,
    extract_prefix,
    shorten_id
)


def test_generate_id_default():
    """Test default ID generation."""
    id1 = generate_id()
    assert len(id1) == 8
    assert all(c in '0123456789abcdef' for c in id1.lower())


def test_generate_id_with_prefix():
    """Test ID generation with prefix."""
    task_id = generate_id(prefix="t", length=5)
    assert task_id.startswith("t")
    assert len(task_id) == 6


def test_validate_id():
    """Test ID validation."""
    assert validate_id("a3f7b2c1") == True
    assert validate_id("t12345", prefix="t") == True
    assert validate_id("xyz") == False


def test_extract_prefix():
    """Test prefix extraction."""
    assert extract_prefix("t12345") == ("t", "12345")
    assert extract_prefix("a3f7b2c1") == ("", "a3f7b2c1")


def test_shorten_id():
    """Test ID shortening."""
    assert shorten_id("a3f7b2c1", 4) == "a3f7"
