# Usage

The grader provides two main commands:

- `single` - Grade a single student submission
- `bulk` - Bulk grade multiple student submissions from a ZIP file

## Single Submission Grading

### Basic Usage

To grade a single submission, you need to provide:

- The directory containing the test files
- A prefix for the test files

```bash
grader single --test-dir path/to/tests --prefix TestL1
```

Or using the short options:

```bash
grader single -t path/to/tests -p TestL1
```

You can also run it as a Python module:

```bash
python -m grader single --test-dir path/to/tests --prefix TestL1
```

The CLI also supports some directory shortcuts:

- `.` for the current directory
- `..` for the parent directory
- `~` for the user's home directory

So, if you have your tests in a directory called `tests` in your home directory, you can run:

```bash
grader single --test-dir ~/tests --prefix TestL1
```

### Specifying the Code Directory

By default, the tool uses the current directory as the target for copying test files. You can specify a different directory:

```bash
grader single --test-dir path/to/tests --prefix TestL1 --code-dir path/to/code
```

Or:

```bash
grader single -t path/to/tests -p TestL1 -c path/to/code
```

### Adding Classpath Entries

If your tests need additional libraries or classpath entries, you can specify them:

```bash
grader single --test-dir path/to/tests --prefix TestL1 --classpath path/to/lib1.jar --classpath path/to/lib2.jar
```

Or:

```bash
grader single -t path/to/tests -p TestL1 -cp path/to/lib1.jar -cp path/to/lib2.jar
```

### Controlling Output Verbosity

You can control the verbosity of the output:

```bash
# Verbose mode (default)
grader single -t path/to/tests -p TestL1 --verbose

# Quiet mode (only show essential output)
grader single -t path/to/tests -p TestL1 --quiet
```

## Bulk Submission Grading

The bulk grading feature allows you to process multiple student submissions at once from a ZIP file downloaded from your learning management system.

### Basic Usage

```bash
grader bulk --submissions submissions.zip --grading-list students.csv --test-dir tests --prefix TestL1
```

Or using short options:

```bash
grader bulk -s submissions.zip -g students.csv -t tests -p TestL1
```

### Required Parameters

- `--submissions` (`-s`): Path to ZIP file containing all student submissions
- `--grading-list` (`-g`): Path to CSV file with student grading list (exported from gradebook)
- `--test-dir` (`-t`): Directory containing test files
- `--prefix` (`-p`): Prefix of test files to search for (e.g., 'TestL3')

### Optional Parameters

- `--output` (`-o`): Output CSV file path (default: `graded_results.csv`)
- `--assignment-name` (`-a`): Name for the assignment grade column (default: `Lab Grade`)
- `--classpath` (`-cp`): Additional classpath entries (can be specified multiple times)
- `--failure-is-null` (`-F`): Use null/empty for failures instead of 0
- `--verbose`/`--quiet` (`-v`/`-q`): Control verbosity of output

### CSV File Format

The grading list CSV should be exported from your gradebook with the following requirements:

- **Sort by**: Student Number, Username, First Name, Last Name
- **Include**: Last Name, First Name as User Details
- **Export with both username and student number as keys**

The tool will automatically normalize the output CSV header to the expected format:
```
OrgDefinedId,Username,Last Name,First Name,Lab Grade,End-of-Line Indicator
```

### Submission Folder Format

Student submission folders should follow this naming convention:
```
<student-id>-<submission-id> - <First Last> - <Month> <Day>, <Year> <Time> <AM/PM>
```

Example: `152711-351765 - John Doe - May 18, 2025 1224 PM`

### Advanced Options

**Custom Assignment Name:**
```bash
grader bulk -s submissions.zip -g students.csv -t tests -p TestL1 --assignment-name "Assignment 1"
```

**With Classpath Dependencies:**
```bash
grader bulk -s submissions.zip -g students.csv -t tests -p TestL1 -cp lib/junit.jar -cp lib/hamcrest.jar
```

**Null for Failures (instead of 0):**
```bash
grader bulk -s submissions.zip -g students.csv -t tests -p TestL1 --failure-is-null
```

### What the Bulk Grader Does

