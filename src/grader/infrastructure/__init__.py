"""Infrastructure layer for the grading system."""

from .protocols import (
    CodePreprocessor,
    FileSystem,
    SubmissionProcessor,
    TestRunner,
    TestRunnerConfig,
)

__all__ = [
    "CodePreprocessor",
    "FileSystem",
    "SubmissionProcessor",
    "TestRunner",
    "TestRunnerConfig",
]
