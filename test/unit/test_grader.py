#!/usr/bin/env python3

"""Unit tests for the _grader module."""

import os
import stat
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from grader._grader import (
    CodeFilePreprocessingOptions,
    FileOperationError,
    Writer,
    add_write_permission,
    build_compile_command,
    build_run_command,
    calculate_grade_from_output,
    collect_code_files,
    find_test_files,
    preprocess_codefile,
    safe_copy_file,
    safe_delete_file,
)


class TestWriter:
    """Test the Writer class."""

    def test_writer_verbose_mode(self, capsys):
        """Test Writer in verbose mode."""
        writer = Writer(verbose=True)
        writer.echo("Test message")
        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_writer_quiet_mode(self, capsys):
        """Test Writer in quiet mode."""
        writer = Writer(verbose=False)
        writer.echo("Test message")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_writer_always_echo(self, capsys):
        """Test Writer always_echo method."""
        writer = Writer(verbose=False)
        writer.always_echo("Always visible")
        captured = capsys.readouterr()
        assert "Always visible" in captured.out


class TestCalculateGradeFromOutput:
    """Test grade calculation from test output."""

    def test_single_grade_line(self):
        """Test parsing single grade line."""
        output = """
Running tests...
Grade for Test1 (out of a possible 10): 8
Test complete
"""
        total, possible = calculate_grade_from_output(output)
        assert total == 8.0
        assert possible == 10.0

    def test_multiple_grade_lines(self):
        """Test parsing multiple grade lines."""
        output = """
Running tests...
Grade for Test1 (out of a possible 10): 8
Grade for Test2 (out of a possible 5): 4.5
Grade for Test3 (out of possible 15): 12
Test complete
"""
        total, possible = calculate_grade_from_output(output)
        assert total == 24.5
        assert possible == 30.0

    def test_decimal_grades(self):
        """Test parsing decimal grades."""
        output = """
Grade for Test1 (out of a possible 10.5): 8.75
Grade for Test2 (out of a possible 5.25): 4.5
"""
        total, possible = calculate_grade_from_output(output)
        assert total == 13.25
        assert possible == 15.75

    def test_no_grade_lines(self):
        """Test parsing output with no grades."""
        output = """
Running tests...
No grades here
Test complete
"""
        total, possible = calculate_grade_from_output(output)
        assert total == 0.0
        assert possible == 0.0

    def test_with_a_prefix(self):
        """Test parsing with 'a possible' prefix."""
        output = "Grade for Test1 (out of a possible 10): 8"
        total, possible = calculate_grade_from_output(output)
        assert total == 8.0
        assert possible == 10.0

    def test_without_a_prefix(self):
        """Test parsing without 'a' prefix."""
        output = "Grade for Test1 (out of possible 10): 8"
        total, possible = calculate_grade_from_output(output)
        assert total == 8.0
        assert possible == 10.0


class TestFindTestFiles:
    """Test finding test files."""

    def test_find_test_files_success(self, tmp_path):
        """Test finding test files successfully."""
        test_dir = tmp_path / "tests"
        test_dir.mkdir()

        # Create test files
        (test_dir / "TestL3.java").write_text("// Main test")
        (test_dir / "TestL3Helper.java").write_text("// Helper")
        (test_dir / "TestL3Utils.java").write_text("// Utils")

        writer = Writer(verbose=False)
        test_files = find_test_files(test_dir, "TestL3", writer)

        assert len(test_files) == 3
        assert any(f.name == "TestL3.java" for f in test_files)

    def test_find_test_files_no_main_file(self, tmp_path):
        """Test error when main test file missing."""
        test_dir = tmp_path / "tests"
        test_dir.mkdir()

        # Create helper file but no main file
        (test_dir / "TestL3Helper.java").write_text("// Helper")

        writer = Writer(verbose=False)
        with pytest.raises(FileOperationError, match="Main test file.*does not exist"):
            find_test_files(test_dir, "TestL3", writer)

    def test_find_test_files_no_directory(self, tmp_path):
        """Test error when directory doesn't exist."""
        test_dir = tmp_path / "nonexistent"

        writer = Writer(verbose=False)
        with pytest.raises(FileOperationError, match="does not exist"):
            find_test_files(test_dir, "TestL3", writer)

    def test_find_test_files_no_matches(self, tmp_path):
        """Test error when no test files found."""
        test_dir = tmp_path / "tests"
        test_dir.mkdir()

        writer = Writer(verbose=False)
        with pytest.raises(FileOperationError, match="No test files found"):
            find_test_files(test_dir, "TestL3", writer)


