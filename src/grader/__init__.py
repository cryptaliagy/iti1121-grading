"""Java test runner and grader for ITI 1121."""

__version__ = "0.1.0"

from .common import (
    FileOperationError,
    StudentRecord,
    GradingResult,
    Submission,
)
from .writer import Writer
from .file_operations import (
    FileHandler,
)
from .test_runner import (
    JavaTestRunner,
)
from .code_preprocessing import (
    CodePreProcessor,
    PackageDeclarationHandler,
)
from .grading_service import GradingService
from .grader import main
from .protocols import (
    TestRunner,
    PreProcessor,
    PreProcessingHandler,
)

__all__ = [
    "FileOperationError",
    "StudentRecord",
    "GradingResult",
    "Submission",
    "Writer",
    "FileHandler",
    "JavaTestRunner",
    "CodePreProcessor",
    "PackageDeclarationHandler",
    "TestRunner",
    "PreProcessor",
    "PreProcessingHandler",
    "GradingService",
    "main",
]
