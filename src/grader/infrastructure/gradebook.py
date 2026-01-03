"""Gradebook repository implementations for loading and saving student grades."""

import pandas as pd
from pathlib import Path

from grader.domain.models import Student, StudentId, GradingResult


class CSVGradebookRepository:
    """Repository for loading and saving gradebook data in CSV format."""

    def __init__(self, assignment_name: str = "Lab Grade"):
        """
        Initialize the CSV gradebook repository.

        Args:
            assignment_name: Name for the assignment grade column
        """
        self.assignment_name = assignment_name

    def load_students(self, csv_path: Path) -> list[Student]:
        """
        Load student records from a CSV file.

        Expected CSV columns:
        - OrgDefinedId: Organization-defined student ID
        - Username: Student username
        - First Name: Student first name
        - Last Name: Student last name

        Args:
            csv_path: Path to the CSV file

        Returns:
            List of Student objects

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV is missing required columns
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file {csv_path} does not exist")

        # Load the CSV
        df = pd.read_csv(csv_path)

        # Validate required columns
        required_columns = ["OrgDefinedId", "Username", "First Name", "Last Name"]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        # Clean and normalize the data
        df["Username"] = df["Username"].astype(str).str.strip("#").str.strip()
        df["OrgDefinedId"] = df["OrgDefinedId"].astype(str).str.strip("#").str.strip()

        # Convert to Student objects
        students = []
        for _, row in df.iterrows():
            student_id = StudentId(
                org_defined_id=str(row["OrgDefinedId"]),
                username=str(row["Username"]),
            )
            student = Student(
                student_id=student_id,
                first_name=str(row["First Name"]),
                last_name=str(row["Last Name"]),
                original_grade=str(row.get(self.assignment_name, "")),
            )
            students.append(student)

        return students

    def save_grades(
        self,
        results: list[GradingResult],
        original_csv_path: Path,
        output_path: Path,
        failure_is_null: bool = False,
    ) -> None:
        """
        Save grading results to a CSV file.

        Args:
            results: List of grading results
            original_csv_path: Path to the original CSV (for preserving structure)
            output_path: Path to save the output CSV
            failure_is_null: Whether to use null for failures instead of 0

        Raises:
            FileNotFoundError: If original CSV doesn't exist
        """
        if not original_csv_path.exists():
            raise FileNotFoundError(
                f"Original CSV file {original_csv_path} does not exist"
            )

        # Load the original CSV
        output_df = pd.read_csv(original_csv_path)

        # Ensure assignment column exists
        if self.assignment_name not in output_df.columns:
            output_df[self.assignment_name] = pd.Series(dtype="str")

        # Clean usernames
        output_df["Username"] = output_df["Username"].astype(str).str.strip("#")
        output_df["OrgDefinedId"] = output_df["OrgDefinedId"].astype(str).str.strip("#")

        # Create a lookup for results by username
        results_lookup = {
            result.student.student_id.username: result for result in results
        }

        # Update the DataFrame with results
        for idx, row in output_df.iterrows():
            username = str(row["Username"])
            if username in results_lookup:
                result = results_lookup[username]
                if result.success and result.grade is not None:
                    output_df.at[idx, self.assignment_name] = f"{result.grade:.3f}"
                else:
                    if failure_is_null:
                        output_df.at[idx, self.assignment_name] = ""
                    else:
                        output_df.at[idx, self.assignment_name] = "0.000"
            else:
                # If no result found, set to empty or 0 based on failure_is_null
                if failure_is_null:
                    output_df.at[idx, self.assignment_name] = ""
                else:
                    output_df.at[idx, self.assignment_name] = "0.000"

        # Remove name columns for output (as per original implementation)
        output_df.drop(
            ["First Name", "Last Name"], axis=1, inplace=True, errors="ignore"
        )

        # Keep only required columns
        output_columns = ["OrgDefinedId", "Username", self.assignment_name]
        # Add End-of-Line Indicator if it exists
        if "End-of-Line Indicator" in output_df.columns:
            output_columns.append("End-of-Line Indicator")

        output_df = output_df[output_columns]

        # Save to CSV
        output_df.to_csv(output_path, index=False)