1. **Extracts submissions** from the ZIP file
2. **Parses student names and timestamps** from folder names
3. **Finds the latest submission** for each student (if multiple exist)
4. **Matches submissions to student records** using fuzzy name matching
5. **Processes each submission** by:
   - Extracting ZIP files or copying Java files
   - Copying test files to the submission directory
   - Compiling and running tests
   - Calculating grades based on test output
6. **Generates a comprehensive report** showing:
   - Students who received a grade of 0
   - Students with failed/null grades
   - Students in CSV but without submissions
   - Students with submissions but not in CSV
   - Overall success statistics
7. **Outputs results** to a CSV file for import back into the gradebook

### Grade Calculation

The tool parses test output looking for lines matching this pattern:
```
Grade for <test-name> (out of possible X.X): Y.Y
```

It sums all achieved points and possible points to calculate a final percentage grade.

## How It Works

### Single Submission Workflow

1. **Finding Test Files**: The tool searches for all `.java` files with the specified prefix in the test directory. It ensures that there's at least one file exactly matching the prefix (e.g., `TestL1.java` for prefix `TestL1`). It also copies `TestUtils.java` if it exists in the test directory.

2. **Copying Test Files**: All matching test files are copied to the target code directory. If any files with the same names already exist in the target directory, they are deleted first (with appropriate permission handling).

3. **Compiling Tests**: The tool compiles the main test file (the one exactly matching the prefix) using the `javac` command. If classpath entries are provided, they are included in the compilation command.

4. **Running Tests**: If compilation succeeds, the tool runs the compiled test using the `java` command and parses the output to calculate grades.

### Bulk Grading Workflow

The bulk grading process is more complex and handles multiple submissions automatically:

1. **Input Validation**: Verifies that all required files exist (ZIP, CSV, test directory)

2. **CSV Processing**: 
   - Loads and normalizes the gradebook CSV header
   - Creates student records with normalized usernames and IDs

3. **Submission Extraction**: 
   - Extracts the main submissions ZIP file
   - Parses submission folder names to extract student names and timestamps
   - Handles various date/time formats from different LMS systems

4. **Student Matching**: 
   - Uses fuzzy string matching to connect submission names with gradebook records
   - Normalizes names by removing accents and handling case differences
   - Finds the latest submission for each student if multiple exist

5. **Individual Processing**: For each matched submission:
   - Creates a temporary grading directory
   - Extracts student's ZIP files or copies Java files directly
   - Flattens directory structures (removes nested folders)
   - Copies test files to the grading directory
   - Compiles and runs tests with error handling
   - Parses output to calculate grades

6. **Results Processing**: 
   - Generates comprehensive reports on grading outcomes
   - Identifies problematic cases (missing submissions, failures, etc.)
   - Creates output CSV with grades ready for gradebook import

7. **Cleanup**: Automatically cleans up temporary directories and files

### Grade Parsing Algorithm

The tool uses regular expressions to parse test output and calculate grades:

```
Pattern: "Grade for .+ \(out of possible (\d+\.\d+)\): (\d+\.\d+)"
```

This allows it to work with any Java test framework that outputs grades in this format, automatically summing up multiple test results to produce a final percentage.

## Output and Reporting

### Single Submission Output

When running in single mode, the tool provides:

1. **Step-by-step progress** (in verbose mode):
   - Test files found and copied
   - Compilation status
   - Test execution output

2. **Test Results**: The actual output from your Java test files

3. **Grade Summary**:
   ```
   ============================================================
   Final Grade Summary:
   Total Points: 85.0 / 100.0
   Percentage: 85.0%
   ============================================================
   ```

### Bulk Grading Output

The bulk grader provides comprehensive reporting:

#### During Processing
- Progress indicators for each major step
- Individual student grading results
- Real-time status updates

#### Post-Grading Report
A detailed report showing:

- **Students who received a grade of 0** (with reasons)
- **Students with failed/null grades** (compilation or runtime errors)
- **Students in CSV but without submissions** (missing submissions)
- **Students with submissions but not in CSV** (extra submissions)
- **Summary statistics** including success rates

#### CSV Output
The tool generates a CSV file compatible with most gradebook systems:
- Maintains original student information
- Adds/updates the specified assignment grade column
- Uses either numerical grades (0.000-1.000) or null/empty for failures
- Ready for direct import into your LMS

