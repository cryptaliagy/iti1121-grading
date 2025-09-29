"""Code file preprocessing utilities."""

import re
from pathlib import Path

from .common import FileOperationError
from .writer import Writer
from .protocols import PreProcessingHandler


class CodePreProcessor:
    preprocessors: "list[PreProcessingHandler]"

    def __init__(self, writer: Writer):
        """
        Initialize the preprocessor with a Writer for console output.

        Args:
            writer: Writer object for console output
        """
        self.writer = writer
        self.preprocessors = []

    def register_handler(self, handler: PreProcessingHandler):
        """
        Register a preprocessing handler.

        Args:
            handler: An instance of a class implementing PreProcessingHandler
        """
        self.preprocessors.append(handler)

    def preprocess(self, code_file: Path):
        """
        Preprocess the code file using registered handlers.

        Args:
            code_file: Path to the code file to preprocess

        Raises:
            FileOperationError: If the code file does not exist
        """
        if not code_file.exists():
            raise FileOperationError(f"Code file {code_file} does not exist.")

        for handler in self.preprocessors:
            handler.preprocess(code_file)
            self.writer.echo(
                f"Preprocessed {code_file} with {handler.__class__.__name__}"
            )

    def _collect_code_files(self, code_dir: Path) -> list[Path]:
        """
        Collect all Java code files from the specified directory.

        Args:
            code_dir: Directory to search for Java code files

        Returns:
            List of Path objects for Java code files found in the directory
        """
        if not code_dir.exists() or not code_dir.is_dir():
            raise FileOperationError(f"Code directory {code_dir} does not exist.")

        java_files = list(code_dir.glob("*.java"))
        if not java_files:
            raise FileOperationError(f"No Java files found in {code_dir}")

        self.writer.echo(f"Found {len(java_files)} Java files in {code_dir}")
        return java_files

    def preprocess_directory(self, code_dir: Path):
        """
        Preprocess all code files in the specified directory.

        Args:
            code_dir: Directory containing code files to preprocess
        """
        if not code_dir.exists() or not code_dir.is_dir():
            raise FileOperationError(f"Code directory {code_dir} does not exist.")

        for code_file in self._collect_code_files(code_dir):
            try:
                self.preprocess(code_file)
            except FileOperationError as e:
                self.writer.echo(f"Error preprocessing {code_file}: {e}")


class PackageDeclarationHandler:
    def __init__(self, writer: Writer):
        """
        Initialize the preprocessor with a Writer for console output.

        Args:
            writer: Writer object for console output
        """
        self.writer = writer
        self.regex = re.compile(
            r"^\s*package\s+[a-zA-Z][a-zA-Z0-9_.]*;\s*", re.MULTILINE
        )

    def preprocess(self, code_file: Path) -> None:
        """
        Preprocess the code file to remove package declarations.

        Args:
            code_file: Path to the code file to preprocess

        Raises:
            FileOperationError: If the code file does not exist
        """
        if not code_file.exists():
            raise FileOperationError(f"Code file {code_file} does not exist.")

        # Read the original content
        with code_file.open("r") as f:
            content = f.read()

        # Remove package declaration
        content = self.regex.sub("", content)

        # Write the modified content back to the file
        with code_file.open("w") as f:
            f.write(content)

        self.writer.echo(f"Preprocessed {code_file} successfully")
