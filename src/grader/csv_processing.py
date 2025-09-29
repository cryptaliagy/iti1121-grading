"""CSV processing utilities for grading."""

import pandas as pd
from pathlib import Path

from grader.writer import Writer

from .common import GradingResult, StudentRecord


class BrightspaceIntegration:
    """Handles integration with Brightspace (D2L) for grading.

    This class handles loading the classlist, and saving the grading results in a Brightspace-compatible format.
    """

    def __init__(
        self,
        writer: Writer,
        csv_path: Path,
        assignment_name: str = "Lab Grade",
    ):
        """
        Initialize the Brightspace integration with the path to the classlist CSV.

        Args:
            csv_path: Path to the classlist CSV file
            assignment_name: Name for the assignment grade column
        """
        self.writer = writer
        self.csv_path = csv_path
        self.assignment_name = assignment_name
        self._classlist: list[StudentRecord] | None = None

    def load_classlist(self) -> list[StudentRecord]:
        """Load the classlist from the CSV file."""
        if self._classlist is not None:
            return self._classlist

        df = pd.read_csv(self.csv_path)
        students = []
        for _, row in df.iterrows():
            student = StudentRecord(
                org_defined_id=row["OrgDefinedId"],
                username=row["Username"],
                last_name=row["LastName"],
                first_name=row["FirstName"],
                original_grade=None,
            )
            student.normalize()
            students.append(student)

        self._classlist = students
        return students

    def save_results(
        self,
        results: list[GradingResult],
        output_path: Path,
        failure_is_null: bool = True,
    ):
        """
        Save grading results to a CSV file.

        Args:
            results: List of grading results
            output_path: Path to save the output CSV
            failure_is_null: Whether to use null for failures instead of 0
        """
        # Create a lookup for results by username
        results_lookup = {
            result.student_record.username: result
            for result in results
            if result.student_record is not None
        }

        classlist = self.load_classlist()

        output_df = pd.DataFrame(
            columns=[
                "OrgDefinedId",
                "Username",
                self.assignment_name,
                "End-of-Line Indicator",
            ]
        )

        for i, student in enumerate(classlist):
            assignment_grade = "0.000" if not failure_is_null else ""

            if student.username in results_lookup:
                result = results_lookup[student.username]
                if result.success:
                    assignment_grade = f"{result.grade:.3f}"

            output_df.loc[i] = (  # type: ignore
                student.org_defined_id,
                student.username,
                assignment_grade,
                "#",
            )
        output_df.to_csv(output_path, index=False)


def load_grading_list(
    csv_path: Path, assignment_name: str = "Lab Grade"
) -> pd.DataFrame:
    """
    Load the grading list CSV file and return DataFrame with student records.

    Args:
        csv_path: Path to the CSV file
        assignment_name: Name for the assignment grade column

    Returns:
        DataFrame with student records
    """
    # Load the CSV with the normalized header
    df = pd.read_csv(csv_path)
    df[assignment_name] = pd.Series(dtype="int")

    df["Username"] = df["Username"].astype(str).str.strip("#")
    df["OrgDefinedId"] = df["OrgDefinedId"].astype(str).str.strip("#")

    return df


def save_results_to_csv(
    results: list[GradingResult],
    original_df: pd.DataFrame,
    output_path: Path,
    failure_is_null: bool,
    assignment_name: str = "Lab Grade",
) -> None:
    """
    Save grading results back to a CSV file.

    Args:
        results: List of grading results
        original_df: Original DataFrame
        output_path: Path to save the output CSV
        failure_is_null: Whether to use null for failures instead of 0
        assignment_name: Name for the assignment grade column
    """
    # Create a lookup for results by username
    results_lookup = {
        result.student_record.username: result
        for result in results
        if result.student_record is not None
    }

    # Update the DataFrame with results
    output_df = original_df.copy()

    for idx, row in output_df.iterrows():
        username = str(row["Username"])
        if username in results_lookup:
            result = results_lookup[username]
            if result.success:
                output_df.at[idx, assignment_name] = f"{result.grade:.3f}"
            else:
                if failure_is_null:
                    output_df.at[idx, assignment_name] = ""
                else:
                    output_df.at[idx, assignment_name] = "0.000"
        if username not in results_lookup:
            # If no result found, set to empty or 0 based on failure_is_null
            if failure_is_null:
                output_df.at[idx, assignment_name] = ""
            else:
                output_df.at[idx, assignment_name] = "0.000"
    output_df.drop(["First Name", "Last Name"], axis=1, inplace=True, errors="ignore")

    output_df = output_df[
        ["OrgDefinedId", "Username", assignment_name, "End-of-Line Indicator"]
    ]

    # Save to CSV with header from DataFrame columns
    output_df.to_csv(output_path, index=False)
