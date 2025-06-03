#!/usr/bin/env python3

import re
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
import rich

import typer

app = typer.Typer(help="CLI for compiling and running Java test files")


class Writer:
    """
    A utility class for conditional writing to console based on verbosity.

    This class wraps rich.print with conditional output based on a verbose flag.
    """

    def __init__(self, verbose: bool = True):
        """Initialize the writer with the verbose flag.

        Args:
            verbose: Whether to print detailed output
        """
        self.verbose = verbose

    def echo(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """
        Echo a message if verbose mode is enabled.

        Args:
            message: The message to echo
            *args: Additional arguments to pass to rich.print
            **kwargs: Additional keyword arguments to pass to rich.print
        """
        if self.verbose:
            rich.print(message, *args, **kwargs)

    def always_echo(self, message: Any, *args: Any, **kwargs: Any) -> None:
        """
        Always echo a message regardless of verbose mode.

        Args:
            message: The message to echo
            *args: Additional arguments to pass to rich.print
            **kwargs: Additional keyword arguments to pass to rich.print
        """
        rich.print(message, *args, **kwargs)


def find_test_files(test_dir: Path, prefix: str, writer: Writer) -> list[Path]:
    """
    Find all Java test files matching the given prefix in the specified directory.

    Args:
        test_dir: Directory where test files are located
        prefix: Prefix of test files to search for
        writer: Writer object for console output

    Returns:
        List of Path objects for test files that match the criteria

    Raises:
        SystemExit: If no test files are found or if the main test file doesn't exist
    """
    if not test_dir.exists() or not test_dir.is_dir():
        writer.always_echo(
            f"Error: Test directory {test_dir} does not exist or is not a directory."
        )
        sys.exit(1)

    test_files = list(test_dir.glob(f"{prefix}*.java"))

    if not test_files:
        writer.always_echo(
            f"Error: No test files found with prefix '{prefix}' in {test_dir}"
        )
        sys.exit(1)

    main_test_file = test_dir / f"{prefix}.java"

    if not main_test_file.exists():
        writer.always_echo(f"Error: Main test file {main_test_file} does not exist.")
        writer.always_echo(f"Found test files: {[f.name for f in test_files]}")
        sys.exit(1)

    return test_files


def copy_test_files(test_files: list[Path], target_dir: Path, writer: Writer) -> None:
    """
    Copy test files to the target directory, deleting existing ones if necessary.
    Adds write permissions to the target directory if needed.

    Args:
        test_files: List of test files to copy
        target_dir: Directory to copy files to
        writer: Writer object for console output

    Raises:
        SystemExit: If the target directory does not exist or is not a directory
    """
    if not target_dir.exists() or not target_dir.is_dir():
        writer.always_echo(
            f"Error: Target directory {target_dir} does not exist or is not a directory."
        )
        sys.exit(1)

    # Check write permissions on target directory
    if not os.access(target_dir, os.W_OK):
        writer.echo(f"Adding write permissions to directory: {target_dir}")
        try:
            # Get current permissions and add user write permission
            current_mode = target_dir.stat().st_mode
            new_mode = current_mode | 0o200  # Add user write permission
            os.chmod(target_dir, new_mode)
            writer.echo(f"Successfully added write permissions to {target_dir}")
        except Exception as e:
            writer.always_echo(
                f"[red]Warning:[/red] Failed to add write permissions: {e}"
            )
            writer.always_echo("Attempting to continue with copy operation...")

    for test_file in test_files:
        target_file = target_dir / test_file.name

        # Delete existing file if it exists
        if target_file.exists():
            writer.echo(f"Removing existing file: {target_file}")
            try:
                target_file.unlink()
            except PermissionError:
                writer.echo(
                    f"Insufficient permissions to remove {target_file}, trying to add write permissions"
                )
                try:
                    os.chmod(
                        target_file, target_file.stat().st_mode | 0o200
                    )  # Add write permission
                    target_file.unlink()
                except Exception as e:
                    writer.always_echo(
                        f"[red]Error:[/red] Could not remove existing file {target_file}: {e}"
                    )
                    sys.exit(1)

        # Copy the test file
        writer.echo(f"Copying {test_file} to {target_file}")
        try:
            shutil.copy2(test_file, target_file)
        except PermissionError:
            writer.always_echo(
                f"[red]Permission denied[/red] when copying to {target_file}"
            )
            sys.exit(1)

    # Also copy TestUtils.java if it exists in the test directory
    test_dir = test_files[0].parent
    utils_file = test_dir / "TestUtils.java"
    if utils_file.exists():
        target_utils_file = target_dir / "TestUtils.java"
        if target_utils_file.exists():
            writer.echo(f"Removing existing file: {target_utils_file}")
            try:
                target_utils_file.unlink()
            except PermissionError:
                writer.echo(
                    f"Insufficient permissions to remove {target_utils_file}, trying to add write permissions"
                )
                try:
                    os.chmod(
                        target_utils_file, target_utils_file.stat().st_mode | 0o200
                    )  # Add write permission
                    target_utils_file.unlink()
                except Exception as e:
                    writer.always_echo(
                        f"[red]Error:[/red] Could not remove existing file {target_utils_file}: {e}"
                    )
                    sys.exit(1)

        writer.echo(f"Copying {utils_file} to {target_utils_file}")
        try:
            shutil.copy2(utils_file, target_utils_file)
        except PermissionError:
            writer.always_echo(
                f"[red]Permission denied[/red] when copying to {target_utils_file}"
            )
            sys.exit(1)


def compile_test(
    main_test_file: str,
    target_dir: Path,
    writer: Writer,
    classpath: list[str] | None = None,
) -> bool:
    """
    Compile the main test file using javac.

    Args:
        main_test_file: Name of the main test file
        target_dir: Directory where the file is located
        writer: Writer object for console output
        classpath: Optional list of additional classpath entries

    Returns:
        True if compilation succeeded, False otherwise
    """
    # Change to the target directory
    original_dir = os.getcwd()
    os.chdir(target_dir)

    try:
        if classpath:
            if "." not in classpath:
                classpath.append(".")
            cp_string = ":".join(classpath)
            command = ["javac", "-cp", cp_string, f"{main_test_file}.java"]
        else:
            command = ["javac", f"{main_test_file}.java"]

        writer.always_echo(f"Running: {' '.join(command)}\n")
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            writer.always_echo("Compilation [red]failed[/red] with error:")
            writer.always_echo(result.stderr)
            return False

        writer.always_echo("[green]Compilation successful![/green]")
        return True
    finally:
        # Always change back to the original directory
        os.chdir(original_dir)


def run_test(
    main_test_file: str,
    target_dir: Path,
    writer: Writer,
    classpath: list[str] | None = None,
) -> None:
    """
    Run the compiled test using java.

    Args:
        main_test_file: Name of the main test file (without extension)
        target_dir: Directory where the file is
        writer: Writer object for console output
        classpath: Optional list of additional classpath entries

    Raises:
        SystemExit: If the test execution fails
    """
    # Change to the target directory
    original_dir = os.getcwd()
    os.chdir(target_dir)

    try:
        if classpath:
            if "." not in classpath:
                classpath.append(".")
            cp_string = ":".join(classpath)
            command = ["java", "-cp", cp_string, main_test_file]
        else:
            command = ["java", main_test_file]

        writer.always_echo(f"Running: {' '.join(command)}\n\n")

        result = subprocess.run(command, capture_output=True, text=True)
        output = result.stdout

        writer.always_echo(output)

        if result.returncode != 0:
            writer.always_echo(
                f"Test execution failed with exit code: {result.returncode}"
            )
            # Always show error output even in quiet mode
            if not writer.verbose:
                writer.always_echo(output)
            sys.exit(result.returncode)

        # Parse the output to calculate the total grade
        total_points = 0
        possible_points = 0

        grade_pattern = re.compile(
            r"Grade for .+ \(out of possible (\d+\.\d+)\): (\d+\.\d+)"
        )

        for line in output.split("\n"):
            match = grade_pattern.search(line)
            if match:
                possible = float(match.group(1))
                achieved = float(match.group(2))
                total_points += achieved
                possible_points += possible

        # Display the results - always show grade summary regardless of verbosity
        if possible_points > 0:
            percentage = (total_points / possible_points) * 100
            writer.always_echo("\n" + "=" * 60)
            writer.always_echo("Final Grade Summary:")
            writer.always_echo(
                f"Total Points: {total_points:.1f} / {possible_points:.1f}"
            )
            writer.always_echo(f"Percentage: {percentage:.1f}%")
            writer.always_echo("=" * 60)

    finally:
        # Always change back to the original directory
        os.chdir(original_dir)


@app.command()
def main(
    test_dir: str = typer.Option(
        ..., "--test-dir", "-t", help="Directory containing test files"
    ),
    prefix: str = typer.Option(
        ...,
        "--prefix",
        "-p",
        help="Prefix of test files to search for (e.g., 'TestL3')",
    ),
    code_dir: str = typer.Option(
        ".",
        "--code-dir",
        "-c",
        help="Directory containing code files (defaults to current directory)",
    ),
    classpath: list[str] | None = typer.Option(
        None,
        "--classpath",
        "-cp",
        help="Additional classpath entries (can be specified multiple times)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose/--quiet",
        "-v/-q",
        help="Control verbosity of output",
    ),
) -> None:
    """
    Compile and run Java test files.

    This CLI tool finds all Java test files matching a given prefix,
    copies them to a target directory, compiles the main test file,
    and runs it if compilation succeeds.
    """
    # Create our writer utility for console output
    writer = Writer(verbose)

    # Convert paths to Path objects
    test_dir_path = Path(test_dir).resolve()
    code_dir_path = Path(code_dir).resolve()

    writer.echo(f"Test directory: {test_dir_path}")
    writer.echo(f"Code directory: {code_dir_path}")
    writer.echo(f"Test file prefix: {prefix}")

    # Process classpath entries if provided
    resolved_classpath: list[str] | None = None
    if classpath:
        resolved_classpath = []
        for cp_entry in classpath:
            cp_path = Path(cp_entry).resolve()
            if not cp_path.exists():
                writer.always_echo(
                    f"Error: Classpath entry '{cp_entry}' does not exist."
                )
                sys.exit(1)
            resolved_classpath.append(str(cp_path))

        writer.echo(f"Classpath entries: {resolved_classpath}")

    # Find all test files
    test_files = find_test_files(test_dir_path, prefix, writer)
    writer.echo(f"Found {len(test_files)} test files")

    # Copy test files to target directory
    copy_test_files(test_files, code_dir_path, writer)

    # Compile the main test file
    compilation_successful = compile_test(
        prefix,
        code_dir_path,
        writer,
        resolved_classpath,
    )

    if not compilation_successful:
        writer.always_echo("Exiting due to compilation failure")
        sys.exit(1)

    # Run the test
    run_test(prefix, code_dir_path, writer, resolved_classpath)

    writer.echo("Test execution completed successfully")


if __name__ == "__main__":
    app()
