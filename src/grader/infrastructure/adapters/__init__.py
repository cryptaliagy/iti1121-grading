"""Infrastructure adapters for the grading system."""

from .legacy_filesystem import LegacyFileSystemAdapter
from .legacy_preprocessor import LegacyCodePreprocessorAdapter
from .legacy_test_runner import LegacyTestRunnerAdapter

__all__ = [
    "LegacyFileSystemAdapter",
    "LegacyCodePreprocessorAdapter",
    "LegacyTestRunnerAdapter",
]
