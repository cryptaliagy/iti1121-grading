"""Submission processing utilities."""

import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from .common import FileOperationError, Submission, StudentRecord
from .name_matching import Matcher
from .writer import Writer


class SubmissionProcessor:
    def __init__(self, writer: Writer | None = None, matcher: Matcher | None = None):
        """
        Initialize the submission processor.

        Args:
            writer: Writer for output
            matcher: Matcher for name normalization and matching
        """
        self.writer = writer if writer else Writer()
        self.matcher = matcher if matcher else Matcher()

    def parse_submission_folder_name(self, folder_name: str) -> tuple[str, datetime]:
        """
        Parse submission folder name to extract student name and timestamp.

        Expected format: "<ignored>-<ignored> - <names> - <month> <day>, <year> <time> <AM/PM>"
        Example: "152711-351765 - John Doe - May 18, 2025 1224 PM"

        Args:
            folder_name: The folder name to parse

        Returns:
            Tuple of (student_name, timestamp)

        Raises:
            ValueError: If folder name doesn't match expected format
        """
        # Pattern to match the folder name format
        pattern = (
            r"^\d+-\d+\s*-\s*(.+?)\s*-\s*(\w+)\s+(\d+),\s*(\d+)\s+(\d+)\s*(AM|PM)$"
        )

        match = re.match(pattern, folder_name)
        if not match:
            raise ValueError(
                f"Folder name '{folder_name}' doesn't match expected format"
            )

        student_name = match.group(1).strip()
        month_str = match.group(2)
        day = int(match.group(3))
        year = int(match.group(4))
        time_str = match.group(5)
        am_pm = match.group(6)

        # Parse time
        if len(time_str) == 3:
            # Format like "130" -> "1:30"
            hour = int(time_str[0])
            minute = int(time_str[1:3])
        elif len(time_str) == 4:
            # Format like "1224" -> "12:24"
            hour = int(time_str[0:2])
            minute = int(time_str[2:4])
        else:
            raise ValueError(f"Invalid time format: {time_str}")

        # Convert to 24-hour format
        if am_pm == "PM" and hour != 12:
            hour += 12
        elif am_pm == "AM" and hour == 12:
            hour = 0

        # Parse month
        month_mapping = {
            "January": 1,
            "February": 2,
            "March": 3,
            "April": 4,
            "May": 5,
            "June": 6,
            "July": 7,
            "August": 8,
            "September": 9,
            "October": 10,
            "November": 11,
            "December": 12,
            "Jan": 1,
            "Feb": 2,
            "Mar": 3,
            "Apr": 4,
            "Jun": 6,
            "Jul": 7,
            "Aug": 8,
            "Sep": 9,
            "Oct": 10,
            "Nov": 11,
            "Dec": 12,
        }

        month = month_mapping.get(month_str)
        if month is None:
            raise ValueError(f"Unknown month: {month_str}")

        timestamp = datetime(year, month, day, hour, minute)

        return student_name, timestamp

    def extract_submissions(self, zip_path: Path, temp_dir: Path) -> Path:
        """
        Extract the main submissions ZIP file.

        Args:
            zip_path: Path to the submissions ZIP file
            temp_dir: Temporary directory to extract to

        Returns:
            Path to the extracted submissions directory
        """
        submissions_dir = temp_dir / "submissions"
        submissions_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(submissions_dir)

        return submissions_dir

    def find_latest_submissions(
        self,
        submissions_dir: Path,
        grading_df,  # pandas DataFrame
    ) -> dict[str, tuple[StudentRecord, Path]]:
        """
        Find the latest submission for each student.

        Args:
            submissions_dir: Directory containing all submissions
            grading_df: DataFrame with student records

        Returns:
            Dictionary mapping student names to (StudentRecord, submission_path)
        """
        submissions: dict[str, list[Submission]] = {}
        student_records = {}

        # Create student records lookup
        for _, row in grading_df.iterrows():
            record = StudentRecord(
                org_defined_id=str(row["OrgDefinedId"]),
                username=str(row["Username"]),
                last_name=str(row["Last Name"]),
                first_name=str(row["First Name"]),
                original_grade=None,
            )
            record.normalize()
            full_name = f"{record.first_name} {record.last_name}"
            student_records[self.matcher.normalize_name(full_name)] = record

        # Parse all submission folders
        for folder in submissions_dir.iterdir():
            if folder.is_dir():
                try:
                    student_name, timestamp = self.parse_submission_folder_name(
                        folder.name
                    )
                    submission = Submission(student_name, timestamp, folder)

                    # Normalize student name for matching
                    normalized_name = self.matcher.normalize_name(student_name)
                    if normalized_name not in submissions:
                        submissions[normalized_name] = []
                    submissions[normalized_name].append(submission)

                except ValueError as e:
                    self.writer.always_echo(
                        f"[yellow]Warning:[/yellow] Skipping folder '{folder.name}': {e}"
                    )
                    continue

        # Find latest submission for each student and match with records
        latest_submissions = {}

        for normalized_submission_name, submission_list in submissions.items():
            # Find the latest submission
            latest = max(submission_list, key=lambda s: s.timestamp)

            # Try to match with a student record
            best_match = self.matcher.find_best_name_match(
                latest.student_name,
                [
                    record.first_name + " " + record.last_name
                    for record in student_records.values()
                ],
            )

            if best_match:
                normalized_match = self.matcher.normalize_name(best_match)
                if normalized_match in student_records:
                    student_record = student_records[normalized_match]
                    latest_submissions[normalized_submission_name] = (
                        student_record,
                        latest.folder_path,
                    )
                    self.writer.echo(
                        f"Matched '{latest.student_name}' to '{best_match}' (latest: {latest.timestamp})"
                    )
                else:
                    self.writer.always_echo(
                        f"[yellow]Warning:[/yellow] Could not find student record for '{latest.student_name}'"
                    )
            else:
                self.writer.always_echo(
                    f"[yellow]Warning:[/yellow] Could not match submission '{latest.student_name}' to any student record"
                )

        return latest_submissions

    def prepare_grading_directory(
        self,
        submission_path: Path,
        temp_dir: Path,
    ) -> Path:
        """
        Prepare the grading directory from a submission folder.

        Args:
            submission_path: Path to the student's submission folder
            temp_dir: Temporary directory for processing
            writer: Writer for output

        Returns:
            Path to the prepared grading directory
        """
        grading_dir = temp_dir / "grading" / submission_path.name
        grading_dir.mkdir(parents=True, exist_ok=True)

        # Find all files in the submission
        zip_files = list(submission_path.glob("*.zip"))
        java_files = list(submission_path.glob("*.java"))

        if not zip_files and not java_files:
            raise FileOperationError(
                f"No ZIP or Java files found in submission: {submission_path}"
            )

        if java_files:
            # Copy Java files directly
            self.writer.echo(f"Found {len(java_files)} Java files in submission")
            for java_file in java_files:
                target_path = grading_dir / java_file.name
                shutil.copy2(java_file, target_path)
                self.writer.echo(f"  Copied {java_file.name}")

            return grading_dir

        # Extract all ZIP files to the grading directory
        self.writer.echo(f"Found {len(zip_files)} ZIP files in submission")
        for zip_file in zip_files:
            self.writer.echo(f"Extracting {zip_file.name}")
            self.extract_zipfile(grading_dir, zip_file)

        return grading_dir

    def extract_zipfile(self, grading_dir: Path, zip_file: Path):
        """
        Extract a ZIP file to the grading directory.

        Args:
            writer: Writer for output
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
                self.writer.echo(f"  Extracted {filename}")
