"""Domain service protocols for the grading system."""

from typing import Protocol
from .models import Student, TestResult


class StudentMatcher(Protocol):
    """Protocol for matching student names to student records."""

    def find_match(
        self, target_name: str, candidates: list[Student], threshold: int = 80
    ) -> Student | None:
        """
        Find the best matching student using fuzzy string matching.

        Args:
            target_name: The name to match against
            candidates: List of candidate students
            threshold: Minimum match score (0-100)

        Returns:
            Best matching student or None if no good match found
        """
        ...


class GradeCalculator(Protocol):
    """Protocol for calculating grades from test results."""

    def calculate_grade(self, test_result: TestResult) -> float:
        """
        Calculate the final grade from a test result.

        Args:
            test_result: The test result containing points

        Returns:
            Final calculated grade
        """
        ...


class TestOutputParser(Protocol):
    """Protocol for parsing test output to extract grades."""

    def parse_output(self, output: str) -> tuple[float, float]:
        """
        Parse the test output to calculate the total grade.

        Args:
            output: The output string from the test execution

        Returns:
            Tuple containing (points_earned, points_possible)
        """
        ...


class GradingStrategy(Protocol):
    """Protocol for different grading strategies."""

    def apply_strategy(self, points_earned: float, points_possible: float) -> float:
        """
        Apply a grading strategy to calculate the final score.

        Args:
            points_earned: Points earned by the student
            points_possible: Maximum possible points

        Returns:
            Final score after applying the strategy
        """
        ...
