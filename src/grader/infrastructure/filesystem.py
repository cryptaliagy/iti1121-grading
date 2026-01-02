"""File system implementations for the grading infrastructure."""

import shutil
import stat
from pathlib import Path
from typing import Iterator


class LocalFileSystem:
    """Local file system implementation."""

    def read_file(self, path: Path) -> str:
        """
        Read a file and return its contents.

        Args:
            path: Path to the file to read

        Returns:
            File contents as a string

        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file can't be read
        """
        with path.open("r", encoding="utf-8") as f:
            return f.read()

    def write_file(self, path: Path, content: str) -> None:
        """
        Write content to a file.

        Args:
            path: Path to the file to write
            content: Content to write to the file

        Raises:
            PermissionError: If the file can't be written
        """
        with path.open("w", encoding="utf-8") as f:
            f.write(content)

    def copy_file(self, source: Path, target: Path) -> None:
        """
        Copy a file from source to target.

        Args:
            source: Source file path
            target: Target file path

        Raises:
            FileNotFoundError: If source doesn't exist
            PermissionError: If files can't be accessed
        """
        shutil.copy2(source, target)

    def delete_file(self, path: Path) -> bool:
        """
        Delete a file.

        Args:
            path: Path to the file to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            path.unlink()
            return True
        except (FileNotFoundError, PermissionError, OSError):
            return False

    def list_files(self, directory: Path, pattern: str = "*") -> list[Path]:
        """
        List files in a directory matching a pattern.

        Args:
            directory: Directory to search
            pattern: Glob pattern to match

        Returns:
            List of matching file paths

        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        if not directory.exists():
            raise FileNotFoundError(f"Directory {directory} does not exist")
        
        return sorted(directory.glob(pattern))

    def ensure_directory(self, path: Path) -> None:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            path: Path to the directory

        Raises:
            PermissionError: If directory can't be created
        """
        path.mkdir(parents=True, exist_ok=True)

    def make_writable(self, path: Path) -> None:
        """
        Make a file or directory writable.

        Args:
            path: Path to make writable

        Raises:
            FileNotFoundError: If path doesn't exist
            PermissionError: If permissions can't be changed
        """
        if not path.exists():
            raise FileNotFoundError(f"Path {path} does not exist")
        
        # Add write permissions for the owner
        current_mode = path.stat().st_mode
        path.chmod(current_mode | stat.S_IWUSR)


class InMemoryFileSystem:
    """In-memory file system for testing."""

    def __init__(self) -> None:
        """Initialize the in-memory file system."""
        self._files: dict[Path, str] = {}
        self._directories: set[Path] = set()

    def read_file(self, path: Path) -> str:
        """
        Read a file and return its contents.

        Args:
            path: Path to the file to read

        Returns:
            File contents as a string

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        if path not in self._files:
            raise FileNotFoundError(f"File {path} does not exist")
        return self._files[path]

    def write_file(self, path: Path, content: str) -> None:
        """
        Write content to a file.

        Args:
            path: Path to the file to write
            content: Content to write to the file
        """
        # Ensure parent directory exists
        if path.parent != Path("."):
            self._directories.add(path.parent)
        self._files[path] = content

    def copy_file(self, source: Path, target: Path) -> None:
        """
        Copy a file from source to target.

        Args:
            source: Source file path
            target: Target file path

        Raises:
            FileNotFoundError: If source doesn't exist
        """
        if source not in self._files:
            raise FileNotFoundError(f"File {source} does not exist")
        self._files[target] = self._files[source]

    def delete_file(self, path: Path) -> bool:
        """
        Delete a file.

        Args:
            path: Path to the file to delete

        Returns:
            True if successful, False otherwise
        """
        if path in self._files:
            del self._files[path]
            return True
        return False

    def list_files(self, directory: Path, pattern: str = "*") -> list[Path]:
        """
        List files in a directory matching a pattern.

        Args:
            directory: Directory to search
            pattern: Glob pattern to match

        Returns:
            List of matching file paths

        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        if directory != Path(".") and directory not in self._directories:
            # Allow root directory to always exist
            if directory != Path("/") and directory != Path():
                raise FileNotFoundError(f"Directory {directory} does not exist")
        
        # Simple pattern matching - just support "*" and "*.ext" for now
        results = []
        for file_path in self._files.keys():
            # Check if file is in the specified directory by comparing parent
            if file_path.parent == directory or directory == Path("."):
                # Simple pattern matching
                if pattern == "*":
                    results.append(file_path)
                elif pattern.startswith("*."):
                    ext = pattern[1:]  # Get extension including dot
                    if str(file_path).endswith(ext):
                        results.append(file_path)
                elif file_path.name == pattern:
                    results.append(file_path)
        
        return sorted(results)

    def ensure_directory(self, path: Path) -> None:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            path: Path to the directory
        """
        self._directories.add(path)
        # Also add all parent directories
        parent = path.parent
        while parent != path and parent != Path(".") and parent != Path("/"):
            self._directories.add(parent)
            parent = parent.parent

    def make_writable(self, path: Path) -> None:
        """
        Make a file or directory writable.

        Args:
            path: Path to make writable

        Raises:
            FileNotFoundError: If path doesn't exist
        """
        if path not in self._files and path not in self._directories:
            raise FileNotFoundError(f"Path {path} does not exist")
        # In-memory filesystem doesn't track permissions, so this is a no-op
