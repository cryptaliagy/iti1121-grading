"""Unit tests for submission processor implementations."""

import pytest
import tempfile
import zipfile
from pathlib import Path

from grader.infrastructure.submission_processor import ZipSubmissionProcessor


def create_test_zip(zip_path: Path, files: dict[str, str]) -> None:
    """
    Create a test ZIP file with the given files.

    Args:
        zip_path: Path where the ZIP file should be created
        files: Dictionary mapping file paths (in ZIP) to contents
    """
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file_path, content in files.items():
            zf.writestr(file_path, content)


class TestZipSubmissionProcessor:
    """Test the ZipSubmissionProcessor implementation."""

    def test_extract_submission(self):
        """Test extracting a submission ZIP file."""
        processor = ZipSubmissionProcessor(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a test ZIP file
            zip_path = tmppath / "submissions.zip"
            create_test_zip(
                zip_path,
                {
                    "student1/Test.java": "public class Test {}",
                    "student2/Other.java": "public class Other {}",
                },
            )

            # Extract the submissions
            result = processor.extract_submission(zip_path, tmppath)

            # Check that files were extracted
            assert result.exists()
            assert (result / "student1" / "Test.java").exists()
            assert (result / "student2" / "Other.java").exists()

    def test_extract_submission_nonexistent_file(self):
        """Test extracting a ZIP file that doesn't exist."""
        processor = ZipSubmissionProcessor(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            nonexistent = tmppath / "nonexistent.zip"

            with pytest.raises(FileNotFoundError):
                processor.extract_submission(nonexistent, tmppath)

    def test_prepare_grading_directory_with_java_files(self):
        """Test preparing grading directory with Java files."""
        processor = ZipSubmissionProcessor(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a submission directory with Java files
            submission_dir = tmppath / "student_submission"
            submission_dir.mkdir()
            (submission_dir / "Test.java").write_text("public class Test {}")
            (submission_dir / "Helper.java").write_text("public class Helper {}")

            grading_base = tmppath / "grading"

            # Prepare grading directory
            result = processor.prepare_grading_directory(submission_dir, grading_base)

            # Check that files were copied
            assert result.exists()
            assert (result / "Test.java").exists()
            assert (result / "Helper.java").exists()

    def test_prepare_grading_directory_with_zip_files(self):
        """Test preparing grading directory with ZIP files."""
        processor = ZipSubmissionProcessor(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a submission directory with a ZIP file
            submission_dir = tmppath / "student_submission"
            submission_dir.mkdir()

            zip_path = submission_dir / "code.zip"
            create_test_zip(
                zip_path,
                {
                    "src/Test.java": "public class Test {}",
                    "src/Helper.java": "public class Helper {}",
                    "README.txt": "This is a readme",  # Non-Java file
                },
            )

            grading_base = tmppath / "grading"

            # Prepare grading directory
            result = processor.prepare_grading_directory(submission_dir, grading_base)

            # Check that Java files were extracted (flattened)
            assert result.exists()
            assert (result / "Test.java").exists()
            assert (result / "Helper.java").exists()
            # Non-Java files should be skipped
            assert not (result / "README.txt").exists()
            # Directory structure should be flattened
            assert not (result / "src").exists()

    def test_prepare_grading_directory_with_nested_zip(self):
        """Test preparing grading directory with nested directory structure in ZIP."""
        processor = ZipSubmissionProcessor(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a submission directory with a ZIP file
            submission_dir = tmppath / "student_submission"
            submission_dir.mkdir()

            zip_path = submission_dir / "code.zip"
            create_test_zip(
                zip_path,
                {
                    "assignment/src/main/Test.java": "public class Test {}",
                    "assignment/src/util/Helper.java": "public class Helper {}",
                },
            )

            grading_base = tmppath / "grading"

            # Prepare grading directory
            result = processor.prepare_grading_directory(submission_dir, grading_base)

            # Check that Java files were extracted and flattened
            assert result.exists()
            assert (result / "Test.java").exists()
            assert (result / "Helper.java").exists()
            # Directory structure should be completely flattened
            assert not (result / "assignment").exists()
            assert not (result / "src").exists()

    def test_prepare_grading_directory_no_files(self):
        """Test preparing grading directory with no Java or ZIP files."""
        processor = ZipSubmissionProcessor(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a submission directory with no relevant files
            submission_dir = tmppath / "student_submission"
            submission_dir.mkdir()
            (submission_dir / "README.txt").write_text("This is a readme")

            grading_base = tmppath / "grading"

            # Should raise an error
            with pytest.raises(ValueError):
                processor.prepare_grading_directory(submission_dir, grading_base)

    def test_prepare_grading_directory_nonexistent_submission(self):
        """Test preparing grading directory for nonexistent submission."""
        processor = ZipSubmissionProcessor(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            nonexistent = tmppath / "nonexistent"
            grading_base = tmppath / "grading"

            with pytest.raises(FileNotFoundError):
                processor.prepare_grading_directory(nonexistent, grading_base)

    def test_extract_multiple_zip_files(self):
        """Test preparing grading directory with multiple ZIP files."""
        processor = ZipSubmissionProcessor(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a submission directory with multiple ZIP files
            submission_dir = tmppath / "student_submission"
            submission_dir.mkdir()

            # Create first ZIP
            zip1 = submission_dir / "part1.zip"
            create_test_zip(zip1, {"Test.java": "public class Test {}"})

            # Create second ZIP
            zip2 = submission_dir / "part2.zip"
            create_test_zip(zip2, {"Helper.java": "public class Helper {}"})

            grading_base = tmppath / "grading"

            # Prepare grading directory
            result = processor.prepare_grading_directory(submission_dir, grading_base)

            # Check that files from both ZIPs were extracted
            assert result.exists()
            assert (result / "Test.java").exists()
            assert (result / "Helper.java").exists()

    def test_java_files_take_precedence(self):
        """Test that Java files are used if both Java and ZIP files exist."""
        processor = ZipSubmissionProcessor(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a submission directory with both Java and ZIP files
            submission_dir = tmppath / "student_submission"
            submission_dir.mkdir()

            # Create Java files
            (submission_dir / "Test.java").write_text("public class Test {}")

            # Create ZIP file (should be ignored)
            zip_path = submission_dir / "code.zip"
            create_test_zip(zip_path, {"Other.java": "public class Other {}"})

            grading_base = tmppath / "grading"

            # Prepare grading directory
            result = processor.prepare_grading_directory(submission_dir, grading_base)

            # Check that Java files were copied, not ZIP extracted
            assert result.exists()
            assert (result / "Test.java").exists()
            # File from ZIP should not be present
            assert not (result / "Other.java").exists()
