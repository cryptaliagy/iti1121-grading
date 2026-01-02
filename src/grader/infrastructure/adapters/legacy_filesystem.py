"""Legacy adapter for file system operations."""

from pathlib import Path

from grader._grader import (
    Writer,
    add_write_permission,
    ensure_directory_writable,
    safe_copy_file,
    safe_delete_file,
)


class LegacyFileSystemAdapter:
    """
    Adapter that wraps existing file system operations.

    This adapter implements the FileSystem protocol while maintaining
    backward compatibility with the existing implementation.
    """

    def __init__(self, writer: Writer):
        """
        Initialize the adapter.

        Args:
            writer: Writer instance for console output
        """
        self.writer = writer

    def read_file(self, path: Path) -> str:
        """
        Read a file and return its contents.

        Args:
            path: Path to the file to read

        Returns:
            File contents as a string
        """
        return path.read_text()

    def write_file(self, path: Path, content: str) -> None:
        """
        Write content to a file.

        Args:
            path: Path to the file to write
            content: Content to write to the file
        """
        path.write_text(content)

    def copy_file(self, source: Path, target: Path) -> None:
        """
        Copy a file from source to target.

        Args:
            source: Source file path
            target: Target file path
        """
        safe_copy_file(source, target, self.writer)

    def delete_file(self, path: Path) -> bool:
        """
        Delete a file.

        Args:
            path: Path to the file to delete

        Returns:
            True if successful, False otherwise
        """
        return safe_delete_file(path, self.writer)

    def list_files(self, directory: Path, pattern: str = "*") -> list[Path]:
        """
        List files in a directory matching a pattern.

        Args:
            directory: Directory to search
            pattern: Glob pattern to match

        Returns:
            List of matching file paths
        """
        return list(directory.glob(pattern))

    def ensure_directory(self, path: Path) -> None:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            path: Path to the directory
        """
        path.mkdir(parents=True, exist_ok=True)

    def make_writable(self, path: Path) -> None:
        """
        Make a file or directory writable.

        Args:
            path: Path to make writable
        """
        if path.is_dir():
            ensure_directory_writable(path, self.writer)
        else:
            add_write_permission(path, self.writer)
