"""Legacy adapter for test running functionality."""

import os
import subprocess  # nosec: B404
import time

from grader._grader import Writer, build_compile_command, build_run_command
from grader.domain.models import TestRunOutput
from grader.infrastructure.protocols import TestRunnerConfig


class LegacyTestRunnerAdapter:
    """
    Adapter that wraps existing compile_test() and run_test() functions.

    This adapter implements the TestRunner protocol while maintaining
    backward compatibility with the existing implementation.
    """

    def __init__(self, writer: Writer):
        """
        Initialize the adapter.

        Args:
            writer: Writer instance for console output
        """
        self.writer = writer

    def compile(self, config: TestRunnerConfig) -> bool:
        """
        Compile the main test file using javac.

        This wraps the existing compile_test() function logic.

        Args:
            config: Configuration for compilation

        Returns:
            True if compilation succeeded, False otherwise
        """
        # Change to the target directory
        original_dir = os.getcwd()
        os.chdir(config.target_dir)

        try:
            command = build_compile_command(config.main_test_file, config.classpath)
            self.writer.always_echo(f"Running: {' '.join(command)}\n")

            result = subprocess.run(
                command, capture_output=True, text=True
            )  # nosec: B603
            if result.returncode != 0:
                self.writer.always_echo("Compilation [red]failed[/red] with error:")
                self.writer.always_echo(result.stderr)
                return False

            self.writer.always_echo("[green]Compilation successful![/green]")
            return True
        finally:
            # Always change back to the original directory
            os.chdir(original_dir)

    def run(self, config: TestRunnerConfig) -> TestRunOutput:
        """
        Run the compiled test using java.

        This wraps the existing run_test() function logic.

        Args:
            config: Configuration for test execution

        Returns:
            TestRunOutput containing stdout, stderr, exit code, and execution time
        """
        # Change to the target directory
        original_dir = os.getcwd()
        os.chdir(config.target_dir)

        try:
            command = build_run_command(config.main_test_file, config.classpath)
            self.writer.always_echo(f"Running: {' '.join(command)}\n\n")

            start_time = time.time()
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=config.timeout,
            )  # nosec: B603
            execution_time = time.time() - start_time

            output = result.stdout
            self.writer.always_echo(output)
            self.writer.always_echo(result.stderr)

            return TestRunOutput(
                stdout=output,
                stderr=result.stderr,
                exit_code=result.returncode,
                execution_time=execution_time,
            )
        finally:
            # Always change back to the original directory
            os.chdir(original_dir)
