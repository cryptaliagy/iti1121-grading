#!/usr/bin/env python3

"""Unit tests for infrastructure adapters."""

import pytest
from pathlib import Path

from grader._grader import Writer
from grader.infrastructure.adapters import (
    LegacyFileSystemAdapter,
    LegacyCodePreprocessorAdapter,
    LegacyTestRunnerAdapter,
)
from grader.infrastructure.protocols import TestRunnerConfig


class TestLegacyFileSystemAdapter:
    """Test the LegacyFileSystemAdapter."""

    def test_read_file(self, tmp_path):
        """Test reading a file."""
        writer = Writer(verbose=False)
        adapter = LegacyFileSystemAdapter(writer)

        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        content = adapter.read_file(test_file)
        assert content == "Hello, World!"

    def test_write_file(self, tmp_path):
        """Test writing a file."""
        writer = Writer(verbose=False)
        adapter = LegacyFileSystemAdapter(writer)

        test_file = tmp_path / "test.txt"
        adapter.write_file(test_file, "Hello, World!")

        assert test_file.read_text() == "Hello, World!"

    def test_copy_file(self, tmp_path):
        """Test copying a file."""
        writer = Writer(verbose=False)
        adapter = LegacyFileSystemAdapter(writer)

        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        source.write_text("Test content")

        adapter.copy_file(source, target)

        assert target.exists()
        assert target.read_text() == "Test content"

    def test_delete_file(self, tmp_path):
        """Test deleting a file."""
        writer = Writer(verbose=False)
        adapter = LegacyFileSystemAdapter(writer)

        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        result = adapter.delete_file(test_file)

        assert result is True
        assert not test_file.exists()

    def test_list_files(self, tmp_path):
        """Test listing files."""
        writer = Writer(verbose=False)
        adapter = LegacyFileSystemAdapter(writer)

        (tmp_path / "test1.txt").write_text("content")
        (tmp_path / "test2.txt").write_text("content")
        (tmp_path / "other.java").write_text("content")

        txt_files = adapter.list_files(tmp_path, "*.txt")
        assert len(txt_files) == 2
        assert all(f.suffix == ".txt" for f in txt_files)

    def test_ensure_directory(self, tmp_path):
        """Test ensuring a directory exists."""
        writer = Writer(verbose=False)
        adapter = LegacyFileSystemAdapter(writer)

        test_dir = tmp_path / "subdir" / "nested"
        adapter.ensure_directory(test_dir)

        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_make_writable_file(self, tmp_path):
        """Test making a file writable."""
        writer = Writer(verbose=False)
        adapter = LegacyFileSystemAdapter(writer)

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        test_file.chmod(0o444)  # Make read-only

        adapter.make_writable(test_file)

        # File should now be writable
        test_file.write_text("new content")
        assert test_file.read_text() == "new content"


class TestLegacyCodePreprocessorAdapter:
    """Test the LegacyCodePreprocessorAdapter."""

    def test_preprocess_removes_package_declaration(self, tmp_path):
        """Test that preprocessing removes package declaration."""
        writer = Writer(verbose=False)
        adapter = LegacyCodePreprocessorAdapter(writer)

        code_file = tmp_path / "Test.java"
        code_file.write_text(
            "package com.example;\n"
            "\n"
            "public class Test {\n"
            "    public static void main(String[] args) {\n"
            "        System.out.println(\"Hello\");\n"
            "    }\n"
            "}\n"
        )

        adapter.preprocess(code_file)

        content = code_file.read_text()
        assert "package" not in content
        assert "public class Test" in content

    def test_preprocess_keeps_package_declaration_when_configured(self, tmp_path):
        """Test that preprocessing can keep package declaration."""
        from grader._grader import CodeFilePreprocessingOptions

        writer = Writer(verbose=False)
        options = CodeFilePreprocessingOptions(remove_package_declaration=False)
        adapter = LegacyCodePreprocessorAdapter(writer, options)

        code_file = tmp_path / "Test.java"
        original_content = (
            "package com.example;\n"
            "\n"
            "public class Test {\n"
            "}\n"
        )
        code_file.write_text(original_content)

        adapter.preprocess(code_file)

        content = code_file.read_text()
        assert "package com.example;" in content


class TestLegacyTestRunnerAdapter:
    """Test the LegacyTestRunnerAdapter."""

    def test_compile_creates_class_file(self, tmp_path):
        """Test that compilation creates a class file."""
        writer = Writer(verbose=False)
        adapter = LegacyTestRunnerAdapter(writer)

        # Create a simple Java file
        java_file = tmp_path / "HelloWorld.java"
        java_file.write_text(
            "public class HelloWorld {\n"
            "    public static void main(String[] args) {\n"
            "        System.out.println(\"Hello, World!\");\n"
            "    }\n"
            "}\n"
        )

        config = TestRunnerConfig(
            main_test_file="HelloWorld",
            target_dir=tmp_path,
        )

        result = adapter.compile(config)

        assert result is True
        assert (tmp_path / "HelloWorld.class").exists()

    def test_compile_fails_with_syntax_error(self, tmp_path):
        """Test that compilation fails with syntax errors."""
        writer = Writer(verbose=False)
        adapter = LegacyTestRunnerAdapter(writer)

        # Create a Java file with syntax error
        java_file = tmp_path / "BadCode.java"
        java_file.write_text(
            "public class BadCode {\n"
            "    public static void main(String[] args) {\n"
            "        // Missing closing brace\n"
            "}\n"
        )

        config = TestRunnerConfig(
            main_test_file="BadCode",
            target_dir=tmp_path,
        )

        result = adapter.compile(config)

        assert result is False

    def test_run_executes_java_program(self, tmp_path):
        """Test running a compiled Java program."""
        writer = Writer(verbose=False)
        adapter = LegacyTestRunnerAdapter(writer)

        # Create and compile a simple Java file
        java_file = tmp_path / "HelloWorld.java"
        java_file.write_text(
            "public class HelloWorld {\n"
            "    public static void main(String[] args) {\n"
            "        System.out.println(\"Hello, World!\");\n"
            "    }\n"
            "}\n"
        )

        config = TestRunnerConfig(
            main_test_file="HelloWorld",
            target_dir=tmp_path,
        )

        # Compile first
        compile_result = adapter.compile(config)
        assert compile_result is True

        # Run the program
        run_output = adapter.run(config)

        assert run_output.exit_code == 0
        assert "Hello, World!" in run_output.stdout
        assert run_output.execution_time >= 0

    def test_run_captures_stderr(self, tmp_path):
        """Test that stderr is captured."""
        writer = Writer(verbose=False)
        adapter = LegacyTestRunnerAdapter(writer)

        # Create a Java file that writes to stderr
        java_file = tmp_path / "StderrTest.java"
        java_file.write_text(
            "public class StderrTest {\n"
            "    public static void main(String[] args) {\n"
            "        System.err.println(\"Error message\");\n"
            "    }\n"
            "}\n"
        )

        config = TestRunnerConfig(
            main_test_file="StderrTest",
            target_dir=tmp_path,
        )

        # Compile and run
        adapter.compile(config)
        run_output = adapter.run(config)

        assert run_output.exit_code == 0
        assert "Error message" in run_output.stderr
