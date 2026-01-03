# Domain Layer Documentation

## Overview

The domain layer contains the core business logic and models for the grading system. This layer is independent of infrastructure concerns and provides pure domain services and models.

## Student Matching Services

The student matching functionality has been refactored into modular, reusable domain services that support different matching strategies.

### Core Components

#### `normalize_name(name: str) -> str`

Normalizes names for consistent comparison across all matching strategies.

**Features:**
- Removes accents and diacritical marks (e.g., "José" → "jose")
- Converts to lowercase
- Normalizes whitespace (removes extra spaces)
- Handles international characters (Cyrillic, Greek, Arabic, CJK, etc.)

**Example:**
```python
from grader.domain import normalize_name

# Basic normalization
normalize_name("José María")  # Returns "jose maria"
normalize_name("François Côté")  # Returns "francois cote"
normalize_name("  Multiple   Spaces  ")  # Returns "multiple spaces"

# International names
normalize_name("Václav Dvořák")  # Returns "vaclav dvorak"
normalize_name("Björn Åström")  # Returns "bjorn astrom"
```

### Matching Strategies

#### `ExactStudentMatcher`

Fast, precise matching using normalized exact string comparison.

**When to use:**
- Submission names exactly match student records
- Need fastest matching performance
- No typos or variations expected

**Example:**
```python
from grader.domain import ExactStudentMatcher, Student, StudentId

students = [
    Student(StudentId("1", "jdoe"), "John", "Doe"),
    Student(StudentId("2", "jsmith"), "Jane", "Smith"),
]

matcher = ExactStudentMatcher()
result = matcher.find_match("John Doe", students)
# Returns the John Doe student

result = matcher.find_match("john doe", students)
# Also returns John Doe (case-insensitive)

result = matcher.find_match("José María", students)
# Can match both "José María" and "Jose Maria"
```

**Protocol Signature:**
```python
def find_match(
    self, 
    target_name: str, 
    candidates: list[Student], 
    threshold: int = 80
) -> Student | None
```

#### `FuzzyStudentMatcher`

Flexible matching using fuzzy string matching (Levenshtein distance) via the `thefuzz` library.

**When to use:**
- Submission names may have typos or variations
- Need to handle partial matches
- Names may differ slightly from records

**Features:**
- First attempts exact match (fast path)
- Falls back to fuzzy matching with configurable threshold
- Uses Levenshtein distance ratio for scoring
- Default threshold: 80 (0-100 scale)

**Example:**
```python
from grader.domain import FuzzyStudentMatcher, Student, StudentId

students = [
    Student(StudentId("1", "jdoe"), "John", "Doe"),
    Student(StudentId("2", "jsmith"), "Jane", "Smith"),
]

matcher = FuzzyStudentMatcher()

# Exact match (fast path)
result = matcher.find_match("John Doe", students)
# Returns John Doe student

# Fuzzy match with typo
result = matcher.find_match("Jon Doe", students, threshold=70)
# Returns John Doe student (close enough match)

# Partial match with lower threshold
result = matcher.find_match("John", students, threshold=50)
# Returns John Doe student

# Poor match rejected
result = matcher.find_match("Robert Williams", students, threshold=80)
# Returns None (below threshold)
```

**Threshold Guidelines:**
- **90-100**: Very strict, only minor typos
- **80-89**: Default, good balance for most use cases
- **70-79**: Moderate, allows more variation
- **50-69**: Lenient, accepts partial matches
- **Below 50**: Very lenient, may produce false positives

#### `CompositeStudentMatcher`

Combines multiple matching strategies in sequence, using the first successful match.

**When to use:**
- Need fallback strategies
- Different matching requirements for different cases
- Want to optimize performance (fast exact match first, then fuzzy)

