# Contributing to ITI1121 Grading Tool

Thank you for your interest in contributing to the ITI1121 Grading Tool! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/cryptaliagy/iti1121-grading.git
cd iti1121-grading
```

2. Install the package in development mode with all dependencies:
```bash
pip install -e ".[dev]"
```

This will install:
- The main dependencies: typer, pandas, unidecode, rich, thefuzz, pluggy
- Development dependencies: ruff, mypy, pytest, pytest-cov, bandit

## Running Tests

### Run All Tests

To run the complete test suite:

```bash
pytest test/
```

### Run Specific Test Categories

Run only unit tests:
```bash
pytest test/unit/
```

Run only integration tests:
```bash
pytest test/integration/
```

Run a specific test file:
```bash
pytest test/unit/test_grader.py
```

Run a specific test class or function:
```bash
pytest test/unit/test_grader.py::TestWriter
pytest test/unit/test_grader.py::TestWriter::test_writer_verbose_mode
```

### Run Tests with Coverage

To run tests with coverage reporting:

```bash
pytest test/ --cov=src/grader --cov-report=term-missing
```

For an HTML coverage report:

```bash
pytest test/ --cov=src/grader --cov-report=html
```

The HTML report will be generated in `htmlcov/index.html`.

### Run Tests in Verbose Mode

```bash
pytest test/ -v
```

### Run Tests with Output

To see print statements and output:

```bash
pytest test/ -s
```

## Code Quality Tools

### Linting with Ruff

Check code for style issues:

```bash
ruff check .
```

Auto-fix issues where possible:

```bash
ruff check --fix .
```

Format code:

```bash
ruff format .
```

### Type Checking with Mypy

Run static type checking:

```bash
mypy src/
```

### Security Scanning with Bandit

Run security vulnerability scanning:

```bash
bandit -c pyproject.toml -r src/
```

### Run All Quality Checks

To run all quality checks at once:

```bash
ruff check . && mypy src/ && bandit -c pyproject.toml -r src/
```

## Test Structure

The test suite is organized as follows:

```
test/
├── fixtures/           # Test data and sample files
│   ├── TestSimple.java
│   ├── TestUtils.java
│   ├── Calculator.java
│   └── grading_list.csv
├── unit/              # Unit tests for individual functions
│   └── test_grader.py
├── integration/       # Integration tests for workflows
│   └── test_single_grading.py
└── test_bulk_grader.py  # Bulk grading tests
```

## Writing Tests

### Unit Tests

Unit tests should:
- Test individual functions in isolation
- Use mocks for external dependencies
- Be fast and deterministic
- Follow the Arrange-Act-Assert pattern

Example:
```python
def test_calculate_grade_from_output():
    """Test parsing single grade line."""
    output = "Grade for Test1 (out of a possible 10): 8"
    total, possible = calculate_grade_from_output(output)
    assert total == 8.0
    assert possible == 10.0
```

### Integration Tests

Integration tests should:
- Test complete workflows
- Use the `@pytest.mark.integration` decorator
- Use temporary directories (`tmp_path` fixture)
- Clean up resources after testing

Example:
```python
@pytest.mark.integration
def test_complete_workflow(tmp_path):
    """Test complete grading workflow."""
    # Test implementation
    pass
```

### Test Fixtures

Use pytest fixtures for reusable test setup:
```python
@pytest.fixture
def test_env(tmp_path):
    """Set up test environment."""
    # Setup code
    return {"test_dir": test_dir, "code_dir": code_dir}
```

## Code Style Guidelines

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Use descriptive variable names

## Pull Request Process

1. Create a new branch for your changes:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and add tests

3. Run all quality checks:
```bash
ruff check . && mypy src/ && bandit -c pyproject.toml -r src/
```

4. Run the test suite:
```bash
pytest test/ --cov=src/grader
```

5. Commit your changes with clear commit messages:
```bash
git commit -m "Add feature: description of changes"
```

6. Push your branch and create a pull request

## Code Review Guidelines

- All code must pass linting, type checking, and security scans
- All tests must pass
- Code coverage should not decrease
- New features should include tests
- Bug fixes should include regression tests

## Getting Help

If you need help:
- Check existing documentation in the `docs/` directory
- Review existing tests for examples
- Open an issue on GitHub with your question

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
