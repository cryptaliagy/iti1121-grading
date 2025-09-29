"""Test cases for code preprocessing utilities."""

from pathlib import Path
from unittest.mock import Mock
from tempfile import TemporaryDirectory

import pytest

from grader.code_preprocessing import CodePreProcessor, PackageDeclarationHandler
from grader.common import FileOperationError
from grader.writer import Writer


class TestPreprocessCodefile:
    """Test cases for preprocess_codefile function."""

    def test_preprocess_codefile_remove_package_declaration(self):
        """Test removing package declaration from code file."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)

        processor.register_handler(PackageDeclarationHandler(writer=mock_writer))

        with TemporaryDirectory() as temp_dir:
            code_file = Path(temp_dir) / "Test.java"
            original_content = """package com.example.test;

public class Test {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}"""
            code_file.write_text(original_content)

            processor.preprocess(code_file)

            processed_content = code_file.read_text()

        assert "package com.example.test;" not in processed_content
        assert "public class Test {" in processed_content
        assert "Hello World" in processed_content
        # Two calls: one from handler, one from processor
        assert mock_writer.echo.call_count == 2

    def test_preprocess_codefile_keep_package_declaration(self):
        """Test keeping package declaration in code file."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            code_file = Path(temp_dir) / "Test.java"
            original_content = """package com.example.test;

public class Test {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}"""
            code_file.write_text(original_content)

            processor.preprocess(code_file)

            processed_content = code_file.read_text()

        assert "package com.example.test;" in processed_content
        assert "public class Test {" in processed_content
        # No handlers registered, so no writer calls
        assert mock_writer.echo.call_count == 0

    def test_preprocess_codefile_multiple_package_declarations(self):
        """Test removing multiple package declarations."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)
        processor.register_handler(PackageDeclarationHandler(writer=mock_writer))

        with TemporaryDirectory() as temp_dir:
            code_file = Path(temp_dir) / "Test.java"
            original_content = """package com.example.test;
package com.example.another;

public class Test {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}"""
            code_file.write_text(original_content)

            processor.preprocess(code_file)

            processed_content = code_file.read_text()

            assert "package com.example.test;" not in processed_content
            assert "package com.example.another;" not in processed_content
            assert "public class Test {" in processed_content

    def test_preprocess_codefile_package_with_whitespace(self):
        """Test removing package declaration with various whitespace."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)
        processor.register_handler(PackageDeclarationHandler(writer=mock_writer))

        with TemporaryDirectory() as temp_dir:
            code_file = Path(temp_dir) / "Test.java"
            original_content = """    package    com.example.test;

public class Test {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}"""
            code_file.write_text(original_content)

            processor.preprocess(code_file)

            processed_content = code_file.read_text()

            assert "package com.example.test;" not in processed_content
            assert "public class Test {" in processed_content

    def test_preprocess_codefile_no_package_declaration(self):
        """Test preprocessing file without package declaration."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)
        processor.register_handler(PackageDeclarationHandler(writer=mock_writer))

        with TemporaryDirectory() as temp_dir:
            code_file = Path(temp_dir) / "Test.java"
            original_content = """public class Test {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}"""
            code_file.write_text(original_content)

            processor.preprocess(code_file)

            processed_content = code_file.read_text()

        assert processed_content == original_content
        # Two calls: one from handler, one from processor
        assert mock_writer.echo.call_count == 2

    def test_preprocess_codefile_complex_package_name(self):
        """Test removing complex package declaration."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)
        processor.register_handler(PackageDeclarationHandler(writer=mock_writer))

        with TemporaryDirectory() as temp_dir:
            code_file = Path(temp_dir) / "Test.java"
            original_content = """package com.example.test.subpackage.more_subpackage;

public class Test {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}"""
            code_file.write_text(original_content)

            processor.preprocess(code_file)

            processed_content = code_file.read_text()

            assert (
                "package com.example.test.subpackage.more_subpackage;"
                not in processed_content
            )
            assert "public class Test {" in processed_content

    def test_preprocess_codefile_package_in_comment(self):
        """Test that package in comments is not removed."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)
        processor.register_handler(PackageDeclarationHandler(writer=mock_writer))

        with TemporaryDirectory() as temp_dir:
            code_file = Path(temp_dir) / "Test.java"
            original_content = """package com.example.test;

