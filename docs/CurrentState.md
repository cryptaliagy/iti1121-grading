# Current State Documentation

## Overview

The ITI 1121 Grading Tool is a Python-based CLI application designed to automate the grading of Java programming assignments for the ITI 1121 course at the University of Ottawa. The tool provides both single submission grading and bulk grading capabilities, handling the entire workflow from submission extraction to grade calculation and CSV output for LMS import.

## Repository Objective

The primary objectives of this repository are to:

1. **Automate Java Test Execution**: Automatically compile and run Java test files against student submissions
2. **Simplify Bulk Grading**: Process entire classes worth of submissions efficiently from ZIP files downloaded from learning management systems
3. **Integrate with Gradebooks**: Output grades in CSV format compatible with LMS gradebook imports
4. **Handle Common Edge Cases**: Deal with file permissions, ZIP extraction, name matching, and various submission formats
5. **Provide Clear Reporting**: Generate comprehensive reports on grading outcomes, failures, and missing submissions

## Current Architecture

### High-Level Structure

The codebase is organized as a Python package with the following structure:

```
src/grader/
├── __init__.py          # Package initialization
├── __main__.py          # CLI entry point and command orchestration
├── _grader.py           # Single submission grading logic
└── bulk_grader.py       # Bulk grading logic
```

### Component Overview

#### 1. CLI Entry Point (`__main__.py`)

- Uses Typer framework to create a multi-command CLI
- Registers two sub-commands: `single` and `bulk`
- Minimal orchestration layer that delegates to specialized modules

#### 2. Single Submission Grader (`_grader.py`)

**Core Responsibilities:**
- Finding and copying Java test files
- Compiling test files using `javac`
- Running compiled tests using `java`
- Parsing test output to calculate grades
- File permission management
- Code preprocessing (e.g., removing package declarations)

**Key Components:**
- `Writer`: Conditional console output based on verbosity
- `FileOperationError`: Custom exception for file operation failures
- `CodeFilePreprocessingOptions`: Configuration for code preprocessing
- File operation utilities: `find_test_files()`, `copy_test_files()`, `safe_copy_file()`, `safe_delete_file()`
- Compilation and execution: `compile_test()`, `run_test()`, `build_compile_command()`, `build_run_command()`
- Grade calculation: `calculate_grade_from_output()`, `display_grade_summary()`
- Permission management: `add_write_permission()`, `ensure_directory_writable()`
- Code preprocessing: `preprocess_codefile()`, `collect_code_files()`

#### 3. Bulk Grader (`bulk_grader.py`)

**Core Responsibilities:**
- Extracting submissions from ZIP files
- Parsing submission folder names to extract student information and timestamps
- Fuzzy name matching between submissions and gradebook records
- Processing multiple submissions in sequence
- Generating comprehensive post-grading reports
- CSV input/output for gradebook integration

**Key Components:**
- `StudentRecord`: Data class representing a student from the CSV
- `Submission`: Data class representing a student submission with metadata
- `GradingResult`: Data class representing grading outcome for a student
- CSV processing: `load_grading_list()`, `save_results_to_csv()`
- Submission parsing: `parse_submission_folder_name()`, `extract_submissions()`, `find_latest_submissions()`
- Name matching: `normalize_name()`, `find_best_name_match()`
- Grading orchestration: `prepare_grading_directory()`, `run_grader_for_student()`, `extract_zipfile()`
- Reporting: `generate_post_grading_report()`

### Data Flow

#### Single Submission Mode

```
User Input (CLI)
    ↓
Parse arguments (test-dir, prefix, code-dir, classpath)
    ↓
Find test files in test-dir matching prefix
    ↓
Copy test files to code-dir
    ↓
(Optional) Preprocess code files
    ↓
Compile main test file with javac
    ↓
Run compiled test with java
    ↓
Parse output to calculate grade
    ↓
Display grade summary
```

#### Bulk Submission Mode

```
User Input (CLI)
    ↓
Parse arguments (submissions.zip, gradebook.csv, test-dir, prefix)
    ↓
Load gradebook CSV → StudentRecord objects
    ↓
Extract submissions.zip → submission folders
    ↓
Parse folder names → Submission objects with timestamps
    ↓
Fuzzy match submissions to StudentRecords
    ↓
Select latest submission per student
    ↓
For each matched submission:
    ↓
    Extract/prepare grading directory
    ↓
    (Optional) Preprocess code files
    ↓
    Copy test files
    ↓
    Compile and run tests (reuses single grader logic)
    ↓
    Calculate grade → GradingResult
    ↓
Aggregate all GradingResults
    ↓
Save to output CSV
    ↓
Generate post-grading report
```

### Key Design Patterns

#### 1. Command Pattern
The CLI uses the command pattern through Typer, with `single` and `bulk` as separate command handlers.

#### 2. Data Classes
Extensive use of `@dataclass` for structured data: `StudentRecord`, `Submission`, `GradingResult`, `CodeFilePreprocessingOptions`.

#### 3. Utility Classes
The `Writer` class provides a simple abstraction for conditional output based on verbosity.

#### 4. Subprocess Execution
Direct use of `subprocess.run()` to invoke `javac` and `java` commands.

## Current Implementation Details

### Dependencies

**Core Runtime Dependencies:**
- `typer`: CLI framework
- `rich`: Rich terminal output
- `pandas`: CSV/DataFrame processing (bulk mode)
- `thefuzz`: Fuzzy string matching (bulk mode)
- `unidecode`: Unicode normalization (bulk mode)

**Development Dependencies:**
- `uv`: Dependency management and build system
- `ruff`: Code formatting and linting
- `mypy`: Static type checking
- `bandit`: Security scanning
- `pytest`: Testing framework
- `pytest-cov`: Code coverage

