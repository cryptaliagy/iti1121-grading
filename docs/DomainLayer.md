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
