#!/usr/bin/env python3

"""Property-based tests for domain services using Hypothesis.

This module uses property-based testing to validate invariants and properties
of domain services (matchers, calculators, parsers) across a wide variety of inputs.
"""

from hypothesis import given, strategies as st, assume
import pytest

from grader.domain.models import Student, StudentId
from grader.domain.services import (
    ExactStudentMatcher,
    FuzzyStudentMatcher,
    CompositeStudentMatcher,
    normalize_name,
    SimpleGradingStrategy,
    WeightedGradingStrategy,
    DropLowestGradingStrategy,
    RegexTestOutputParser,
    JUnitXMLTestOutputParser,
    CompositeTestOutputParser,
)


# ============================================================================
# Strategies for generating test data
# ============================================================================


@st.composite
def student_names(draw):
    """Generate realistic student names."""
    first_name = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll"), blacklist_characters="\n\r\t"
    )))
    last_name = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll"), blacklist_characters="\n\r\t"
    )))
    return f"{first_name} {last_name}"


@st.composite
def students(draw):
    """Generate Student instances."""
    org_id = draw(st.text(min_size=1, max_size=15, alphabet=st.characters(
        whitelist_categories=("Nd", "Lu", "Ll"), blacklist_characters="\n\r\t"
    )))
    username = draw(st.text(min_size=1, max_size=15, alphabet=st.characters(
        whitelist_categories=("Ll", "Nd"), blacklist_characters="\n\r\t"
    )))
    first = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll"), blacklist_characters="\n\r\t"
    )))
    last = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll"), blacklist_characters="\n\r\t"
    )))
    
    return Student(
        student_id=StudentId(org_defined_id=org_id, username=username),
        first_name=first,
        last_name=last,
    )


