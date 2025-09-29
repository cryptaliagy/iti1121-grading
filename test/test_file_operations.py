"""Test cases for file operations utilities."""

import stat
from pathlib import Path
from unittest.mock import Mock, patch
from tempfile import TemporaryDirectory

import pytest

from grader.file_operations import (
    FileHandler,
)
from grader.common import FileOperationError
from grader.writer import Writer


class TestSafeCopyFile:
    """Test cases for safe_copy_file function."""

    def test_safe_copy_file_success(self):
        """Test successful file copy."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.txt"
            target = Path(temp_dir) / "target.txt"

            source.write_text("test content")

            handler.safe_copy_file(source, target)

            assert target.exists()
            assert target.read_text() == "test content"
            mock_writer.echo.assert_called()

    def test_safe_copy_file_overwrites_existing(self):
        """Test file copy overwrites existing target."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.txt"
            target = Path(temp_dir) / "target.txt"

            source.write_text("new content")
            target.write_text("old content")

            handler.safe_copy_file(source, target)

            assert target.read_text() == "new content"

    def test_safe_copy_file_nonexistent_source(self):
        """Test file copy with nonexistent source."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "nonexistent.txt"
            target = Path(temp_dir) / "target.txt"

            with pytest.raises(FileOperationError):
                handler.safe_copy_file(source, target)

    @patch("shutil.copy2")
    def test_safe_copy_file_permission_error(self, mock_copy2):
        """Test file copy with permission error."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)
        mock_copy2.side_effect = PermissionError("Permission denied")

        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.txt"
            target = Path(temp_dir) / "target.txt"

            source.write_text("test content")

            with pytest.raises(FileOperationError) as exc_info:
                handler.safe_copy_file(source, target)

            assert "Permission denied" in str(exc_info.value)


class TestAddWritePermission:
    """Test cases for add_write_permission function."""

    def test_add_write_permission_success(self):
        """Test successful addition of write permission."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            # Remove write permission
            current_mode = test_file.stat().st_mode
            test_file.chmod(current_mode & ~stat.S_IWUSR)

            result = handler.add_write_permission(test_file)

            assert result is True
            assert test_file.stat().st_mode & stat.S_IWUSR
            mock_writer.echo.assert_called()

    def test_add_write_permission_already_writable(self):
        """Test adding write permission to already writable file."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            result = handler.add_write_permission(test_file)

            assert result is True
            mock_writer.echo.assert_called()

    @patch("os.chmod")
    def test_add_write_permission_failure(self, mock_chmod):
        """Test failure to add write permission."""
        mock_writer = Mock(spec=Writer)
        mock_chmod.side_effect = OSError("Permission denied")
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            result = handler.add_write_permission(test_file)

            assert result is False
            mock_writer.always_echo.assert_called()


class TestSafeDeleteFile:
    """Test cases for safe_delete_file function."""

    def test_safe_delete_file_success(self):
        """Test successful file deletion."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            result = handler.safe_delete_file(test_file)

            assert result is True
            assert not test_file.exists()
            mock_writer.echo.assert_called()

    def test_safe_delete_file_nonexistent(self):
        """Test deletion of nonexistent file."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "nonexistent.txt"

            result = handler.safe_delete_file(test_file)

            assert result is True

    def test_safe_delete_file_permission_error_then_success(self):
        """Test deletion with permission error that gets resolved."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            # Remove write permission
            current_mode = test_file.stat().st_mode
            test_file.chmod(current_mode & ~stat.S_IWUSR)

            result = handler.safe_delete_file(test_file)

            assert result is True
            assert not test_file.exists()

    @patch("os.chmod")
    @patch("pathlib.Path.unlink")
    def test_safe_delete_file_permission_error_cant_fix(
        self,
        mock_unlink,
        mock_chmod,
    ):
        """Test deletion with permission error that can't be fixed."""
        mock_writer = Mock(spec=Writer)
        mock_unlink.side_effect = PermissionError("Permission denied")
        mock_chmod.side_effect = OSError("Cannot change permissions")
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            with pytest.raises(FileOperationError):
                handler.safe_delete_file(test_file)


