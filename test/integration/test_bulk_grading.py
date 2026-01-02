#!/usr/bin/env python3

"""Integration tests for bulk grading workflow."""

import shutil
import zipfile
from pathlib import Path

import pytest

from grader.bulk_grader import (
    extract_submissions,
    find_latest_submissions,
    load_grading_list,
    normalize_name,
    parse_submission_folder_name,
    prepare_grading_directory,
)
from grader._grader import Writer


class TestBulkGradingWorkflow:
    """Test the bulk grading workflow components."""

    @pytest.fixture
    def test_env(self, tmp_path):
        """Set up test environment with fixtures."""
        fixture_dir = Path(__file__).parent.parent / "fixtures"

        # Create submissions zip
        submissions_zip = tmp_path / "submissions.zip"

        # Read student code once
        student_code = (fixture_dir / "submissions" / "StudentCode.java").read_text()

        with zipfile.ZipFile(submissions_zip, "w") as zf:
            # Create submission folders
            folder1 = "152711-351765 - Alice Smith - May 18, 2025 1224 PM"
            folder2 = "123456-789012 - Bob Jones - June 15, 2025 930 AM"

            # Add student code to both folders
            zf.writestr(f"{folder1}/StudentCode.java", student_code)
            zf.writestr(f"{folder2}/StudentCode.java", student_code)

        # Copy grading list
        grading_list = tmp_path / "grading_list.csv"
        shutil.copy(fixture_dir / "grading_list.csv", grading_list)

        return {
            "submissions_zip": submissions_zip,
            "grading_list": grading_list,
            "fixture_dir": fixture_dir,
            "tmp_path": tmp_path,
        }

    def test_load_grading_list(self, test_env):
        """Test loading grading list CSV."""
        df = load_grading_list(test_env["grading_list"])

        assert len(df) >= 3
        assert "Username" in df.columns
        assert "OrgDefinedId" in df.columns
        assert "First Name" in df.columns
        assert "Last Name" in df.columns

    def test_parse_submission_folder_name(self):
        """Test parsing submission folder names."""
        folder_name = "152711-351765 - Alice Smith - May 18, 2025 1224 PM"
        name, timestamp = parse_submission_folder_name(folder_name)

        assert name == "Alice Smith"
        assert timestamp.year == 2025
        assert timestamp.month == 5
        assert timestamp.day == 18

    def test_normalize_name(self):
        """Test name normalization."""
        assert normalize_name("Alice Smith") == "alice smith"
        assert normalize_name("  Alice   Smith  ") == "alice smith"
        assert normalize_name("José María") == "jose maria"

    def test_extract_submissions(self, test_env):
        """Test extracting submissions from ZIP."""
        temp_dir = test_env["tmp_path"] / "temp"
        temp_dir.mkdir()

        submissions_dir = extract_submissions(test_env["submissions_zip"], temp_dir)

        assert submissions_dir.exists()
        # Should have extracted 2 submission folders
        submission_folders = list(submissions_dir.iterdir())
        assert len(submission_folders) == 2

    def test_prepare_grading_directory(self, test_env):
        """Test preparing grading directory."""
        # Extract submissions first
        temp_dir = test_env["tmp_path"] / "temp"
        temp_dir.mkdir()

        submissions_dir = extract_submissions(test_env["submissions_zip"], temp_dir)

        # Get first submission folder
        submission_folder = list(submissions_dir.iterdir())[0]

        writer = Writer(verbose=False)
        grading_dir = prepare_grading_directory(submission_folder, temp_dir, writer)

        assert grading_dir.exists()
        assert (grading_dir / "StudentCode.java").exists()

    def test_find_latest_submissions(self, test_env):
        """Test finding latest submissions for students."""
        # Extract submissions first
        temp_dir = test_env["tmp_path"] / "temp"
        temp_dir.mkdir()

        submissions_dir = extract_submissions(test_env["submissions_zip"], temp_dir)

        # Load grading list
        grading_df = load_grading_list(test_env["grading_list"])

        writer = Writer(verbose=False)
        latest_submissions = find_latest_submissions(
            submissions_dir, grading_df, writer
        )

        # Should find matches for Alice and Bob
        assert len(latest_submissions) >= 2


class TestEndToEndBulkGrading:
    """End-to-end test for bulk grading workflow."""

    @pytest.mark.integration
    def test_bulk_workflow_components(self, tmp_path):
        """Test bulk grading workflow components working together."""
        fixture_dir = Path(__file__).parent.parent / "fixtures"

        # Read student code once
        student_code = (fixture_dir / "submissions" / "StudentCode.java").read_text()

        # Create submissions zip with multiple students
        submissions_zip = tmp_path / "submissions.zip"
        with zipfile.ZipFile(submissions_zip, "w") as zf:
            folders = [
                "152711-351765 - Alice Smith - May 18, 2025 1224 PM",
                "123456-789012 - Bob Jones - June 15, 2025 930 AM",
            ]

            for folder in folders:
                zf.writestr(f"{folder}/StudentCode.java", student_code)

        # Copy grading list
        grading_list = tmp_path / "grading_list.csv"
        shutil.copy(fixture_dir / "grading_list.csv", grading_list)

        # 1. Load grading list
        grading_df = load_grading_list(grading_list)
        assert len(grading_df) >= 2

        # 2. Extract submissions
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        submissions_dir = extract_submissions(submissions_zip, temp_dir)
        assert submissions_dir.exists()

        # 3. Find latest submissions for each student
        writer = Writer(verbose=False)
        latest_submissions = find_latest_submissions(
            submissions_dir, grading_df, writer
        )
        assert len(latest_submissions) >= 2

        # 4. Prepare grading directory for one student
        first_submission = list(latest_submissions.values())[0]
        grading_dir = prepare_grading_directory(first_submission[1], temp_dir, writer)
        assert grading_dir.exists()
        assert (grading_dir / "StudentCode.java").exists()
