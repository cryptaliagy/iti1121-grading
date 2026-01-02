#!/usr/bin/env python3

from dataclasses import dataclass
import re
import os
import shutil
import subprocess  # nosec: B404
import sys
from pathlib import Path
from typing import Any
import rich

import typer

app = typer.Typer(help="CLI for compiling and running Java test files")

# Constants
SUCCESS_EXIT_CODE = 0
ERROR_EXIT_CODE = 1
JAVA_FILE_EXTENSION = ".java"
JAVA_COMPILER_CMD = "javac"
JAVA_RUNTIME_CMD = "java"
TEST_UTILS_FILE = "TestUtils.java"
CLASSPATH_SEPARATOR = ":"
PACKAGE_DECLARATION_PATTERN = r"^\s*package\s+[\w.]+;\s*\n?"


class FileOperationError(Exception):
    """Exception raised for errors in file operations."""

    pass


@dataclass
class CodeFilePreprocessingOptions:
    """
    Options for preprocessing code files.

    This class can be extended in the future to include more options.
    Currently, it is a placeholder for future enhancements.
    """

    remove_package_declaration: bool = True


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
        FileOperationError: If no test files are found or the directory doesn't exist
    """
    if not test_dir.exists() or not test_dir.is_dir():
        raise FileOperationError(
            f"Test directory {test_dir} does not exist or is not a directory."
        )

    test_files = list(test_dir.glob(f"{prefix}*{JAVA_FILE_EXTENSION}"))

    if not test_files:
        raise FileOperationError(
            f"No test files found with prefix '{prefix}' in {test_dir}"
        )

    main_test_file = test_dir / f"{prefix}{JAVA_FILE_EXTENSION}"

    if not main_test_file.exists():
        raise FileOperationError(
            f"Main test file {main_test_file} does not exist.\n"
            f"Found test files: {[f.name for f in test_files]}"
        )

    return test_files


def safe_copy_file(source: Path, target: Path, writer: Writer) -> None:
    """
    Safely copy a file, ensuring the target is writable.

    Args:
        source: Source file path
        target: Target file path
        writer: Writer object for console output

    Raises:
        FileOperationError: If file copy fails
    """
    # Delete existing file if it exists
    if target.exists():
        safe_delete_file(target, writer)

    # Copy the file
    writer.echo(f"Copying {source} to {target}")
    try:
        shutil.copy2(source, target)
    except PermissionError:
        raise FileOperationError(f"Permission denied when copying to {target}")
    except Exception as e:
        raise FileOperationError(f"Failed to copy {source} to {target}: {e}")


def copy_test_files(test_files: list[Path], target_dir: Path, writer: Writer) -> None:
    """
    Copy test files to the target directory, deleting existing ones if necessary.
    Adds write permissions to the target directory if needed.

    Args:
        test_files: List of test files to copy
        target_dir: Directory to copy files to
        writer: Writer object for console output

    Raises:
        FileOperationError: If file operations fail
    """
    # Ensure target directory is writable
    ensure_directory_writable(target_dir, writer)

    # Copy all test files
    for test_file in test_files:
        target_file = target_dir / test_file.name
        safe_copy_file(test_file, target_file, writer)

    # Also copy TestUtils.java if it exists in the test directory
    test_dir = test_files[0].parent
    utils_file = test_dir / TEST_UTILS_FILE
    if utils_file.exists():
        target_utils_file = target_dir / TEST_UTILS_FILE
        safe_copy_file(utils_file, target_utils_file, writer)


def build_compile_command(
    main_test_file: str, classpath: list[str] | None = None
) -> list[str]:
    """
    Build the javac command for compilation.

    Args:
        main_test_file: Name of the main test file (without extension)
        classpath: Optional list of additional classpath entries

    Returns:
        Command as a list of strings
    """
    if classpath:
        if "." not in classpath:
            classpath.append(".")
        cp_string = CLASSPATH_SEPARATOR.join(classpath)
        return [
            JAVA_COMPILER_CMD,
            "-cp",
            cp_string,
            f"{main_test_file}{JAVA_FILE_EXTENSION}",
        ]
    else:
        return [JAVA_COMPILER_CMD, f"{main_test_file}{JAVA_FILE_EXTENSION}"]


def build_run_command(
    main_test_file: str, classpath: list[str] | None = None
) -> list[str]:
    """
    Build the java command for execution.

    Args:
        main_test_file: Name of the main test file (without extension)
        classpath: Optional list of additional classpath entries

    Returns:
        Command as a list of strings
    """
    if classpath:
        if "." not in classpath:
            classpath.append(".")
        cp_string = CLASSPATH_SEPARATOR.join(classpath)
        return [JAVA_RUNTIME_CMD, "-cp", cp_string, main_test_file]
    else:
        return [JAVA_RUNTIME_CMD, main_test_file]


def compile_test(
    main_test_file: str,
    target_dir: Path,
    writer: Writer,
    classpath: list[str] | None = None,
) -> bool:
    """
    Compile the main test file using javac.

    Args:
        main_test_file: Name of the main test file (without extension)
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
        command = build_compile_command(main_test_file, classpath)
        writer.always_echo(f"Running: {' '.join(command)}\n")

        result = subprocess.run(command, capture_output=True, text=True)  # nosec: B603
        if result.returncode != 0:
            writer.always_echo("Compilation [red]failed[/red] with error:")
            writer.always_echo(result.stderr)
            return False

        writer.always_echo("[green]Compilation successful![/green]")
        return True
    finally:
        # Always change back to the original directory
        os.chdir(original_dir)


