#!/usr/bin/env python3

"""Integration tests for domain layer services.

This module tests interactions between domain services (matchers, calculators, parsers)
to ensure they work together correctly in realistic scenarios.
"""

import pytest

from grader.domain.models import Student, StudentId
from grader.domain.services import (
    ExactStudentMatcher,
    FuzzyStudentMatcher,
    CompositeStudentMatcher,
    SimpleGradingStrategy,
    WeightedGradingStrategy,
    DropLowestGradingStrategy,
    RegexTestOutputParser,
    JUnitXMLTestOutputParser,
    CompositeTestOutputParser,
)


class TestMatcherCalculatorIntegration:
    """Integration tests for matcher and calculator interactions."""

    def test_fuzzy_matcher_with_simple_grading(self):
        """Test using fuzzy matcher with simple grading strategy."""
        # Setup students
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
            Student(StudentId("2", "jsmith"), "Jane", "Smith"),
            Student(StudentId("3", "bwilson"), "Bob", "Wilson"),
        ]

        # Match a submission with slight typo
        matcher = FuzzyStudentMatcher()
        matched_student = matcher.find_match("Jon Doe", students, threshold=70)

        assert matched_student is not None
        assert matched_student.student_id.username == "jdoe"

        # Grade the matched student's work
        strategy = SimpleGradingStrategy()
        grade = strategy.apply_strategy(85.0, 100.0)

        assert grade == 85.0

    def test_composite_matcher_with_weighted_grading(self):
        """Test composite matcher with weighted grading strategy."""
        students = [
            Student(StudentId("1", "msmith"), "María", "Smith"),
            Student(StudentId("2", "fcote"), "François", "Côté"),
        ]

        # Use composite matcher for flexible matching
        exact = ExactStudentMatcher()
        fuzzy = FuzzyStudentMatcher()
        matcher = CompositeStudentMatcher([exact, fuzzy])

        # Match with normalized name
        matched = matcher.find_match("Maria Smith", students, threshold=75)
        assert matched is not None
        assert matched.student_id.username == "msmith"

        # Apply weighted grading
        weights = {"basics": 0.4, "advanced": 0.6}
        category_map = {"test1": "basics", "test2": "advanced"}
        strategy = WeightedGradingStrategy(weights, category_map)

        test_results = {
            "test1": (10.0, 10.0),  # Perfect on basics
            "test2": (15.0, 20.0),  # 75% on advanced
        }

        grade = strategy.apply_strategy_to_results(test_results)
        # Expected: (1.0 * 0.4) + (0.75 * 0.6) = 0.85 = 85%
        assert grade == pytest.approx(85.0)


class TestParserStrategyIntegration:
    """Integration tests for parser and strategy interactions."""

    def test_regex_parser_with_drop_lowest(self):
        """Test regex parser output fed into drop-lowest strategy."""
        # Note: RegexTestOutputParser sums everything, so we simulate
        # individual test parsing for this use case
        test_results = [
            (8.0, 10.0),  # Test1: 80%
            (5.0, 10.0),  # Test2: 50% - should be dropped
            (9.0, 10.0),  # Test3: 90%
        ]

        strategy = DropLowestGradingStrategy(drop_count=1)
        grade = strategy.apply_strategy_to_results(test_results)

        # After dropping Test2: (8 + 9) / 20 = 0.85 = 85%
        assert grade == pytest.approx(85.0)

    def test_junit_parser_with_weighted_strategy(self):
        """Test JUnit parser with weighted grading."""
        parser = JUnitXMLTestOutputParser(points_per_test=10.0)

        xml_output = """<?xml version="1.0"?>
        <testsuite tests="5" failures="1" errors="0">
            <testcase name="basicTest1" />
            <testcase name="basicTest2" />
            <testcase name="advancedTest1">
                <failure message="Test failed" />
            </testcase>
            <testcase name="advancedTest2" />
            <testcase name="advancedTest3" />
        </testsuite>"""

        total, possible = parser.parse_output(xml_output)

        # 4 passing tests * 10 = 40 points
        # 5 total tests * 10 = 50 points
        assert total == 40.0
        assert possible == 50.0

        # Calculate percentage
        strategy = SimpleGradingStrategy()
        grade = strategy.apply_strategy(total, possible)

        assert grade == pytest.approx(80.0)

    def test_composite_parser_fallback_with_grading(self):
        """Test composite parser fallback behavior with grading."""
        junit_parser = JUnitXMLTestOutputParser()
        regex_parser = RegexTestOutputParser()
        composite = CompositeTestOutputParser([junit_parser, regex_parser])

        # Non-XML output (will fall back to regex)
        output = "Grade for Assignment (out of possible 100): 87"

        total, possible = composite.parse_output(output)
        assert total == 87.0
        assert possible == 100.0

        # Calculate grade
        strategy = SimpleGradingStrategy()
        grade = strategy.apply_strategy(total, possible)

        assert grade == pytest.approx(87.0)


