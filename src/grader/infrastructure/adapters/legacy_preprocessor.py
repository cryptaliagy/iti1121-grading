"""Legacy adapter for code preprocessing."""

from pathlib import Path

from grader._grader import CodeFilePreprocessingOptions, Writer, preprocess_codefile


class LegacyCodePreprocessorAdapter:
    """
    Adapter that wraps existing code preprocessing functionality.

    This adapter implements the CodePreprocessor protocol while maintaining
    backward compatibility with the existing implementation.
    """

    def __init__(
        self,
        writer: Writer,
        options: CodeFilePreprocessingOptions | None = None,
    ):
        """
        Initialize the adapter.

        Args:
            writer: Writer instance for console output
            options: Preprocessing options (defaults to removing package declarations)
        """
        self.writer = writer
        self.options = options or CodeFilePreprocessingOptions(
            remove_package_declaration=True
        )

    def preprocess(self, code_file: Path) -> None:
        """
        Preprocess a code file (e.g., remove package declarations).

        Args:
            code_file: Path to the code file to preprocess
        """
        preprocess_codefile(self.options, code_file, self.writer)
