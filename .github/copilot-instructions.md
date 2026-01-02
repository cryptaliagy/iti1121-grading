# Copilot Instructions for ITI 1121 Grading Tool

## Project Overview

This is a Python CLI tool for automating the grading of Java assignments for ITI 1121 at the University of Ottawa. It provides both single submission grading and bulk grading capabilities, handling Java compilation, test execution, and gradebook integration.

**Key Capabilities:**
- Compile and run Java test files against student submissions
- Process single submissions or bulk ZIP files
- Fuzzy name matching for student submissions
- Generate CSV reports for LMS import
- Handle external Java dependencies via classpath

## Technology Stack

### Core Technologies
- **Language**: Python 3.10+ (tested on 3.10, 3.11, 3.12, 3.13)
- **CLI Framework**: Typer for command-line interface
- **Build System**: UV (Python package manager and build tool)
- **Java**: Requires JDK with `javac` and `java` in PATH

### Key Dependencies
- `typer` - CLI framework
- `rich` - Terminal output formatting
- `pandas` - CSV processing and data manipulation
- `thefuzz` - Fuzzy string matching for student names
- `unidecode` - Unicode text normalization
- `pluggy` - Plugin system (future extensibility)

### Development Tools
- `ruff` - Linting and formatting (replaces black, flake8, isort)
- `mypy` - Static type checking
- `pytest` - Testing framework
- `pytest-cov` - Code coverage reporting
- `bandit` - Security vulnerability scanning

## Development Setup

### Initial Setup
```bash
# Clone the repository
git clone https://github.com/cryptaliagy/iti1121-grading.git
cd iti1121-grading

# Install using UV (recommended for development)
uv sync

# Or install globally with UV
uv tool install .

# Or use pipx
pipx install .
```

### Running the Tool
```bash
# If installed with uv sync
uv run grader

# If installed globally
grader
```

## Build and Test Commands

### Linting and Formatting
```bash
# Check code style
ruff check .

# Auto-fix style issues
ruff check --fix .

# Format code
ruff format .
```

### Type Checking
```bash
# Run static type checking
mypy src/
```

### Security Scanning
```bash
# Run security vulnerability scan
bandit -c pyproject.toml -r src/
```

### Testing
```bash
# Run all tests
pytest test/

# Run with coverage
pytest test/ --cov=src/grader --cov-report=term-missing

# Run only unit tests
pytest test/unit/

# Run only integration tests
pytest test/integration/

# Run specific test file
pytest test/unit/test_grader.py

# Run in verbose mode
pytest test/ -v
```

### Building
```bash
# Build package
uv build
```

### All Quality Checks (CI Pipeline)
```bash
ruff check . && ruff format --check . && mypy src/ && bandit -c pyproject.toml -r src/ && pytest test/ --cov=src/grader
```

## Code Style and Conventions

### Python Style
- **Style Guide**: Follow PEP 8 with Ruff enforcement
- **Line Length**: 88 characters (Black-compatible)
- **Quotes**: Double quotes for strings
- **Indentation**: 4 spaces (no tabs)
- **Type Hints**: Always use type hints for function parameters and return values
- **Docstrings**: Required for all public functions and classes

### Type Annotations
```python
from pathlib import Path
from typing import Any

def process_file(file_path: Path, verbose: bool = True) -> list[str]:
    """Process a file and return results.
    
    Args:
        file_path: Path to the file to process
        verbose: Whether to print verbose output
        
    Returns:
        List of processed items
    """
    pass
```

### Error Handling
- Use custom exceptions (e.g., `FileOperationError`) for domain-specific errors
- Raise exceptions with descriptive messages
- Handle subprocess calls with proper error checking

### Security
- Mark subprocess calls with `# nosec: B404` when intentional (after security review)
- Never commit secrets or credentials
- Use `bandit` to scan for security issues

### Imports Organization
```python
# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import typer
import pandas as pd

# Local imports
from grader._grader import process_files
```

## Testing Practices

### Test Structure
```
test/
├── fixtures/           # Test data (Java files, CSV files)
├── unit/              # Unit tests for individual functions
├── integration/       # Integration tests for complete workflows
└── test_bulk_grader.py
```

### Writing Tests

**Unit Tests:**
- Test individual functions in isolation
- Use mocks for external dependencies
- Fast and deterministic
- Follow Arrange-Act-Assert pattern

```python
def test_calculate_grade_from_output():
    """Test parsing single grade line."""
    output = "Grade for Test1 (out of a possible 10): 8"
    total, possible = calculate_grade_from_output(output)
    assert total == 8.0
    assert possible == 10.0
```

**Integration Tests:**
- Test complete workflows
- Use `@pytest.mark.integration` decorator
- Use `tmp_path` fixture for file operations
- Clean up resources after testing

```python
@pytest.mark.integration
def test_complete_workflow(tmp_path):
    """Test complete grading workflow."""
    # Test implementation
    pass
```

### Test Fixtures
- Use pytest fixtures for reusable test setup
- Store test data in `test/fixtures/`
- Use `tmp_path` for temporary file operations

## Architecture Patterns

### Current Architecture
- **CLI Layer**: Typer-based command-line interface (`__main__.py`)
- **Application Layer**: Main grading logic (`_grader.py`, `bulk_grader.py`)
- **Utilities**: Helper functions for file operations, compilation, testing

### Key Components

**Writer Class**: Conditional console output based on verbosity
```python
writer = Writer(verbose=True)
writer.echo("Verbose message")  # Only prints if verbose=True
writer.always_echo("Always shown")  # Always prints
```