**Example:**
```python
from grader.domain import (
    CompositeStudentMatcher,
    ExactStudentMatcher,
    FuzzyStudentMatcher,
    Student,
    StudentId,
)

students = [
    Student(StudentId("1", "jdoe"), "John", "Doe"),
    Student(StudentId("2", "jsmith"), "Jane", "Smith"),
]

# Create composite strategy: exact first, then fuzzy
exact_matcher = ExactStudentMatcher()
fuzzy_matcher = FuzzyStudentMatcher()
matcher = CompositeStudentMatcher([exact_matcher, fuzzy_matcher])

# Exact match uses first matcher (faster)
result = matcher.find_match("John Doe", students)
# Returns John Doe via exact matcher

# Fuzzy match falls back to second matcher
result = matcher.find_match("Jon Doe", students, threshold=70)
# Returns John Doe via fuzzy matcher
```

**Best Practice Pattern:**
```python
# Recommended production configuration
matcher = CompositeStudentMatcher([
    ExactStudentMatcher(),      # Fast path for exact matches
    FuzzyStudentMatcher(),      # Fallback for variations
])
```

### Custom Matcher Implementation

You can create custom matchers by implementing the `StudentMatcherProtocol`:

```python
from typing import Protocol
from grader.domain import Student

class StudentMatcherProtocol(Protocol):
    def find_match(
        self, 
        target_name: str, 
        candidates: list[Student], 
        threshold: int = 80
    ) -> Student | None:
        ...

# Example custom matcher
class FirstLetterMatcher:
    """Matches students by first letter of first and last name."""
    
    def find_match(self, target_name, candidates, threshold=80):
        parts = target_name.split()
        if len(parts) < 2:
            return None
            
        target_initials = parts[0][0] + parts[-1][0]
        
        for student in candidates:
            student_initials = student.first_name[0] + student.last_name[0]
            if target_initials.lower() == student_initials.lower():
                return student
        
        return None

# Use in composite
matcher = CompositeStudentMatcher([
    ExactStudentMatcher(),
    FuzzyStudentMatcher(),
    FirstLetterMatcher(),  # Custom fallback
])
```

## Integration with Bulk Grader

The bulk grader provides backward-compatible wrapper functions:

```python
from grader.bulk_grader import normalize_name, find_best_name_match

# These delegate to domain services
name = normalize_name("José María")
best_match = find_best_name_match("John Doe", ["Jane Smith", "John Doe"])
```

**Migration Path:**

For new code, import directly from domain:
```python
# Old way (legacy)
from grader.bulk_grader import normalize_name, find_best_name_match

# New way (recommended)
from grader.domain import normalize_name, FuzzyStudentMatcher
```

## Testing

### Unit Tests

Comprehensive unit tests are available in `test/unit/test_student_matchers.py`:

```bash
# Run all matcher tests
pytest test/unit/test_student_matchers.py -v

# Run specific test class
pytest test/unit/test_student_matchers.py::TestFuzzyStudentMatcher -v
```

**Test Coverage:**
- `TestNormalizeName`: Name normalization with various inputs
- `TestExactStudentMatcher`: Exact matching scenarios
- `TestFuzzyStudentMatcher`: Fuzzy matching with thresholds
- `TestCompositeStudentMatcher`: Composite strategy behavior
- `TestStudentMatcherIntegration`: Real-world scenarios

### Integration Tests

Integration tests verify backward compatibility:

```bash
# Run bulk grader tests
pytest test/test_bulk_grader.py::TestNameMatching -v
```

## Performance Considerations

### Matching Strategy Performance

1. **ExactStudentMatcher**: O(n) where n = number of candidates
   - Fastest for exact matches
   - Recommended as first strategy in composite

2. **FuzzyStudentMatcher**: O(n × m) where n = candidates, m = name length
   - Has O(n) fast path for exact matches
   - More expensive for fuzzy matching
   - Caches normalized names to reduce overhead

3. **CompositeStudentMatcher**: Sum of all matchers until success
   - Optimized by ordering strategies from fastest to slowest
   - Early exit on first match

### Optimization Tips

```python
# Good: Fast exact match first
matcher = CompositeStudentMatcher([
    ExactStudentMatcher(),     # O(n) - fast
    FuzzyStudentMatcher(),     # O(n×m) - slower
])

# Not optimal: Slow matcher first
matcher = CompositeStudentMatcher([
    FuzzyStudentMatcher(),     # Always runs, even for exact matches
    ExactStudentMatcher(),     # Never reached for exact matches
])
```

## Error Handling

