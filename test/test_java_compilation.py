"""Test cases for Java compilation utilities."""

from pathlib import Path
from unittest.mock import Mock, patch
from tempfile import TemporaryDirectory

import pytest

from grader.test_runner import JavaTestRunner
from grader.writer import Writer


class TestBuildCompileCommand:
    """Test cases for build_compile_command function."""

    def test_build_compile_command_no_classpath(self):
        """Test building compile command without classpath."""
        writer = Mock(spec=Writer)
        command = JavaTestRunner(
            writer=writer,
        ).compile_command + ["TestL1.java"]
        assert command == ["javac", "TestL1.java"]

    def test_build_compile_command_with_classpath(self):
        """Test building compile command with classpath."""
        with TemporaryDirectory() as temp_dir:
            classpath_dir1 = Path(temp_dir) / "lib1"
            classpath_dir2 = Path(temp_dir) / "lib2"
            classpath_dir1.mkdir()
            classpath_dir2.mkdir()

            classpath = [str(classpath_dir1), str(classpath_dir2)]
            writer = Mock(spec=Writer)
            command = JavaTestRunner(
                writer=writer, classpath=classpath
            ).compile_command + ["TestL1.java"]
            # Check that command has expected structure - the exact path order can vary
            assert command[0] == "javac"
            assert command[1] == "-cp"
            assert str(classpath_dir1) in command[2]
            assert str(classpath_dir2) in command[2]
            assert "TestL1.java" in command

    def test_build_compile_command_with_classpath_including_dot(self):
        """Test building compile command with classpath that includes current directory."""
        with TemporaryDirectory() as temp_dir:
            classpath_dir1 = Path(temp_dir) / "lib1"
            classpath_dir2 = Path(temp_dir) / "lib2"
            classpath_dir1.mkdir()
            classpath_dir2.mkdir()

            classpath = [str(classpath_dir1), ".", str(classpath_dir2)]
            writer = Mock(spec=Writer)
            command = JavaTestRunner(
                writer=writer, classpath=classpath
            ).compile_command + ["TestL1.java"]
            # Check that command has expected structure
            assert command[0] == "javac"
            assert command[1] == "-cp"
            assert str(classpath_dir1) in command[2]
            assert str(classpath_dir2) in command[2]
            # Current directory should be included (as resolved path)
            assert str(Path.cwd()) in command[2]
            assert "TestL1.java" in command

    def test_build_compile_command_empty_classpath(self):
        """Test building compile command with empty classpath."""
        writer = Mock(spec=Writer)
        command = JavaTestRunner(writer=writer, classpath=[]).compile_command + [
            "TestL1.java"
        ]
        assert command == ["javac", "TestL1.java"]


class TestBuildRunCommand:
    """Test cases for build_run_command function."""

    def test_build_run_command_no_classpath(self):
        """Test building run command without classpath."""
        command = JavaTestRunner(writer=Mock(spec=Writer)).run_command + ["TestL1"]
        assert command == ["java", "TestL1"]

    def test_build_run_command_with_classpath(self):
        """Test building run command with classpath."""
        with TemporaryDirectory() as temp_dir:
            classpath_dir1 = Path(temp_dir) / "lib1"
            classpath_dir2 = Path(temp_dir) / "lib2"
            classpath_dir1.mkdir()
            classpath_dir2.mkdir()

            classpath = [str(classpath_dir1), str(classpath_dir2)]
            command = JavaTestRunner(
                writer=Mock(spec=Writer), classpath=classpath
            ).run_command + ["TestL1"]

            # Check that command has expected structure
            assert command[0] == "java"
            assert command[1] == "-cp"
            assert str(classpath_dir1) in command[2]
            assert str(classpath_dir2) in command[2]
            assert "TestL1" in command

    def test_build_run_command_with_classpath_including_dot(self):
        """Test building run command with classpath that includes current directory."""
        with TemporaryDirectory() as temp_dir:
            classpath_dir1 = Path(temp_dir) / "lib1"
            classpath_dir2 = Path(temp_dir) / "lib2"
            classpath_dir1.mkdir()
            classpath_dir2.mkdir()

            classpath = [str(classpath_dir1), ".", str(classpath_dir2)]
            command = JavaTestRunner(
                writer=Mock(spec=Writer), classpath=classpath
            ).run_command + ["TestL1"]
            # Check that command has expected structure
            assert command[0] == "java"
            assert command[1] == "-cp"
            assert str(classpath_dir1) in command[2]
            assert str(classpath_dir2) in command[2]
            # Current directory should be included (as resolved path)
            assert str(Path.cwd()) in command[2]
            assert "TestL1" in command

    def test_build_run_command_empty_classpath(self):
        """Test building run command with empty classpath."""
        command = JavaTestRunner(writer=Mock(spec=Writer), classpath=[]).run_command + [
            "TestL1"
        ]
        assert command == ["java", "TestL1"]