### Test File Discovery

The system uses a convention-based approach:
1. Searches for `{prefix}*.java` files in the test directory
2. Requires a main test file named exactly `{prefix}.java`
3. Optionally includes `TestUtils.java` if present
4. Copies all matching files to the grading directory

### Compilation and Execution

**Compilation:**
```bash
javac [-cp <classpath>] <TestFile>.java
```

**Execution:**
```bash
java [-cp <classpath>] <TestFile>
```

The classpath is constructed from user-provided entries, automatically including `.` (current directory).

### Grade Parsing

Grades are extracted using a regex pattern:
```regex
Grade for .+ \(out of (a\s+)?possible (?P<max>\d+(\.\d+)?)\): (?P<total>\d+(\.\d+)?)
```

This allows the system to work with any Java test framework that outputs grades in this format. Multiple grade lines are summed to produce a final percentage.

### Name Matching Algorithm

The bulk grader uses a multi-step approach for matching submissions to students:

1. **Normalization**: Remove accents using `unidecode`, convert to lowercase, normalize whitespace
2. **Exact Match**: Try exact match on normalized names first
3. **Fuzzy Matching**: Use `thefuzz` library with ratio scorer if no exact match
4. **Threshold**: Accept matches with score ≥ 80

### File Permission Handling

The system handles read-only file systems and permission issues:
- Attempts to delete existing files before copying
- If permission denied, adds write permission and retries
- Ensures target directories are writable before operations
- Clear error messages when permission fixes fail

### Preprocessing

Optional code preprocessing feature (enabled with `--preprocess-code`):
- Removes package declarations from Java files
- Allows student code with package statements to be tested
- Applied to all `.java` files in the code directory before testing

## Current Limitations and Tight Coupling

### 1. Monolithic Functions

Many functions in both `_grader.py` and `bulk_grader.py` are large and handle multiple responsibilities. For example:
- `main()` in both files handles argument parsing, validation, orchestration, and error handling
- `run_grader_for_student()` combines directory management, preprocessing, compilation, execution, and result aggregation

### 2. Tightly Coupled Java Execution

The Java compilation and execution logic is hardcoded:
- Direct `subprocess` calls to `javac` and `java`
- No abstraction for the test runner
- Difficult to substitute alternative test execution strategies (e.g., Docker containers, remote execution, different JDKs)

### 3. Fixed Grade Parsing Strategy

The regex-based grade parsing is embedded in `calculate_grade_from_output()`:
- Works only with specific output format
- Cannot easily support alternative test frameworks (JUnit, TestNG, etc.)
- No plugin system for custom grade extractors

### 4. Hardcoded CSV Format

The gradebook integration assumes a specific CSV structure:
- Column names are hardcoded: `OrgDefinedId`, `Username`, `Last Name`, `First Name`
- Limited flexibility for different LMS exports
- No configuration for custom CSV formats

### 5. Single Submission Processing Strategy

Bulk grading processes submissions sequentially in a single thread:
- No parallelization or concurrent processing
- Long wait times for large classes
- No progress persistence (if process crashes, must restart from beginning)

### 6. Limited Extensibility

Adding new features requires modifying core files:
- No plugin architecture
- No dependency injection
- Hard to extend without forking

### 7. File System Coupling

The system assumes local file system operations:
- Cannot easily work with remote storage (S3, cloud storage)
- Temporary directory handling is implicit
- No abstraction for file/directory operations

### 8. Console Output Coupling

The `Writer` class is passed through most function calls:
- Output strategy is tied to implementation
- Difficult to redirect output to logs, files, or monitoring systems
- No structured logging

### 9. Error Handling Strategy

Error handling is inconsistent:
- Some functions raise `FileOperationError`
- Some functions call `sys.exit()`
- Some functions return success booleans
- Difficult to handle errors uniformly in different contexts

### 10. Testing Challenges

The current architecture makes testing difficult:
- Heavy reliance on file system operations
- Subprocess calls are hard to mock
- Large functions with multiple responsibilities
- Limited separation of concerns

## Strengths of Current Implementation

Despite the limitations, the current implementation has several strengths:

1. **Works Well**: Successfully grades hundreds of submissions for ITI 1121
2. **Clear User Interface**: Intuitive CLI with helpful options and documentation
3. **Comprehensive Error Reporting**: Detailed post-grading reports identify issues
4. **Robust Name Matching**: Fuzzy matching handles variations in student names
5. **Handles Edge Cases**: Permission issues, ZIP nesting, missing files
6. **Good Documentation**: README and Usage.md provide clear instructions
7. **Type Hints**: Uses Python type hints throughout for better IDE support
8. **Code Quality Tools**: Integrated with ruff, mypy, bandit for code quality

## Technical Debt

Areas of technical debt that should be addressed in a refactoring:

1. **Hard-coded strings**: Magic strings scattered throughout code
2. **Global state**: Use of `os.chdir()` changes global state
3. **Mixed concerns**: UI, business logic, and I/O intertwined
4. **Limited test coverage**: Few automated tests for core functionality
5. **Duplicate code**: Similar logic between single and bulk graders
6. **No configuration file**: All configuration via CLI arguments
7. **Breakpoint in production code**: Line 718 in `bulk_grader.py` contains `breakpoint()`

## Conclusion

The ITI 1121 Grading Tool is a functional and practical solution for automating Java assignment grading. It successfully handles the core use cases and has been battle-tested in real grading scenarios. However, the architecture is monolithic with tight coupling between components, making it difficult to extend, test, and maintain. A refactoring to a more modular architecture with clear separation of concerns would improve maintainability and enable new features while preserving the existing functionality that works well.