class TestSafeCopyFile:
    """Test safe file copying."""

    def test_copy_new_file(self, tmp_path):
        """Test copying to new location."""
        source = tmp_path / "source.java"
        target = tmp_path / "target.java"
        source.write_text("public class Test {}")

        writer = Writer(verbose=False)
        safe_copy_file(source, target, writer)

        assert target.exists()
        assert target.read_text() == "public class Test {}"

    def test_copy_overwrites_existing(self, tmp_path):
        """Test copying overwrites existing file."""
        source = tmp_path / "source.java"
        target = tmp_path / "target.java"
        source.write_text("new content")
        target.write_text("old content")

        writer = Writer(verbose=False)
        safe_copy_file(source, target, writer)

        assert target.read_text() == "new content"


class TestSafeDeleteFile:
    """Test safe file deletion."""

    def test_delete_existing_file(self, tmp_path):
        """Test deleting existing file."""
        file_path = tmp_path / "test.java"
        file_path.write_text("content")

        writer = Writer(verbose=False)
        result = safe_delete_file(file_path, writer)

        assert result is True
        assert not file_path.exists()

    def test_delete_nonexistent_file(self, tmp_path):
        """Test deleting nonexistent file returns True."""
        file_path = tmp_path / "nonexistent.java"

        writer = Writer(verbose=False)
        result = safe_delete_file(file_path, writer)

        assert result is True

    def test_delete_readonly_file(self, tmp_path):
        """Test deleting read-only file."""
        file_path = tmp_path / "readonly.java"
        file_path.write_text("content")
        # Make file read-only
        os.chmod(file_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        writer = Writer(verbose=False)
        # Should succeed by adding write permissions
        result = safe_delete_file(file_path, writer)

        assert result is True
        assert not file_path.exists()


class TestAddWritePermission:
    """Test adding write permissions."""

    def test_add_write_permission_to_file(self, tmp_path):
        """Test adding write permission to file."""
        file_path = tmp_path / "test.java"
        file_path.write_text("content")
        # Remove write permission
        os.chmod(file_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        writer = Writer(verbose=False)
        result = add_write_permission(file_path, writer)

        assert result is True
        # Check file is now writable
        assert os.access(file_path, os.W_OK)

    def test_add_write_permission_to_directory(self, tmp_path):
        """Test adding write permission to directory."""
        dir_path = tmp_path / "testdir"
        dir_path.mkdir()
        # Remove write permission
        os.chmod(dir_path, stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP)

        writer = Writer(verbose=False)
        result = add_write_permission(dir_path, writer)

        assert result is True
        assert os.access(dir_path, os.W_OK)


class TestPreprocessCodefile:
    """Test code file preprocessing."""

    def test_remove_package_declaration(self, tmp_path):
        """Test removing package declaration."""
        code_file = tmp_path / "Test.java"
        code_file.write_text(
            """package com.example;

public class Test {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
"""
        )

        writer = Writer(verbose=False)
        options = CodeFilePreprocessingOptions(remove_package_declaration=True)
        preprocess_codefile(options, code_file, writer)

        content = code_file.read_text()
        assert "package" not in content
        assert "public class Test" in content

    def test_keep_package_declaration(self, tmp_path):
        """Test keeping package declaration."""
        code_file = tmp_path / "Test.java"
        original_content = """package com.example;

public class Test {
}
"""
        code_file.write_text(original_content)

        writer = Writer(verbose=False)
        options = CodeFilePreprocessingOptions(remove_package_declaration=False)
        preprocess_codefile(options, code_file, writer)

        content = code_file.read_text()
        assert "package com.example;" in content

    def test_preprocess_nonexistent_file(self, tmp_path):
        """Test preprocessing nonexistent file raises error."""
        code_file = tmp_path / "nonexistent.java"

        writer = Writer(verbose=False)
        options = CodeFilePreprocessingOptions()
        with pytest.raises(FileOperationError, match="does not exist"):
            preprocess_codefile(options, code_file, writer)


class TestCollectCodeFiles:
    """Test collecting code files."""

    def test_collect_java_files(self, tmp_path):
        """Test collecting Java files from directory."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()

        (code_dir / "Test.java").write_text("class Test {}")
        (code_dir / "Helper.java").write_text("class Helper {}")
        (code_dir / "readme.txt").write_text("Not a Java file")

        writer = Writer(verbose=False)
        java_files = collect_code_files(code_dir, writer)

        assert len(java_files) == 2
        assert all(f.suffix == ".java" for f in java_files)

    def test_collect_from_empty_directory(self, tmp_path):
        """Test collecting from empty directory."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()

        writer = Writer(verbose=False)
        with pytest.raises(FileOperationError, match="No Java files found"):
            collect_code_files(code_dir, writer)

    def test_collect_from_nonexistent_directory(self, tmp_path):
        """Test collecting from nonexistent directory."""
        code_dir = tmp_path / "nonexistent"

        writer = Writer(verbose=False)
        with pytest.raises(FileOperationError, match="does not exist"):
            collect_code_files(code_dir, writer)


class TestBuildCommands:
    """Test command building functions."""

    def test_build_compile_command_simple(self):
        """Test building simple compile command."""
        cmd = build_compile_command("TestL3")
        assert cmd == ["javac", "TestL3.java"]

    def test_build_compile_command_with_classpath(self):
        """Test building compile command with classpath."""
        cmd = build_compile_command("TestL3", ["/path/to/lib", "/path/to/lib2"])
        assert cmd == ["javac", "-cp", "/path/to/lib:/path/to/lib2:.", "TestL3.java"]

    def test_build_compile_command_classpath_includes_current(self):
        """Test that current directory is added to classpath."""
        cmd = build_compile_command("TestL3", ["/path/to/lib"])
        assert "." in cmd[2]

    def test_build_compile_command_classpath_already_has_current(self):
        """Test classpath already containing current directory."""
        cmd = build_compile_command("TestL3", ["/path/to/lib", "."])
        # Should not add duplicate .
        assert cmd[2].count(".") == 1

    def test_build_run_command_simple(self):
        """Test building simple run command."""
        cmd = build_run_command("TestL3")
        assert cmd == ["java", "TestL3"]

    def test_build_run_command_with_classpath(self):
        """Test building run command with classpath."""
        cmd = build_run_command("TestL3", ["/path/to/lib", "/path/to/lib2"])
        assert cmd == ["java", "-cp", "/path/to/lib:/path/to/lib2:.", "TestL3"]


class TestCodeFilePreprocessingOptions:
    """Test CodeFilePreprocessingOptions dataclass."""

    def test_default_options(self):
        """Test default preprocessing options."""
        options = CodeFilePreprocessingOptions()
        assert options.remove_package_declaration is True

    def test_custom_options(self):
        """Test custom preprocessing options."""
        options = CodeFilePreprocessingOptions(remove_package_declaration=False)
        assert options.remove_package_declaration is False


class TestFileOperationError:
    """Test FileOperationError exception."""

    def test_exception_message(self):
        """Test exception message."""
        error = FileOperationError("Test error message")
        assert str(error) == "Test error message"

    def test_exception_raised(self):
        """Test exception can be raised and caught."""
        with pytest.raises(FileOperationError, match="Test error"):
            raise FileOperationError("Test error")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
