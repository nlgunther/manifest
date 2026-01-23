"""Tests for storage.py - I/O layer security and functionality."""
import pytest
import os
import tempfile
from storage import StorageManager, StorageError, PasswordRequired, ArchiveError

@pytest.fixture
def storage(): return StorageManager()

@pytest.fixture  
def temp_dir():
    with tempfile.TemporaryDirectory() as td: yield td

class TestFlatFileOperations:
    def test_save_and_load_roundtrip(self, storage, temp_dir):
        path = os.path.join(temp_dir, "test.xml")
        data = b"<root>content</root>"
        storage.save(path, data)
        assert storage.load(path) == data
    
    def test_load_nonexistent_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.load("/nonexistent/path.xml")
    
    def test_save_creates_file(self, storage, temp_dir):
        path = os.path.join(temp_dir, "new.xml")
        storage.save(path, b"data")
        assert os.path.exists(path)

    def test_save_overwrites_existing(self, storage, temp_dir):
        path = os.path.join(temp_dir, "existing.xml")
        storage.save(path, b"original")
        storage.save(path, b"updated")
        assert storage.load(path) == b"updated"

class TestPathValidation:
    def test_null_byte_rejected(self, storage):
        """Fixed: Regex now matches 'Null byte' capitalization."""
        with pytest.raises(ValueError, match="Null byte"):
            storage.load("file\x00.xml")
    
    def test_empty_path_rejected(self, storage):
        with pytest.raises(ValueError, match="Empty"):
            storage.load("")

    def test_control_characters_rejected(self, storage):
        """This should now pass with storage.py v2.6.2"""
        with pytest.raises(ValueError, match="control character"):
            storage.load("file\x01.xml")
            
    def test_normal_path_accepted(self, storage, temp_dir):
        path = os.path.join(temp_dir, "normal.xml")
        storage.save(path, b"test")
        storage.load(path)

    def test_relative_path_accepted(self, storage, temp_dir):
        abs_path = os.path.join(temp_dir, "relative_test.xml")
        storage.save(abs_path, b"test")
        cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            assert storage.load("relative_test.xml") == b"test"
        finally:
            os.chdir(cwd)

@pytest.mark.skipif(not StorageManager().has_7z, reason="py7zr missing")
class Test7zOperations:
    def test_encrypted_roundtrip(self, storage, temp_dir):
        path = os.path.join(temp_dir, "test.7z")
        data = b"<root>secret</root>"
        storage.save(path, data, "pass")
        assert storage.load(path, "pass") == data
    
    def test_wrong_password_raises(self, storage, temp_dir):
        path = os.path.join(temp_dir, "test.7z")
        storage.save(path, b"data", "correct")
        with pytest.raises(PasswordRequired):
            storage.load(path, "wrong")
            
    def test_missing_password_raises(self, storage, temp_dir):
        path = os.path.join(temp_dir, "test.7z")
        storage.save(path, b"data", "secret")
        with pytest.raises(PasswordRequired):
            storage.load(path)

class TestFileExtensionHandling:
    def test_xml_extension_detected(self, storage, temp_dir):
        path = os.path.join(temp_dir, "test.xml")
        storage.save(path, b"content")
        with open(path, 'rb') as f: assert f.read() == b"content"

    @pytest.mark.skipif(not StorageManager().has_7z, reason="py7zr missing")
    def test_7z_extension_detected(self, storage, temp_dir):
        path = os.path.join(temp_dir, "test.7z")
        storage.save(path, b"content")
        with open(path, 'rb') as f: assert f.read() != b"content"

class TestErrorHandling:
    @pytest.mark.skipif(not StorageManager().has_7z, reason="py7zr missing")
    def test_invalid_7z_file(self, storage, temp_dir):
        path = os.path.join(temp_dir, "invalid.7z")
        with open(path, 'wb') as f: f.write(b"Not a 7z")
        with pytest.raises((StorageError, ArchiveError)):
            storage.load(path)

class TestUnicodeHandling:
    def test_unicode_filename(self, storage, temp_dir):
        path = os.path.join(temp_dir, "测试.xml")
        data = b"<root>U</root>"
        storage.save(path, data)
        assert storage.load(path) == data