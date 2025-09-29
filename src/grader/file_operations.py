"""File operation utilities for the grading system."""

import os
import shutil
from pathlib import Path

from .common import FileOperationError
from .writer import Writer


class FileHandler:
    """Handler class for file operations in the grading system."""

    def __init__(self, writer: Writer):
        """
        Initialize the FileHandler with a writer.

        Args:
            writer: Writer object for console output
        """
        self.writer = writer

    def safe_copy_file(self, source: Path, target: Path) -> None:
        """
        Safely copy a file, ensuring the target is writable.

        Args:
            source: Source file path
            target: Target file path

        Raises:
            FileOperationError: If file copy fails
        """
        # Delete existing file if it exists
        if target.exists():
            self.safe_delete_file(target)

        # Copy the file
        self.writer.echo(f"Copying {source} to {target}")
        try:
            shutil.copy2(source, target)
        except PermissionError:
            raise FileOperationError(f"Permission denied when copying to {target}")
        except Exception as e:
            raise FileOperationError(f"Failed to copy {source} to {target}: {e}")

    def add_write_permission(self, path: Path) -> bool:
        """
        Add write permission to a file or directory.

        Args:
            path: Path to add write permission to

        Returns:
            True if permission was successfully added, False otherwise
        """
        self.writer.echo(f"Adding write permissions to: {path}")
        try:
            current_mode = path.stat().st_mode
            new_mode = current_mode | 0o200  # Add user write permission
            os.chmod(path, new_mode)
            self.writer.echo(f"Successfully added write permissions to {path}")
            return True
        except Exception as e:
            self.writer.always_echo(
                f"[red]Warning:[/red] Failed to add write permissions: {e}"
            )
            return False

    def safe_delete_file(self, file_path: Path) -> bool:
        """
        Safely delete a file, attempting to add write permissions if needed.

        Args:
            file_path: Path to the file to delete

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            FileOperationError: If file deletion fails after attempts to fix permissions
        """
        if not file_path.exists():
            return True

        self.writer.echo(f"Removing existing file: {file_path}")
        try:
            file_path.unlink()
            return True
        except PermissionError:
            self.writer.echo(
                f"Insufficient permissions to remove {file_path}, trying to add write permissions"
            )
            if self.add_write_permission(file_path):
                try:
                    file_path.unlink()
                    return True
                except Exception:
                    # Ignore the exception to trigger our own
                    pass  # nosec: B110

        # If we get here, all attempts failed
        raise FileOperationError(f"Could not remove existing file {file_path}")

    def ensure_directory_writable(self, directory: Path) -> None:
        """
        Ensure a directory exists and is writable, adding permissions if necessary.

        Args:
            directory: Directory path to check

        Raises:
            FileOperationError: If directory does not exist or cannot be made writable
        """
        if not directory.exists() or not directory.is_dir():
            raise FileOperationError(
                f"Directory {directory} does not exist or is not a directory."
            )

        # Check write permissions on directory
        if not os.access(directory, os.W_OK):
            if not self.add_write_permission(directory):
                self.writer.always_echo(
                    "Attempting to continue with operations despite permission issues..."
                )

    def copy_test_files(self, test_files: list[Path], target_dir: Path) -> None:
        """
        Copy test files to the target directory, deleting existing ones if necessary.
        Adds write permissions to the target directory if needed.

        Args:
            test_files: List of test files to copy
            target_dir: Directory to copy files to

        Raises:
            FileOperationError: If file operations fail
        """
        # Ensure target directory is writable
        self.ensure_directory_writable(target_dir)

        # Copy all test files
        for test_file in test_files:
            target_file = target_dir / test_file.name
            self.safe_copy_file(test_file, target_file)

        # Also copy TestUtils.java if it exists in the test directory
        test_dir = test_files[0].parent
        utils_file = test_dir / "TestUtils.java"
        if utils_file.exists():
            target_utils_file = target_dir / "TestUtils.java"
            self.safe_copy_file(utils_file, target_utils_file)

    def find_test_files(self, test_dir: Path, prefix: str) -> list[Path]:
        """
        Find all Java test files matching the given prefix in the specified directory.

        Args:
            test_dir: Directory where test files are located
            prefix: Prefix of test files to search for

        Returns:
            List of Path objects for test files that match the criteria

        Raises:
            FileOperationError: If no test files are found or the directory doesn't exist
        """
        if not test_dir.exists() or not test_dir.is_dir():
            raise FileOperationError(
                f"Test directory {test_dir} does not exist or is not a directory."
            )

        test_files = list(test_dir.glob(f"{prefix}*.java"))

        if not test_files:
            raise FileOperationError(
                f"No test files found with prefix '{prefix}' in {test_dir}"
            )

        main_test_file = test_dir / f"{prefix}.java"

        if not main_test_file.exists():
            raise FileOperationError(
                f"Main test file {main_test_file} does not exist.\n"
                f"Found test files: {[f.name for f in test_files]}"
            )

        return test_files
