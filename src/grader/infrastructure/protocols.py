"""Infrastructure protocols for the grading system."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from grader.domain.models import TestRunOutput


@dataclass
class TestRunnerConfig:
    """Configuration for running tests."""

    main_test_file: str
    target_dir: Path
    classpath: list[str] | None = None
    timeout: int | None = None


class FileSystem(Protocol):
    """Protocol for file system operations."""

    def read_file(self, path: Path) -> str:
        """
        Read a file and return its contents.

        Args:
            path: Path to the file to read

        Returns:
            File contents as a string
        """
        ...

    def write_file(self, path: Path, content: str) -> None:
        """
        Write content to a file.

        Args:
            path: Path to the file to write
            content: Content to write to the file
        """
        ...

    def copy_file(self, source: Path, target: Path) -> None:
        """
        Copy a file from source to target.

        Args:
            source: Source file path
            target: Target file path
        """
        ...

    def delete_file(self, path: Path) -> bool:
        """
        Delete a file.

        Args:
            path: Path to the file to delete

        Returns:
            True if successful, False otherwise
        """
        ...

    def list_files(self, directory: Path, pattern: str = "*") -> list[Path]:
        """
        List files in a directory matching a pattern.

        Args:
            directory: Directory to search
            pattern: Glob pattern to match

        Returns:
            List of matching file paths
        """
        ...

    def ensure_directory(self, path: Path) -> None:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            path: Path to the directory
        """
        ...

    def make_writable(self, path: Path) -> None:
        """
        Make a file or directory writable.

        Args:
            path: Path to make writable
        """
        ...


class TestRunner(Protocol):
    """Protocol for compiling and running tests."""

    def compile(self, config: TestRunnerConfig) -> bool:
        """
        Compile the test files.

        Args:
            config: Configuration for compilation

        Returns:
            True if compilation succeeded, False otherwise
        """
        ...

    def run(self, config: TestRunnerConfig) -> TestRunOutput:
        """
        Run the compiled test.

        Args:
            config: Configuration for test execution

        Returns:
            TestRunOutput containing stdout, stderr, exit code, and execution time
        """
        ...


class SubmissionProcessor(Protocol):
    """Protocol for processing student submissions."""

    def extract_submission(self, zip_path: Path, target_dir: Path) -> Path:
        """
        Extract a submission ZIP file.

        Args:
            zip_path: Path to the ZIP file
            target_dir: Directory to extract to

        Returns:
            Path to the extracted submission directory
        """
        ...

    def prepare_grading_directory(
        self, submission_path: Path, grading_dir: Path
    ) -> Path:
        """
        Prepare a grading directory for a submission.

        Args:
            submission_path: Path to the submission
            grading_dir: Base grading directory

        Returns:
            Path to the prepared grading directory
        """
        ...


class CodePreprocessor(Protocol):
    """Protocol for preprocessing code files before compilation."""

    def preprocess(self, code_file: Path) -> None:
        """
        Preprocess a code file (e.g., remove package declarations).

        Args:
            code_file: Path to the code file to preprocess
        """
        ...