**File Operations**: Use `pathlib.Path` for all file operations
```python
from pathlib import Path

test_dir = Path("/path/to/tests")
if test_dir.exists() and test_dir.is_dir():
    # Process directory
    pass
```

**Subprocess Calls**: For Java compilation and execution
```python
import subprocess

result = subprocess.run(
    [JAVA_COMPILER_CMD, "Test.java"],
    cwd=working_dir,
    capture_output=True,
    text=True
)
```

### Design Principles
- **Single Responsibility**: Each function has one clear purpose
- **Type Safety**: Use type hints throughout
- **Error Handling**: Raise exceptions with clear messages
- **Testability**: Write testable code with minimal side effects
- **Dependency Injection**: Pass dependencies as parameters (e.g., `Writer` object)

### Future Architecture
See `docs/ModularArchitecture.md` for the planned modular architecture with:
- Layered architecture (Presentation → Application → Domain → Infrastructure)
- Plugin system for extensibility
- Dependency injection framework
- Enhanced testability

## Common Workflows

### Adding a New Feature
1. Create a feature branch: `git checkout -b feature/feature-name`
2. Write tests first (TDD approach recommended)
3. Implement the feature
4. Run quality checks: `ruff check . && mypy src/ && bandit -c pyproject.toml -r src/`
5. Run tests: `pytest test/ --cov=src/grader`
6. Commit with clear messages
7. Create a pull request

### Debugging
- Use `writer.echo()` for verbose debug output
- Use `pytest -s` to see print statements in tests
- Check `test/fixtures/` for sample Java files to test with

### Adding Dependencies
1. Add to `dependencies` in `pyproject.toml`
2. Run `uv sync` to update `uv.lock`
3. Verify with `uv run pytest test/`

### Updating Documentation
- Update relevant docs in `docs/` directory
- Keep README.md in sync with major changes
- Update CONTRIBUTING.md for process changes

## Project Structure

```
iti1121-grading/
├── .github/
│   ├── workflows/          # CI/CD pipelines
│   └── copilot-instructions.md
├── docs/                   # Comprehensive documentation
│   ├── Usage.md           # User guide
│   ├── CurrentState.md    # Current architecture
│   ├── ModularArchitecture.md  # Future vision
│   └── RefactoringPlan.md # Migration roadmap
├── src/grader/            # Source code
│   ├── __init__.py
│   ├── __main__.py        # CLI entry point
│   ├── _grader.py         # Single submission grading
│   └── bulk_grader.py     # Bulk grading functionality
├── test/                  # Test suite
│   ├── fixtures/          # Test data
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── pyproject.toml         # Project configuration
├── uv.lock               # Dependency lock file
├── README.md             # Main documentation
└── CONTRIBUTING.md       # Contribution guidelines
```

## CI/CD Pipeline

### Build Workflow
Runs on: `push` and `pull_request` to `main` branch

**Jobs:**
1. **Lint** - `ruff check .`
2. **Format** - `ruff format --check .`
3. **Security** - `bandit -r src/`
4. **Type Check** - `mypy --follow-untyped-imports`
5. **Tests** - Matrix testing on Python 3.10-3.13 with coverage
6. **Docker Build** - Test Docker Compose builds
7. **Build Package** - `uv build`

All jobs must pass before merge.

## Key Constants and Patterns

### Java-Related Constants
```python
JAVA_FILE_EXTENSION = ".java"
JAVA_COMPILER_CMD = "javac"
JAVA_RUNTIME_CMD = "java"
TEST_UTILS_FILE = "TestUtils.java"
CLASSPATH_SEPARATOR = ":"
```

### Exit Codes
```python
SUCCESS_EXIT_CODE = 0
ERROR_EXIT_CODE = 1
```

### Regular Expressions
```python
PACKAGE_DECLARATION_PATTERN = r"^\s*package\s+[\w.]+;\s*\n?"
```

## Important Notes

### Java Integration
- This tool interacts with Java via subprocess calls
- Requires JDK installed and in system PATH
- Handles classpath configuration for external dependencies
- Can remove package declarations from student code

### File Handling
- Uses `pathlib.Path` exclusively (not `os.path`)
- Creates temporary directories for compilation
- Handles ZIP file extraction for bulk grading
- Preserves file permissions where necessary

### Name Matching
- Uses fuzzy matching (`thefuzz`) for student names
- Normalizes Unicode characters (`unidecode`)
- Matches submissions to gradebook records

### CSV Processing
- Uses `pandas` for gradebook manipulation
- Outputs LMS-compatible CSV format
- Handles missing data gracefully

## Troubleshooting

### Common Issues
1. **Java not found**: Ensure JDK is installed and in PATH
2. **Import errors**: Run `uv sync` to install dependencies
3. **Type errors**: Check with `mypy src/`
4. **Test failures**: Use `pytest -v` for detailed output
5. **Coverage drops**: Run `pytest --cov=src --cov-report=html` for detailed report

### Getting Help
- Check documentation in `docs/` directory
- Review existing tests for examples
- See `CONTRIBUTING.md` for development guidelines
- Contact maintainer: Natalia Maximo <natalia.maximo@uottawa.ca>

## References

- **Main README**: [README.md](../README.md)
- **Contributing Guide**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Documentation Index**: [docs/README.md](../docs/README.md)
- **Usage Guide**: [docs/Usage.md](../docs/Usage.md)
- **Architecture Docs**: [docs/ModularArchitecture.md](../docs/ModularArchitecture.md)
