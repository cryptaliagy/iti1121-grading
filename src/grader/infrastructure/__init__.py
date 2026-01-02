"""Infrastructure layer for the grading system."""

from .protocols import (
    CodePreprocessor,
    FileSystem,
    SubmissionProcessor,
    TestRunner,
    TestRunnerConfig,
)
from .filesystem import LocalFileSystem, InMemoryFileSystem
from .test_runner import JavaProcessTestRunner, MockTestRunner
from .preprocessor import (
    PackageRemovalPreprocessor,
    PackageRemovalRule,
    CompositePreprocessor,
)
from .submission_processor import ZipSubmissionProcessor
from .gradebook import CSVGradebookRepository

__all__ = [
    # Protocols
    "CodePreprocessor",
    "FileSystem",
    "SubmissionProcessor",
    "TestRunner",
    "TestRunnerConfig",
    # FileSystem implementations
    "LocalFileSystem",
    "InMemoryFileSystem",
    # TestRunner implementations
    "JavaProcessTestRunner",
    "MockTestRunner",
    # Preprocessor implementations
    "PackageRemovalPreprocessor",
    "PackageRemovalRule",
    "CompositePreprocessor",
    # SubmissionProcessor implementations
    "ZipSubmissionProcessor",
    # Gradebook implementations
    "CSVGradebookRepository",
]
