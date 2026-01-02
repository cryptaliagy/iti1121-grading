"""Test runner implementations for executing Java tests."""

import os
import subprocess  # nosec: B404
import time
from pathlib import Path

from grader.domain.models import TestRunOutput
from grader.infrastructure.protocols import TestRunnerConfig


class JavaProcessTestRunner:
    """Test runner that compiles and executes Java tests using javac and java."""

    JAVA_COMPILER_CMD = "javac"
    JAVA_RUNTIME_CMD = "java"
    CLASSPATH_SEPARATOR = ":"
    JAVA_FILE_EXTENSION = ".java"

    def __init__(self, verbose: bool = True):
        """
        Initialize the Java process test runner.

        Args:
            verbose: Whether to print detailed output
        """
        self.verbose = verbose

    def _build_compile_command(
        self, main_test_file: str, classpath: list[str] | None = None
    ) -> list[str]:
        """
        Build the javac compilation command.

        Args:
            main_test_file: Name of the main test file (without extension)
            classpath: Optional list of additional classpath entries

        Returns:
            Command as a list of strings
        """
        if classpath:
            # Ensure current directory is in classpath
            if "." not in classpath:
                classpath.append(".")
            cp_string = self.CLASSPATH_SEPARATOR.join(classpath)
            return [
                self.JAVA_COMPILER_CMD,
                "-cp",
                cp_string,
                f"{main_test_file}{self.JAVA_FILE_EXTENSION}",
            ]
        else:
            return [
                self.JAVA_COMPILER_CMD,
                f"{main_test_file}{self.JAVA_FILE_EXTENSION}",
            ]

    def _build_run_command(
        self, main_test_file: str, classpath: list[str] | None = None
    ) -> list[str]:
        """
        Build the java execution command.

        Args:
            main_test_file: Name of the main test file (without extension)
            classpath: Optional list of additional classpath entries

        Returns:
            Command as a list of strings
        """
        if classpath:
            if "." not in classpath:
                classpath.append(".")
            cp_string = self.CLASSPATH_SEPARATOR.join(classpath)
            return [self.JAVA_RUNTIME_CMD, "-cp", cp_string, main_test_file]
        else:
            return [self.JAVA_RUNTIME_CMD, main_test_file]

    def compile(self, config: TestRunnerConfig) -> bool:
        """
        Compile the test files using javac.

        Args:
            config: Configuration for compilation

        Returns:
            True if compilation succeeded, False otherwise
        """
        # Change to the target directory
        original_dir = os.getcwd()
        os.chdir(config.target_dir)

        try:
            command = self._build_compile_command(
                config.main_test_file, config.classpath
            )

            if self.verbose:
                print(f"Running: {' '.join(command)}\n")

            result = subprocess.run(  # nosec: B603
                command,
                capture_output=True,
                text=True,
                timeout=config.timeout,
            )

            if result.returncode != 0:
                if self.verbose:
                    print("Compilation failed with error:")
                    print(result.stderr)
                return False

            if self.verbose:
                print("Compilation successful!")
            return True

        except subprocess.TimeoutExpired:
            if self.verbose:
                print(f"Compilation timed out after {config.timeout} seconds")
            return False

        finally:
            # Always change back to the original directory
            os.chdir(original_dir)

    def run(self, config: TestRunnerConfig) -> TestRunOutput:
        """
        Run the compiled test using java.

        Args:
            config: Configuration for test execution

        Returns:
            TestRunOutput containing stdout, stderr, exit code, and execution time
        """
        # Change to the target directory
        original_dir = os.getcwd()
        os.chdir(config.target_dir)

        start_time = time.time()
        try:
            command = self._build_run_command(config.main_test_file, config.classpath)

            if self.verbose:
                print(f"Running: {' '.join(command)}\n\n")

            result = subprocess.run(  # nosec: B603
                command,
                capture_output=True,
                text=True,
                timeout=config.timeout,
            )
            execution_time = time.time() - start_time

            return TestRunOutput(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                execution_time=execution_time,
            )

        except subprocess.TimeoutExpired as e:
            execution_time = time.time() - start_time
            return TestRunOutput(
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=f"Test execution timed out after {config.timeout} seconds",
                exit_code=-1,
                execution_time=execution_time,
            )

        finally:
            # Always change back to the original directory
            os.chdir(original_dir)


class MockTestRunner:
    """Mock test runner for testing purposes."""

    def __init__(
        self,
        compile_result: bool = True,
        run_output: TestRunOutput | None = None,
    ):
        """
        Initialize the mock test runner.

        Args:
            compile_result: Whether compilation should succeed
            run_output: Output to return when running tests
        """
        self.compile_result = compile_result
        self.run_output = run_output or TestRunOutput(
            stdout="Mock test output",
            stderr="",
            exit_code=0,
            execution_time=0.1,
        )
        self.compile_called = False
        self.run_called = False
        self.last_compile_config: TestRunnerConfig | None = None
        self.last_run_config: TestRunnerConfig | None = None

    def compile(self, config: TestRunnerConfig) -> bool:
        """
        Mock compile method.

        Args:
            config: Configuration for compilation

        Returns:
            Predefined compile result
        """
        self.compile_called = True
        self.last_compile_config = config
        return self.compile_result

    def run(self, config: TestRunnerConfig) -> TestRunOutput:
        """
        Mock run method.

        Args:
            config: Configuration for test execution

        Returns:
            Predefined test run output
        """
        self.run_called = True
        self.last_run_config = config
        return self.run_output
