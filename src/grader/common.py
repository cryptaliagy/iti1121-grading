"""Common data structures and types used across the grading system."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class StudentRecord:
    """Represents a student record from the CSV file."""

    org_defined_id: str
    username: str
    last_name: str
    first_name: str
    original_grade: str | None = None

    def normalize(self):
        """
        Remove invalid character from username and org defined id
        """
        self.username = self.username.replace("#", "").replace(" ", "")
        self.org_defined_id = self.org_defined_id.replace("#", "").replace(" ", "")


@dataclass
class Submission:
    """Represents a student submission with metadata."""

    student_name: str
    timestamp: datetime
    folder_path: Path


class ClassList:
    """Represents a class list with student records."""

    def __init__(self, students: list[StudentRecord]):
        self.students_by_id = {student.org_defined_id: student for student in students}
        self.students = {student.username: student for student in students}

    def find_student_by_id(self, org_defined_id: str) -> StudentRecord | None:
        """Find a student by their organization defined ID."""
        return self.students_by_id.get(org_defined_id)

    def find_student_by_username(self, username: str) -> StudentRecord | None:
        """Find a student by their username."""
        return self.students.get(username)

    def add_student(self, student: StudentRecord):
        """Add a student to the class list."""
        self.students_by_id[student.org_defined_id] = student
        self.students[student.username] = student

    def __iter__(self):
        return iter(self.students_by_id.values())


@dataclass
class GradingResult:
    """Represents the result of grading a student's submission."""

    student_record: StudentRecord | None
    grade: float | None
    error_message: str | None = None
    success: bool = True


class FileOperationError(Exception):
    """Exception raised for errors in file operations."""

    pass
