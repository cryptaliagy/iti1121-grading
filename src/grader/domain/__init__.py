"""Domain layer for the grading system."""

from .models import (
    GradingResult,
    Student,
    StudentId,
    Submission,
    TestResult,
    TestRunOutput,
)
from .protocols import (
    GradeCalculator,
    GradingStrategy,
    StudentMatcher,
    TestOutputParser,
)

__all__ = [
    # Models
    "GradingResult",
    "Student",
    "StudentId",
    "Submission",
    "TestResult",
    "TestRunOutput",
    # Protocols
    "GradeCalculator",
    "GradingStrategy",
    "StudentMatcher",
    "TestOutputParser",
]