### Error Handling and Troubleshooting

The tool provides clear error messages for common issues:

#### Single Mode Errors
- Missing test directories or files
- Compilation failures with detailed javac output
- Runtime errors with stack traces
- Permission issues when copying files

#### Bulk Mode Errors
- Invalid ZIP file structure
- CSV format issues
- Submission folder naming problems
- Student name matching failures

The bulk grader continues processing even when individual submissions fail, ensuring you get results for all processable submissions.

## Examples

### Single Submission Examples

#### Running Tests without Classpath

```bash
# Copy all TestL1*.java files from tests/ to the current directory and run TestL1
grader single -t tests -p TestL1

# Copy tests to a specific directory
grader single -t /path/to/assignment/tests -p Lab2 -c /path/to/student/submission
```

#### Running Tests with Classpath

```bash
# Include JUnit in the classpath
grader single -t tests -p TestL1 -cp lib/junit-4.13.jar -cp lib/hamcrest-core-1.3.jar

# Multiple libraries and a custom code directory
grader single -t assignment/tests -p Assignment1Test -c student/code -cp lib/junit.jar -cp lib/commons-io.jar
```

#### Verbose and Quiet Modes

```bash
# Verbose mode (shows detailed step-by-step output)
grader single -t tests -p TestL1 --verbose

# Quiet mode (minimal output, only essential information)
grader single -t tests -p TestL1 --quiet
```

### Bulk Grading Examples

#### Basic Bulk Grading

```bash
# Process all submissions with default settings
grader bulk -s submissions.zip -g gradebook.csv -t tests -p TestL3

# Specify custom output file
grader bulk -s submissions.zip -g gradebook.csv -t tests -p TestL3 -o results.csv
```

#### Advanced Bulk Grading

```bash
# Custom assignment name and classpath
grader bulk \
  --submissions lab2_submissions.zip \
  --grading-list class_roster.csv \
  --test-dir assignment2/tests \
  --prefix TestA2 \
  --assignment-name "Lab 2 Grade" \
  --classpath lib/junit.jar \
  --classpath lib/custom-utils.jar \
  --output lab2_results.csv

# Use null for failures and quiet mode
grader bulk -s submissions.zip -g students.csv -t tests -p TestL1 --failure-is-null --quiet
```

#### Complete Workflow Example

```bash
# 1. Download submissions ZIP from your LMS
# 2. Export gradebook CSV with proper format
# 3. Run bulk grading
grader bulk \
  --submissions "Lab 3 Submissions-20250617.zip" \
  --grading-list "ITI1121_gradebook.csv" \
  --test-dir "lab3/tests" \
  --prefix "TestL3" \
  --assignment-name "Lab 3 Grade" \
  --output "lab3_graded.csv" \
  --verbose

# 4. Import lab3_graded.csv back into your gradebook
```

## Command Reference

### Single Submission Command

```bash
grader single [OPTIONS]
```

**Required Options:**
- `--test-dir`, `-t`: Directory containing test files
- `--prefix`, `-p`: Prefix of test files to search for

**Optional Options:**
- `--code-dir`, `-c`: Directory containing code files (default: current directory)
- `--classpath`, `-cp`: Additional classpath entries (can be repeated)
- `--verbose`/`--quiet`, `-v`/`-q`: Control output verbosity (default: verbose)

### Bulk Grading Command

```bash
grader bulk [OPTIONS]
```

**Required Options:**
- `--submissions`, `-s`: Path to ZIP file containing all student submissions
- `--grading-list`, `-g`: Path to CSV file with student grading list
- `--test-dir`, `-t`: Directory containing test files
- `--prefix`, `-p`: Prefix of test files to search for

**Optional Options:**
- `--output`, `-o`: Output CSV file path (default: `graded_results.csv`)
- `--assignment-name`, `-a`: Name for assignment grade column (default: `Lab Grade`)
- `--classpath`, `-cp`: Additional classpath entries (can be repeated)
- `--failure-is-null`, `-F`: Use null/empty for failures instead of 0
- `--verbose`/`--quiet`, `-v`/`-q`: Control output verbosity (default: verbose)

### Getting Help

```bash
# General help
grader --help

# Help for specific commands
grader single --help
grader bulk --help
```