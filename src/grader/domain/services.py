"""Domain services for the grading system."""

from typing import TYPE_CHECKING
from thefuzz import fuzz, process
from unidecode import unidecode

from .models import Student

if TYPE_CHECKING:
    from .protocols import StudentMatcher


def normalize_name(name: str) -> str:
    """
    Normalize a name for comparison by removing accents and converting to lowercase.

    This function is used across all student matching strategies to ensure
    consistent name comparison regardless of encoding or case differences.

    Args:
        name: The name to normalize

    Returns:
        Normalized name with accents removed and in lowercase

    Examples:
        >>> normalize_name("José María")
        'jose maria'
        >>> normalize_name("  Multiple   Spaces  ")
        'multiple spaces'
        >>> normalize_name("François Côté")
        'francois cote'
    """
    # Convert unicode characters to ASCII equivalents
    normalized = unidecode(name)
    # Convert to lowercase and remove extra whitespace
    normalized = " ".join(normalized.lower().split())
    return normalized


class ExactStudentMatcher:
    """
    Student matcher that uses exact name matching.

    This matcher normalizes names and performs exact string comparison.
    It's the fastest and most precise matching strategy, suitable when
    submission names exactly match student records.

    Examples:
        >>> matcher = ExactStudentMatcher()
        >>> students = [
        ...     Student(StudentId("1", "jdoe"), "John", "Doe"),
        ...     Student(StudentId("2", "jsmith"), "Jane", "Smith")
        ... ]
        >>> result = matcher.find_match("John Doe", students)
        >>> result.student_id.username
        'jdoe'
    """

    def find_match(
        self, target_name: str, candidates: list[Student], threshold: int = 80
    ) -> Student | None:
        """
        Find exact matching student by normalized name.

        Args:
            target_name: The name to match against
            candidates: List of candidate students
            threshold: Ignored for exact matching (kept for protocol compatibility)

        Returns:
            Matching student or None if no exact match found
        """
        normalized_target = normalize_name(target_name)

        for student in candidates:
            full_name = student.full_name
            if normalize_name(full_name) == normalized_target:
                return student

        return None


class FuzzyStudentMatcher:
    """
    Student matcher that uses fuzzy string matching.

    This matcher uses the Levenshtein distance algorithm via thefuzz library
    to find approximate matches. It's useful when submission names may have
    typos, slight variations, or partial names.

    The matcher first tries exact matching, then falls back to fuzzy matching
    if no exact match is found.

    Examples:
        >>> matcher = FuzzyStudentMatcher()
        >>> students = [
        ...     Student(StudentId("1", "jdoe"), "John", "Doe"),
        ...     Student(StudentId("2", "jsmith"), "Jane", "Smith")
        ... ]
        >>> # Exact match
        >>> result = matcher.find_match("John Doe", students)
        >>> result.student_id.username
        'jdoe'
        >>> # Fuzzy match with typo
        >>> result = matcher.find_match("Jon Doe", students, threshold=70)
        >>> result.student_id.username
        'jdoe'
    """

    def find_match(
        self, target_name: str, candidates: list[Student], threshold: int = 80
    ) -> Student | None:
        """
        Find best matching student using fuzzy string matching.

        First attempts exact match, then falls back to fuzzy matching
        using Levenshtein distance ratio.

        Args:
            target_name: The name to match against
            candidates: List of candidate students
            threshold: Minimum match score (0-100), default 80

        Returns:
            Best matching student or None if no good match found
        """
        if not candidates:
            return None

        normalized_target = normalize_name(target_name)
        candidate_names = [student.full_name for student in candidates]
        normalized_candidates = [normalize_name(name) for name in candidate_names]

        # Try exact match first
        if normalized_target in normalized_candidates:
            idx = normalized_candidates.index(normalized_target)
            return candidates[idx]

        # Try fuzzy matching
        result = process.extractOne(
            normalized_target, normalized_candidates, scorer=fuzz.ratio
        )
        if result and result[1] >= threshold:
            idx = normalized_candidates.index(result[0])
            return candidates[idx]

        return None


class CompositeStudentMatcher:
    """
    Student matcher that tries multiple matching strategies in sequence.

    This matcher applies a chain of matchers, returning the first successful match.
    This is useful for implementing fallback strategies, such as trying exact matching
    first, then fuzzy matching with different thresholds.

    Examples:
        >>> exact_matcher = ExactStudentMatcher()
        >>> fuzzy_matcher = FuzzyStudentMatcher()
        >>> composite = CompositeStudentMatcher([exact_matcher, fuzzy_matcher])
        >>> students = [
        ...     Student(StudentId("1", "jdoe"), "John", "Doe"),
        ... ]
        >>> # Will use exact matcher
        >>> result = composite.find_match("John Doe", students)
        >>> result.student_id.username
        'jdoe'
        >>> # Will fall back to fuzzy matcher
        >>> result = composite.find_match("Jon Doe", students, threshold=70)
        >>> result.student_id.username
        'jdoe'
    """

    def __init__(self, matchers: list["StudentMatcher"]):
        """
        Initialize composite matcher with a list of matchers.

        Args:
            matchers: List of matchers to try in sequence
        """
        self.matchers = matchers

    def find_match(
        self, target_name: str, candidates: list[Student], threshold: int = 80
    ) -> Student | None:
        """
        Try each matcher in sequence until a match is found.

        Args:
            target_name: The name to match against
            candidates: List of candidate students
            threshold: Minimum match score (0-100), passed to all matchers

        Returns:
            First successful match or None if no matcher finds a match
        """
        for matcher in self.matchers:
            result = matcher.find_match(target_name, candidates, threshold)
            if result is not None:
                return result

        return None
