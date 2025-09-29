"""Test cases for GradingService class."""

from pathlib import Path
from unittest.mock import Mock
from tempfile import TemporaryDirectory

from grader.grading_service import GradingService
from grader.common import StudentRecord
from grader.writer import Writer
from grader.test_runner import JavaTestRunner
from grader.code_preprocessing import CodePreProcessor
from grader.file_operations import FileHandler


class TestGradingService:
    """Test cases for GradingService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_writer = Mock(spec=Writer)
        self.mock_file_handler = Mock(spec=FileHandler)
        self.mock_preprocessor = Mock(spec=CodePreProcessor)
        self.mock_runner = Mock(spec=JavaTestRunner)
        self.service = GradingService(
            self.mock_writer,
            self.mock_file_handler,
            self.mock_preprocessor,
            self.mock_runner,
        )

        self.student_record = StudentRecord(
            org_defined_id="123456",
            username="jdoe001",
            last_name="Doe",
            first_name="John",
        )

    def test_grading_service_creation(self):
        """Test GradingService creation."""
        assert self.service.writer is self.mock_writer
        assert self.service.file_handler is self.mock_file_handler

        # Test creation with default FileHandler
        service_with_default = GradingService(self.mock_writer)
        assert service_with_default.writer is self.mock_writer
        assert service_with_default.file_handler is not None
        assert service_with_default.code_preprocessor is not None
        assert service_with_default.test_runner is not None

    def test_grade_student_success(self):
        """Test successful student grading."""
        # Setup mocks
        self.mock_file_handler.find_test_files.return_value = [Path("/tmp/test1.java")]
        self.mock_runner.compile_test.return_value = True
        self.mock_runner.run_test.return_value = (True, 8.5, 10.0)

        with TemporaryDirectory() as temp_dir:
            grading_dir = Path(temp_dir) / "grading"
            grading_dir.mkdir()
            test_dir = Path(temp_dir) / "test"
            test_dir.mkdir()

            result = self.service.grade_single_student(
                grading_dir=grading_dir,
                test_dir=test_dir,
                prefix="TestL1",
            )

            assert result.success is True
            assert result.grade == 0.85
            assert result.error_message is None
            assert result.student_record is None

            # Verify that FileHandler methods were called correctly
            self.mock_file_handler.find_test_files.assert_called_once_with(
                test_dir, "TestL1"
            )
            self.mock_file_handler.copy_test_files.assert_called_once_with(
                [Path("/tmp/test1.java")], grading_dir
            )

    def test_grade_student_compilation_failure(self):
        """Test student grading with compilation failure."""
        # Setup mocks
        self.mock_file_handler.find_test_files.return_value = [Path("/tmp/test1.java")]
        self.mock_runner.compile_test.return_value = False

        with TemporaryDirectory() as temp_dir:
            grading_dir = Path(temp_dir) / "grading"
            grading_dir.mkdir()
            test_dir = Path(temp_dir) / "test"
            test_dir.mkdir()

            result = self.service.grade_single_student(
                grading_dir=grading_dir,
                test_dir=test_dir,
                prefix="TestL1",
            )

            assert result.success is False
            assert result.grade == 0.0
            assert result.error_message == "Compilation failed"
            assert result.student_record is None

    def test_grade_student_zero_possible_points(self):
        """Test student grading with zero possible points."""
        # Setup mocks
        self.mock_file_handler.find_test_files.return_value = [Path("/tmp/test1.java")]
        self.mock_runner.compile_test.return_value = True
        self.mock_runner.run_test.return_value = (True, 0.0, 0.0)

        with TemporaryDirectory() as temp_dir:
            grading_dir = Path(temp_dir) / "grading"
            grading_dir.mkdir()
            test_dir = Path(temp_dir) / "test"
            test_dir.mkdir()

            result = self.service.grade_single_student(
                grading_dir=grading_dir,
                test_dir=test_dir,
                prefix="TestL1",
            )

            assert result.success is True
            assert result.grade == 0.0
            assert result.error_message is None
            assert result.student_record is None

    def test_grade_student_exception_handling(self):
        """Test student grading with exception handling."""
        # Setup mock to raise exception
        self.mock_file_handler.find_test_files.side_effect = Exception("Test exception")

        with TemporaryDirectory() as temp_dir:
            grading_dir = Path(temp_dir) / "grading"
            grading_dir.mkdir()
            test_dir = Path(temp_dir) / "test"
            test_dir.mkdir()

            result = self.service.grade_single_student(
                grading_dir=grading_dir,
                test_dir=test_dir,
                prefix="TestL1",
            )

            assert result.success is False
            assert result.grade == 0.0
            assert result.error_message == "Test exception"
            assert result.student_record is None

    def test_grade_student_writer_calls(self):
        """Test that writer methods are called appropriately."""
        # Setup mocks so that find_test_files succeeds and writer.echo is called
        self.mock_file_handler.find_test_files.return_value = [Path("/tmp/test1.java")]
        self.mock_runner.compile_test.return_value = (
            False  # This will cause early return
        )

        with TemporaryDirectory() as temp_dir:
            grading_dir = Path(temp_dir) / "grading"
            grading_dir.mkdir()
            test_dir = Path(temp_dir) / "test"
            test_dir.mkdir()

            self.service.grade_single_student(
                grading_dir=grading_dir,
                test_dir=test_dir,
                prefix="TestL1",
            )

            # Verify writer was called with test file count info
            self.mock_writer.echo.assert_called_with("Found 1 test files")
