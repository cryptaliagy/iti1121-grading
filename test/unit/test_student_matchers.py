#!/usr/bin/env python3

"""Unit tests for domain services (student matchers)."""

import pytest

from grader.domain.models import Student, StudentId
from grader.domain.services import (
    CompositeStudentMatcher,
    ExactStudentMatcher,
    FuzzyStudentMatcher,
    normalize_name,
)


class TestNormalizeName:
    """Test the normalize_name utility function."""

    @pytest.mark.parametrize(
        "input_name,expected",
        [
            # Basic accented characters
            ("José María", "jose maria"),
            ("François Côté", "francois cote"),
            # Case and spacing normalization
            ("  Multiple   Spaces  ", "multiple spaces"),
            ("UPPERCASE", "uppercase"),
            # Extended Latin characters
            ("Müller", "muller"),
            ("Åse Bjørk", "ase bjork"),
            # Edge cases
            ("", ""),
            ("   ", ""),
            ("A", "a"),
        ],
    )
    def test_normalize_name(self, input_name, expected):
        """Test name normalization with various inputs."""
        assert normalize_name(input_name) == expected


class TestExactStudentMatcher:
    """Test the ExactStudentMatcher implementation."""

    def test_exact_match_found(self):
        """Test finding an exact match."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
            Student(StudentId("2", "jsmith"), "Jane", "Smith"),
            Student(StudentId("3", "bwilson"), "Bob", "Wilson"),
        ]

        matcher = ExactStudentMatcher()
        result = matcher.find_match("John Doe", students)

        assert result is not None
        assert result.student_id.username == "jdoe"
        assert result.first_name == "John"
        assert result.last_name == "Doe"

    def test_exact_match_case_insensitive(self):
        """Test exact match is case insensitive."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
        ]

        matcher = ExactStudentMatcher()
        result = matcher.find_match("john doe", students)

        assert result is not None
        assert result.student_id.username == "jdoe"

    def test_exact_match_with_accents(self):
        """Test exact match handles accented characters."""
        students = [
            Student(StudentId("1", "jmaria"), "José", "María"),
        ]

        matcher = ExactStudentMatcher()
        
        # Match with accents
        result = matcher.find_match("José María", students)
        assert result is not None
        assert result.student_id.username == "jmaria"

        # Match without accents
        result = matcher.find_match("Jose Maria", students)
        assert result is not None
        assert result.student_id.username == "jmaria"

    def test_exact_match_with_extra_whitespace(self):
        """Test exact match handles extra whitespace."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
        ]

        matcher = ExactStudentMatcher()
        result = matcher.find_match("  John   Doe  ", students)

        assert result is not None
        assert result.student_id.username == "jdoe"

    def test_exact_match_not_found(self):
        """Test when no exact match exists."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
            Student(StudentId("2", "jsmith"), "Jane", "Smith"),
        ]

        matcher = ExactStudentMatcher()
        result = matcher.find_match("Bob Wilson", students)

        assert result is None

    def test_exact_match_partial_name_not_found(self):
        """Test that partial names don't match."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
        ]

        matcher = ExactStudentMatcher()
        result = matcher.find_match("John", students)

        assert result is None

    def test_exact_match_empty_candidates(self):
        """Test with empty candidate list."""
        matcher = ExactStudentMatcher()
        result = matcher.find_match("John Doe", [])

        assert result is None

    def test_exact_match_threshold_ignored(self):
        """Test that threshold parameter is ignored for exact matching."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
        ]

        matcher = ExactStudentMatcher()
        # Threshold should be ignored
        result = matcher.find_match("John Doe", students, threshold=0)

        assert result is not None
        assert result.student_id.username == "jdoe"