All matchers gracefully handle edge cases:

```python
# Empty candidate list
matcher.find_match("John Doe", [])  # Returns None

# Empty name
matcher.find_match("", candidates)  # Returns None

# Single-word names
matcher.find_match("John", candidates)  # May match with low threshold

# Special characters
matcher.find_match("Mary-Jane O'Connor", candidates)  # Handled correctly
```

## Design Principles

1. **Single Responsibility**: Each matcher implements one strategy
2. **Open/Closed**: Easy to add new matchers without modifying existing code
3. **Dependency Inversion**: Depends on `Student` domain model, not infrastructure
4. **Protocol-Based**: Uses structural typing for flexibility
5. **Immutability**: Matchers don't modify input data

## Future Enhancements

Potential improvements for future versions:

1. **Phonetic Matching**: Use Soundex or Metaphone for sound-alike names
2. **Weighted Matching**: Different weights for first name vs. last name
3. **Machine Learning**: Train model on historical matching data
4. **Caching**: Cache normalized names across multiple matching operations
5. **Async Support**: Async variants for large-scale batch processing

## References

- [thefuzz library](https://github.com/seatgeek/thefuzz): Fuzzy string matching
- [unidecode library](https://pypi.org/project/Unidecode/): Unicode normalization
- [Levenshtein distance](https://en.wikipedia.org/wiki/Levenshtein_distance): String similarity algorithm

---

## Test Output Parsers

The test output parsing functionality provides extensible parsers for extracting grades from various test output formats. This allows the grading system to work with different testing frameworks and custom output formats.

### Core Components

All parsers implement the `TestOutputParser` protocol:

```python
class TestOutputParser(Protocol):
    def parse_output(self, output: str) -> tuple[float, float]:
        """
        Parse test output to extract grades.
        
        Returns:
            Tuple of (points_earned, points_possible)
        """
        ...
```

### Parser Implementations

#### `RegexTestOutputParser`

Flexible regex-based parser with customizable patterns. This is the default parser used by the grading system.

**Default Pattern:**
```
Grade for <name> (out of [a] possible <max>): <total>
```

**When to use:**
- Custom test output formats
- Simple text-based test results
- Need pattern customization
- Default grading system behavior

**Features:**
- Configurable regex patterns with named groups
- Supports regex flags (case-insensitive, multiline, etc.)
- Sums multiple matches in output
- Handles decimal points
- Backward compatible with legacy `calculate_grade_from_output`

**Example:**
```python
from grader.domain import RegexTestOutputParser

# Use default pattern
parser = RegexTestOutputParser()
output = "Grade for Test1 (out of possible 10): 8\n"
points, possible = parser.parse_output(output)
# Returns: (8.0, 10.0)

# Use custom pattern
pattern = r"Score: (?P<total>\d+)/(?P<max>\d+)"
parser = RegexTestOutputParser(pattern)
output = "Score: 42/50\n"
points, possible = parser.parse_output(output)
# Returns: (42.0, 50.0)

# Use regex flags
import re
pattern = r"SCORE: (?P<total>\d+)/(?P<max>\d+)"
parser = RegexTestOutputParser(pattern, flags=re.IGNORECASE)
output = "score: 10/20\n"  # lowercase matches with IGNORECASE
points, possible = parser.parse_output(output)
# Returns: (10.0, 20.0)
```

**Pattern Requirements:**
- Must have named group `total` for points earned
- Must have named group `max` for points possible
- Both groups should match numeric values (int or float)

**Common Patterns:**
```python
# ITI1121 default format
DEFAULT_PATTERN = (
    r"Grade for .+ \(out of (a\s+)?possible (?P<max>\d+(\.\d+)?)\): "
    r"(?P<total>\d+(\.\d+)?)"
)

# Simple format: "Test: 8/10"
SIMPLE_PATTERN = r"Test: (?P<total>\d+)/(?P<max>\d+)"

# JSON-like: "points": 8, "max": 10
JSON_PATTERN = r'"points":\s*(?P<total>\d+),\s*"max":\s*(?P<max>\d+)'
```

#### `JUnitXMLTestOutputParser`

Parser for JUnit XML test output format, commonly used by Java testing frameworks.

**When to use:**
- JUnit or TestNG test output
- Standard XML test reports
- Need structured test result parsing
- Automated testing frameworks

**Features:**
- Parses `<testsuite>` and `<testcase>` elements
- Detects failures and errors automatically
- Customizable points per test
- Handles both `<testsuites>` wrapper and direct `<testsuite>`
- Gracefully handles malformed XML

**Example:**
```python
from grader.domain import JUnitXMLTestOutputParser

# Default: 1 point per passing test
parser = JUnitXMLTestOutputParser()
xml = """<?xml version="1.0"?>
<testsuite tests="3" failures="1" errors="0">
    <testcase name="test1" />
    <testcase name="test2">
        <failure message="Expected 5 but got 3" />
    </testcase>
    <testcase name="test3" />
</testsuite>"""

points, possible = parser.parse_output(xml)
# Returns: (2.0, 3.0) - 2 passing tests out of 3

# Custom points per test
parser = JUnitXMLTestOutputParser(points_per_test=10.0)
points, possible = parser.parse_output(xml)
# Returns: (20.0, 30.0) - 2 passing × 10 points each
```

**XML Format Support:**
```xml
<!-- Single test suite -->
<testsuite tests="N" failures="F" errors="E">
    <testcase name="test1" />
    <testcase name="test2">
        <failure message="..." />
    </testcase>
</testsuite>

<!-- Multiple test suites -->
<testsuites>
    <testsuite tests="N1" ...>...</testsuite>
    <testsuite tests="N2" ...>...</testsuite>
</testsuites>
```

**Security Note:**
This parser uses `xml.etree.ElementTree` which is suitable for parsing trusted test output from your own test runners. Do not use with arbitrary XML from untrusted sources.

#### `CustomPatternTestOutputParser`

Highly flexible parser supporting custom functions or pattern lists.

**When to use:**
- Completely custom output formats
- Complex parsing logic needed
- Multiple different patterns in same output
- Non-standard test result formats

**Features:**
- Function-based parsing with full control
- Pattern list with custom handlers
- Exception handling for robustness
- Maximum flexibility

**Example - Function-based:**
```python
from grader.domain import CustomPatternTestOutputParser

def parse_scores(output):
    """Custom parsing logic."""
    if "PASSED:" in output:
        parts = output.split("PASSED:")[1].strip().split("/")
        return float(parts[0]), float(parts[1])
    return 0.0, 0.0

parser = CustomPatternTestOutputParser(parse_scores)
output = "PASSED: 8/10"
points, possible = parser.parse_output(output)
# Returns: (8.0, 10.0)
```

**Example - Pattern list:**
```python
patterns = [
    # Pattern 1: Handle passed tests
    (r"Passed: (\d+)", lambda m: (float(m.group(1)), 10.0)),
    # Pattern 2: Handle failed tests
    (r"Failed: (\d+)", lambda m: (0.0, float(m.group(1)))),
]
parser = CustomPatternTestOutputParser(patterns)
output = """
Passed: 8
Failed: 2
"""
points, possible = parser.parse_output(output)
# Returns: (8.0, 12.0)
```

**Pattern List Format:**
```python
patterns = [
    (regex_pattern, handler_function),
    ...
]
```
- `regex_pattern`: Regular expression string
- `handler_function`: Function receiving regex match object, returns `(earned, possible)`

#### `CompositeTestOutputParser`

Combines multiple parsers in sequence, using the first successful one.

**When to use:**
- Support multiple output formats
- Fallback strategies needed
- Optimize with fast parser first
- Migration between formats

**Features:**
- Tries parsers in sequence
- Returns first non-zero result
- Exception handling per parser
- Early exit on success

**Example:**
```python
from grader.domain import (
    CompositeTestOutputParser,
    JUnitXMLTestOutputParser,
    RegexTestOutputParser,
)

# Try JUnit XML first (for automated tests), then regex (for custom tests)
junit_parser = JUnitXMLTestOutputParser(points_per_test=10.0)
regex_parser = RegexTestOutputParser()

composite = CompositeTestOutputParser([junit_parser, regex_parser])

# Works with JUnit XML
xml_output = """<?xml version="1.0"?>
<testsuite tests="3" failures="1" errors="0">
    <testcase name="test1" />
    <testcase name="test2"><failure message="Failed" /></testcase>
    <testcase name="test3" />
</testsuite>"""
points, possible = composite.parse_output(xml_output)
# Returns: (20.0, 30.0) - Uses JUnit parser

# Falls back to regex for non-XML
text_output = "Grade for Test1 (out of possible 100): 85\n"
points, possible = composite.parse_output(text_output)
# Returns: (85.0, 100.0) - Uses regex parser
```

**Best Practice Pattern:**
```python
# Recommended production configuration
composite = CompositeTestOutputParser([
    JUnitXMLTestOutputParser(),      # Fast for XML formats
    RegexTestOutputParser(),          # Default fallback
    CustomPatternTestOutputParser()   # Final fallback for edge cases
])
```

### Integration with Grading System

#### Legacy Compatibility

The existing `calculate_grade_from_output` function now uses `RegexTestOutputParser` internally:

```python
from grader._grader import calculate_grade_from_output

# Legacy function (backward compatible)
output = "Grade for Test1 (out of possible 10): 8\n"
points, possible = calculate_grade_from_output(output)
# Still works exactly as before
```

#### Migration Path

For new code, import directly from domain:

```python
# Old way (legacy)
from grader._grader import calculate_grade_from_output
points, possible = calculate_grade_from_output(output)

# New way (recommended)
from grader.domain import RegexTestOutputParser
parser = RegexTestOutputParser()
points, possible = parser.parse_output(output)
```

### Custom Parser Implementation

Create custom parsers by implementing the `TestOutputParser` protocol:

```python
from grader.domain import TestOutputParser

class MyCustomParser:
    """Custom parser for specific format."""
    
    def parse_output(self, output: str) -> tuple[float, float]:
        """Parse custom format."""
        # Your parsing logic here
        earned = 0.0
        possible = 0.0
        
        # ... parse output ...
        
        return earned, possible

# Use in composite
from grader.domain import CompositeTestOutputParser, RegexTestOutputParser

composite = CompositeTestOutputParser([
    MyCustomParser(),          # Try custom first
    RegexTestOutputParser(),   # Fallback to default
])
```

### Testing

#### Unit Tests

Comprehensive unit tests are available in `test/unit/test_output_parsers.py`:

```bash
# Run all parser tests
pytest test/unit/test_output_parsers.py -v

# Run specific parser tests
pytest test/unit/test_output_parsers.py::TestRegexTestOutputParser -v
pytest test/unit/test_output_parsers.py::TestJUnitXMLTestOutputParser -v
```

**Test Coverage:**
- `TestRegexTestOutputParser`: Default patterns, custom patterns, edge cases
- `TestJUnitXMLTestOutputParser`: XML parsing, failures, errors, malformed XML
- `TestCustomPatternTestOutputParser`: Function-based, pattern lists, error handling
- `TestCompositeTestOutputParser`: Fallback strategies, exception handling
- `TestOutputParserIntegration`: Backward compatibility, real-world scenarios

#### Example Test Cases

```python
def test_regex_parser():
    parser = RegexTestOutputParser()
    output = "Grade for Test1 (out of possible 10): 8\n"
    total, possible = parser.parse_output(output)
    assert total == 8.0
    assert possible == 10.0

def test_junit_parser():
    parser = JUnitXMLTestOutputParser()
    xml = """<?xml version="1.0"?>
    <testsuite tests="3" failures="1" errors="0">
        <testcase name="test1" />
        <testcase name="test2"><failure/></testcase>
        <testcase name="test3" />
    </testsuite>"""
    total, possible = parser.parse_output(xml)
    assert total == 2.0
    assert possible == 3.0
```

### Performance Considerations

#### Parser Performance

1. **RegexTestOutputParser**: O(n) where n = number of lines
   - Fast for most use cases
   - Minimal overhead for pattern matching

2. **JUnitXMLTestOutputParser**: O(n) where n = number of test cases
   - XML parsing has higher overhead
   - Still fast for typical test suites (<1000 tests)

3. **CustomPatternTestOutputParser**: Depends on implementation
   - Function-based: As fast as your function
   - Pattern-based: O(n × m) where m = number of patterns

4. **CompositeTestOutputParser**: Sum of parsers until success
   - Optimize by ordering from fastest to slowest
   - Early exit on first match

#### Optimization Tips

```python
# Good: Fast parser first
composite = CompositeTestOutputParser([
    RegexTestOutputParser(),      # O(n) - fast
    JUnitXMLTestOutputParser(),   # O(n) with XML overhead
    CustomPatternTestOutputParser()  # Potentially slower
])

# Not optimal: Slow parser first
composite = CompositeTestOutputParser([
    CustomPatternTestOutputParser(),  # Always runs first
    RegexTestOutputParser(),          # Rarely used
])
```

### Error Handling

All parsers gracefully handle edge cases:

```python
# Empty output
parser.parse_output("")  # Returns (0.0, 0.0)

# No matches found
parser.parse_output("Random text")  # Returns (0.0, 0.0)

# Malformed data
junit_parser.parse_output("Not XML")  # Returns (0.0, 0.0)

# Invalid numbers
regex_parser.parse_output("Grade: abc/xyz")  # Returns (0.0, 0.0)
```

### Design Principles

1. **Single Responsibility**: Each parser handles one format type
2. **Open/Closed**: Easy to add new parsers without modifying existing ones
3. **Dependency Inversion**: Depends on protocol, not concrete implementations
4. **Protocol-Based**: Uses structural typing for flexibility
5. **Fail-Safe**: Returns (0, 0) instead of raising exceptions
6. **Composability**: Parsers can be combined and chained

### Future Enhancements

Potential improvements for future versions:

1. **YAML/JSON Parsers**: Support for structured data formats
2. **TAP Parser**: Test Anything Protocol support
3. **Custom Scoring**: Weighted test cases, partial credit
4. **Streaming Parser**: For very large test outputs
5. **Async Support**: Async variants for I/O-bound parsing
6. **Parser Registry**: Plugin system for dynamic parser loading
7. **Performance Metrics**: Track parsing time and success rates

### Use Cases

#### Use Case 1: Standard ITI1121 Grading
```python
# Use default regex parser
parser = RegexTestOutputParser()
points, possible = parser.parse_output(test_output)
```

#### Use Case 2: JUnit-based Testing
```python
# Use JUnit XML parser with custom points
parser = JUnitXMLTestOutputParser(points_per_test=5.0)
points, possible = parser.parse_output(junit_xml_output)
```

#### Use Case 3: Mixed Output Formats
```python
# Use composite parser for flexibility
composite = CompositeTestOutputParser([
    JUnitXMLTestOutputParser(),
    RegexTestOutputParser(),
])
points, possible = composite.parse_output(unknown_format_output)
```

#### Use Case 4: Custom Test Framework
```python
# Use custom parser for proprietary format
def parse_custom_format(output):
    # Your custom parsing logic
    return earned, possible

parser = CustomPatternTestOutputParser(parse_custom_format)
points, possible = parser.parse_output(custom_output)
```

### Migration Guide

#### Migrating from Legacy Code

1. **Replace direct regex usage:**
   ```python
   # Before
   import re
   pattern = re.compile(r"...")
   for line in output.split("\n"):
       match = pattern.search(line)
       # ... processing ...
   
   # After
   from grader.domain import RegexTestOutputParser
   parser = RegexTestOutputParser(r"...")
   points, possible = parser.parse_output(output)
   ```

2. **Replace calculate_grade_from_output:**
   ```python
   # Before
   from grader._grader import calculate_grade_from_output
   total, possible = calculate_grade_from_output(output)
   
   # After
   from grader.domain import RegexTestOutputParser
   parser = RegexTestOutputParser()
   total, possible = parser.parse_output(output)
   ```

3. **Add fallback strategies:**
   ```python
   # Add composite parser for robustness
   from grader.domain import CompositeTestOutputParser, RegexTestOutputParser
   
   composite = CompositeTestOutputParser([
       RegexTestOutputParser(),
       # Add fallback parsers as needed
   ])
   ```
