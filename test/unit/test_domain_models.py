#!/usr/bin/env python3

"""Unit tests for domain models."""

import pytest
from datetime import datetime
from pathlib import Path

from grader.domain.models import (
    GradingResult,
    Student,
    StudentId,
    Submission,
    TestResult,
    TestRunOutput,
)


class TestStudentId:
    """Test the StudentId model."""

    def test_student_id_creation(self):
        """Test creating a StudentId."""
        student_id = StudentId(org_defined_id="123", username="jdoe")
        assert student_id.org_defined_id == "123"
        assert student_id.username == "jdoe"

    def test_student_id_normalize(self):
        """Test normalizing a StudentId."""
        student_id = StudentId(org_defined_id="#123 ", username="# jdoe ")
        normalized = student_id.normalize()
        assert normalized.org_defined_id == "123"
        assert normalized.username == "jdoe"


class TestStudent:
    """Test the Student model."""

    def test_student_creation(self):
        """Test creating a Student."""
        student_id = StudentId(org_defined_id="123", username="jdoe")
        student = Student(
            student_id=student_id,
            first_name="John",
            last_name="Doe",
        )
        assert student.student_id == student_id
        assert student.first_name == "John"
        assert student.last_name == "Doe"

    def test_student_full_name(self):
        """Test getting full name."""
        student_id = StudentId(org_defined_id="123", username="jdoe")
        student = Student(
            student_id=student_id,
            first_name="John",
            last_name="Doe",
        )
        assert student.full_name == "John Doe"


class TestSubmission:
    """Test the Submission model."""

    def test_submission_creation(self):
        """Test creating a Submission."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        submission = Submission(
            student_name="John Doe",
            timestamp=timestamp,
            folder_path=Path("/path/to/submission"),
        )
        assert submission.student_name == "John Doe"
        assert submission.timestamp == timestamp
        assert submission.folder_path == Path("/path/to/submission")


class TestTestRunOutput:
    """Test the TestRunOutput model."""

    def test_test_run_output_creation(self):
        """Test creating a TestRunOutput."""
        output = TestRunOutput(
            stdout="Test passed",
            stderr="",
            exit_code=0,
            execution_time=1.5,
        )
        assert output.stdout == "Test passed"
        assert output.stderr == ""
        assert output.exit_code == 0
        assert output.execution_time == 1.5


class TestTestResult:
    """Test the TestResult model."""

    def test_test_result_creation(self):
        """Test creating a TestResult."""
        output = TestRunOutput(stdout="Test output", stderr="", exit_code=0)
        result = TestResult(
            points_earned=8.0,
            points_possible=10.0,
            output=output,
            success=True,
        )
        assert result.points_earned == 8.0
        assert result.points_possible == 10.0
        assert result.output == output
        assert result.success is True

    def test_test_result_percentage(self):
        """Test calculating percentage."""
        result = TestResult(points_earned=8.0, points_possible=10.0)
        assert result.percentage == 80.0

    def test_test_result_percentage_zero_possible(self):
        """Test percentage when no points possible."""
        result = TestResult(points_earned=0.0, points_possible=0.0)
        assert result.percentage == 0.0


class TestGradingResult:
    """Test the GradingResult model."""

    def test_grading_result_creation(self):
        """Test creating a GradingResult."""
        student_id = StudentId(org_defined_id="123", username="jdoe")
        student = Student(
            student_id=student_id,
            first_name="John",
            last_name="Doe",
        )
        test_result = TestResult(points_earned=8.0, points_possible=10.0)
        grading_result = GradingResult(
            student=student,
            test_result=test_result,
            success=True,
        )
        assert grading_result.student == student
        assert grading_result.test_result == test_result
        assert grading_result.success is True

    def test_grading_result_final_grade_explicit(self):
        """Test final_grade with explicit grade."""
        student_id = StudentId(org_defined_id="123", username="jdoe")
        student = Student(
            student_id=student_id,
            first_name="John",
            last_name="Doe",
        )
        test_result = TestResult(points_earned=8.0, points_possible=10.0)
        grading_result = GradingResult(
            student=student,
            test_result=test_result,
            grade=9.0,
            success=True,
        )
        assert grading_result.final_grade == 9.0

    def test_grading_result_final_grade_from_test_result(self):
        """Test final_grade from test result."""
        student_id = StudentId(org_defined_id="123", username="jdoe")
        student = Student(
            student_id=student_id,
            first_name="John",
            last_name="Doe",
        )
        test_result = TestResult(points_earned=8.0, points_possible=10.0)
        grading_result = GradingResult(
            student=student,
            test_result=test_result,
            success=True,
        )
        assert grading_result.final_grade == 8.0

    def test_grading_result_final_grade_default(self):
        """Test final_grade with no grade or test result."""
        student_id = StudentId(org_defined_id="123", username="jdoe")
        student = Student(
            student_id=student_id,
            first_name="John",
            last_name="Doe",
        )
        grading_result = GradingResult(
            student=student,
            success=False,
        )
        assert grading_result.final_grade == 0.0