class TestFuzzyStudentMatcher:
    """Test the FuzzyStudentMatcher implementation."""

    def test_fuzzy_exact_match(self):
        """Test fuzzy matcher finds exact matches."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
            Student(StudentId("2", "jsmith"), "Jane", "Smith"),
        ]

        matcher = FuzzyStudentMatcher()
        result = matcher.find_match("John Doe", students)

        assert result is not None
        assert result.student_id.username == "jdoe"

    def test_fuzzy_match_with_typo(self):
        """Test fuzzy matcher handles typos."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
            Student(StudentId("2", "jsmith"), "Jane", "Smith"),
        ]

        matcher = FuzzyStudentMatcher()
        # Small typo should still match with default threshold
        result = matcher.find_match("Jon Doe", students, threshold=70)

        assert result is not None
        assert result.student_id.username == "jdoe"

    def test_fuzzy_match_partial_name(self):
        """Test fuzzy matcher with partial names."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
            Student(StudentId("2", "jsmith"), "Jane", "Smith"),
        ]

        matcher = FuzzyStudentMatcher()
        # Partial name with lower threshold
        result = matcher.find_match("John", students, threshold=50)

        assert result is not None
        assert result.student_id.username == "jdoe"

    def test_fuzzy_match_below_threshold(self):
        """Test fuzzy matcher rejects poor matches."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
            Student(StudentId("2", "jsmith"), "Jane", "Smith"),
        ]

        matcher = FuzzyStudentMatcher()
        # Very different name with high threshold
        result = matcher.find_match("Robert Williams", students, threshold=80)

        assert result is None

    def test_fuzzy_match_with_accents(self):
        """Test fuzzy matcher handles accented characters."""
        students = [
            Student(StudentId("1", "jmaria"), "José", "María"),
            Student(StudentId("2", "fcote"), "François", "Côté"),
        ]

        matcher = FuzzyStudentMatcher()

        # Match with normalized names
        result = matcher.find_match("Jose Maria", students)
        assert result is not None
        assert result.student_id.username == "jmaria"

        result = matcher.find_match("Francois Cote", students)
        assert result is not None
        assert result.student_id.username == "fcote"

    def test_fuzzy_match_international_names(self):
        """Test fuzzy matcher with international names."""
        students = [
            Student(StudentId("1", "vdvorak"), "Václav", "Dvořák"),
            Student(StudentId("2", "bastrom"), "Björn", "Åström"),
        ]

        matcher = FuzzyStudentMatcher()

        result = matcher.find_match("Vaclav Dvorak", students)
        assert result is not None
        assert result.student_id.username == "vdvorak"

        result = matcher.find_match("Bjorn Astrom", students)
        assert result is not None
        assert result.student_id.username == "bastrom"

    def test_fuzzy_match_empty_candidates(self):
        """Test with empty candidate list."""
        matcher = FuzzyStudentMatcher()
        result = matcher.find_match("John Doe", [])

        assert result is None

    def test_fuzzy_match_custom_threshold(self):
        """Test fuzzy matcher with various threshold values."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
        ]

        matcher = FuzzyStudentMatcher()

        # Very low threshold - partial match should succeed
        result = matcher.find_match("J D", students, threshold=30)
        assert result is not None

        # Very high threshold - partial match should fail
        result = matcher.find_match("J D", students, threshold=90)
        assert result is None

    def test_fuzzy_match_best_candidate(self):
        """Test fuzzy matcher selects best match when multiple candidates exist."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
            Student(StudentId("2", "jdoeson"), "John", "Doeson"),
            Student(StudentId("3", "jdoetwo"), "John", "Doetwo"),
        ]

        matcher = FuzzyStudentMatcher()
        result = matcher.find_match("John Doe", students)

        # Should match exact "John Doe"
        assert result is not None
        assert result.student_id.username == "jdoe"


