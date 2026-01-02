"""Unit tests for test runner implementations."""

import pytest
import tempfile
from pathlib import Path

from grader.domain.models import TestRunOutput
from grader.infrastructure.protocols import TestRunnerConfig
from grader.infrastructure.test_runner import JavaProcessTestRunner, MockTestRunner


class TestMockTestRunner:
    """Test the MockTestRunner implementation."""

    def test_mock_compile_success(self):
        """Test mock compilation success."""
        runner = MockTestRunner(compile_result=True)
        config = TestRunnerConfig(
            main_test_file="TestFile",
            target_dir=Path("/tmp"),
        )

        result = runner.compile(config)

        assert result is True
        assert runner.compile_called
        assert runner.last_compile_config == config

    def test_mock_compile_failure(self):
        """Test mock compilation failure."""
        runner = MockTestRunner(compile_result=False)
        config = TestRunnerConfig(
            main_test_file="TestFile",
            target_dir=Path("/tmp"),
        )

        result = runner.compile(config)

        assert result is False
        assert runner.compile_called

    def test_mock_run(self):
        """Test mock test execution."""
        expected_output = TestRunOutput(
            stdout="Test passed",
            stderr="",
            exit_code=0,
            execution_time=0.5,
        )
        runner = MockTestRunner(run_output=expected_output)
        config = TestRunnerConfig(
            main_test_file="TestFile",
            target_dir=Path("/tmp"),
        )

        result = runner.run(config)

        assert result == expected_output
        assert runner.run_called
        assert runner.last_run_config == config

    def test_mock_run_default_output(self):
        """Test mock run with default output."""
        runner = MockTestRunner()
        config = TestRunnerConfig(
            main_test_file="TestFile",
            target_dir=Path("/tmp"),
        )

        result = runner.run(config)

        assert result.stdout == "Mock test output"
        assert result.exit_code == 0


class TestJavaProcessTestRunner:
    """Test the JavaProcessTestRunner implementation."""

    def test_build_compile_command_without_classpath(self):
        """Test building compile command without classpath."""
        runner = JavaProcessTestRunner(verbose=False)

        command = runner._build_compile_command("TestFile")

        assert command == ["javac", "TestFile.java"]

    def test_build_compile_command_with_classpath(self):
        """Test building compile command with classpath."""
        runner = JavaProcessTestRunner(verbose=False)

        command = runner._build_compile_command("TestFile", ["/lib/junit.jar"])

        assert command == ["javac", "-cp", "/lib/junit.jar:.", "TestFile.java"]

    def test_build_compile_command_with_classpath_including_dot(self):
        """Test building compile command with classpath already including current dir."""
        runner = JavaProcessTestRunner(verbose=False)

        command = runner._build_compile_command("TestFile", ["/lib/junit.jar", "."])

        # Should not duplicate the dot
        assert command == ["javac", "-cp", "/lib/junit.jar:.", "TestFile.java"]

    def test_build_run_command_without_classpath(self):
        """Test building run command without classpath."""
        runner = JavaProcessTestRunner(verbose=False)

        command = runner._build_run_command("TestFile")

        assert command == ["java", "TestFile"]

    def test_build_run_command_with_classpath(self):
        """Test building run command with classpath."""
        runner = JavaProcessTestRunner(verbose=False)

        command = runner._build_run_command("TestFile", ["/lib/junit.jar"])

        assert command == ["java", "-cp", "/lib/junit.jar:.", "TestFile"]

    @pytest.mark.integration
    def test_compile_simple_java_file(self):
        """Integration test: Compile a simple Java file."""
        runner = JavaProcessTestRunner(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a simple Java file
            java_file = tmppath / "HelloWorld.java"
            java_file.write_text(
                """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
"""
            )

            config = TestRunnerConfig(
                main_test_file="HelloWorld",
                target_dir=tmppath,
            )

            result = runner.compile(config)

            assert result is True
            # Check that .class file was created
            assert (tmppath / "HelloWorld.class").exists()

    @pytest.mark.integration
    def test_compile_java_file_with_syntax_error(self):
        """Integration test: Compile a Java file with syntax error."""
        runner = JavaProcessTestRunner(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a Java file with syntax error
            java_file = tmppath / "BadCode.java"
            java_file.write_text(
                """
public class BadCode {
    public static void main(String[] args) {
        System.out.println("Missing semicolon")
    }
}
"""
            )

            config = TestRunnerConfig(
                main_test_file="BadCode",
                target_dir=tmppath,
            )

            result = runner.compile(config)

            assert result is False

    @pytest.mark.integration
    def test_run_simple_java_program(self):
        """Integration test: Run a simple Java program."""
        runner = JavaProcessTestRunner(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create and compile a simple Java file
            java_file = tmppath / "HelloWorld.java"
            java_file.write_text(
                """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
"""
            )

            config = TestRunnerConfig(
                main_test_file="HelloWorld",
                target_dir=tmppath,
            )

            # Compile first
            compile_result = runner.compile(config)
            assert compile_result is True

            # Run the program
            run_result = runner.run(config)

            assert run_result.exit_code == 0
            assert "Hello, World!" in run_result.stdout
            assert run_result.execution_time > 0

    @pytest.mark.integration
    def test_run_program_with_error(self):
        """Integration test: Run a program that exits with error."""
        runner = JavaProcessTestRunner(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a Java file that exits with error
            java_file = tmppath / "ErrorProgram.java"
            java_file.write_text(
                """
public class ErrorProgram {
    public static void main(String[] args) {
        System.err.println("Error occurred");
        System.exit(1);
    }
}
"""
            )

            config = TestRunnerConfig(
                main_test_file="ErrorProgram",
                target_dir=tmppath,
            )

            # Compile first
            compile_result = runner.compile(config)
            assert compile_result is True

            # Run the program
            run_result = runner.run(config)

            assert run_result.exit_code == 1
            assert "Error occurred" in run_result.stderr

    @pytest.mark.integration
    def test_compile_with_timeout(self):
        """Integration test: Compilation with timeout."""
        runner = JavaProcessTestRunner(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a simple Java file (won't actually timeout)
            java_file = tmppath / "SimpleClass.java"
            java_file.write_text(
                """
public class SimpleClass {
    public static void main(String[] args) {
        System.out.println("Simple");
    }
}
"""
            )

            config = TestRunnerConfig(
                main_test_file="SimpleClass",
                target_dir=tmppath,
                timeout=30,  # 30 seconds should be plenty
            )

            result = runner.compile(config)

            assert result is True

    @pytest.mark.integration
    def test_run_with_timeout(self):
        """Integration test: Run with timeout."""
        runner = JavaProcessTestRunner(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a program that runs quickly
            java_file = tmppath / "QuickProgram.java"
            java_file.write_text(
                """
public class QuickProgram {
    public static void main(String[] args) {
        System.out.println("Quick execution");
    }
}
"""
            )

            config = TestRunnerConfig(
                main_test_file="QuickProgram",
                target_dir=tmppath,
                timeout=30,
            )

            # Compile first
            compile_result = runner.compile(config)
            assert compile_result is True

            # Run the program
            run_result = runner.run(config)

            assert run_result.exit_code == 0
            assert "Quick execution" in run_result.stdout