def calculate_grade_from_output(output: str) -> tuple[float, float]:
    """
    Parse the test output to calculate the total grade.

    Args:
        output: The output string from the test execution

    Returns:
        Tuple containing total points and possible points
    """
    total_points = 0.0
    possible_points = 0.0

    grade_pattern = re.compile(
        r"Grade for .+ \(out of (a\s+)?possible (?P<max>\d+(\.\d+)?)\): (?P<total>\d+(\.\d+)?)"
    )

    for line in output.split("\n"):
        match = grade_pattern.search(line)
        if match:
            possible = float(match.group("max"))
            achieved = float(match.group("total"))
            total_points += achieved
            possible_points += possible

    return total_points, possible_points


def display_grade_summary(
    writer: Writer, total_points: float, possible_points: float
) -> None:
    """
    Display a summary of the test results.

    Args:
        writer: Writer object for console output
        total_points: Total points earned
        possible_points: Total points possible
    """
    if possible_points > 0:
        percentage = (total_points / possible_points) * 100
        writer.always_echo("\n" + "=" * 60)
        writer.always_echo("Final Grade Summary:")
        writer.always_echo(f"Total Points: {total_points:.1f} / {possible_points:.1f}")
        writer.always_echo(f"Percentage: {percentage:.1f}%")
        writer.always_echo("=" * 60)


def run_test(
    main_test_file: str,
    target_dir: Path,
    writer: Writer,
    classpath: list[str] | None = None,
) -> tuple[bool, float, float]:
    """
    Run the compiled test using java.

    Args:
        main_test_file: Name of the main test file (without extension)
        target_dir: Directory where the file is
        writer: Writer object for console output
        classpath: Optional list of additional classpath entries

    Returns:
        Tuple containing:
          - Success status (boolean)
          - Total points earned (float)
          - Total possible points (float)

    Raises:
        SystemExit: If the test execution fails
    """
    # Change to the target directory
    original_dir = os.getcwd()
    os.chdir(target_dir)

    try:
        command = build_run_command(main_test_file, classpath)
        writer.always_echo(f"Running: {' '.join(command)}\n\n")

        result = subprocess.run(command, capture_output=True, text=True)  # nosec: B603
        output = result.stdout

        writer.always_echo(output)
        writer.always_echo(result.stderr)

        if result.returncode != 0:
            writer.always_echo(
                f"[yellow]Grader.py[/yellow]: Test execution [red]failed[/red] with exit code: {result.returncode}"
            )
            sys.exit(result.returncode)

        # Parse the output to calculate the total grade
        total_points, possible_points = calculate_grade_from_output(output)

        # Display the results
        display_grade_summary(writer, total_points, possible_points)
        return True, total_points, possible_points

    finally:
        # Always change back to the original directory
        os.chdir(original_dir)


def add_write_permission(path: Path, writer: Writer) -> bool:
    """
    Add write permission to a file or directory.

    Args:
        path: Path to add write permission to
        writer: Writer object for console output

    Returns:
        True if permission was successfully added, False otherwise
    """
    writer.echo(f"Adding write permissions to: {path}")
    try:
        current_mode = path.stat().st_mode
        new_mode = current_mode | 0o200  # Add user write permission
        os.chmod(path, new_mode)
        writer.echo(f"Successfully added write permissions to {path}")
        return True
    except Exception as e:
        writer.always_echo(f"[red]Warning:[/red] Failed to add write permissions: {e}")
        return False


