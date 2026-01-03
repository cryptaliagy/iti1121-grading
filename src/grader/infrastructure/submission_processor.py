"""Submission processor implementations for extracting and preparing student submissions."""

import shutil
import zipfile
from pathlib import Path


class ZipSubmissionProcessor:
    """Processor for extracting and preparing ZIP file submissions."""

    def __init__(self, verbose: bool = True):
        """
        Initialize the ZIP submission processor.

        Args:
            verbose: Whether to print detailed output
        """
        self.verbose = verbose

    def extract_submission(self, zip_path: Path, target_dir: Path) -> Path:
        """
        Extract a submission ZIP file.

        Args:
            zip_path: Path to the ZIP file
            target_dir: Directory to extract to

        Returns:
            Path to the extracted submission directory

        Raises:
            FileNotFoundError: If ZIP file doesn't exist
            zipfile.BadZipFile: If file is not a valid ZIP
        """
        if not zip_path.exists():
            raise FileNotFoundError(f"ZIP file {zip_path} does not exist")

        submissions_dir = target_dir / "submissions"
        submissions_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(submissions_dir)

        if self.verbose:
            print(f"Extracted {zip_path} to {submissions_dir}")

        return submissions_dir

    def prepare_grading_directory(
        self, submission_path: Path, grading_dir: Path
    ) -> Path:
        """
        Prepare a grading directory for a submission.

        This method:
        1. Creates the grading directory structure
        2. Finds Java files or ZIP files in the submission
        3. Copies Java files directly or extracts from ZIPs
        4. Flattens directory structure for grading

        Args:
            submission_path: Path to the submission folder
            grading_dir: Base grading directory

        Returns:
            Path to the prepared grading directory

        Raises:
            FileNotFoundError: If submission path doesn't exist
            ValueError: If no Java or ZIP files found
        """
        if not submission_path.exists():
            raise FileNotFoundError(f"Submission path {submission_path} does not exist")

        # Create grading directory for this submission
        target_dir = grading_dir / submission_path.name
        target_dir.mkdir(parents=True, exist_ok=True)

        # Find all files in the submission
        zip_files = list(submission_path.glob("*.zip"))
        java_files = list(submission_path.glob("*.java"))

        if not zip_files and not java_files:
            raise ValueError(
                f"No ZIP or Java files found in submission: {submission_path}"
            )

        if java_files:
            # Copy Java files directly
            if self.verbose:
                print(f"Found {len(java_files)} Java files in submission")
            for java_file in java_files:
                target_path = target_dir / java_file.name
                shutil.copy2(java_file, target_path)
                if self.verbose:
                    print(f"  Copied {java_file.name}")

            return target_dir

        # Extract all ZIP files to the grading directory
        if self.verbose:
            print(f"Found {len(zip_files)} ZIP files in submission")
        for zip_file in zip_files:
            if self.verbose:
                print(f"Extracting {zip_file.name}")
            self._extract_zipfile_flattened(target_dir, zip_file)

        return target_dir

    def _extract_zipfile_flattened(self, grading_dir: Path, zip_file: Path) -> None:
        """
        Extract a ZIP file to the grading directory with flattened structure.

        Only extracts .java files, ignoring directory structure.

        Args:
            grading_dir: Directory to extract files into
            zip_file: Path to the ZIP file to extract
        """
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            # Extract all files, flattening directory structure
            for member in zip_ref.infolist():
                if member.is_dir() or not member.filename.endswith(".java"):
                    # Skip directories and non-Java files
                    continue

                # Get just the filename, ignore directory structure
                filename = Path(member.filename).name
                target_path = grading_dir / filename

                # Extract to target path
                with (
                    zip_ref.open(member) as source,
                    open(target_path, "wb") as target,
                ):
                    target.write(source.read())

                if self.verbose:
                    print(f"  Extracted {filename}")
