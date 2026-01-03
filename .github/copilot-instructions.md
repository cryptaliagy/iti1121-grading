# Copilot Instructions for ITI1121 Grading Tool

## Project Overview

This is a Python CLI tool for automating the grading process for Java assignments in ITI 1121 at the University of Ottawa. The tool supports both single submission grading and bulk grading of multiple student submissions.

**Key capabilities:**
- Compile and run Java test files against student code
- Process individual submissions or bulk ZIP files
- Fuzzy matching of student names to gradebook records
- Generate CSV reports for LMS import
- Handle external Java libraries via classpath

## Technology Stack

- **Language:** Python 3.10+
- **CLI Framework:** Typer
- **Package Manager:** uv (preferred) or pip
- **Testing:** pytest with pytest-cov
- **Linting/Formatting:** ruff
- **Type Checking:** mypy
- **Security:** bandit

## Project Structure

```
src/grader/           # Main source code
test/                 # Test suite
  ├── fixtures/       # Test data and sample files
  ├── unit/          # Unit tests
  ├── integration/   # Integration tests
  └── test_bulk_grader.py
docs/                # Detailed documentation
pyproject.toml       # Package configuration
```

## Development Setup

### Installation

1. Clone the repository
2. Install with uv (preferred): `uv sync` or `uv tool install .`
3. Or use pipx: `pipx install .`
4. Or use pip: `pip install -e ".[dev]"`

### Running the Tool

- With uv: `uv run grader [command]`
- After install: `grader [command]`

## Code Style and Conventions

### Python Standards
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Use descriptive variable names

### Formatting
- Line length: 88 characters (Black style)
- Quote style: Double quotes for strings
- Indentation: 4 spaces

### Type Hints
- Always use type hints
- Import types from `typing` module as needed
- Use `pandas` type stubs for DataFrame operations

### Pull Request Etiquette

- Try to keep PRs small and focused
- If large changes are needed, break into multiple PRs
- Provide clear descriptions of changes
- Reference related issues or tasks
- Ensure all tests pass before requesting review
- Ensure code quality checks pass

## Testing Guidelines

### Running Tests

```bash
# All tests
pytest test/

# Unit tests only
pytest test/unit/

# Integration tests only
pytest test/integration/

# With coverage
pytest test/ --cov=src/grader --cov-report=term-missing

# Verbose mode
pytest test/ -v
```

### Writing Tests

**Unit Tests:**
- Test individual functions in isolation
- Use mocks for external dependencies
- Follow Arrange-Act-Assert pattern
- Be fast and deterministic

**Integration Tests:**
- Mark with `@pytest.mark.integration`
- Test complete workflows
- Use `tmp_path` fixture for file operations
- Clean up resources after testing

**Test Fixtures:**
- Use pytest fixtures for reusable test setup
- Store test data in `test/fixtures/`

## Code Quality Tools

### Linting and Formatting

```bash
# Check for style issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Type Checking

```bash
mypy src/
```

### Security Scanning

```bash
bandit -c pyproject.toml -r src/
```

### Run All Quality Checks

```bash
ruff check . && mypy src/ && bandit -c pyproject.toml -r src/
```

## Common Tasks

### Adding New Features

1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make changes and add tests
3. Run quality checks: `ruff check . && mypy src/ && bandit -c pyproject.toml -r src/`
4. Run tests: `pytest test/ --cov=src/grader`
5. Commit and push changes

### Fixing Bugs

1. Write a regression test that reproduces the bug
2. Fix the bug
3. Ensure the test passes
4. Run full test suite and quality checks

### Working with Dependencies

- Add dependencies in `pyproject.toml` under `dependencies`
- Add dev dependencies under `[dependency-groups].dev`
- Use `uv sync` to update lock file
- Keep versions constrained (e.g., `>=2.0.0,<3.0.0`)

## Important Notes

### Java Integration
- The tool compiles and runs Java code using `javac` and `java`
- JDK must be available in system PATH
- Support for external JAR files via classpath parameter

### File Handling
- Automatically extracts ZIP files
- Handles file copying and permissions
- Uses temporary directories for processing

### Student Name Matching
- Uses fuzzy string matching with `thefuzz` library
- Normalizes Unicode characters with `unidecode`
- Requires gradebook CSV in specific format

## Pull Request Requirements

- [ ] All tests pass
- [ ] Code coverage does not decrease
- [ ] Linting passes (ruff check)
- [ ] Type checking passes (mypy)
- [ ] Security scan passes (bandit)
- [ ] New features include tests
- [ ] Bug fixes include regression tests
- [ ] Code follows style guidelines

## Additional Resources

- Comprehensive documentation in `docs/` directory
- Usage guide: `docs/Usage.md`
- Architecture docs: `docs/ModularArchitecture.md`
- Refactoring plan: `docs/RefactoringPlan.md`
- Contributing guide: `CONTRIBUTING.md`

## License

MIT License - see LICENSE file for details