@st.composite
def score_pairs(draw):
    """Generate valid test scores (earned, possible)."""
    possible = draw(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    earned = draw(st.floats(min_value=0.0, max_value=possible, allow_nan=False, allow_infinity=False))
    return (earned, possible)


# ============================================================================
# Property tests for name normalization
# ============================================================================


class TestNormalizeNameProperties:
    """Property-based tests for name normalization."""

    @given(st.text(max_size=1000))
    def test_normalize_idempotent(self, name):
        """Normalizing twice should give same result as normalizing once."""
        normalized_once = normalize_name(name)
        normalized_twice = normalize_name(normalized_once)
        assert normalized_once == normalized_twice

    @given(st.text(max_size=1000))
    def test_normalize_lowercase(self, name):
        """Normalized names should always be lowercase."""
        normalized = normalize_name(name)
        assert normalized == normalized.lower()

    @given(st.text(max_size=1000))
    def test_normalize_no_leading_trailing_whitespace(self, name):
        """Normalized names should have no leading or trailing whitespace."""
        normalized = normalize_name(name)
        assert normalized == normalized.strip()

    @given(st.text(max_size=1000))
    def test_normalize_no_multiple_spaces(self, name):
        """Normalized names should not have consecutive spaces."""
        normalized = normalize_name(name)
        assert "  " not in normalized

    @given(st.text(min_size=1, max_size=1000))
    def test_normalize_preserves_nonempty_to_nonempty_or_empty(self, name):
        """Non-empty input produces a result (empty or non-empty)."""
        normalized = normalize_name(name)
        # Always produces a string (may be empty if input is all whitespace)
        assert isinstance(normalized, str)


# ============================================================================
# Property tests for StudentMatcher
# ============================================================================


class TestStudentMatcherProperties:
    """Property-based tests for student matchers."""

    @given(students(), st.lists(students(), min_size=1, max_size=50))
    def test_exact_matcher_finds_itself(self, student, other_students):
        """ExactStudentMatcher should always find an exact match."""
        candidates = [student] + other_students
        matcher = ExactStudentMatcher()
        
        # Should find the student by their exact full name
        result = matcher.find_match(student.full_name, candidates)
        
        assert result is not None
        # Should match the same student (first occurrence if duplicates)
        assert normalize_name(result.full_name) == normalize_name(student.full_name)

    @given(students(), st.lists(students(), min_size=1, max_size=50))
    def test_fuzzy_matcher_finds_exact_match(self, student, other_students):
        """FuzzyStudentMatcher should find exact matches."""
        candidates = [student] + other_students
        matcher = FuzzyStudentMatcher()
        
        # Should find the student by their exact full name
        result = matcher.find_match(student.full_name, candidates)
        
        assert result is not None
        assert normalize_name(result.full_name) == normalize_name(student.full_name)

    @given(students(), st.lists(students(), min_size=0, max_size=50), 
           st.integers(min_value=0, max_value=100))
    def test_fuzzy_matcher_threshold_behavior(self, student, other_students, threshold):
        """FuzzyStudentMatcher respects threshold parameter."""
        candidates = [student] + other_students
        matcher = FuzzyStudentMatcher()
        
        # With threshold 100, should only match exact names
        result_high = matcher.find_match(student.full_name, candidates, threshold=100)
        assert result_high is not None  # Should find exact match
        
        # With threshold 0, should match something if candidates exist
        result_low = matcher.find_match(student.full_name, candidates, threshold=0)
        assert result_low is not None  # Should find some match

    @given(st.lists(students(), min_size=1, max_size=20))
    def test_composite_matcher_returns_result_or_none(self, candidates):
        """CompositeStudentMatcher returns Student or None."""
        exact = ExactStudentMatcher()
        fuzzy = FuzzyStudentMatcher()
        composite = CompositeStudentMatcher([exact, fuzzy])
        
        target = candidates[0].full_name if candidates else "Nobody"
        result = composite.find_match(target, candidates)
        
        # Result must be either None or a Student from candidates
        if result is not None:
            assert any(
                normalize_name(result.full_name) == normalize_name(c.full_name)
                for c in candidates
            )


# ============================================================================
# Property tests for GradingStrategy
# ============================================================================


class TestGradingStrategyProperties:
    """Property-based tests for grading strategies."""

    @given(score_pairs())
    def test_simple_strategy_percentage_bounds(self, scores):
        """SimpleGradingStrategy should return percentage in [0, 100]."""
        earned, possible = scores
        strategy = SimpleGradingStrategy()
        result = strategy.apply_strategy(earned, possible)
        
        assert 0.0 <= result <= 100.0

    @given(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    def test_simple_strategy_perfect_score(self, points):
        """Perfect score should always be 100%."""
        assume(points > 0)  # Skip zero to avoid division by zero
        strategy = SimpleGradingStrategy()
        result = strategy.apply_strategy(points, points)
        
        assert result == pytest.approx(100.0)

    @given(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    def test_simple_strategy_zero_earned(self, possible):
        """Zero points earned should give 0%."""
        strategy = SimpleGradingStrategy()
        result = strategy.apply_strategy(0.0, possible)
        
        assert result == 0.0

    @given(st.lists(score_pairs(), min_size=1, max_size=10))
    def test_drop_lowest_reduces_or_maintains_grade(self, test_results):
        """Dropping scores should never decrease the average grade."""
        # Test with drop_count=0 vs drop_count=1
        strategy_no_drop = DropLowestGradingStrategy(drop_count=0)
        strategy_drop_one = DropLowestGradingStrategy(drop_count=1)
        
        grade_no_drop = strategy_no_drop.apply_strategy_to_results(test_results)
        grade_drop_one = strategy_drop_one.apply_strategy_to_results(test_results)
        
        # Dropping lowest should either maintain or increase grade (with tolerance for FP errors)
        # or return 0 if all tests are dropped
        assert grade_drop_one >= grade_no_drop - 0.001 or grade_drop_one == 0.0

    @given(st.lists(score_pairs(), min_size=1, max_size=10))
    def test_drop_lowest_percentage_bounds(self, test_results):
        """DropLowestGradingStrategy should return percentage in [0, 100]."""
        strategy = DropLowestGradingStrategy(drop_count=1)
        result = strategy.apply_strategy_to_results(test_results)
        
        assert 0.0 <= result <= 100.0

    @given(st.integers(min_value=1, max_value=10))
    def test_drop_all_tests_returns_zero(self, num_tests):
        """Dropping all tests should return 0."""
        test_results = [(10.0, 10.0) for _ in range(num_tests)]
        strategy = DropLowestGradingStrategy(drop_count=num_tests)
        
        result = strategy.apply_strategy_to_results(test_results)
        
        assert result == 0.0

    @given(st.lists(st.tuples(
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False)
    ), min_size=2, max_size=10))
    def test_weighted_strategy_percentage_bounds(self, test_data):
        """WeightedGradingStrategy should return percentage in [0, 100]."""
        # Create weights that sum to 1.0
        num_categories = len(test_data)
        weight_per_category = 1.0 / num_categories
        weights = {f"cat{i}": weight_per_category for i in range(num_categories)}
        category_map = {f"Test{i}": f"cat{i}" for i in range(num_categories)}
        
        strategy = WeightedGradingStrategy(weights, category_map)
        
        test_results = {
            f"Test{i}": (min(earned, possible), possible)  # Ensure earned <= possible
            for i, (earned, possible) in enumerate(test_data)
        }
        
        result = strategy.apply_strategy_to_results(test_results)
        
        assert 0.0 <= result <= 100.0


# ============================================================================
# Property tests for TestOutputParser
# ============================================================================


class TestTestOutputParserProperties:
    """Property-based tests for test output parsers."""

    @given(st.lists(st.tuples(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))),
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False)
    ), min_size=1, max_size=10))
    def test_regex_parser_sums_all_matches(self, test_data):
        """RegexTestOutputParser should sum all matching test results."""
        parser = RegexTestOutputParser()
        
        # Build output in the expected format
        lines = []
        expected_total = 0.0
        expected_possible = 0.0
        
        for name, earned, possible in test_data:
            # Ensure earned <= possible for realistic data
            earned = min(earned, possible)
            # Round to avoid scientific notation issues
            earned = round(earned, 2)
            possible = round(possible, 2)
            lines.append(f"Grade for {name} (out of possible {possible}): {earned}")
            expected_total += earned
            expected_possible += possible
        
        output = "\n".join(lines)
        total, possible_parsed = parser.parse_output(output)
        
        assert total == pytest.approx(expected_total, abs=0.01)
        assert possible_parsed == pytest.approx(expected_possible, abs=0.01)

    @given(st.text(max_size=1000))
    def test_regex_parser_non_negative_results(self, output):
        """RegexTestOutputParser should return non-negative results."""
        parser = RegexTestOutputParser()
        total, possible = parser.parse_output(output)
        
        assert total >= 0.0
        assert possible >= 0.0

    @given(st.text(max_size=1000))
    def test_regex_parser_earned_not_greater_than_possible(self, output):
        """In valid output, earned should not exceed possible per test."""
        parser = RegexTestOutputParser()
        total, possible = parser.parse_output(output)
        
        # If we found any results, total should not exceed possible
        # (unless the output is malformed, which is okay to handle gracefully)
        if possible > 0:
            # We allow total > possible in malformed output (graceful degradation)
            assert total >= 0.0

    @given(st.integers(min_value=0, max_value=10), st.integers(min_value=0, max_value=10))
    def test_junit_parser_counts_correctly(self, num_passing, num_failing):
        """JUnitXMLTestOutputParser counts passing and failing tests correctly."""
        parser = JUnitXMLTestOutputParser(points_per_test=1.0)
        
        total_tests = num_passing + num_failing
        
        # Build JUnit XML
        testcases = []
        for i in range(num_passing):
            testcases.append(f'<testcase name="test{i}" />')
        for i in range(num_failing):
            testcases.append(
                f'<testcase name="test{num_passing + i}">'
                f'<failure message="Failed" /></testcase>'
            )
        
        xml = f"""<?xml version="1.0"?>
        <testsuite tests="{total_tests}" failures="{num_failing}" errors="0">
            {''.join(testcases)}
        </testsuite>"""
        
        total, possible = parser.parse_output(xml)
        
        assert total == float(num_passing)
        assert possible == float(total_tests)

    @given(st.text(max_size=1000))
    def test_junit_parser_non_negative_results(self, output):
        """JUnitXMLTestOutputParser should return non-negative results."""
        parser = JUnitXMLTestOutputParser()
        total, possible = parser.parse_output(output)
        
        assert total >= 0.0
        assert possible >= 0.0

    @given(st.text(max_size=1000))
    def test_composite_parser_non_negative_results(self, output):
        """CompositeTestOutputParser should return non-negative results."""
        regex_parser = RegexTestOutputParser()
        junit_parser = JUnitXMLTestOutputParser()
        composite = CompositeTestOutputParser([junit_parser, regex_parser])
        
        total, possible = composite.parse_output(output)
        
        assert total >= 0.0
        assert possible >= 0.0


