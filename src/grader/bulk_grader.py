#!/usr/bin/env python3

import re
import shutil
import tempfile
import zipfile
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
import typer

from ._grader import (
    Writer,
    compile_test,
    copy_test_files,
    find_test_files,
    run_test,
    FileOperationError,
    preprocess_codefile,
    CodeFilePreprocessingOptions,
    collect_code_files,
)
from .domain import normalize_name as domain_normalize_name
from .domain import FuzzyStudentMatcher, Student, StudentId

app = typer.Typer(help="Bulk grader for processing multiple student submissions")


@dataclass
class StudentRecord:
    """Represents a student record from the CSV file."""

    org_defined_id: str
    username: str
    last_name: str
    first_name: str
    original_grade: str | None = None

    def normalize(self):
        """
        Remove invalid character from username and org defined id
        """
        self.username = self.username.replace("#", "").replace(" ", "")
        self.org_defined_id = self.org_defined_id.replace("#", "").replace(" ", "")


@dataclass
class Submission:
    """Represents a student submission with metadata."""

    student_name: str
    timestamp: datetime
    folder_path: Path


@dataclass
class GradingResult:
    """Represents the result of grading a student's submission."""

    student_record: StudentRecord
    grade: float | None
    error_message: str | None = None
    success: bool = True


def load_grading_list(
    csv_path: Path, assignment_name: str = "Lab Grade"
) -> pd.DataFrame:
    """
    Load the grading list CSV file and return DataFrame with student records.

    Args:
        csv_path: Path to the CSV file
        assignment_name: Name for the assignment grade column

    Returns:
        DataFrame with student records
    """
    # Load the CSV with the normalized header
    df = pd.read_csv(csv_path)
    df[assignment_name] = pd.Series(dtype="int")

    df["Username"] = df["Username"].astype(str).str.strip("#")
    df["OrgDefinedId"] = df["OrgDefinedId"].astype(str).str.strip("#")

    return df


def parse_submission_folder_name(folder_name: str) -> tuple[str, datetime]:
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
    pattern = r"^\d+-\d+\s*-\s*(.+?)\s*-\s*(\w+)\s+(\d+),\s*(\d+)\s+(\d+)\s*(AM|PM)$"

    match = re.match(pattern, folder_name)
    if not match:
        raise ValueError(f"Folder name '{folder_name}' doesn't match expected format")

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


def normalize_name(name: str) -> str:
    """
    Normalize a name for comparison by removing accents and converting to lowercase.

    This is a backward-compatible wrapper around the domain service implementation.
    New code should import from grader.domain.services instead.

    Args:
        name: The name to normalize

    Returns:
        Normalized name

    See Also:
        grader.domain.services.normalize_name: Domain service implementation
    """
    return domain_normalize_name(name)


def find_best_name_match(
    target_name: str, candidate_names: list[str], threshold: int = 80
) -> str | None:
    """
    Find the best matching name using fuzzy string matching.

    This is a backward-compatible wrapper around the domain service implementation.
    New code should use FuzzyStudentMatcher from grader.domain.services instead.

    Args:
        target_name: The name to match against
        candidate_names: List of candidate names
        threshold: Minimum match score (0-100)

    Returns:
        Best matching name or None if no good match found

    See Also:
        grader.domain.services.FuzzyStudentMatcher: Domain service implementation
    """
    # Create temporary Student objects for matching
    candidates = [
        Student(
            StudentId(str(i), f"temp_{i}"),
            first_name=name.split()[0] if name.split() else name,
            last_name=" ".join(name.split()[1:]) if len(name.split()) > 1 else "",
        )
        for i, name in enumerate(candidate_names)
    ]

    matcher = FuzzyStudentMatcher()
    result = matcher.find_match(target_name, candidates, threshold)

    if result is not None:
        # Find the original name
        idx = int(result.student_id.org_defined_id)
        return candidate_names[idx]

    return None