class TestCompileTest:
    """Test cases for compile_test function."""

    def test_compile_test_success(self):
        """Test successful compilation."""
        mock_writer = Mock(spec=Writer)
        test_runner = JavaTestRunner(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)

            # Create a dummy Java file
            java_file = target_dir / "TestL1.java"
            java_file.write_text(
                "public class TestL1 { public static void main(String[] args) {} }"
            )

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stderr = ""

                result = test_runner.compile_test(target_dir, "TestL1")

                assert result is True
                mock_writer.always_echo.assert_called()
                mock_run.assert_called_once()

    def test_compile_test_failure(self):
        """Test compilation failure."""
        mock_writer = Mock(spec=Writer)
        test_runner = JavaTestRunner(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stderr = "Compilation error"

                result = test_runner.compile_test(target_dir, "TestL1")

                assert result is False
                mock_writer.always_echo.assert_called()

    def test_compile_test_with_classpath(self):
        """Test compilation with classpath."""
        mock_writer = Mock(spec=Writer)

        with TemporaryDirectory() as temp_dir:
            classpath_dir = Path(temp_dir) / "lib"
            classpath_dir.mkdir()
            classpath = [str(classpath_dir)]
            test_runner = JavaTestRunner(writer=mock_writer, classpath=classpath)
            target_dir = Path(temp_dir)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stderr = ""

                result = test_runner.compile_test(target_dir, "TestL1")

                assert result is True
                # Check that subprocess.run was called with classpath
                args, kwargs = mock_run.call_args
                # The classpath should be in the command (at index 2)
                assert "-cp" in args[0]
                cp_index = args[0].index("-cp")
                assert str(classpath_dir) in args[0][cp_index + 1]

    @patch("os.getcwd")
    @patch("os.chdir")
    def test_compile_test_directory_handling(self, mock_chdir, mock_getcwd):
        """Test that compile_test properly handles directory changes."""
        mock_writer = Mock(spec=Writer)
        mock_getcwd.return_value = "/original/dir"
        test_runner = JavaTestRunner(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stderr = ""

                _ = test_runner.compile_test(target_dir, "TestL1")

                # Check that directory was changed to target_dir and back
                mock_chdir.assert_any_call(target_dir)
                mock_chdir.assert_any_call("/original/dir")

    @patch("os.getcwd")
    @patch("os.chdir")
    def test_compile_test_directory_restore_on_exception(self, mock_chdir, mock_getcwd):
        """Test that compile_test restores directory even on exception."""
        mock_writer = Mock(spec=Writer)
        mock_getcwd.return_value = "/original/dir"
        test_runner = JavaTestRunner(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = Exception("Subprocess error")

                with pytest.raises(Exception):
                    test_runner.compile_test(target_dir, "TestL1")

                # Check that directory was restored even after exception
                mock_chdir.assert_any_call("/original/dir")


class TestRunTest:
    """Test cases for run_test function."""

    def test_run_test_success(self):
        """Test successful test execution."""
        mock_writer = Mock(spec=Writer)
        test_runner = JavaTestRunner(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = (
                    "Grade for test1 (out of possible 10): 8.5"
                )
                mock_run.return_value.stderr = ""

                success, total_points, possible_points = test_runner.run_test(
                    target_dir, "TestL1"
                )

                assert success is True
                assert total_points == 8.5
                assert possible_points == 10.0
                mock_writer.always_echo.assert_called()

    def test_run_test_with_classpath(self):
        """Test test execution with classpath."""
        mock_writer = Mock(spec=Writer)

        with TemporaryDirectory() as temp_dir:
            classpath_dir = Path(temp_dir) / "lib"
            classpath_dir.mkdir()
            classpath = [str(classpath_dir)]
            test_runner = JavaTestRunner(writer=mock_writer, classpath=classpath)
            target_dir = Path(temp_dir)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = (
                    "Grade for test1 (out of possible 10): 10.0"
                )
                mock_run.return_value.stderr = ""

                success, total_points, possible_points = test_runner.run_test(
                    target_dir, "TestL1"
                )

                assert success is True
                assert total_points == 10.0
                assert possible_points == 10.0
                # Check that subprocess.run was called with classpath
                args, kwargs = mock_run.call_args
                # The classpath should be in the command
                assert "-cp" in args[0]
                cp_index = args[0].index("-cp")
                assert str(classpath_dir) in args[0][cp_index + 1]

    def test_run_test_failure(self):
        """Test test execution failure."""
        mock_writer = Mock(spec=Writer)
        test_runner = JavaTestRunner(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stdout = "Test output"
                mock_run.return_value.stderr = "Error output"

                with pytest.raises(SystemExit) as exc_info:
                    test_runner.run_test(target_dir, "TestL1")

                assert exc_info.value.code == 1

    @patch("os.getcwd")
    @patch("os.chdir")
    def test_run_test_directory_handling(self, mock_chdir, mock_getcwd):
        """Test that run_test properly handles directory changes."""
        mock_writer = Mock(spec=Writer)
        mock_getcwd.return_value = "/original/dir"
        test_runner = JavaTestRunner(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = (
                    "Grade for test1 (out of possible 10): 10.0"
                )
                mock_run.return_value.stderr = ""

                test_runner.run_test(target_dir, "TestL1")

                # Check that directory was changed to target_dir and back
                mock_chdir.assert_any_call(target_dir)
                mock_chdir.assert_any_call("/original/dir")

    @patch("os.getcwd")
    @patch("os.chdir")
    def test_run_test_directory_restore_on_exception(self, mock_chdir, mock_getcwd):
        """Test that run_test restores directory even on exception."""
        mock_writer = Mock(spec=Writer)
        mock_getcwd.return_value = "/original/dir"
        test_runner = JavaTestRunner(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = Exception("Subprocess error")

                with pytest.raises(Exception):
                    test_runner.run_test(target_dir, "TestL1")

                # Check that directory was restored even after exception
                mock_chdir.assert_any_call("/original/dir")

    def test_run_test_output_processing(self):
        """Test that run_test properly processes output."""
        mock_writer = Mock(spec=Writer)
        test_runner = JavaTestRunner(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = (
                    "Grade for test1 (out of possible 7.5): 7.5"
                )
                mock_run.return_value.stderr = "Test stderr"

                success, total_points, possible_points = test_runner.run_test(
                    target_dir, "TestL1"
                )

                # Check that both stdout and stderr were echoed
                assert mock_writer.always_echo.call_count >= 2
                # Check grade calculation
                assert total_points == 7.5
                assert possible_points == 7.5