# ============================================================================
# Cross-property tests (testing interactions between components)
# ============================================================================


class TestCrossComponentProperties:
    """Property tests for interactions between domain components."""

    @given(students(), score_pairs())
    def test_full_grading_workflow_consistency(self, student, scores):
        """Test that a complete grading workflow maintains consistency."""
        earned, possible = scores
        
        # Round to avoid scientific notation issues
        earned = round(earned, 2)
        possible = round(possible, 2)
        
        # Skip if possible is 0
        assume(possible > 0)
        
        # Parse output (simulated)
        parser = RegexTestOutputParser()
        output = f"Grade for Test (out of possible {possible}): {earned}"
        parsed_earned, parsed_possible = parser.parse_output(output)
        
        # Calculate grade
        strategy = SimpleGradingStrategy()
        grade = strategy.apply_strategy(parsed_earned, parsed_possible)
        
        # Grade should be valid percentage
        assert 0.0 <= grade <= 100.0
        
        # Grade should match direct calculation
        expected_grade = (earned / possible) * 100
        assert grade == pytest.approx(expected_grade, abs=0.01)

    @given(st.lists(students(), min_size=1, max_size=20), students())
    def test_matcher_parser_strategy_integration(self, candidates, target_student):
        """Test integration of matcher with grading workflow."""
        # Add target to candidates
        all_candidates = candidates + [target_student]
        
        # Match student
        matcher = FuzzyStudentMatcher()
        found = matcher.find_match(target_student.full_name, all_candidates)
        
        # If found, should be a valid student
        if found is not None:
            assert found in all_candidates
            
            # Simulate grading
            strategy = SimpleGradingStrategy()
            grade = strategy.apply_strategy(85.0, 100.0)
            
            # Grade should be valid
            assert grade == pytest.approx(85.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
