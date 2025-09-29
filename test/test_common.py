"""Test cases for common data structures and utilities."""

import pytest
from datetime import datetime
from pathlib import Path

from grader.common import (
    StudentRecord,
    Submission,
    GradingResult,
    FileOperationError,
)


class TestStudentRecord:
    """Test cases for StudentRecord dataclass."""

    def test_student_record_creation(self):
        """Test basic StudentRecord creation."""
        record = StudentRecord(
            org_defined_id="123456",
            username="jdoe001",
            last_name="Doe",
            first_name="John",
        )
        assert record.org_defined_id == "123456"
        assert record.username == "jdoe001"
        assert record.last_name == "Doe"
        assert record.first_name == "John"
        assert record.original_grade is None

    def test_student_record_with_grade(self):
        """Test StudentRecord creation with original grade."""
        record = StudentRecord(
            org_defined_id="123456",
            username="jdoe001",
            last_name="Doe",
            first_name="John",
            original_grade="85.5",
        )
        assert record.original_grade == "85.5"

    def test_normalize_username(self):
        """Test normalize method removes # and spaces from username."""
        record = StudentRecord(
            org_defined_id="123456",
            username="#jdoe001 ",
            last_name="Doe",
            first_name="John",
        )
        record.normalize()
        assert record.username == "jdoe001"

    def test_normalize_org_defined_id(self):
        """Test normalize method removes # and spaces from org_defined_id."""
        record = StudentRecord(
            org_defined_id="#123456 ",
            username="jdoe001",
            last_name="Doe",
            first_name="John",
        )
        record.normalize()
        assert record.org_defined_id == "123456"

    def test_normalize_both_fields(self):
        """Test normalize method handles both username and org_defined_id."""
        record = StudentRecord(
            org_defined_id="# 123456 ",
            username="# jdoe001 ",
            last_name="Doe",
            first_name="John",
        )
        record.normalize()
        assert record.org_defined_id == "123456"
        assert record.username == "jdoe001"

    def test_normalize_no_changes_needed(self):
        """Test normalize method when no changes are needed."""
        record = StudentRecord(
            org_defined_id="123456",
            username="jdoe001",
            last_name="Doe",
            first_name="John",
        )
        record.normalize()
        assert record.org_defined_id == "123456"
        assert record.username == "jdoe001"


class TestSubmission:
    """Test cases for Submission dataclass."""

    def test_submission_creation(self):
        """Test basic Submission creation."""
        timestamp = datetime(2025, 1, 15, 10, 30)
        folder_path = Path("/tmp/submission")
        submission = Submission(
            student_name="John Doe",
            timestamp=timestamp,
            folder_path=folder_path,
        )
        assert submission.student_name == "John Doe"
        assert submission.timestamp == timestamp
        assert submission.folder_path == folder_path


class TestGradingResult:
    """Test cases for GradingResult dataclass."""

    def test_grading_result_success(self):
        """Test successful GradingResult creation."""
        record = StudentRecord(
            org_defined_id="123456",
            username="jdoe001",
            last_name="Doe",
            first_name="John",
        )
        result = GradingResult(
            student_record=record,
            grade=0.85,
            success=True,
        )
        assert result.student_record == record
        assert result.grade == 0.85
        assert result.success is True
        assert result.error_message is None

    def test_grading_result_failure(self):
        """Test failed GradingResult creation."""
        record = StudentRecord(
            org_defined_id="123456",
            username="jdoe001",
            last_name="Doe",
            first_name="John",
        )
        result = GradingResult(
            student_record=record,
            grade=0.0,
            error_message="Compilation failed",
            success=False,
        )
        assert result.student_record == record
        assert result.grade == 0.0
        assert result.success is False
        assert result.error_message == "Compilation failed"

    def test_grading_result_default_success(self):
        """Test GradingResult with default success value."""
        record = StudentRecord(
            org_defined_id="123456",
            username="jdoe001",
            last_name="Doe",
            first_name="John",
        )
        result = GradingResult(
            student_record=record,
            grade=0.90,
        )
        assert result.success is True
        assert result.error_message is None


class TestFileOperationError:
    """Test cases for FileOperationError exception."""

    def test_exception_creation(self):
        """Test FileOperationError creation."""
        error = FileOperationError("Test error message")
        assert str(error) == "Test error message"

    def test_exception_inheritance(self):
        """Test FileOperationError inherits from Exception."""
        error = FileOperationError("Test error")
        assert isinstance(error, Exception)

    def test_exception_raising(self):
        """Test FileOperationError can be raised and caught."""
        with pytest.raises(FileOperationError) as exc_info:
            raise FileOperationError("Test exception")
        assert str(exc_info.value) == "Test exception"