def extract_submissions(zip_path: Path, temp_dir: Path) -> Path:
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
    submissions_dir: Path,
    grading_df: pd.DataFrame,
    writer: Writer,
) -> dict[str, tuple[StudentRecord, Path]]:
    """
    Find the latest submission for each student.

    Args:
        submissions_dir: Directory containing all submissions
        grading_df: DataFrame with student records
        writer: Writer for output

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
        student_records[normalize_name(full_name)] = record

    # Parse all submission folders
    for folder in submissions_dir.iterdir():
        if folder.is_dir():
            try:
                student_name, timestamp = parse_submission_folder_name(folder.name)
                submission = Submission(student_name, timestamp, folder)

                # Normalize student name for matching
                normalized_name = normalize_name(student_name)
                if normalized_name not in submissions:
                    submissions[normalized_name] = []
                submissions[normalized_name].append(submission)

            except ValueError as e:
                writer.always_echo(
                    f"[yellow]Warning:[/yellow] Skipping folder '{folder.name}': {e}"
                )
                continue

    # Find latest submission for each student and match with records
    latest_submissions = {}

    for normalized_submission_name, submission_list in submissions.items():
        # Find the latest submission
        latest = max(submission_list, key=lambda s: s.timestamp)

        # Try to match with a student record
        best_match = find_best_name_match(
            latest.student_name,
            [
                record.first_name + " " + record.last_name
                for record in student_records.values()
            ],
        )

        if best_match:
            normalized_match = normalize_name(best_match)
            if normalized_match in student_records:
                student_record = student_records[normalized_match]
                latest_submissions[normalized_submission_name] = (
                    student_record,
                    latest.folder_path,
                )
                writer.echo(
                    f"Matched '{latest.student_name}' to '{best_match}' (latest: {latest.timestamp})"
                )
            else:
                writer.always_echo(
                    f"[yellow]Warning:[/yellow] Could not find student record for '{latest.student_name}'"
                )
        else:
            writer.always_echo(
                f"[yellow]Warning:[/yellow] Could not match submission '{latest.student_name}' to any student record"
            )

    return latest_submissions


def prepare_grading_directory(
    submission_path: Path, temp_dir: Path, writer: Writer
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
        writer.echo(f"Found {len(java_files)} Java files in submission")
        for java_file in java_files:
            target_path = grading_dir / java_file.name
            shutil.copy2(java_file, target_path)
            writer.echo(f"  Copied {java_file.name}")

        return grading_dir

    # Extract all ZIP files to the grading directory
    writer.echo(f"Found {len(zip_files)} ZIP files in submission")
    for zip_file in zip_files:
        writer.echo(f"Extracting {zip_file.name}")
        extract_zipfile(writer, grading_dir, zip_file)

    return grading_dir


def extract_zipfile(writer: Writer, grading_dir: Path, zip_file: Path):
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
            writer.echo(f"  Extracted {filename}")


def run_grader_for_student(
    student_record: StudentRecord,
    grading_dir: Path,
    test_dir: Path,
    prefix: str,
    classpath: list[str] | None,
    writer: Writer,
    should_preprocess: bool = False,
) -> GradingResult:
    """
    Run the grader for a single student.

    Args:
        student_record: Student record information
        grading_dir: Directory containing student's code
        test_dir: Directory containing test files
        prefix: Test file prefix
        classpath: Optional classpath entries
        writer: Writer for output
        should_preprocess: Whether to preprocess code files before grading

    Returns:
        GradingResult with the outcome
    """
    try:
        writer.always_echo(f"\n{'=' * 60}")
        writer.always_echo(
            f"Grading: {student_record.first_name} {student_record.last_name} ({student_record.username})"
        )
        writer.always_echo(f"{'=' * 60}")

        # Preprocess code files if enabled
        if should_preprocess:
            code_files = collect_code_files(grading_dir, writer)
            options = CodeFilePreprocessingOptions()
            for code_file in code_files:
                preprocess_codefile(options, code_file, writer)

        # Find test files
        test_files = find_test_files(test_dir, prefix, writer)

        # Copy test files to grading directory
        copy_test_files(test_files, grading_dir, writer)

        # Compile the test
        compilation_successful = compile_test(prefix, grading_dir, writer, classpath)
        if not compilation_successful:
            return GradingResult(
                student_record=student_record,
                grade=0.0,
                error_message="Compilation failed",
                success=False,
            )

        # Run the test
        success, total_points, possible_points = run_test(
            prefix, grading_dir, writer, classpath
        )

        if possible_points > 0:
            grade = total_points / possible_points
        else:
            grade = 0.0

        return GradingResult(
            student_record=student_record, grade=grade, success=success
        )

    except Exception as e:
        return GradingResult(
            student_record=student_record,
            grade=0.0,
            error_message=str(e),
            success=False,
        )


def save_results_to_csv(
    results: list[GradingResult],
    original_df: pd.DataFrame,
    output_path: Path,
    failure_is_null: bool,
    assignment_name: str = "Lab Grade",
) -> None:
    """
    Save grading results back to a CSV file.

    Args:
        results: List of grading results
        original_df: Original DataFrame
        output_path: Path to save the output CSV
        failure_is_null: Whether to use null for failures instead of 0
        assignment_name: Name for the assignment grade column
    """
    # Create a lookup for results by username
    results_lookup = {result.student_record.username: result for result in results}

    # Update the DataFrame with results
    output_df = original_df.copy()

    for idx, row in output_df.iterrows():
        username = str(row["Username"])
        if username in results_lookup:
            result = results_lookup[username]
            if result.success:
                output_df.at[idx, assignment_name] = f"{result.grade:.3f}"
            else:
                if failure_is_null:
                    output_df.at[idx, assignment_name] = ""
                else:
                    output_df.at[idx, assignment_name] = "0.000"
        if username not in results_lookup:
            # If no result found, set to empty or 0 based on failure_is_null
            if failure_is_null:
                output_df.at[idx, assignment_name] = ""
            else:
                output_df.at[idx, assignment_name] = "0.000"
    output_df.drop(["First Name", "Last Name"], axis=1, inplace=True, errors="ignore")

    output_df = output_df[
        ["OrgDefinedId", "Username", assignment_name, "End-of-Line Indicator"]
    ]

    # Save to CSV with header from DataFrame columns
    output_df.to_csv(output_path, index=False)


@app.command(name="bulk")
def main(
    submissions: str = typer.Option(
        ...,
        "--submissions",
        "-s",
        help="Path to ZIP file containing all student submissions",
    ),
    grading_list: str = typer.Option(
        ..., "--grading-list", "-g", help="Path to CSV file with student grading list"
    ),
    test_dir: str = typer.Option(
        ..., "--test-dir", "-t", help="Directory containing test files"
    ),
    prefix: str = typer.Option(
        ...,
        "--prefix",
        "-p",
        help="Prefix of test files to search for (e.g., 'TestL3')",
    ),
    output: str = typer.Option(
        "graded_results.csv", "--output", "-o", help="Output CSV file path"
    ),
    assignment_name: str = typer.Option(
        "Lab Grade",
        "--assignment-name",
        "-a",
        help="Name for the assignment grade column",
    ),
    classpath: list[str] | None = typer.Option(
        None,
        "--classpath",
        "-cp",
        help="Additional classpath entries (can be specified multiple times)",
    ),
    failure_is_null: bool = typer.Option(
        False,
        "--failure-is-null",
        "-F",
        help="Use null/empty for failures instead of 0",
    ),
    verbose: bool = typer.Option(
        False, "--verbose/--quiet", "-v/-q", help="Control verbosity of output"
    ),
    grade_only: int | None = typer.Option(
        None,
        "--grade-only",
        "-G",
        help="A debug option to test the grading script. Limits the number of students to grade, if set.",
    ),
    preprocess_code: bool = typer.Option(
        False,
        "--preprocess-code",
        "-P",
        help="Preprocess code files before grading (e.g. remove package statements)",
    ),
) -> None:
    """
    Bulk grader for processing multiple student submissions.

    This tool processes a ZIP file containing student submissions, grades each submission
    using the specified test files, and outputs results to a CSV file.

    The grading list CSV should be exported from the gradebook using:
    - Sort by: Student Number, Username, First Name, Last Name
    - Include: Last Name, First Name as User Details
    - Export with both username and student number as keys
    """
    writer = Writer(verbose)

    try:
        # Convert paths to Path objects
        submissions_path = Path(submissions).resolve()
        grading_list_path = Path(grading_list).resolve()
        test_dir_path = Path(test_dir).resolve()
        output_path = Path(output).resolve()

        writer.always_echo("🎓 Starting bulk grading process...")

        if preprocess_code:
            writer.always_echo(
                "🔧 Preprocessing code files before grading is enabled. "
                "This will remove package statements and other unnecessary parts."
            )

        writer.always_echo(f"Submissions: {submissions_path}")
        writer.always_echo(f"Grading list: {grading_list_path}")
        writer.always_echo(f"Test directory: {test_dir_path}")
        writer.always_echo(f"Output: {output_path}")

        # Validate input files
        if not submissions_path.exists():
            raise FileOperationError(f"Submissions file not found: {submissions_path}")
        if not grading_list_path.exists():
            raise FileOperationError(
                f"Grading list file not found: {grading_list_path}"
            )
        if not test_dir_path.exists():
            raise FileOperationError(f"Test directory not found: {test_dir_path}")

        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            writer.echo(f"Using temporary directory: {temp_path}")

            # Load grading list
            writer.always_echo("\n📋 Loading grading list...")
            grading_df = load_grading_list(grading_list_path, assignment_name)
            writer.always_echo(f"Loaded {len(grading_df)} students from grading list")

            # Extract submissions
            writer.always_echo("\n📦 Extracting submissions...")
            submissions_dir = extract_submissions(submissions_path, temp_path)

            # Find latest submissions for each student
            writer.always_echo("\n🔍 Finding latest submissions...")
            latest_submissions = find_latest_submissions(
                submissions_dir,
                grading_df,
                writer,
            )
            writer.always_echo(
                f"Found submissions for {len(latest_submissions)} students"
            )

            # Process classpath
            resolved_classpath = None
            if classpath:
                resolved_classpath = []
                for cp_entry in classpath:
                    cp_path = Path(cp_entry).resolve()
                    if not cp_path.exists():
                        raise FileOperationError(
                            f"Classpath entry '{cp_entry}' does not exist"
                        )
                    resolved_classpath.append(str(cp_path))
                writer.echo(f"Classpath entries: {resolved_classpath}")

            # Grade each submission
            writer.always_echo("\n⚡ Starting grading process...")
            results = []

            for i, (
                submission_name,
                (
                    student_record,
                    submission_path,
                ),
            ) in enumerate(latest_submissions.items()):
                if grade_only is not None and i >= grade_only:
                    writer.always_echo(
                        f"🔚 Reached grade limit of {grade_only} students, stopping grading."
                    )
                    break
                try:
                    # Prepare grading directory
                    grading_dir = prepare_grading_directory(
                        submission_path, temp_path, writer
                    )

                    # Run grader
                    result = run_grader_for_student(
                        student_record,
                        grading_dir,
                        test_dir_path,
                        prefix,
                        resolved_classpath,
                        writer,
                        should_preprocess=preprocess_code,
                    )
                    results.append(result)

                    # Show result summary
                    if result.success and result.grade:
                        percentage = (
                            result.grade * 100 if result.grade is not None else 0.0
                        )
                        writer.always_echo(f"✅ Grade: {percentage:.1f}%")
                    else:
                        if result.error_message is None:
                            writer.always_echo("❌ Failed: No grade available")
                        else:
                            writer.always_echo(f"❌ Failed: {result.error_message}")

                except Exception as e:
                    writer.always_echo(
                        f"❌ Error processing {student_record.username}: {e}"
                    )
                    results.append(
                        GradingResult(
                            student_record=student_record,
                            grade=0.0,
                            error_message=str(e),
                            success=False,
                        )
                    )

            # Save results
            writer.always_echo(f"\n💾 Saving results to {output_path}...")
            save_results_to_csv(
                results, grading_df, output_path, failure_is_null, assignment_name
            )

            # Generate post-grading report
            writer.always_echo("\n📊 Generating post-grading report...")
            generate_post_grading_report(
                results, grading_df, latest_submissions, writer
            )

            # Summary
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            avg_grade = sum(
                r.grade if r.grade is not None else 0 for r in results if r.success
            ) / max(successful, 1)

            writer.always_echo("\n" + "=" * 60)
            writer.always_echo("📊 GRADING SUMMARY")
            writer.always_echo("=" * 60)
            writer.always_echo(f"Total submissions processed: {len(results)}")
            writer.always_echo(f"Successful: {successful}")
            writer.always_echo(f"Failed: {failed}")
            if successful > 0:
                writer.always_echo(f"Average grade: {avg_grade * 100:.1f}%")
            writer.always_echo(f"Results saved to: {output_path}")
            writer.always_echo("=" * 60)

    except FileOperationError as e:
        writer.always_echo(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        writer.always_echo(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            import traceback

            writer.always_echo(traceback.format_exc())
        raise typer.Exit(1)


def generate_post_grading_report(
    results: list[GradingResult],
    grading_df: pd.DataFrame,
    latest_submissions: dict[str, tuple[StudentRecord, Path]],
    writer: Writer,
) -> None:
    """
    Generate a comprehensive post-grading report focusing on problematic cases.

    Args:
        results: List of grading results
        grading_df: Original DataFrame with student records
        latest_submissions: Dictionary of found submissions
        writer: Writer for output
    """
    writer.always_echo("\n" + "=" * 80)
    writer.always_echo("📋 POST-GRADING REPORT")
    writer.always_echo("=" * 80)

    # Create lookups for analysis
    submitted_students = set()
    for _, (student_record, _) in latest_submissions.items():
        submitted_students.add(student_record.username)

    all_csv_students = set()
    for _, row in grading_df.iterrows():
        all_csv_students.add(str(row["Username"]))

    # 1. Students who received a grade of 0
    zero_grade_students = []
    for result in results:
        if result.grade == 0.0:
            zero_grade_students.append(result)

    writer.always_echo(
        f"\n🚨 STUDENTS WHO RECEIVED A GRADE OF 0 ({len(zero_grade_students)} students):"
    )
    writer.always_echo("-" * 60)
    if zero_grade_students:
        for result in zero_grade_students:
            student = result.student_record
            reason = result.error_message if result.error_message else "Test failures"
            writer.always_echo(
                f"  • {student.first_name} {student.last_name} ({student.username})"
            )
            writer.always_echo(f"    Reason: {reason}")
            writer.always_echo("")
    else:
        writer.always_echo("  ✅ No students received a grade of 0")

    # 2. Students who received NaN grades (failures marked as null)
    nan_grade_students = []
    for result in results:
        # Check for actual NaN values or explicit failures that would result in empty grades
        has_nan_grade = (
            result.grade is None
            or (isinstance(result.grade, float) and math.isnan(result.grade))
            or not result.success
        )
        if has_nan_grade:
            nan_grade_students.append(result)

    writer.always_echo(
        f"\n📊 STUDENTS WITH FAILED/NULL GRADES ({len(nan_grade_students)} students):"
    )
    writer.always_echo("-" * 60)
    if nan_grade_students:
        for result in nan_grade_students:
            student = result.student_record
            reason = result.error_message if result.error_message else "Grading failed"
            writer.always_echo(
                f"  • {student.first_name} {student.last_name} ({student.username})"
            )
            writer.always_echo(f"    Reason: {reason}")
            writer.always_echo("")
    else:
        writer.always_echo("  ✅ No students have failed/null grades")

    # 3. Students in CSV but without submissions
    csv_no_submission = all_csv_students - submitted_students

    writer.always_echo(
        f"\n📝 STUDENTS IN CSV BUT WITHOUT SUBMISSIONS ({len(csv_no_submission)} students):"
    )
    writer.always_echo("-" * 60)
    if csv_no_submission:
        for username in sorted(csv_no_submission):
            # Find the student record
            student_row = grading_df[grading_df["Username"] == username]
            if not student_row.empty:
                row = student_row.iloc[0]
                first_name = str(row["First Name"])
                last_name = str(row["Last Name"])
                writer.always_echo(f"  • {first_name} {last_name} ({username})")
                writer.always_echo("")
    else:
        writer.always_echo("  ✅ All students in CSV have submissions")

    # 4. Students with submissions but not in CSV
    submission_no_csv = submitted_students - all_csv_students

    writer.always_echo(
        f"\n📤 STUDENTS WITH SUBMISSIONS BUT NOT IN CSV ({len(submission_no_csv)} students):"
    )
    writer.always_echo("-" * 60)
    if submission_no_csv:
        for username in sorted(submission_no_csv):
            # Find the submission info
            for _, (student_record, submission_path) in latest_submissions.items():
                if student_record.username == username:
                    writer.always_echo(
                        f"  • {student_record.first_name} {student_record.last_name} ({username})"
                    )
                    writer.always_echo(f"    Submission folder: {submission_path.name}")
                    writer.always_echo("")
                    break
    else:
        writer.always_echo("  ✅ All submissions correspond to students in CSV")

    # Summary statistics
    writer.always_echo("\n📈 SUMMARY STATISTICS:")
    writer.always_echo("-" * 60)
    writer.always_echo(f"  Total students in CSV: {len(all_csv_students)}")
    writer.always_echo(f"  Total submissions found: {len(submitted_students)}")
    writer.always_echo(f"  Total students graded: {len(results)}")
    writer.always_echo(f"  Students with grade 0: {len(zero_grade_students)}")
    writer.always_echo(f"  Students with failed grades: {len(nan_grade_students)}")
    writer.always_echo(f"  Students missing submissions: {len(csv_no_submission)}")
    writer.always_echo(f"  Extra submissions (not in CSV): {len(submission_no_csv)}")

    # Calculate success rate
    successful_grades = len(
        [r for r in results if r.success and r.grade is not None and r.grade > 0]
    )
    total_expected = len(all_csv_students)
    if total_expected > 0:
        success_rate = (successful_grades / total_expected) * 100
        writer.always_echo(
            f"  Success rate: {success_rate:.1f}% ({successful_grades}/{total_expected})"
        )

    writer.always_echo("=" * 80)
