# Java Test Runner for ITI 1121

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A CLI tool for automating the process of running Java tests for ITI 1121 assignments at the University of Ottawa. This tool finds Java test files with a specified prefix, copies them to a target directory, compiles them, and runs the tests.

## Dependencies

- Python 3.10 or higher
- Java Development Kit (JDK) installed and available in the system PATH
- `javac` and `java` commands available in the system PATH
- `Typer` for command-line interface
- `rich` for rich text output in the terminal
- (Optional) `pipx` for isolated Python environments
- (Optional) All Java libraries/JAR files required for the tests should be available in the user's CLASSPATH variable.

## Features

- Quickly compile and run Java test files
- Automatically find test files with a specific prefix
- Copy test files to a target directory, replacing existing files if necessary
- Support for additional classpath entries
- Detailed output at each step of the process

## Installation

First, clone the repository:

```bash
git clone https://github.com/cryptaliagy/iti1121-grading.git
cd iti1121-grading
```

### Using pipx (Recommended)

[pipx](https://pypa.github.io/pipx/) is recommended for command-line tools as it installs each package in its own isolated environment:

```bash
pipx install .
```

### Using Poetry (Useful for development)

```bash
poetry install
```

If installing with Poetry, you can run the tool using:

```bash
poetry run grader
```

If following along with the usage example below, replace `grader` with `poetry run grader`.

### Using pip (Not recommended)

```bash
pip install .
```

For development installation:

```bash
pip install -e .
```

## Usage

### Basic Usage

To run the grader, you need to provide:

- The directory containing the test files
- A prefix for the test files

```bash
grader --test-dir path/to/tests --prefix TestL1
```

Or using the short options:

```bash
grader -t path/to/tests -p TestL1
```

You can also run it as a Python module:

```bash
python -m grader --test-dir path/to/tests --prefix TestL1
```

The CLI also supports some directory shortcuts:

- `.` for the current directory
- `..` for the parent directory
- `~` for the user's home directory

So, if you have your tests in a directory called `tests` in your home directory, you can run:

```bash
grader --test-dir ~/tests --prefix TestL1
```

### Specifying the Code Directory

By default, the tool uses the current directory as the target for copying test files. You can specify a different directory:

```bash
grader --test-dir path/to/tests --prefix TestL1 --code-dir path/to/code
```

Or:

```bash
grader -t path/to/tests -p TestL1 -c path/to/code
```

### Adding Classpath Entries

If your tests need additional libraries or classpath entries, you can specify them:

```bash
grader --test-dir path/to/tests --prefix TestL1 --classpath path/to/lib1.jar --classpath path/to/lib2.jar
```

Or:

```bash
grader -t path/to/tests -p TestL1 -cp path/to/lib1.jar -cp path/to/lib2.jar
```

## How It Works

1. **Finding Test Files**: The tool searches for all `.java` files with the specified prefix in the test directory. It ensures that there's at least one file exactly matching the prefix (e.g., `TestL1.java` for prefix `TestL1`). It also copies `TestUtils.java` if it exists in the test directory.

2. **Copying Test Files**: All matching test files are copied to the target code directory. If any files with the same names already exist in the target directory, they are deleted first.

3. **Compiling Tests**: The tool compiles the main test file (the one exactly matching the prefix) using the `javac` command. If classpath entries are provided, they are included in the compilation command.

4. **Running Tests**: If compilation succeeds, the tool runs the compiled test using the `java` command.

## Examples

### Running Tests without Classpath

```bash
# Copy all TestL1*.java files from tests/ to the current directory and run TestL1
grader -t tests -p TestL1

# Copy tests to a specific directory
grader -t /path/to/assignment/tests -p Lab2 -c /path/to/student/submission
```

### Running Tests with Classpath

```bash
# Include JUnit in the classpath
grader -t tests -p TestL1 -cp lib/junit-4.13.jar -cp lib/hamcrest-core-1.3.jar

# Multiple libraries and a custom code directory
grader -t assignment/tests -p Assignment1Test -c student/code -cp lib/junit.jar -cp lib/commons-io.jar
```

## Error Handling

The tool provides clear error messages for common issues:

- Missing test directories
- No matching test files
- Missing main test file
- Compilation errors
- Test execution failures
- Permission issues when copying files

It will also attempt to resolve issues where it can.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Natalia Maximo - <natalia.maximo@uottawa.ca>
