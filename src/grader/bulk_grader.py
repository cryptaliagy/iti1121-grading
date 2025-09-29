#!/usr/bin/env python3

import math
import tempfile
from pathlib import Path

import pandas as pd
import typer

from .test_runner import JavaTestRunner

from .common import FileOperationError, GradingResult, StudentRecord
from .csv_processing import load_grading_list, save_results_to_csv
from .grading_service import GradingService
from .submission_processing import (
    SubmissionProcessor,
)
from .name_matching import Matcher
from .writer import Writer
from .file_operations import FileHandler
from .code_preprocessing import CodePreProcessor, PackageDeclarationHandler

app = typer.Typer(help="Bulk grader for processing multiple student submissions")


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
    preprocess_package: bool = typer.Option(
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
    file_handler = FileHandler(writer)
    code_preprocessor = CodePreProcessor(writer)
    test_runner = JavaTestRunner(writer, classpath)
    matcher = Matcher()
    submission_processor = SubmissionProcessor(writer, matcher)

    if preprocess_package:
        code_preprocessor.register_handler(PackageDeclarationHandler(writer))

    try:
        # Convert paths to Path objects
        submissions_path = Path(submissions).resolve()
        grading_list_path = Path(grading_list).resolve()
        test_dir_path = Path(test_dir).resolve()
        output_path = Path(output).resolve()

        writer.always_echo("🎓 Starting bulk grading process...")

        if preprocess_package:
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
            submissions_dir = submission_processor.extract_submissions(
                submissions_path, temp_path
            )

            # Find latest submissions for each student
            writer.always_echo("\n🔍 Finding latest submissions...")
            latest_submissions = submission_processor.find_latest_submissions(
                submissions_dir,
                grading_df,
            )
            writer.always_echo(
                f"Found submissions for {len(latest_submissions)} students"
            )

            # Grade each submission
            writer.always_echo("\n⚡ Starting grading process...")
            results = []

            # Create grading service
            grading_service = GradingService(
                writer,
                file_handler,
                code_preprocessor,
                test_runner,
            )

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
                    grading_dir = submission_processor.prepare_grading_directory(
                        submission_path, temp_path
                    )

                    writer.always_echo(f"\n{'=' * 60}")
                    writer.always_echo(
                        f"Grading: {student_record.first_name} {student_record.last_name} ({student_record.username})"
                    )
                    writer.always_echo(f"{'=' * 60}")

                    # Run grader
                    result = grading_service.grade_single_student(
                        grading_dir,
                        test_dir_path,
                        prefix,
                    )

                    # Bind student record to result
                    result.student_record = student_record
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
