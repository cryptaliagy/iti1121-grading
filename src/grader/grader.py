#!/usr/bin/env python3

import sys
from pathlib import Path
import typer

from .common import FileOperationError
from .code_preprocessing import CodePreProcessor, PackageDeclarationHandler
from .file_operations import FileHandler
from .test_runner import JavaTestRunner
from .writer import Writer
from .grading_service import GradingService

app = typer.Typer(help="CLI for compiling and running Java test files")

# Constants
SUCCESS_EXIT_CODE = 0
ERROR_EXIT_CODE = 1


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

    # Create file handler
    file_handler = FileHandler(writer)
    code_preprocessor = CodePreProcessor(writer)
    test_runner = JavaTestRunner(writer, classpath)

    if preprocess_code:
        code_preprocessor.register_handler(PackageDeclarationHandler(writer))

    grader_service = GradingService(
        writer=writer,
        file_handler=file_handler,
        code_preprocessor=code_preprocessor,
        test_runner=test_runner,
    )

    try:
        # Convert paths to Path objects
        test_dir_path = Path(test_dir).resolve()
        code_dir_path = Path(code_dir).resolve()

        writer.echo(f"Test directory: {test_dir_path}")
        writer.echo(f"Code directory: {code_dir_path}")
        writer.echo(f"Test file prefix: {prefix}")

        result = grader_service.grade_single_student(
            grading_dir=code_dir_path,
            test_dir=test_dir_path,
            prefix=prefix,
        )

        if not result.success:
            writer.always_echo(f"[red]Grading failed:[/red] {result.error_message}")
            sys.exit(ERROR_EXIT_CODE)

        writer.always_echo(
            f"[green]Grading successful:[/green] {result.grade:.2f} points"
        )

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
