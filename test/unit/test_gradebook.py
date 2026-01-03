"""Unit tests for gradebook repository implementations."""

import pytest
import tempfile
from pathlib import Path

from grader.domain.models import Student, StudentId, GradingResult
from grader.infrastructure.gradebook import CSVGradebookRepository


def create_test_csv(
    csv_path: Path, rows: list[dict], include_header: bool = True
) -> None:
    """
    Create a test CSV file.

    Args:
        csv_path: Path where CSV should be created
        rows: List of dictionaries representing rows
        include_header: Whether to include header row
    """
    import csv

    if not rows:
        return

    with open(csv_path, "w", newline="") as f:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if include_header:
            writer.writeheader()
        writer.writerows(rows)


class TestCSVGradebookRepository:
    """Test the CSVGradebookRepository implementation."""

    def test_load_students(self):
        """Test loading students from a CSV file."""
        repo = CSVGradebookRepository()

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "students.csv"
            create_test_csv(
                csv_path,
                [
                    {
                        "OrgDefinedId": "123",
                        "Username": "jdoe",
                        "First Name": "John",
                        "Last Name": "Doe",
                        "End-of-Line Indicator": "#",
                    },
                    {
                        "OrgDefinedId": "456",
                        "Username": "jsmith",
                        "First Name": "Jane",
                        "Last Name": "Smith",
                        "End-of-Line Indicator": "#",
                    },
                ],
            )

            students = repo.load_students(csv_path)

            assert len(students) == 2
            assert students[0].student_id.org_defined_id == "123"
            assert students[0].student_id.username == "jdoe"
            assert students[0].first_name == "John"
            assert students[0].last_name == "Doe"

    def test_load_students_with_hash_symbols(self):
        """Test loading students with hash symbols in IDs."""
        repo = CSVGradebookRepository()

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "students.csv"
            create_test_csv(
                csv_path,
                [
                    {
                        "OrgDefinedId": "#123#",
                        "Username": "#jdoe#",
                        "First Name": "John",
                        "Last Name": "Doe",
                        "End-of-Line Indicator": "#",
                    },
                ],
            )

            students = repo.load_students(csv_path)

            # Hash symbols should be stripped
            assert students[0].student_id.org_defined_id == "123"
            assert students[0].student_id.username == "jdoe"

    def test_load_students_nonexistent_file(self):
        """Test loading students from a file that doesn't exist."""
        repo = CSVGradebookRepository()

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "nonexistent.csv"

            with pytest.raises(FileNotFoundError):
                repo.load_students(csv_path)

    def test_load_students_missing_columns(self):
        """Test loading students from CSV missing required columns."""
        repo = CSVGradebookRepository()

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "students.csv"
            create_test_csv(
                csv_path,
                [
                    {
                        "OrgDefinedId": "123",
                        "Username": "jdoe",
                        # Missing First Name and Last Name
                    },
                ],
            )

            with pytest.raises(ValueError) as exc_info:
                repo.load_students(csv_path)
            assert "missing required columns" in str(exc_info.value).lower()

    def test_save_grades(self):
        """Test saving grades to a CSV file."""
        repo = CSVGradebookRepository(assignment_name="Lab1")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create original CSV
            original_csv = Path(tmpdir) / "students.csv"
            create_test_csv(
                original_csv,
                [
                    {
                        "OrgDefinedId": "123",
                        "Username": "jdoe",
                        "First Name": "John",
                        "Last Name": "Doe",
                        "End-of-Line Indicator": "#",
                    },
                    {
                        "OrgDefinedId": "456",
                        "Username": "jsmith",
                        "First Name": "Jane",
                        "Last Name": "Smith",
                        "End-of-Line Indicator": "#",
                    },
                ],
            )

            # Create grading results
            student1 = Student(
                student_id=StudentId(org_defined_id="123", username="jdoe"),
                first_name="John",
                last_name="Doe",
            )
            student2 = Student(
                student_id=StudentId(org_defined_id="456", username="jsmith"),
                first_name="Jane",
                last_name="Smith",
            )

            results = [
                GradingResult(student=student1, grade=8.5, success=True),
                GradingResult(student=student2, grade=9.0, success=True),
            ]

            output_csv = Path(tmpdir) / "results.csv"
            repo.save_grades(results, original_csv, output_csv)

            # Read the output CSV
            import pandas as pd

            output_df = pd.read_csv(output_csv)

            # Check that grades were saved
            assert len(output_df) == 2
            assert "Lab1" in output_df.columns
            # Pandas reads numeric strings as floats
            assert output_df[output_df["Username"] == "jdoe"]["Lab1"].values[0] == 8.5
            assert output_df[output_df["Username"] == "jsmith"]["Lab1"].values[0] == 9.0

    def test_save_grades_with_failures(self):
        """Test saving grades with failed submissions."""
        repo = CSVGradebookRepository(assignment_name="Lab1")

        with tempfile.TemporaryDirectory() as tmpdir:
            original_csv = Path(tmpdir) / "students.csv"
            create_test_csv(
                original_csv,
                [
                    {
                        "OrgDefinedId": "123",
                        "Username": "jdoe",
                        "First Name": "John",
                        "Last Name": "Doe",
                        "End-of-Line Indicator": "#",
                    },
                ],
            )

            student1 = Student(
                student_id=StudentId(org_defined_id="123", username="jdoe"),
                first_name="John",
                last_name="Doe",
            )

            results = [
                GradingResult(
                    student=student1,
                    grade=None,
                    error_message="Compilation failed",
                    success=False,
                ),
            ]

            output_csv = Path(tmpdir) / "results.csv"
            repo.save_grades(results, original_csv, output_csv, failure_is_null=False)

            import pandas as pd

            output_df = pd.read_csv(output_csv)
            # Pandas reads numeric strings as floats
            assert output_df[output_df["Username"] == "jdoe"]["Lab1"].values[0] == 0.0

    def test_save_grades_with_failures_as_null(self):
        """Test saving grades with failures as null."""
        repo = CSVGradebookRepository(assignment_name="Lab1")

        with tempfile.TemporaryDirectory() as tmpdir:
            original_csv = Path(tmpdir) / "students.csv"
            create_test_csv(
                original_csv,
                [
                    {
                        "OrgDefinedId": "123",
                        "Username": "jdoe",
                        "First Name": "John",
                        "Last Name": "Doe",
                        "End-of-Line Indicator": "#",
                    },
                ],
            )

            student1 = Student(
                student_id=StudentId(org_defined_id="123", username="jdoe"),
                first_name="John",
                last_name="Doe",
            )

            results = [
                GradingResult(
                    student=student1,
                    grade=None,
                    error_message="Compilation failed",
                    success=False,
                ),
            ]

            output_csv = Path(tmpdir) / "results.csv"
            repo.save_grades(results, original_csv, output_csv, failure_is_null=True)

            import pandas as pd

            output_df = pd.read_csv(output_csv)
            # Should be empty string (which pandas reads as NaN)
            assert pd.isna(output_df[output_df["Username"] == "jdoe"]["Lab1"].values[0])

    def test_save_grades_removes_name_columns(self):
        """Test that save_grades removes name columns from output."""
        repo = CSVGradebookRepository(assignment_name="Lab1")

        with tempfile.TemporaryDirectory() as tmpdir:
            original_csv = Path(tmpdir) / "students.csv"
            create_test_csv(
                original_csv,
                [
                    {
                        "OrgDefinedId": "123",
                        "Username": "jdoe",
                        "First Name": "John",
                        "Last Name": "Doe",
                        "End-of-Line Indicator": "#",
                    },
                ],
            )

            student1 = Student(
                student_id=StudentId(org_defined_id="123", username="jdoe"),
                first_name="John",
                last_name="Doe",
            )

            results = [GradingResult(student=student1, grade=8.5, success=True)]

            output_csv = Path(tmpdir) / "results.csv"
            repo.save_grades(results, original_csv, output_csv)

            import pandas as pd

            output_df = pd.read_csv(output_csv)

            # Name columns should be removed
            assert "First Name" not in output_df.columns
            assert "Last Name" not in output_df.columns

    def test_save_grades_nonexistent_original(self):
        """Test saving grades when original CSV doesn't exist."""
        repo = CSVGradebookRepository()

        with tempfile.TemporaryDirectory() as tmpdir:
            original_csv = Path(tmpdir) / "nonexistent.csv"
            output_csv = Path(tmpdir) / "results.csv"

            with pytest.raises(FileNotFoundError):
                repo.save_grades([], original_csv, output_csv)
