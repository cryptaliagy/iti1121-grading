# Infrastructure Layer

This directory contains the infrastructure layer implementations for the grading system, following the modular architecture design documented in `docs/ModularArchitecture.md`.

## Overview

The infrastructure layer provides concrete implementations of low-level operations such as:
- File system operations (reading, writing, copying files)
- Test execution (compiling and running Java tests)
- Submission processing (extracting and preparing submissions)
- Code preprocessing (removing package declarations, etc.)
- Gradebook I/O (loading students, saving grades)

## Components

### File System (`filesystem.py`)

**Purpose**: Abstract file system operations for easier testing and future extensibility.

**Implementations**:
- `LocalFileSystem`: Real file system operations using Python's standard library
- `InMemoryFileSystem`: In-memory file system for testing without disk I/O

**Usage**:
```python
from grader.infrastructure import LocalFileSystem

fs = LocalFileSystem()
content = fs.read_file(Path("/path/to/file.txt"))
fs.write_file(Path("/path/to/output.txt"), "Hello, World!")
```

### Test Runner (`test_runner.py`)

**Purpose**: Compile and execute Java tests, capturing output and results.

**Implementations**:
- `JavaProcessTestRunner`: Runs tests using `javac` and `java` commands
- `MockTestRunner`: Mock implementation for testing without actual Java execution

**Usage**:
```python
from grader.infrastructure import JavaProcessTestRunner, TestRunnerConfig
from pathlib import Path

runner = JavaProcessTestRunner(verbose=True)
config = TestRunnerConfig(
    main_test_file="TestL1Q1",
    target_dir=Path("/path/to/grading"),
    classpath=["/path/to/junit.jar"]
)

# Compile
success = runner.compile(config)

# Run
if success:
    result = runner.run(config)
    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.stdout}")
```

### Code Preprocessor (`preprocessor.py`)

**Purpose**: Modify code files before compilation (e.g., remove package declarations).

**Implementations**:
- `PackageRemovalPreprocessor`: Removes Java package declarations
- `PackageRemovalRule`: Individual preprocessing rule for package removal
- `CompositePreprocessor`: Chains multiple preprocessing rules

**Usage**:
```python
from grader.infrastructure import PackageRemovalPreprocessor
from pathlib import Path

preprocessor = PackageRemovalPreprocessor()
preprocessor.preprocess(Path("/path/to/Student.java"))

# Or use composite for multiple rules
from grader.infrastructure import CompositePreprocessor, PackageRemovalRule

preprocessor = CompositePreprocessor([
    PackageRemovalRule(),
    # Add more rules here
])
preprocessor.preprocess(Path("/path/to/Student.java"))
```

### Submission Processor (`submission_processor.py`)

**Purpose**: Extract and prepare student submissions for grading.

**Implementations**:
- `ZipSubmissionProcessor`: Handles ZIP file extraction and directory flattening

**Usage**:
```python
from grader.infrastructure import ZipSubmissionProcessor
from pathlib import Path

processor = ZipSubmissionProcessor(verbose=True)

# Extract main submissions ZIP
submissions_dir = processor.extract_submission(
    Path("/path/to/submissions.zip"),
    Path("/tmp")
)

# Prepare individual submission for grading
grading_dir = processor.prepare_grading_directory(
    Path("/path/to/student_submission"),
    Path("/tmp/grading")
)
```

### Gradebook Repository (`gradebook.py`)

**Purpose**: Load student records and save grading results to CSV files.

**Implementations**:
- `CSVGradebookRepository`: CSV-based gradebook operations

**Usage**:
```python
from grader.infrastructure import CSVGradebookRepository
from pathlib import Path

repo = CSVGradebookRepository(assignment_name="Lab1")

# Load students
students = repo.load_students(Path("/path/to/students.csv"))

# Save grades (after grading)
repo.save_grades(
    results=grading_results,
    original_csv_path=Path("/path/to/students.csv"),
    output_path=Path("/path/to/results.csv"),
    failure_is_null=False
)
```

## Protocols

All implementations follow the protocols defined in `protocols.py`:
- `FileSystem`: File operations interface
- `TestRunner`: Test compilation and execution interface
- `CodePreprocessor`: Code preprocessing interface
- `SubmissionProcessor`: Submission extraction interface

These protocols enable:
- **Dependency injection**: Swap implementations easily
- **Testing**: Use mock/in-memory implementations
- **Extensibility**: Add new implementations without changing calling code

## Testing

Each component has comprehensive unit tests in `test/unit/`:
- `test_filesystem.py`: FileSystem implementations
- `test_test_runner.py`: TestRunner implementations
- `test_preprocessor.py`: Preprocessor implementations
- `test_submission_processor.py`: SubmissionProcessor implementations
- `test_gradebook.py`: Gradebook repository implementations

Run tests with:
```bash
pytest test/unit/
```

## Design Principles

These implementations follow:
1. **Single Responsibility**: Each class has one clear purpose
2. **Protocol-Based Design**: All follow well-defined interfaces
3. **Testability**: Easy to test with mocks and in-memory implementations
4. **Minimal Dependencies**: Rely on standard library where possible
5. **Error Handling**: Proper exception handling with informative messages

## Future Enhancements

Potential future implementations:
- `DockerTestRunner`: Run tests in Docker containers
- `S3FileSystem`: File operations on AWS S3
- `DatabaseGradebookRepository`: Store grades in a database
- `GitSubmissionProcessor`: Process submissions from Git repositories
