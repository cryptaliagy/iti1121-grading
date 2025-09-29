"""Core grading service that orchestrates the grading process."""

from pathlib import Path

from .protocols import TestRunner, PreProcessor

from .code_preprocessing import CodePreProcessor
from .common import GradingResult
from .file_operations import FileHandler
from .test_runner import JavaTestRunner


from .writer import Writer


class GradingService:
    """
    Service class that orchestrates the grading process for a single student.
    """

    def __init__(
        self,
        writer: Writer,
        file_handler: FileHandler | None = None,
        code_preprocessor: PreProcessor | None = None,
        test_runner: TestRunner | None = None,
    ):
        """
        Initialize the grading service.

        Args:
            writer: Writer for output
            file_handler: Optional FileHandler instance. If None, creates a new one.
        """
        self.writer = writer
        self.file_handler = file_handler or FileHandler(writer)

        # By default, uses a CodePreProcessor with no handlers
        self.code_preprocessor = code_preprocessor or CodePreProcessor(writer)

        self.test_runner = test_runner or JavaTestRunner(writer)

    def grade_single_student(
        self,
        grading_dir: Path,
        test_dir: Path,
        prefix: str,
    ) -> GradingResult:
        """
        Grade a single student's submission.

        Args:
            student_record: Student record information
            grading_dir: Directory containing student's code
            test_dir: Directory containing test files
            prefix: Test file prefix
            classpath: Optional classpath entries

        Returns:
            GradingResult with the outcome
        """
        try:
            self.code_preprocessor.preprocess_directory(grading_dir)

            # Find test files
            test_files = self.file_handler.find_test_files(test_dir, prefix)
            self.writer.echo(f"Found {len(test_files)} test files")

            # Copy test files to grading directory
            self.file_handler.copy_test_files(test_files, grading_dir)

            # Compile the test
            compilation_successful = self.test_runner.compile_test(grading_dir, prefix)
            if not compilation_successful:
                return GradingResult(
                    student_record=None,
                    grade=0.0,
                    error_message="Compilation failed",
                    success=False,
                )

            # Run the test
            success, total_points, possible_points = self.test_runner.run_test(
                grading_dir, prefix
            )

            if possible_points > 0:
                grade = total_points / possible_points
            else:
                grade = 0.0

            return GradingResult(student_record=None, grade=grade, success=success)

        except Exception as e:
            return GradingResult(
                student_record=None,
                grade=0.0,
                error_message=str(e),
                success=False,
            )


class BulkGradingService:
    """
    Service class that orchestrates the bulk grading process for multiple students.
    """

    def __init__(self, writer: Writer, grading_service: GradingService):
        """
        Initialize the bulk grading service.

        Args:
            writer: Writer for output
            grading_service: GradingService instance to use for grading
        """
        self.writer = writer
        self.grading_service = grading_service
