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


class SimpleGradingStrategy:
    """
    Simple grading strategy that calculates grade as a percentage.

    This strategy calculates the final grade as a simple percentage:
    (points_earned / points_possible) * 100

    This is the default grading strategy and matches the current behavior
    of the calculate_grade_from_output function.

    Examples:
        >>> strategy = SimpleGradingStrategy()
        >>> strategy.apply_strategy(85.0, 100.0)
        85.0
        >>> strategy.apply_strategy(42.5, 50.0)
        85.0
    """

    def apply_strategy(self, points_earned: float, points_possible: float) -> float:
        """
        Calculate grade as a simple percentage.

        Args:
            points_earned: Points earned by the student
            points_possible: Maximum possible points

        Returns:
            Percentage score (0-100)
        """
        if points_possible == 0:
            return 0.0
        return (points_earned / points_possible) * 100


class WeightedGradingStrategy:
    """
    Weighted grading strategy that applies weights to test categories.

    This strategy allows different test categories to have different weights
    in the final grade calculation. Each test name can be mapped to a category,
    and each category has an associated weight.

    Examples:
        >>> weights = {"basics": 0.3, "advanced": 0.7}
        >>> category_map = {"Test1": "basics", "Test2": "advanced"}
        >>> strategy = WeightedGradingStrategy(weights, category_map)
        >>> # If basics: 10/10 and advanced: 14/20
        >>> # Final: (10/10 * 0.3 + 14/20 * 0.7) * 100 = 79.0
    """

    def __init__(
        self, category_weights: dict[str, float], test_categories: dict[str, str] | None = None
    ):
        """
        Initialize weighted grading strategy.

        Args:
            category_weights: Mapping of category names to weights (must sum to 1.0)
            test_categories: Optional mapping of test names to categories
        """
        self.category_weights = category_weights
        self.test_categories = test_categories or {}
        
        # Validate weights sum to 1.0 (with small tolerance for floating point)
        total_weight = sum(category_weights.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(
                f"Category weights must sum to 1.0, got {total_weight}"
            )

    def apply_strategy(self, points_earned: float, points_possible: float) -> float:
        """
        Calculate weighted grade.

        Note: This is a simplified implementation that assumes a single test result.
        For multiple weighted tests, use apply_strategy_to_results instead.

        Args:
            points_earned: Points earned by the student
            points_possible: Maximum possible points

        Returns:
            Percentage score (0-100)
        """
        if points_possible == 0:
            return 0.0
        return (points_earned / points_possible) * 100

    def apply_strategy_to_results(
        self, test_results: dict[str, tuple[float, float]]
    ) -> float:
        """
        Calculate weighted grade from multiple test results.

        Args:
            test_results: Dictionary mapping test names to (earned, possible) tuples

        Returns:
            Weighted percentage score (0-100)
        """
        if not test_results:
            return 0.0

        weighted_score = 0.0
        
        for test_name, (earned, possible) in test_results.items():
            category = self.test_categories.get(test_name, "default")
            weight = self.category_weights.get(category, 0.0)
            
            if possible > 0:
                test_percentage = earned / possible
                weighted_score += test_percentage * weight

        return weighted_score * 100


class DropLowestGradingStrategy:
    """
    Drop-lowest grading strategy that drops N lowest test scores.

    This strategy calculates the grade by dropping a specified number of
    the lowest-scoring tests before calculating the final percentage.
    This is useful for giving students some flexibility with their performance.

    Examples:
        >>> strategy = DropLowestGradingStrategy(drop_count=1)
        >>> # Test results: [8/10, 5/10, 9/10] - drops 5/10
        >>> # Final: (8 + 9) / (10 + 10) * 100 = 85.0
    """

    def __init__(self, drop_count: int = 1):
        """
        Initialize drop-lowest grading strategy.

        Args:
            drop_count: Number of lowest scores to drop (default: 1)
        """
        if drop_count < 0:
            raise ValueError("drop_count must be non-negative")
        self.drop_count = drop_count

    def apply_strategy(self, points_earned: float, points_possible: float) -> float:
        """
        Calculate grade with drop-lowest applied.

        Note: This is a simplified implementation for a single test result.
        For multiple tests, use apply_strategy_to_results instead.

        Args:
            points_earned: Points earned by the student
            points_possible: Maximum possible points

        Returns:
            Percentage score (0-100)
        """
        if points_possible == 0:
            return 0.0
        return (points_earned / points_possible) * 100

    def apply_strategy_to_results(
        self, test_results: list[tuple[float, float]]
    ) -> float:
        """
        Calculate grade after dropping lowest N scores.

        Args:
            test_results: List of (earned, possible) tuples for each test

        Returns:
            Percentage score (0-100) after dropping lowest scores
        """
        if not test_results:
            return 0.0

        # If we're dropping all or more tests than we have, return 0
        if self.drop_count >= len(test_results):
            return 0.0

        # Calculate percentage for each test
        test_percentages = []
        for earned, possible in test_results:
            if possible > 0:
                percentage = (earned / possible) * 100
                test_percentages.append((percentage, earned, possible))
            else:
                test_percentages.append((0.0, earned, possible))

        # Sort by percentage (ascending) to identify lowest scores
        test_percentages.sort(key=lambda x: x[0])

        # Drop the lowest N scores
        kept_tests = test_percentages[self.drop_count:]

        # Calculate final grade from kept tests
        if not kept_tests:
            return 0.0

        total_earned = sum(t[1] for t in kept_tests)
        total_possible = sum(t[2] for t in kept_tests)

        if total_possible == 0:
            return 0.0

        return (total_earned / total_possible) * 100
