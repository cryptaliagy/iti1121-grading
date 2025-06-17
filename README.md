# Java Test Runner for ITI 1121

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A CLI tool for automating the process of running Java tests for ITI 1121 assignments at the University of Ottawa. This tool provides both single submission grading and bulk grading capabilities for processing multiple student submissions efficiently.

## Key Features

- **Single Submission Grading**: Quickly test individual student submissions
- **Bulk Grading**: Process entire classes worth of submissions from ZIP files
- **Automatic Test Discovery**: Finds Java test files with specified prefixes
- **Smart File Handling**: Extracts ZIPs, copies files, handles permissions
- **Fuzzy Name Matching**: Matches student submissions to gradebook records
- **Comprehensive Reporting**: Detailed reports on grading outcomes and issues
- **Gradebook Integration**: Outputs CSV files ready for LMS import
- **Flexible Classpath Support**: Handle external dependencies and libraries

## Dependencies

- Python 3.10 or higher
- Java Development Kit (JDK) installed and available in the system PATH
- `javac` and `java` commands available in the system PATH
- Python packages (automatically installed):
  - `typer` - Command-line interface framework
  - `rich` - Rich text output in the terminal
  - `pandas` - Data manipulation for CSV processing (bulk mode)
  - `thefuzz` - Fuzzy string matching for student name matching (bulk mode)
  - `unidecode` - Unicode text normalization (bulk mode)
- (Optional) `pipx` for isolated Python environments
- (Optional) All Java libraries/JAR files required for the tests should be available in your classpath

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

See the [Usage.md](./docs/Usage.md) file.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Natalia Maximo - <natalia.maximo@uottawa.ca>
