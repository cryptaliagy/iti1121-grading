"""Domain models for the grading system."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class StudentId:
    """Represents a unique student identifier."""

    org_defined_id: str
    username: str

    def normalize(self) -> "StudentId":
        """
        Normalize the student ID by removing invalid characters.

        Returns:
            Normalized StudentId instance
        """
        return StudentId(
            org_defined_id=self.org_defined_id.replace("#", "").replace(" ", ""),
            username=self.username.replace("#", "").replace(" ", ""),
        )


@dataclass
class Student:
    """Represents a student in the grading system."""

    student_id: StudentId
    first_name: str
    last_name: str
    original_grade: str | None = None

    @property
    def full_name(self) -> str:
        """Get the full name of the student."""
        return f"{self.first_name} {self.last_name}"


@dataclass
class Submission:
    """Represents a student submission with metadata."""

    student_name: str
    timestamp: datetime
    folder_path: Path


@dataclass
class TestRunOutput:
    """Represents the output from running a test."""

    stdout: str
    stderr: str
    exit_code: int
    execution_time: float = 0.0


@dataclass
class TestResult:
    """Represents the result of a test execution."""

    points_earned: float
    points_possible: float
    output: TestRunOutput | None = None
    success: bool = True
    error_message: str | None = None

    @property
    def percentage(self) -> float:
        """Calculate the percentage score."""
        if self.points_possible == 0:
            return 0.0
        return (self.points_earned / self.points_possible) * 100


@dataclass
class GradingResult:
    """Represents the complete result of grading a student's submission."""

    student: Student
    test_result: TestResult | None = None
    grade: float | None = None
    error_message: str | None = None
    success: bool = True

    @property
    def final_grade(self) -> float:
        """Get the final grade, preferring explicit grade over test result."""
        if self.grade is not None:
            return self.grade
        if self.test_result is not None:
            return self.test_result.points_earned
        return 0.0