def safe_delete_file(file_path: Path, writer: Writer) -> bool:
    """
    Safely delete a file, attempting to add write permissions if needed.

    Args:
        file_path: Path to the file to delete
        writer: Writer object for console output

    Returns:
        True if deletion was successful, False otherwise

    Raises:
        FileOperationError: If file deletion fails after attempts to fix permissions
    """
    if not file_path.exists():
        return True

    writer.echo(f"Removing existing file: {file_path}")
    try:
        file_path.unlink()
        return True
    except PermissionError:
        writer.echo(
            f"Insufficient permissions to remove {file_path}, trying to add write permissions"
        )
        if add_write_permission(file_path, writer):
            try:
                file_path.unlink()
                return True
            except Exception:
                # Ignore the exception to trigger our own
                pass  # nosec: B110

    # If we get here, all attempts failed
    raise FileOperationError(f"Could not remove existing file {file_path}")


def ensure_directory_writable(directory: Path, writer: Writer) -> None:
    """
    Ensure a directory exists and is writable, adding permissions if necessary.

    Args:
        directory: Directory path to check
        writer: Writer object for console output

    Raises:
        FileOperationError: If directory does not exist or cannot be made writable
    """
    if not directory.exists() or not directory.is_dir():
        raise FileOperationError(
            f"Directory {directory} does not exist or is not a directory."
        )

    # Check write permissions on directory
    if not os.access(directory, os.W_OK):
        if not add_write_permission(directory, writer):
            writer.always_echo(
                "Attempting to continue with operations despite permission issues..."
            )


def preprocess_codefile(
    options: CodeFilePreprocessingOptions,
    code_file: Path,
    writer: Writer,
) -> None:
    """
    Preprocess a code file to ensure it is ready for compilation.

    Args:
        options: Preprocessing options
        code_file: Path to the code file to preprocess
        writer: Writer object for console output
    """

    if not code_file.exists():
        raise FileOperationError(f"Code file {code_file} does not exist.")

    # Read the original content
    with code_file.open("r") as f:
        content = f.read()

    # Remove package declaration if specified
    if options.remove_package_declaration:
        content = re.sub(PACKAGE_DECLARATION_PATTERN, "", content, flags=re.MULTILINE)

    # Write the modified content back to the file
    with code_file.open("w") as f:
        f.write(content)

    writer.echo(f"Preprocessed {code_file} successfully")


def collect_code_files(code_dir: Path, writer: Writer) -> list[Path]:
    """
    Collect all Java code files from the specified directory.

    Args:
        code_dir: Directory to search for Java code files
        writer: Writer object for console output

    Returns:
        List of Path objects for Java code files found in the directory
    """
    if not code_dir.exists() or not code_dir.is_dir():
        raise FileOperationError(f"Code directory {code_dir} does not exist.")

    java_files = list(code_dir.glob(f"*{JAVA_FILE_EXTENSION}"))
    if not java_files:
        raise FileOperationError(f"No Java files found in {code_dir}")

    writer.echo(f"Found {len(java_files)} Java files in {code_dir}")
    return java_files


@app.command(name="single")
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
    preprocess_code: bool = typer.Option(
        False,
        "--preprocess-code/",
        "-P",
        help="Enable or disable preprocessing of code files (e.g. removes package statements)",
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

    try:
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
                    raise FileOperationError(
                        f"Classpath entry '{cp_entry}' does not exist."
                    )
                resolved_classpath.append(str(cp_path))

            writer.echo(f"Classpath entries: {resolved_classpath}")

        # Preprocess code files in the code directory
        if preprocess_code:
            code_files = collect_code_files(code_dir_path, writer)
            for code_file in code_files:
                try:
                    preprocess_codefile(
                        CodeFilePreprocessingOptions(),
                        code_file,
                        writer,
                    )
                except FileOperationError as e:
                    writer.always_echo(f"[red]Error:[/red] {e}")
                    sys.exit(ERROR_EXIT_CODE)

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
            sys.exit(ERROR_EXIT_CODE)

        # Run the test
        success, _, _ = run_test(prefix, code_dir_path, writer, resolved_classpath)

        if success:
            writer.echo("Test execution completed successfully")
            sys.exit(SUCCESS_EXIT_CODE)
        else:
            sys.exit(ERROR_EXIT_CODE)

    except FileOperationError as e:
        writer.always_echo(f"[red]Error:[/red] {e}")
        sys.exit(ERROR_EXIT_CODE)
    except Exception as e:
        writer.always_echo(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            import traceback

            writer.always_echo(traceback.format_exc())
        sys.exit(ERROR_EXIT_CODE)


if __name__ == "__main__":
    app()