class TestEnsureDirectoryWritable:
    """Test cases for ensure_directory_writable function."""

    def test_ensure_directory_writable_success(self):
        """Test ensuring directory is writable."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_dir"
            test_dir.mkdir()

            handler.ensure_directory_writable(test_dir)

            # Should not raise exception

    def test_ensure_directory_writable_nonexistent(self):
        """Test ensuring nonexistent directory is writable."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "nonexistent"

            with pytest.raises(FileOperationError):
                handler.ensure_directory_writable(test_dir)

    def test_ensure_directory_writable_not_directory(self):
        """Test ensuring file (not directory) is writable."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")

            with pytest.raises(FileOperationError):
                handler.ensure_directory_writable(test_file)


class TestCopyTestFiles:
    """Test cases for copy_test_files function."""

    def test_copy_test_files_success(self):
        """Test successful copying of test files."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            target_dir = Path(temp_dir) / "target"
            source_dir.mkdir()
            target_dir.mkdir()

            # Create test files
            test_file1 = source_dir / "Test1.java"
            test_file2 = source_dir / "Test2.java"
            test_file1.write_text("test content 1")
            test_file2.write_text("test content 2")

            test_files = [test_file1, test_file2]

            handler.copy_test_files(test_files, target_dir)

            assert (target_dir / "Test1.java").exists()
            assert (target_dir / "Test2.java").exists()
            assert (target_dir / "Test1.java").read_text() == "test content 1"
            assert (target_dir / "Test2.java").read_text() == "test content 2"

    def test_copy_test_files_with_utils(self):
        """Test copying test files with TestUtils.java."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            target_dir = Path(temp_dir) / "target"
            source_dir.mkdir()
            target_dir.mkdir()

            # Create test files
            test_file = source_dir / "Test1.java"
            utils_file = source_dir / "TestUtils.java"
            test_file.write_text("test content")
            utils_file.write_text("utils content")

            test_files = [test_file]

            handler.copy_test_files(test_files, target_dir)

            assert (target_dir / "Test1.java").exists()
            assert (target_dir / "TestUtils.java").exists()
            assert (target_dir / "TestUtils.java").read_text() == "utils content"

    def test_copy_test_files_no_utils(self):
        """Test copying test files without TestUtils.java."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            target_dir = Path(temp_dir) / "target"
            source_dir.mkdir()
            target_dir.mkdir()

            # Create test files
            test_file = source_dir / "Test1.java"
            test_file.write_text("test content")

            test_files = [test_file]

            handler.copy_test_files(test_files, target_dir)

            assert (target_dir / "Test1.java").exists()
            assert not (target_dir / "TestUtils.java").exists()


class TestFindTestFiles:
    """Test cases for find_test_files function."""

    def test_find_test_files_success(self):
        """Test successful finding of test files."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "tests"
            test_dir.mkdir()

            # Create test files
            main_test = test_dir / "TestL1.java"
            other_test = test_dir / "TestL1Helper.java"
            main_test.write_text("main test")
            other_test.write_text("helper test")

            test_files = handler.find_test_files(test_dir, "TestL1")

            assert len(test_files) == 2
            assert main_test in test_files
            assert other_test in test_files

    def test_find_test_files_nonexistent_directory(self):
        """Test finding test files in nonexistent directory."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            nonexistent_dir = Path(temp_dir) / "nonexistent"

            with pytest.raises(FileOperationError):
                handler.find_test_files(nonexistent_dir, "TestL1")

    def test_find_test_files_no_matches(self):
        """Test finding test files with no matching files."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "tests"
            test_dir.mkdir()

            # Create non-matching file
            other_file = test_dir / "SomeOtherTest.java"
            other_file.write_text("other test")

            with pytest.raises(FileOperationError):
                handler.find_test_files(test_dir, "TestL1")

    def test_find_test_files_no_main_test(self):
        """Test finding test files without main test file."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "tests"
            test_dir.mkdir()

            # Create helper test but not main test
            helper_test = test_dir / "TestL1Helper.java"
            helper_test.write_text("helper test")

            with pytest.raises(FileOperationError):
                handler.find_test_files(test_dir, "TestL1")

    def test_find_test_files_directory_as_file(self):
        """Test finding test files when directory is actually a file."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "tests"
            test_file.write_text("this is a file, not a directory")

            with pytest.raises(FileOperationError):
                handler.find_test_files(test_file, "TestL1")


class TestFileHandler:
    """Test cases for FileHandler class."""

    def test_file_handler_initialization(self):
        """Test FileHandler initialization."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        assert handler.writer == mock_writer

    def test_file_handler_safe_copy_file(self):
        """Test FileHandler safe_copy_file method."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.txt"
            target = Path(temp_dir) / "target.txt"

            source.write_text("test content")

            handler.safe_copy_file(source, target)

            assert target.exists()
            assert target.read_text() == "test content"
            mock_writer.echo.assert_called()

    def test_file_handler_find_test_files(self):
        """Test FileHandler find_test_files method."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)

            # Create test files
            (test_dir / "Test1.java").write_text("test1")
            (test_dir / "Test1Extra.java").write_text("test1extra")
            (test_dir / "Test2.java").write_text("test2")

            test_files = handler.find_test_files(test_dir, "Test1")

            assert len(test_files) == 2
            file_names = [f.name for f in test_files]
            assert "Test1.java" in file_names
            assert "Test1Extra.java" in file_names
            assert "Test2.java" not in file_names

    def test_file_handler_copy_test_files(self):
        """Test FileHandler copy_test_files method."""
        mock_writer = Mock(spec=Writer)
        handler = FileHandler(mock_writer)

        with TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            target_dir = Path(temp_dir) / "target"

            source_dir.mkdir()
            target_dir.mkdir()

            # Create test files
            test_file1 = source_dir / "Test1.java"
            test_file2 = source_dir / "Test1Extra.java"
            test_file1.write_text("test1")
            test_file2.write_text("test1extra")

            test_files = [test_file1, test_file2]

            handler.copy_test_files(test_files, target_dir)

            assert (target_dir / "Test1.java").exists()
            assert (target_dir / "Test1Extra.java").exists()
            assert (target_dir / "Test1.java").read_text() == "test1"
            assert (target_dir / "Test1Extra.java").read_text() == "test1extra"
