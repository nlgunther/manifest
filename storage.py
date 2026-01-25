"""
Storage Layer for Manifest Manager
==================================
Handles file I/O for plain XML files and encrypted 7z archives.
"""
import os
import tempfile
from typing import Optional

class StorageError(Exception): """Base class for storage errors."""
class PasswordRequired(StorageError): """Raised when a file requires a password."""
class ArchiveError(StorageError): """Raised for multi-file or empty archives."""

class StorageManager:
    def __init__(self):
        try:
            import py7zr
            self.has_7z = True
        except ImportError:
            self.has_7z = False

    @staticmethod
    def _validate_path(filepath: str) -> str:
        """Validate file path for security.
        
        Args:
            filepath: Path to validate
            
        Returns:
            Normalized path
            
        Raises:
            ValueError: If path contains dangerous patterns
        """
        if not filepath or not filepath.strip(): 
            raise ValueError("Empty file path")
        if '\x00' in filepath: 
            raise ValueError("null byte in path")
        if any(ord(c) < 32 for c in filepath if c not in '\t\n'):
            raise ValueError("invalid control characters in path")
        return os.path.normpath(filepath)

    def load(self, filepath: str, password: Optional[str] = None) -> bytes:
        """Load file contents. Supports plain XML and encrypted .7z archives.
        
        Args:
            filepath: Path to file (absolute or relative)
            password: Optional password for encrypted archives
            
        Returns:
            Raw file contents as bytes
            
        Raises:
            FileNotFoundError: File doesn't exist
            PasswordRequired: Encrypted file needs password
            StorageError: I/O or decompression error
        """
        filepath = self._validate_path(filepath)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        if filepath.lower().endswith(".7z"):
            return self._load_7z(filepath, password)
        return self._load_flat(filepath)

    def save(self, filepath: str, data: bytes, password: Optional[str] = None) -> None:
        """Write file contents. Supports plain XML and encrypted .7z archives.
        
        Args:
            filepath: Path to file (absolute or relative)
            data: Raw bytes to write
            password: Optional password for .7z encryption
            
        Raises:
            StorageError: Write failure
        """
        filepath = self._validate_path(filepath)
        if filepath.lower().endswith(".7z"):
            self._save_7z(filepath, data, password)
        else:
            self._save_flat(filepath, data)

    def _load_flat(self, path: str) -> bytes:
        try:
            with open(path, 'rb') as f: return f.read()
        except Exception as e: raise StorageError(f"IO Error: {e}")

    def _save_flat(self, path: str, data: bytes) -> None:
        try:
            with open(path, 'wb') as f: f.write(data)
        except Exception as e: raise StorageError(f"Write failed: {e}")

    def _load_7z(self, path: str, password: Optional[str]) -> bytes:
        if not self.has_7z: raise StorageError("py7zr missing. Run: pip install py7zr")
        import py7zr
        import lzma # Import lzma to catch the specific error if it bubbles up natively
        
        try:
            with py7zr.SevenZipFile(path, mode='r', password=password) as archive:
                if not archive.getnames(): raise ArchiveError("Empty archive")
                if len(archive.getnames()) > 1: raise ArchiveError("Archive contains multiple files.")
                target_file = archive.getnames()[0]
                
                with tempfile.TemporaryDirectory() as tmp:
                    archive.extractall(path=tmp)
                    extracted_path = os.path.join(tmp, target_file)
                    with open(extracted_path, 'rb') as f:
                        return f.read()

        except py7zr.exceptions.PasswordRequired: 
            raise PasswordRequired("Encrypted file.")
        except (lzma.LZMAError, py7zr.exceptions.Bad7zFile):
            # This catches "Corrupt input data" which often means wrong password
            raise PasswordRequired("Invalid password (or corrupt file).")
        except Exception as e:
            # Fallback for generic exceptions with specific messages
            msg = str(e).lower()
            if "password" in msg or "corrupt input data" in msg: 
                raise PasswordRequired("Invalid password.")
            raise StorageError(f"7-Zip Error: {e}")

    def _save_7z(self, path: str, data: bytes, password: Optional[str]) -> None:
        if not self.has_7z: raise StorageError("py7zr missing.")
        import py7zr
        
        internal_name = "data.xml"
        if os.path.exists(path):
            try:
                with py7zr.SevenZipFile(path, mode='r', password=password) as z:
                    if z.getnames(): internal_name = z.getnames()[0]
            except (FileNotFoundError, PermissionError, Exception):
                pass  # Use default name on read failure

        try:
            with py7zr.SevenZipFile(path, 'w', password=password) as z:
                z.writestr(data, internal_name)
        except Exception as e: raise StorageError(f"7z Write Error: {e}")