// This is a comment about package com.example.other
public class Test {
    // package keyword in comment should remain
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}"""
            code_file.write_text(original_content)

            processor.preprocess(code_file)

            processed_content = code_file.read_text()

            assert "package com.example.test;" not in processed_content
            assert (
                "// This is a comment about package com.example.other"
                in processed_content
            )
            assert "// package keyword in comment should remain" in processed_content

    def test_preprocess_codefile_nonexistent_file(self):
        """Test preprocessing nonexistent file."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)
        processor.register_handler(PackageDeclarationHandler(writer=mock_writer))

        with TemporaryDirectory() as temp_dir:
            code_file = Path(temp_dir) / "nonexistent.java"

            with pytest.raises(FileOperationError):
                processor.preprocess(code_file)

    def test_preprocess_codefile_empty_file(self):
        """Test preprocessing empty file."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)
        processor.register_handler(PackageDeclarationHandler(writer=mock_writer))

        with TemporaryDirectory() as temp_dir:
            code_file = Path(temp_dir) / "Empty.java"
            code_file.write_text("")

            processor.preprocess(code_file)

            processed_content = code_file.read_text()

        assert processed_content == ""
        # Two calls: one from handler, one from processor
        assert mock_writer.echo.call_count == 2

    def test_preprocess_codefile_preserves_file_structure(self):
        """Test that preprocessing preserves overall file structure."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)
        processor.register_handler(PackageDeclarationHandler(writer=mock_writer))

        with TemporaryDirectory() as temp_dir:
            code_file = Path(temp_dir) / "Test.java"
            original_content = """package com.example.test;

import java.util.List;
import java.util.ArrayList;

public class Test {
    private List<String> items;
    
    public Test() {
        items = new ArrayList<>();
    }
    
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}"""
            code_file.write_text(original_content)

            processor.preprocess(code_file)

            processed_content = code_file.read_text()

            assert "package com.example.test;" not in processed_content
            assert "import java.util.List;" in processed_content
            assert "import java.util.ArrayList;" in processed_content
            assert "public class Test {" in processed_content
            assert "private List<String> items;" in processed_content


class TestCollectCodeFiles:
    """Test cases for collect_code_files function."""

    def test_collect_code_files_single_file(self):
        """Test collecting single Java file."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            code_dir = Path(temp_dir) / "code"
            code_dir.mkdir()

            java_file = code_dir / "Test.java"
            java_file.write_text("public class Test {}")

            code_files = processor._collect_code_files(code_dir)

            assert len(code_files) == 1
            assert java_file in code_files
            mock_writer.echo.assert_called_once()

    def test_collect_code_files_multiple_files(self):
        """Test collecting multiple Java files."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            code_dir = Path(temp_dir) / "code"
            code_dir.mkdir()

            java_file1 = code_dir / "Test1.java"
            java_file2 = code_dir / "Test2.java"
            java_file3 = code_dir / "Helper.java"
            java_file1.write_text("public class Test1 {}")
            java_file2.write_text("public class Test2 {}")
            java_file3.write_text("public class Helper {}")

            code_files = processor._collect_code_files(code_dir)

            assert len(code_files) == 3
            assert java_file1 in code_files
            assert java_file2 in code_files
            assert java_file3 in code_files
            mock_writer.echo.assert_called_once()

    def test_collect_code_files_ignores_non_java_files(self):
        """Test that non-Java files are ignored."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            code_dir = Path(temp_dir) / "code"
            code_dir.mkdir()

            java_file = code_dir / "Test.java"
            txt_file = code_dir / "readme.txt"
            py_file = code_dir / "script.py"
            class_file = code_dir / "Test.class"

            java_file.write_text("public class Test {}")
            txt_file.write_text("This is a readme")
            py_file.write_text("print('hello')")
            class_file.write_text("compiled java")

            code_files = processor._collect_code_files(code_dir)

            assert len(code_files) == 1
            assert java_file in code_files
            assert txt_file not in code_files
            assert py_file not in code_files
            assert class_file not in code_files

    def test_collect_code_files_empty_directory(self):
        """Test collecting from empty directory."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            code_dir = Path(temp_dir) / "code"
            code_dir.mkdir()

            with pytest.raises(FileOperationError):
                processor._collect_code_files(code_dir)

    def test_collect_code_files_no_java_files(self):
        """Test collecting from directory with no Java files."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            code_dir = Path(temp_dir) / "code"
            code_dir.mkdir()

            txt_file = code_dir / "readme.txt"
            py_file = code_dir / "script.py"
            txt_file.write_text("This is a readme")
            py_file.write_text("print('hello')")

            with pytest.raises(FileOperationError):
                processor._collect_code_files(code_dir)

    def test_collect_code_files_nonexistent_directory(self):
        """Test collecting from nonexistent directory."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            code_dir = Path(temp_dir) / "nonexistent"

            with pytest.raises(FileOperationError):
                processor._collect_code_files(code_dir)

    def test_collect_code_files_directory_is_file(self):
        """Test collecting when directory path is actually a file."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            code_file = Path(temp_dir) / "code.java"
            code_file.write_text("public class Test {}")

            with pytest.raises(FileOperationError):
                processor._collect_code_files(code_file)

    def test_collect_code_files_subdirectories_ignored(self):
        """Test that subdirectories are ignored."""
        mock_writer = Mock(spec=Writer)
        processor = CodePreProcessor(writer=mock_writer)

        with TemporaryDirectory() as temp_dir:
            code_dir = Path(temp_dir) / "code"
            code_dir.mkdir()

            # Create java file in main directory
            java_file = code_dir / "Test.java"
            java_file.write_text("public class Test {}")

            # Create subdirectory with java file
            subdir = code_dir / "subdir"
            subdir.mkdir()
            sub_java_file = subdir / "SubTest.java"
            sub_java_file.write_text("public class SubTest {}")

            code_files = processor._collect_code_files(code_dir)

            assert len(code_files) == 1
            assert java_file in code_files
            assert sub_java_file not in code_files
