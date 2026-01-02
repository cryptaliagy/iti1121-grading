"""Application protocols for the grading system."""

from pathlib import Path
from typing import Protocol

from grader.domain.models import GradingResult, Student, Submission


class GradingOrchestrator(Protocol):
    """Protocol for orchestrating the grading of a single submission."""

    def grade_submission(
        self, submission: Submission, test_files: list[Path]
    ) -> GradingResult:
        """
        Grade a single student submission.

        Args:
            submission: The submission to grade
            test_files: List of test files to use

        Returns:
            GradingResult containing the grade and any errors
        """
        ...


class BulkGradingOrchestrator(Protocol):
    """Protocol for orchestrating bulk grading of multiple submissions."""

    def grade_all_submissions(
        self,
        submissions_path: Path,
        students: list[Student],
        test_files: list[Path],
    ) -> list[GradingResult]:
        """
        Grade all submissions for a list of students.

        Args:
            submissions_path: Path to the directory containing submissions
            students: List of students to grade
            test_files: List of test files to use

        Returns:
            List of GradingResults
        """
        ...


class ResultPublisher(Protocol):
    """Protocol for publishing grading results."""

    def publish_results(self, results: list[GradingResult]) -> None:
        """
        Publish the grading results.

        Args:
            results: List of grading results to publish
        """
        ...
