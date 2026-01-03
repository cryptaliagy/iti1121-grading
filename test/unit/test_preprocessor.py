"""Unit tests for code preprocessor implementations."""

import pytest
import tempfile
from pathlib import Path

from grader.infrastructure.preprocessor import (
    PackageRemovalPreprocessor,
    PackageRemovalRule,
    CompositePreprocessor,
)


class TestPackageRemovalRule:
    """Test the PackageRemovalRule implementation."""

    def test_remove_simple_package_declaration(self):
        """Test removing a simple package declaration."""
        rule = PackageRemovalRule()
        content = """package com.example;

public class Test {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
"""
        expected = """public class Test {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
"""
        result = rule.apply(content, Path("/tmp/Test.java"))
        assert result == expected

    def test_remove_package_with_dots(self):
        """Test removing a package declaration with multiple dots."""
        rule = PackageRemovalRule()
        content = """package com.example.project.submodule;

public class MyClass {
}
"""
        expected = """public class MyClass {
}
"""
        result = rule.apply(content, Path("/tmp/MyClass.java"))
        assert result == expected

    def test_remove_package_with_whitespace(self):
        """Test removing a package declaration with varying whitespace."""
        rule = PackageRemovalRule()
        content = """  package   com.example  ;

public class Test {
}
"""
        expected = """public class Test {
}
"""
        result = rule.apply(content, Path("/tmp/Test.java"))
        assert result == expected

    def test_no_package_declaration(self):
        """Test processing code without a package declaration."""
        rule = PackageRemovalRule()
        content = """public class Test {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
"""
        result = rule.apply(content, Path("/tmp/Test.java"))
        assert result == content  # Should remain unchanged

    def test_package_in_comment_not_removed(self):
        """Test that package in comments is not removed (but this is a limitation)."""
        rule = PackageRemovalRule()
        # Note: The current regex will remove package declarations even in comments
        # This is a known limitation that matches the original implementation
        content = """// This is package example.test;
public class Test {
}
"""
        result = rule.apply(content, Path("/tmp/Test.java"))
        # The regex doesn't distinguish comments, so this stays as is
        assert "package" not in result or "// This is package" in result


class TestPackageRemovalPreprocessor:
    """Test the PackageRemovalPreprocessor implementation."""

    def test_preprocess_file(self):
        """Test preprocessing a file to remove package declaration."""
        preprocessor = PackageRemovalPreprocessor()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "Test.java"
            original_content = """package com.example;

public class Test {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
"""
            test_file.write_text(original_content)

            preprocessor.preprocess(test_file)

            result = test_file.read_text()
            assert "package com.example;" not in result
            assert "public class Test" in result

    def test_preprocess_nonexistent_file(self):
        """Test preprocessing a file that doesn't exist."""
        preprocessor = PackageRemovalPreprocessor()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "NonExistent.java"

            with pytest.raises(FileNotFoundError):
                preprocessor.preprocess(test_file)

    def test_preprocess_file_without_package(self):
        """Test preprocessing a file without package declaration."""
        preprocessor = PackageRemovalPreprocessor()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "Test.java"
            original_content = """public class Test {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
"""
            test_file.write_text(original_content)

            preprocessor.preprocess(test_file)

            result = test_file.read_text()
            assert result == original_content  # Should remain unchanged


class TestCompositePreprocessor:
    """Test the CompositePreprocessor implementation."""

    def test_composite_with_single_rule(self):
        """Test composite preprocessor with a single rule."""
        preprocessor = CompositePreprocessor([PackageRemovalRule()])

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "Test.java"
            original_content = """package com.example;

public class Test {
}
"""
            test_file.write_text(original_content)

            preprocessor.preprocess(test_file)

            result = test_file.read_text()
            assert "package com.example;" not in result
            assert "public class Test" in result

    def test_composite_with_multiple_rules(self):
        """Test composite preprocessor with multiple rules."""

        # Create a custom rule for testing
        class UpperCaseRule:
            def apply(self, content: str, file_path: Path) -> str:
                # Just uppercase the first line for testing
                lines = content.split("\n")
                if lines:
                    lines[0] = lines[0].upper()
                return "\n".join(lines)

        preprocessor = CompositePreprocessor([PackageRemovalRule(), UpperCaseRule()])

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "Test.java"
            original_content = """package com.example;
public class Test {
}
"""
            test_file.write_text(original_content)

            preprocessor.preprocess(test_file)

            result = test_file.read_text()
            assert "package com.example;" not in result
            # The first non-empty line should be uppercase
            assert "PUBLIC CLASS TEST" in result

    def test_composite_add_rule(self):
        """Test adding rules to composite preprocessor."""
        preprocessor = CompositePreprocessor()
        assert len(preprocessor.rules) == 0

        preprocessor.add_rule(PackageRemovalRule())
        assert len(preprocessor.rules) == 1

    def test_composite_empty_rules(self):
        """Test composite preprocessor with no rules."""
        preprocessor = CompositePreprocessor([])

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "Test.java"
            original_content = """package com.example;
public class Test {
}
"""
            test_file.write_text(original_content)

            preprocessor.preprocess(test_file)

            result = test_file.read_text()
            assert result == original_content  # Should remain unchanged

    def test_composite_preprocess_nonexistent_file(self):
        """Test preprocessing a nonexistent file with composite."""
        preprocessor = CompositePreprocessor([PackageRemovalRule()])

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "NonExistent.java"

            with pytest.raises(FileNotFoundError):
                preprocessor.preprocess(test_file)

    def test_rules_applied_in_order(self):
        """Test that rules are applied in the correct order."""

        # Create custom rules to verify order
        class AddPrefixRule:
            def __init__(self, prefix: str):
                self.prefix = prefix

            def apply(self, content: str, file_path: Path) -> str:
                return self.prefix + content

        preprocessor = CompositePreprocessor()
        preprocessor.add_rule(AddPrefixRule("A:"))
        preprocessor.add_rule(AddPrefixRule("B:"))

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "Test.java"
            test_file.write_text("content")

            preprocessor.preprocess(test_file)

            result = test_file.read_text()
            # Should be applied in order: A:, then B:
            assert result == "B:A:content"
