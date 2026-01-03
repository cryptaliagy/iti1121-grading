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
from .services import (
    CompositeStudentMatcher,
    CompositeTestOutputParser,
    CustomPatternTestOutputParser,
    DropLowestGradingStrategy,
    ExactStudentMatcher,
    FuzzyStudentMatcher,
    JUnitXMLTestOutputParser,
    RegexTestOutputParser,
    SimpleGradingStrategy,
    WeightedGradingStrategy,
    normalize_name,
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
    # Services
    "CompositeStudentMatcher",
    "CompositeTestOutputParser",
    "CustomPatternTestOutputParser",
    "DropLowestGradingStrategy",
    "ExactStudentMatcher",
    "FuzzyStudentMatcher",
    "JUnitXMLTestOutputParser",
    "RegexTestOutputParser",
    "SimpleGradingStrategy",
    "WeightedGradingStrategy",
    "normalize_name",
]