class TestCompositeStudentMatcher:
    """Test the CompositeStudentMatcher implementation."""

    def test_composite_uses_first_matcher(self):
        """Test composite uses first successful matcher."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
        ]

        exact_matcher = ExactStudentMatcher()
        fuzzy_matcher = FuzzyStudentMatcher()
        composite = CompositeStudentMatcher([exact_matcher, fuzzy_matcher])

        # Exact match should be found by first matcher
        result = composite.find_match("John Doe", students)

        assert result is not None
        assert result.student_id.username == "jdoe"

    def test_composite_falls_back_to_second_matcher(self):
        """Test composite falls back when first matcher fails."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
        ]

        exact_matcher = ExactStudentMatcher()
        fuzzy_matcher = FuzzyStudentMatcher()
        composite = CompositeStudentMatcher([exact_matcher, fuzzy_matcher])

        # Typo won't match exact, but should match fuzzy
        result = composite.find_match("Jon Doe", students, threshold=70)

        assert result is not None
        assert result.student_id.username == "jdoe"

    def test_composite_returns_none_when_all_fail(self):
        """Test composite returns None when all matchers fail."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
        ]

        exact_matcher = ExactStudentMatcher()
        fuzzy_matcher = FuzzyStudentMatcher()
        composite = CompositeStudentMatcher([exact_matcher, fuzzy_matcher])

        # Very different name with high threshold
        result = composite.find_match("Robert Williams", students, threshold=90)

        assert result is None

    def test_composite_with_single_matcher(self):
        """Test composite with only one matcher."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
        ]

        exact_matcher = ExactStudentMatcher()
        composite = CompositeStudentMatcher([exact_matcher])

        result = composite.find_match("John Doe", students)

        assert result is not None
        assert result.student_id.username == "jdoe"

    def test_composite_with_no_matchers(self):
        """Test composite with empty matcher list."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
        ]

        composite = CompositeStudentMatcher([])
        result = composite.find_match("John Doe", students)

        assert result is None

    def test_composite_matcher_order_matters(self):
        """Test that matcher order affects results."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
            Student(StudentId("2", "jdoeson"), "John", "Doeson"),
        ]

        exact_matcher = ExactStudentMatcher()
        fuzzy_matcher = FuzzyStudentMatcher()

        # Exact first
        composite1 = CompositeStudentMatcher([exact_matcher, fuzzy_matcher])
        result1 = composite1.find_match("John Doe", students)

        # Fuzzy first
        composite2 = CompositeStudentMatcher([fuzzy_matcher, exact_matcher])
        result2 = composite2.find_match("John Doe", students)

        # Both should find same result for exact match
        assert result1 is not None
        assert result2 is not None
        assert result1.student_id.username == result2.student_id.username

    def test_composite_passes_threshold_to_matchers(self):
        """Test that threshold is passed to all matchers."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
        ]

        fuzzy_matcher = FuzzyStudentMatcher()
        composite = CompositeStudentMatcher([fuzzy_matcher])

        # Low threshold should allow partial match
        result = composite.find_match("J D", students, threshold=30)
        assert result is not None

        # High threshold should reject partial match
        result = composite.find_match("J D", students, threshold=90)
        assert result is None

    def test_composite_with_custom_matcher_implementation(self):
        """Test composite works with any matcher implementing the protocol."""

        class AlwaysMatchMatcher:
            """Custom matcher that always returns first candidate."""

            def find_match(self, target_name, candidates, threshold=80):
                return candidates[0] if candidates else None

        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
            Student(StudentId("2", "jsmith"), "Jane", "Smith"),
        ]

        always_match = AlwaysMatchMatcher()
        composite = CompositeStudentMatcher([always_match])

        result = composite.find_match("Anyone", students)

        assert result is not None
        assert result.student_id.username == "jdoe"


class TestStudentMatcherIntegration:
    """Integration tests for student matchers."""

    def test_real_world_scenario_exact_matches(self):
        """Test real-world scenario with exact name matches."""
        students = [
            Student(StudentId("300069634", "cwils001"), "Charlie", "Wilson"),
            Student(StudentId("300173416", "drodr002"), "Dana", "Rodriguez"),
            Student(StudentId("300234567", "ethom003"), "Emma", "Thompson"),
        ]

        matcher = FuzzyStudentMatcher()

        # Exact matches
        assert matcher.find_match("Charlie Wilson", students) is not None
        assert matcher.find_match("Dana Rodriguez", students) is not None
        assert matcher.find_match("Emma Thompson", students) is not None

    def test_real_world_scenario_accent_variations(self):
        """Test real-world scenario with accented names."""
        students = [
            Student(StudentId("1", "jmaria"), "José", "María"),
            Student(StudentId("2", "fcote"), "François", "Côté"),
            Student(StudentId("3", "muller"), "Müller", "Schmidt"),
        ]

        matcher = FuzzyStudentMatcher()

        # Without accents
        result = matcher.find_match("Jose Maria", students)
        assert result is not None
        assert result.student_id.username == "jmaria"

        result = matcher.find_match("Francois Cote", students)
        assert result is not None
        assert result.student_id.username == "fcote"

        result = matcher.find_match("Muller Schmidt", students)
        assert result is not None
        assert result.student_id.username == "muller"

    def test_real_world_scenario_with_typos(self):
        """Test handling of common submission typos."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
            Student(StudentId("2", "jsmith"), "Jane", "Smith"),
        ]

        matcher = FuzzyStudentMatcher()

        # Common typos with reasonable threshold
        result = matcher.find_match("Jhon Doe", students, threshold=75)
        assert result is not None
        assert result.student_id.username == "jdoe"

        result = matcher.find_match("Jane Smth", students, threshold=75)
        assert result is not None
        assert result.student_id.username == "jsmith"

    def test_real_world_scenario_composite_strategy(self):
        """Test real-world use of composite matcher."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
            Student(StudentId("2", "jsmith"), "Jane", "Smith"),
        ]

        # Create a strategy: exact first, then fuzzy
        exact_matcher = ExactStudentMatcher()
        fuzzy_matcher = FuzzyStudentMatcher()
        composite = CompositeStudentMatcher([exact_matcher, fuzzy_matcher])

        # Exact match uses first matcher (faster)
        result = composite.find_match("John Doe", students)
        assert result is not None
        assert result.student_id.username == "jdoe"

        # Fuzzy match falls back to second matcher
        result = composite.find_match("Jon Doe", students, threshold=70)
        assert result is not None
        assert result.student_id.username == "jdoe"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
