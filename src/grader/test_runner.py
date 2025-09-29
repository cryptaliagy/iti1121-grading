"""Java compilation and execution utilities."""

import os
import subprocess  # nosec: B404
import sys
import re
from pathlib import Path

from .writer import Writer


class JavaTestRunner:
    """
    Class to handle test compilation and execution.
    """

    def __init__(
        self,
        writer: Writer,
        classpath: list[str] | None = None,
    ):
        self.writer = writer
        if classpath:
            if "." not in classpath:
                classpath.append(".")
            resolved = []
            for entry in classpath:
                entry = Path(entry).resolve()
                if not entry.exists():
                    raise FileNotFoundError(
                        f"Classpath entry '{entry}' does not exist."
                    )
                resolved.append(str(entry))
            classpath_string = ":".join(resolved)
            self.compile_command = [
                "javac",
                "-cp",
                classpath_string,
            ]
            self.run_command = ["java", "-cp", classpath_string]
        else:
            self.compile_command = ["javac"]
            self.run_command = ["java"]

    def compile_test(self, target_dir: Path, test_file: str) -> bool:
        """
        Compile the main test file using javac.

        Args:
            target_dir: Directory where the file is located
            target_dir: Directory where the file is located

        Returns:
            True if compilation succeeded, False otherwise
        """
        # Change to the target directory
        original_dir = os.getcwd()
        os.chdir(target_dir)

        try:
            command = self.compile_command + [f"{test_file}.java"]
            self.writer.always_echo(f"Running: {' '.join(command)}\n")

            result = subprocess.run(  # nosec: B603
                command,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                self.writer.always_echo("Compilation [red]failed[/red] with error:")
                self.writer.always_echo(result.stderr)
                return False

            self.writer.always_echo("[green]Compilation successful![/green]")
            return True
        finally:
            # Always change back to the original directory
            os.chdir(original_dir)

    def run_test(self, target_dir: Path, test_file: str) -> tuple[bool, float, float]:
        """
        Run the compiled test using java.

        Args:
            main_test_file: Name of the main test file (without extension)
            target_dir: Directory where the file is located

        Returns:
            Tuple containing:
                - Success status (boolean)
                - Total points earned (float)
                - Total possible points (float)
        """
        # Change to the target directory
        original_dir = os.getcwd()
        os.chdir(target_dir)

        try:
            command = self.run_command + [test_file]
            self.writer.always_echo(f"Running: {' '.join(command)}\n")

            result = subprocess.run(command, capture_output=True, text=True)  # nosec: B603
            output = result.stdout

            self.writer.always_echo(output)
            self.writer.always_echo(result.stderr)

            if result.returncode != 0:
                self.writer.always_echo(
                    f"[yellow]Grader.py[/yellow]: Test execution [red]failed[/red] with exit code: {result.returncode}"
                )
                sys.exit(result.returncode)

            # Parse the output to calculate the total grade
            total_points, possible_points = self._calculate_grade_from_output(output)

            # Display the results
            self._display_grade_summary(total_points, possible_points)
            return True, total_points, possible_points

        finally:
            # Always change back to the original directory
            os.chdir(original_dir)

    def _calculate_grade_from_output(self, output: str) -> tuple[float, float]:
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

    def _display_grade_summary(
        self, total_points: float, possible_points: float
    ) -> None:
        """
        Display a summary of the test results.

        Args:
            total_points: Total points earned
            possible_points: Total points possible
        """
        if possible_points > 0:
            percentage = (total_points / possible_points) * 100
            self.writer.always_echo("\n" + "=" * 60)
            self.writer.always_echo("Final Grade Summary:")
            self.writer.always_echo(
                f"Total Points: {total_points:.1f} / {possible_points:.1f}"
            )
            self.writer.always_echo(f"Percentage: {percentage:.1f}%")
            self.writer.always_echo("=" * 60)
