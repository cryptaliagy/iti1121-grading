"""Unit tests for file system implementations."""

import pytest
import tempfile
from pathlib import Path

from grader.infrastructure.filesystem import LocalFileSystem, InMemoryFileSystem


class TestLocalFileSystem:
    """Test the LocalFileSystem implementation."""

    def test_read_write_file(self):
        """Test reading and writing files."""
        fs = LocalFileSystem()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            content = "Hello, World!"

            fs.write_file(test_file, content)
            assert test_file.exists()

            read_content = fs.read_file(test_file)
            assert read_content == content

    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        fs = LocalFileSystem()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "nonexistent.txt"

            with pytest.raises(FileNotFoundError):
                fs.read_file(test_file)

    def test_copy_file(self):
        """Test copying files."""
        fs = LocalFileSystem()
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source.txt"
            target = Path(tmpdir) / "target.txt"
            content = "Test content"

            fs.write_file(source, content)
            fs.copy_file(source, target)

            assert target.exists()
            assert fs.read_file(target) == content

    def test_copy_nonexistent_file(self):
        """Test copying a file that doesn't exist."""
        fs = LocalFileSystem()
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "nonexistent.txt"
            target = Path(tmpdir) / "target.txt"

            with pytest.raises(FileNotFoundError):
                fs.copy_file(source, target)

    def test_delete_file(self):
        """Test deleting files."""
        fs = LocalFileSystem()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"

            fs.write_file(test_file, "content")
            assert test_file.exists()

            result = fs.delete_file(test_file)
            assert result is True
            assert not test_file.exists()

    def test_delete_nonexistent_file(self):
        """Test deleting a file that doesn't exist."""
        fs = LocalFileSystem()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "nonexistent.txt"

            result = fs.delete_file(test_file)
            assert result is False

    def test_list_files(self):
        """Test listing files in a directory."""
        fs = LocalFileSystem()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            fs.write_file(tmppath / "file1.txt", "content1")
            fs.write_file(tmppath / "file2.txt", "content2")
            fs.write_file(tmppath / "file3.java", "content3")

            all_files = fs.list_files(tmppath, "*")
            assert len(all_files) == 3

            txt_files = fs.list_files(tmppath, "*.txt")
            assert len(txt_files) == 2
            assert all(str(f).endswith(".txt") for f in txt_files)

    def test_list_files_nonexistent_directory(self):
        """Test listing files in a directory that doesn't exist."""
        fs = LocalFileSystem()
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / "nonexistent"

            with pytest.raises(FileNotFoundError):
                fs.list_files(nonexistent)

    def test_ensure_directory(self):
        """Test ensuring a directory exists."""
        fs = LocalFileSystem()
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new" / "nested" / "directory"

            fs.ensure_directory(new_dir)
            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_make_writable(self):
        """Test making a file writable."""
        fs = LocalFileSystem()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"

            fs.write_file(test_file, "content")
            test_file.chmod(0o444)  # Make read-only

            fs.make_writable(test_file)

            # Should be able to write now
            fs.write_file(test_file, "new content")
            assert fs.read_file(test_file) == "new content"

    def test_make_writable_nonexistent_file(self):
        """Test making a nonexistent file writable."""
        fs = LocalFileSystem()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "nonexistent.txt"

            with pytest.raises(FileNotFoundError):
                fs.make_writable(test_file)


class TestInMemoryFileSystem:
    """Test the InMemoryFileSystem implementation."""

    def test_read_write_file(self):
        """Test reading and writing files."""
        fs = InMemoryFileSystem()
        path = Path("/test.txt")
        content = "Hello, World!"

        fs.write_file(path, content)
        assert fs.read_file(path) == content

    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        fs = InMemoryFileSystem()

        with pytest.raises(FileNotFoundError):
            fs.read_file(Path("/nonexistent.txt"))

    def test_copy_file(self):
        """Test copying files."""
        fs = InMemoryFileSystem()
        source = Path("/source.txt")
        target = Path("/target.txt")
        content = "Test content"

        fs.write_file(source, content)
        fs.copy_file(source, target)

        assert fs.read_file(target) == content

    def test_copy_nonexistent_file(self):
        """Test copying a file that doesn't exist."""
        fs = InMemoryFileSystem()

        with pytest.raises(FileNotFoundError):
            fs.copy_file(Path("/nonexistent.txt"), Path("/target.txt"))

    def test_delete_file(self):
        """Test deleting files."""
        fs = InMemoryFileSystem()
        path = Path("/test.txt")

        fs.write_file(path, "content")
        assert fs.delete_file(path) is True

        with pytest.raises(FileNotFoundError):
            fs.read_file(path)

    def test_delete_nonexistent_file(self):
        """Test deleting a file that doesn't exist."""
        fs = InMemoryFileSystem()

        assert fs.delete_file(Path("/nonexistent.txt")) is False

    def test_list_files(self):
        """Test listing files in a directory."""
        fs = InMemoryFileSystem()
        base = Path("/testdir")

        fs.ensure_directory(base)
        fs.write_file(base / "file1.txt", "content1")
        fs.write_file(base / "file2.txt", "content2")
        fs.write_file(base / "file3.java", "content3")

        all_files = fs.list_files(base, "*")
        assert len(all_files) == 3

        txt_files = fs.list_files(base, "*.txt")
        assert len(txt_files) == 2

    def test_list_files_nonexistent_directory(self):
        """Test listing files in a directory that doesn't exist."""
        fs = InMemoryFileSystem()

        with pytest.raises(FileNotFoundError):
            fs.list_files(Path("/nonexistent"))

    def test_ensure_directory(self):
        """Test ensuring a directory exists."""
        fs = InMemoryFileSystem()
        path = Path("/new/nested/directory")

        fs.ensure_directory(path)
        # Directory should be tracked
        assert path in fs._directories

    def test_make_writable(self):
        """Test making a file writable (no-op in memory)."""
        fs = InMemoryFileSystem()
        path = Path("/test.txt")

        fs.write_file(path, "content")
        fs.make_writable(path)  # Should not raise

        # Should still be able to write
        fs.write_file(path, "new content")
        assert fs.read_file(path) == "new content"

    def test_make_writable_nonexistent_file(self):
        """Test making a nonexistent file writable."""
        fs = InMemoryFileSystem()

        with pytest.raises(FileNotFoundError):
            fs.make_writable(Path("/nonexistent.txt"))

    def test_nested_directories(self):
        """Test working with nested directory structures."""
        fs = InMemoryFileSystem()

        fs.write_file(Path("/a/b/c/file.txt"), "content")

        # Parent directories should be created automatically
        files = fs.list_files(Path("/a/b/c"), "*")
        assert len(files) == 1
        assert files[0] == Path("/a/b/c/file.txt")
