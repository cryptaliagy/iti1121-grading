#!/usr/bin/env python3

"""Integration tests for single grading workflow."""

import shutil
from pathlib import Path

import pytest

from grader._grader import (
    CodeFilePreprocessingOptions,
    Writer,
    collect_code_files,
    compile_test,
    copy_test_files,
    find_test_files,
    preprocess_codefile,
    run_test,
)


class TestSingleGradingWorkflow:
    """Test the complete single grading workflow."""

    @pytest.fixture
    def test_env(self, tmp_path):
        """Set up test environment with fixtures."""
        # Get fixture directory
        fixture_dir = Path(__file__).parent.parent / "fixtures"

        # Create test directory
        test_dir = tmp_path / "tests"
        test_dir.mkdir()

        # Copy test files
        shutil.copy(fixture_dir / "TestSimple.java", test_dir / "TestSimple.java")
        shutil.copy(fixture_dir / "TestUtils.java", test_dir / "TestUtils.java")

        # Create code directory
        code_dir = tmp_path / "code"
        code_dir.mkdir()

        return {
            "test_dir": test_dir,
            "code_dir": code_dir,
            "fixture_dir": fixture_dir,
        }

    def test_find_and_copy_test_files(self, test_env):
        """Test finding and copying test files."""
        writer = Writer(verbose=False)

        # Find test files
        test_files = find_test_files(test_env["test_dir"], "TestSimple", writer)
        assert len(test_files) >= 1
        assert any(f.name == "TestSimple.java" for f in test_files)

        # Copy test files to code directory
        copy_test_files(test_files, test_env["code_dir"], writer)

        # Verify files were copied
        assert (test_env["code_dir"] / "TestSimple.java").exists()
        assert (test_env["code_dir"] / "TestUtils.java").exists()

    def test_compile_and_run_test(self, test_env):
        """Test compiling and running a test."""
        writer = Writer(verbose=False)

        # Find and copy test files
        test_files = find_test_files(test_env["test_dir"], "TestSimple", writer)
        copy_test_files(test_files, test_env["code_dir"], writer)

        # Compile the test
        compilation_success = compile_test(
            "TestSimple", test_env["code_dir"], writer, None
        )
        assert compilation_success is True

        # Run the test
        success, total_points, possible_points = run_test(
            "TestSimple", test_env["code_dir"], writer, None
        )

        assert success is True
        assert total_points == 15.0  # 10 + 5
        assert possible_points == 15.0

    def test_preprocess_code_file(self, test_env):
        """Test preprocessing student code."""
        # Copy student code with package declaration
        student_code = test_env["code_dir"] / "Calculator.java"
        shutil.copy(test_env["fixture_dir"] / "Calculator.java", student_code)

        writer = Writer(verbose=False)
        options = CodeFilePreprocessingOptions(remove_package_declaration=True)

        # Preprocess the file
        preprocess_codefile(options, student_code, writer)

        # Verify package declaration was removed
        content = student_code.read_text()
        assert "package com.example.student;" not in content
        assert "public class Calculator" in content

    def test_collect_and_preprocess_all_files(self, test_env):
        """Test collecting and preprocessing all code files."""
        # Copy student code
        shutil.copy(
            test_env["fixture_dir"] / "Calculator.java",
            test_env["code_dir"] / "Calculator.java",
        )

        writer = Writer(verbose=False)

        # Collect Java files
        java_files = collect_code_files(test_env["code_dir"], writer)
        assert len(java_files) == 1

        # Preprocess all files
        options = CodeFilePreprocessingOptions(remove_package_declaration=True)
        for code_file in java_files:
            preprocess_codefile(options, code_file, writer)

        # Verify preprocessing worked
        for code_file in java_files:
            content = code_file.read_text()
            assert "package com.example.student;" not in content


class TestEndToEndSingleGrading:
    """End-to-end test for single grading workflow."""

    @pytest.mark.integration
    def test_complete_workflow(self, tmp_path):
        """Test complete grading workflow from start to finish."""
        # Get fixture directory
        fixture_dir = Path(__file__).parent.parent / "fixtures"

        # Set up directories
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        code_dir = tmp_path / "code"
        code_dir.mkdir()

        # Copy test files
        shutil.copy(fixture_dir / "TestSimple.java", test_dir / "TestSimple.java")
        shutil.copy(fixture_dir / "TestUtils.java", test_dir / "TestUtils.java")

        writer = Writer(verbose=False)

        # 1. Find test files
        test_files = find_test_files(test_dir, "TestSimple", writer)
        assert len(test_files) >= 1

        # 2. Copy test files
        copy_test_files(test_files, code_dir, writer)
        assert (code_dir / "TestSimple.java").exists()

        # 3. Compile the test
        compilation_success = compile_test("TestSimple", code_dir, writer, None)
        assert compilation_success is True

        # 4. Run the test
        success, total_points, possible_points = run_test(
            "TestSimple", code_dir, writer, None
        )

        # 5. Verify results
        assert success is True
        assert total_points == 15.0
        assert possible_points == 15.0
        assert (total_points / possible_points) == 1.0  # 100% grade


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