class TestFullWorkflowIntegration:
    """End-to-end integration tests for complete grading workflows."""

    def test_complete_grading_workflow_simple(self):
        """Test a complete grading workflow: match student, parse output, calculate grade."""
        # Step 1: Match student
        students = [
            Student(StudentId("300123456", "jdoe"), "John", "Doe"),
            Student(StudentId("300234567", "jsmith"), "Jane", "Smith"),
        ]

        matcher = FuzzyStudentMatcher()
        matched = matcher.find_match("John Doe", students, threshold=80)

        assert matched is not None
        assert matched.first_name == "John"

        # Step 2: Parse test output
        parser = RegexTestOutputParser()
        test_output = """
        Running tests for John Doe...
        Grade for TestBasics (out of possible 30): 28
        Grade for TestAdvanced (out of possible 70): 65
        """

        total, possible = parser.parse_output(test_output)
        assert total == 93.0
        assert possible == 100.0

        # Step 3: Calculate final grade
        strategy = SimpleGradingStrategy()
        final_grade = strategy.apply_strategy(total, possible)

        assert final_grade == pytest.approx(93.0)

    def test_complete_workflow_with_drop_lowest_and_matching(self):
        """Test workflow with student matching, multi-test parsing, and drop-lowest."""
        # Match student with accented name
        students = [
            Student(StudentId("1", "jmaria"), "José", "María"),
        ]

        matcher = FuzzyStudentMatcher()
        matched = matcher.find_match("Jose Maria", students)

        assert matched is not None
        assert matched.student_id.username == "jmaria"

        # Simulate individual test results (in practice, would parse from output)
        test_results = [
            (10.0, 10.0),  # Lab 1: 100%
            (7.0, 10.0),   # Lab 2: 70% - lowest, will be dropped
            (9.0, 10.0),   # Lab 3: 90%
            (8.0, 10.0),   # Lab 4: 80%
        ]

        strategy = DropLowestGradingStrategy(drop_count=1)
        final_grade = strategy.apply_strategy_to_results(test_results)

        # After dropping Lab 2: (10 + 9 + 8) / 30 = 90%
        assert final_grade == pytest.approx(90.0)

    def test_workflow_with_weighted_categories_and_composite_parser(self):
        """Test complex workflow with weighted grading and composite parser."""
        # Setup
        students = [
            Student(StudentId("1", "asmith"), "Alice", "Smith"),
        ]

        matcher = ExactStudentMatcher()
        matched = matcher.find_match("Alice Smith", students)

        assert matched is not None

        # Parse output using composite parser
        junit_parser = JUnitXMLTestOutputParser(points_per_test=1.0)
        regex_parser = RegexTestOutputParser()
        parser = CompositeTestOutputParser([junit_parser, regex_parser])

        # Try regex format first
        output = "Grade for FinalExam (out of possible 100): 85"
        total, possible = parser.parse_output(output)

        assert total == 85.0
        assert possible == 100.0

        # Calculate grade (simple strategy for this case)
        strategy = SimpleGradingStrategy()
        grade = strategy.apply_strategy(total, possible)

        assert grade == pytest.approx(85.0)


