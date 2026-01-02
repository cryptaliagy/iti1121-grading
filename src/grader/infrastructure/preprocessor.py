"""Code preprocessor implementations for modifying code before compilation."""

import re
from pathlib import Path
from typing import Protocol


class PreprocessingRule(Protocol):
    """Protocol for individual preprocessing rules."""

    def apply(self, content: str, file_path: Path) -> str:
        """
        Apply a preprocessing rule to code content.

        Args:
            content: The code content to preprocess
            file_path: Path to the file (for context)

        Returns:
            Preprocessed code content
        """
        ...


class PackageRemovalRule:
    """Preprocessing rule that removes package declarations from Java code."""

    # Match package declarations with optional leading whitespace, package name, semicolon, and trailing newline
    PACKAGE_DECLARATION_PATTERN = r"^\s*package\s+[\w.]+\s*;\s*\n?"

    def apply(self, content: str, file_path: Path) -> str:
        """
        Remove package declarations from Java code.

        Args:
            content: The code content to preprocess
            file_path: Path to the file (for context)

        Returns:
            Code with package declarations removed
        """
        return re.sub(
            self.PACKAGE_DECLARATION_PATTERN,
            "",
            content,
            flags=re.MULTILINE,
        )


class CompositePreprocessor:
    """Preprocessor that chains multiple preprocessing rules."""

    def __init__(self, rules: list[PreprocessingRule] | None = None):
        """
        Initialize the composite preprocessor.

        Args:
            rules: List of preprocessing rules to apply in order
        """
        self.rules = rules or []

    def add_rule(self, rule: PreprocessingRule) -> None:
        """
        Add a preprocessing rule to the chain.

        Args:
            rule: Preprocessing rule to add
        """
        self.rules.append(rule)

    def preprocess(self, code_file: Path) -> None:
        """
        Preprocess a code file by applying all rules in sequence.

        Args:
            code_file: Path to the code file to preprocess

        Raises:
            FileNotFoundError: If the code file doesn't exist
        """
        if not code_file.exists():
            raise FileNotFoundError(f"Code file {code_file} does not exist")

        # Read the original content
        with code_file.open("r", encoding="utf-8") as f:
            content = f.read()

        # Apply all rules in sequence
        for rule in self.rules:
            content = rule.apply(content, code_file)

        # Write the modified content back to the file
        with code_file.open("w", encoding="utf-8") as f:
            f.write(content)


class PackageRemovalPreprocessor:
    """Preprocessor that removes package declarations from code files."""

    def __init__(self):
        """Initialize the package removal preprocessor."""
        self.rule = PackageRemovalRule()

    def preprocess(self, code_file: Path) -> None:
        """
        Preprocess a code file to remove package declarations.

        Args:
            code_file: Path to the code file to preprocess

        Raises:
            FileNotFoundError: If the code file doesn't exist
        """
        if not code_file.exists():
            raise FileNotFoundError(f"Code file {code_file} does not exist")

        # Read the original content
        with code_file.open("r", encoding="utf-8") as f:
            content = f.read()

        # Apply the package removal rule
        content = self.rule.apply(content, code_file)

        # Write the modified content back to the file
        with code_file.open("w", encoding="utf-8") as f:
            f.write(content)