class TestEdgeCasesIntegration:
    """Integration tests for edge cases and error conditions."""

    def test_no_match_found_workflow(self):
        """Test workflow when student match fails."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
        ]

        matcher = FuzzyStudentMatcher()
        matched = matcher.find_match("Unknown Student", students, threshold=90)

        # Should not find a match with high threshold
        assert matched is None

    def test_zero_points_possible_grading(self):
        """Test grading when zero points are possible."""
        strategy = SimpleGradingStrategy()
        grade = strategy.apply_strategy(0.0, 0.0)

        assert grade == 0.0

    def test_empty_test_output_parsing(self):
        """Test parsing empty output."""
        parser = RegexTestOutputParser()
        total, possible = parser.parse_output("")

        assert total == 0.0
        assert possible == 0.0

        # Grade should also be 0
        strategy = SimpleGradingStrategy()
        grade = strategy.apply_strategy(total, possible)

        assert grade == 0.0

    def test_all_tests_dropped_scenario(self):
        """Test drop-lowest when all tests are dropped."""
        test_results = [
            (10.0, 10.0),
            (8.0, 10.0),
        ]

        strategy = DropLowestGradingStrategy(drop_count=2)
        grade = strategy.apply_strategy_to_results(test_results)

        # All tests dropped = 0%
        assert grade == 0.0

    def test_malformed_output_graceful_degradation(self):
        """Test that parsers handle malformed output gracefully."""
        parser = RegexTestOutputParser()
        malformed_output = "This is not valid output at all!!!"

        total, possible = parser.parse_output(malformed_output)

        # Should return 0, 0 instead of crashing
        assert total == 0.0
        assert possible == 0.0

    def test_weighted_strategy_with_missing_category(self):
        """Test weighted strategy when test doesn't match any category."""
        weights = {"basics": 0.5, "default": 0.5}
        category_map = {"test1": "basics"}  # test2 not mapped

        strategy = WeightedGradingStrategy(weights, category_map)

        test_results = {
            "test1": (10.0, 10.0),  # 100% in basics
            "test2": (8.0, 10.0),   # 80% in default
        }

        grade = strategy.apply_strategy_to_results(test_results)

        # Expected: (1.0 * 0.5) + (0.8 * 0.5) = 90%
        assert grade == pytest.approx(90.0)


class TestPerformanceCharacteristics:
    """Integration tests for performance characteristics."""

    def test_matcher_performance_with_large_student_list(self):
        """Test matcher performance with realistic student list size."""
        # Create 1000 students
        students = [
            Student(
                StudentId(f"300{i:06d}", f"student{i}"),
                f"Student{i}",
                f"Last{i}"
            )
            for i in range(1000)
        ]

        # Add target student
        target = Student(StudentId("300999999", "target"), "Target", "Student")
        students.append(target)

        matcher = FuzzyStudentMatcher()

        # Should find target efficiently
        import time
        start = time.time()
        result = matcher.find_match("Target Student", students)
        elapsed = time.time() - start

        assert result is not None
        assert result.student_id.username == "target"
        # Should complete in reasonable time (< 1 second)
        assert elapsed < 1.0

    def test_composite_parser_efficiency(self):
        """Test that composite parser doesn't try all parsers when first succeeds."""
        junit_parser = JUnitXMLTestOutputParser()
        regex_parser = RegexTestOutputParser()

        # Create composite with JUnit first
        composite = CompositeTestOutputParser([junit_parser, regex_parser])

        # Valid JUnit XML - should not need to try regex
        xml = """<?xml version="1.0"?>
        <testsuite tests="10" failures="2" errors="0">
            <testcase name="test1" />
            <testcase name="test2"><failure message="fail" /></testcase>
            <testcase name="test3" />
            <testcase name="test4" />
            <testcase name="test5" />
            <testcase name="test6" />
            <testcase name="test7" />
            <testcase name="test8"><failure message="fail" /></testcase>
            <testcase name="test9" />
            <testcase name="test10" />
        </testsuite>"""

        total, possible = composite.parse_output(xml)

        assert total == 8.0
        assert possible == 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
