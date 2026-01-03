#!/usr/bin/env python3

"""Unit tests for test output parsers."""

from grader.domain import (
    CompositeTestOutputParser,
    CustomPatternTestOutputParser,
    JUnitXMLTestOutputParser,
    RegexTestOutputParser,
)


class TestRegexTestOutputParser:
    """Test the RegexTestOutputParser implementation."""

    def test_default_pattern_single_test(self):
        """Test parsing output with default pattern for a single test."""
        parser = RegexTestOutputParser()
        output = "Grade for Test1 (out of possible 10): 8\n"

        total, possible = parser.parse_output(output)

        assert total == 8.0
        assert possible == 10.0

    def test_default_pattern_multiple_tests(self):
        """Test parsing output with multiple test results."""
        parser = RegexTestOutputParser()
        output = """
        Grade for Test1 (out of possible 10): 8
        Grade for Test2 (out of possible 20): 15
        Grade for Test3 (out of possible 5): 5
        """

        total, possible = parser.parse_output(output)

        assert total == 28.0  # 8 + 15 + 5
        assert possible == 35.0  # 10 + 20 + 5

    def test_default_pattern_with_a_possible(self):
        """Test parsing output with 'a possible' in the text."""
        parser = RegexTestOutputParser()
        output = "Grade for Test1 (out of a possible 100): 85.5\n"

        total, possible = parser.parse_output(output)

        assert total == 85.5
        assert possible == 100.0

    def test_default_pattern_decimal_points(self):
        """Test parsing output with decimal points."""
        parser = RegexTestOutputParser()
        output = "Grade for Test1 (out of possible 10.5): 8.75\n"

        total, possible = parser.parse_output(output)

        assert total == 8.75
        assert possible == 10.5

    def test_default_pattern_no_matches(self):
        """Test parsing output with no matching patterns."""
        parser = RegexTestOutputParser()
        output = "This is random output with no grades\n"

        total, possible = parser.parse_output(output)

        assert total == 0.0
        assert possible == 0.0

    def test_default_pattern_empty_output(self):
        """Test parsing empty output."""
        parser = RegexTestOutputParser()
        output = ""

        total, possible = parser.parse_output(output)

        assert total == 0.0
        assert possible == 0.0

    def test_custom_pattern_simple(self):
        """Test parser with custom pattern."""
        # Pattern for format like "Test: 42/50"
        pattern = r"Test: (?P<total>\d+)/(?P<max>\d+)"
        parser = RegexTestOutputParser(pattern)
        output = "Test: 42/50\n"

        total, possible = parser.parse_output(output)

        assert total == 42.0
        assert possible == 50.0

    def test_custom_pattern_multiple_matches(self):
        """Test custom pattern with multiple matches."""
        pattern = r"Score: (?P<total>\d+(\.\d+)?)/(?P<max>\d+(\.\d+)?)"
        parser = RegexTestOutputParser(pattern)
        output = """
        Score: 10.5/15.0
        Score: 8.0/10.0
        """

        total, possible = parser.parse_output(output)

        assert total == 18.5
        assert possible == 25.0

    def test_custom_pattern_with_flags(self):
        """Test custom pattern with regex flags."""
        import re

        pattern = r"SCORE: (?P<total>\d+)/(?P<max>\d+)"
        parser = RegexTestOutputParser(pattern, flags=re.IGNORECASE)
        output = "score: 10/20\n"  # lowercase should match with IGNORECASE

        total, possible = parser.parse_output(output)

        assert total == 10.0
        assert possible == 20.0

    def test_malformed_pattern_groups(self):
        """Test parser gracefully handles missing named groups."""
        pattern = r"Test: (\d+)/(\d+)"  # Missing named groups
        parser = RegexTestOutputParser(pattern)
        output = "Test: 42/50\n"

        total, possible = parser.parse_output(output)

        # Should return 0,0 when named groups are missing (catches IndexError/KeyError)
        assert total == 0.0
        assert possible == 0.0


class TestJUnitXMLTestOutputParser:
    """Test the JUnitXMLTestOutputParser implementation."""

    def test_simple_testsuite_all_pass(self):
        """Test parsing JUnit XML with all tests passing."""
        parser = JUnitXMLTestOutputParser()
        xml = """<?xml version="1.0"?>
        <testsuite tests="3" failures="0" errors="0">
            <testcase name="test1" />
            <testcase name="test2" />
            <testcase name="test3" />
        </testsuite>"""

        total, possible = parser.parse_output(xml)

        assert total == 3.0
        assert possible == 3.0

    def test_simple_testsuite_with_failures(self):
        """Test parsing JUnit XML with some failures."""
        parser = JUnitXMLTestOutputParser()
        xml = """<?xml version="1.0"?>
        <testsuite tests="3" failures="1" errors="0">
            <testcase name="test1" />
            <testcase name="test2">
                <failure message="Expected 5 but got 3" />
            </testcase>
            <testcase name="test3" />
        </testsuite>"""

        total, possible = parser.parse_output(xml)

        assert total == 2.0  # 2 passing tests
        assert possible == 3.0

    def test_simple_testsuite_with_errors(self):
        """Test parsing JUnit XML with errors."""
        parser = JUnitXMLTestOutputParser()
        xml = """<?xml version="1.0"?>
        <testsuite tests="3" failures="0" errors="1">
            <testcase name="test1" />
            <testcase name="test2">
                <error message="NullPointerException" />
            </testcase>
            <testcase name="test3" />
        </testsuite>"""

        total, possible = parser.parse_output(xml)

        assert total == 2.0  # 2 passing tests
        assert possible == 3.0

    def test_testsuites_wrapper(self):
        """Test parsing JUnit XML with testsuites wrapper."""
        parser = JUnitXMLTestOutputParser()
        xml = """<?xml version="1.0"?>
        <testsuites>
            <testsuite tests="2" failures="0" errors="0">
                <testcase name="test1" />
                <testcase name="test2" />
            </testsuite>
            <testsuite tests="2" failures="1" errors="0">
                <testcase name="test3" />
                <testcase name="test4">
                    <failure message="Test failed" />
                </testcase>
            </testsuite>
        </testsuites>"""

        total, possible = parser.parse_output(xml)

        assert total == 3.0  # 3 passing tests total
        assert possible == 4.0

    def test_custom_points_per_test(self):
        """Test parser with custom points per test."""
        parser = JUnitXMLTestOutputParser(points_per_test=5.0)
        xml = """<?xml version="1.0"?>
        <testsuite tests="3" failures="1" errors="0">
            <testcase name="test1" />
            <testcase name="test2">
                <failure message="Failed" />
            </testcase>
            <testcase name="test3" />
        </testsuite>"""

        total, possible = parser.parse_output(xml)

        assert total == 10.0  # 2 passing * 5 points each
        assert possible == 15.0  # 3 tests * 5 points each

    def test_invalid_xml(self):
        """Test parser handles invalid XML gracefully."""
        parser = JUnitXMLTestOutputParser()
        xml = "This is not XML at all"

        total, possible = parser.parse_output(xml)

        assert total == 0.0
        assert possible == 0.0

    def test_malformed_xml(self):
        """Test parser handles malformed XML gracefully."""
        parser = JUnitXMLTestOutputParser()
        xml = "<?xml version='1.0'?><testsuite><testcase>"  # Unclosed tags

        total, possible = parser.parse_output(xml)

        assert total == 0.0
        assert possible == 0.0

    def test_empty_testsuite(self):
        """Test parser handles empty test suite."""
        parser = JUnitXMLTestOutputParser()
        xml = """<?xml version="1.0"?>
        <testsuite tests="0" failures="0" errors="0">
        </testsuite>"""

        total, possible = parser.parse_output(xml)

        assert total == 0.0
        assert possible == 0.0

    def test_wrong_root_element(self):
        """Test parser handles XML with wrong root element."""
        parser = JUnitXMLTestOutputParser()
        xml = """<?xml version="1.0"?>
        <wrongelement>
            <testcase name="test1" />
        </wrongelement>"""

        total, possible = parser.parse_output(xml)

        assert total == 0.0
        assert possible == 0.0


class TestCustomPatternTestOutputParser:
    """Test the CustomPatternTestOutputParser implementation."""

    def test_function_based_parser(self):
        """Test parser with custom function."""

        def parse_scores(output):
            # Parse format like "PASSED: 8/10"
            if "PASSED:" in output:
                parts = output.split("PASSED:")[1].strip().split("/")
                return float(parts[0]), float(parts[1])
            return 0.0, 0.0

        parser = CustomPatternTestOutputParser(parse_scores)
        output = "PASSED: 8/10"

        total, possible = parser.parse_output(output)

        assert total == 8.0
        assert possible == 10.0

    def test_function_based_parser_no_match(self):
        """Test function-based parser with no match."""

        def parse_scores(output):
            if "PASSED:" in output:
                parts = output.split("PASSED:")[1].strip().split("/")
                return float(parts[0]), float(parts[1])
            return 0.0, 0.0

        parser = CustomPatternTestOutputParser(parse_scores)
        output = "FAILED: test failed"

        total, possible = parser.parse_output(output)

        assert total == 0.0
        assert possible == 0.0

    def test_function_based_parser_exception_handling(self):
        """Test function-based parser handles exceptions."""

        def parse_scores(output):
            raise ValueError("Intentional error")

        parser = CustomPatternTestOutputParser(parse_scores)
        output = "Some output"

        total, possible = parser.parse_output(output)

        assert total == 0.0
        assert possible == 0.0

    def test_pattern_list_single_pattern(self):
        """Test parser with pattern list."""
        patterns = [
            (r"Passed: (\d+)", lambda m: (float(m.group(1)), float(m.group(1)))),
        ]
        parser = CustomPatternTestOutputParser(patterns)
        output = "Passed: 8\n"

        total, possible = parser.parse_output(output)

        assert total == 8.0
        assert possible == 8.0

    def test_pattern_list_multiple_patterns(self):
        """Test parser with multiple patterns."""
        patterns = [
            (r"Passed: (\d+)", lambda m: (float(m.group(1)), 10.0)),
            (r"Failed: (\d+)", lambda m: (0.0, float(m.group(1)))),
        ]
        parser = CustomPatternTestOutputParser(patterns)
        output = """
        Passed: 8
        Failed: 2
        """

        total, possible = parser.parse_output(output)

        assert total == 8.0  # Only from Passed
        assert possible == 12.0  # 10 from Passed + 2 from Failed

    def test_pattern_list_with_exception_handling(self):
        """Test pattern list handles exceptions in handlers."""

        def bad_handler(m):
            raise ValueError("Intentional error")

        patterns = [
            (r"Test: (\d+)", bad_handler),
            (r"Score: (\d+)/(\d+)", lambda m: (float(m.group(1)), float(m.group(2)))),
        ]
        parser = CustomPatternTestOutputParser(patterns)
        output = """
        Test: 5
        Score: 8/10
        """

        total, possible = parser.parse_output(output)

        # Should skip the bad handler and use the second pattern
        assert total == 8.0
        assert possible == 10.0

    def test_none_parse_func(self):
        """Test parser with None parse function."""
        parser = CustomPatternTestOutputParser(None)
        output = "Some output"

        total, possible = parser.parse_output(output)

        assert total == 0.0
        assert possible == 0.0


class TestCompositeTestOutputParser:
    """Test the CompositeTestOutputParser implementation."""

    def test_first_parser_succeeds(self):
        """Test composite uses first successful parser."""
        regex_parser = RegexTestOutputParser()
        junit_parser = JUnitXMLTestOutputParser()

        composite = CompositeTestOutputParser([regex_parser, junit_parser])
        output = "Grade for Test1 (out of possible 10): 8\n"

        total, possible = composite.parse_output(output)

        assert total == 8.0
        assert possible == 10.0

    def test_fallback_to_second_parser(self):
        """Test composite falls back to second parser."""
        junit_parser = JUnitXMLTestOutputParser()
        regex_parser = RegexTestOutputParser()

        composite = CompositeTestOutputParser([junit_parser, regex_parser])
        # This is regex format, not JUnit XML
        output = "Grade for Test1 (out of possible 10): 8\n"

        total, possible = composite.parse_output(output)

        assert total == 8.0
        assert possible == 10.0

    def test_multiple_parsers_in_chain(self):
        """Test composite with multiple parsers."""
        junit_parser = JUnitXMLTestOutputParser()
        regex_parser = RegexTestOutputParser()
        custom_parser = CustomPatternTestOutputParser(
            lambda output: (5.0, 10.0) if "CUSTOM" in output else (0.0, 0.0)
        )

        composite = CompositeTestOutputParser(
            [junit_parser, regex_parser, custom_parser]
        )
        output = "CUSTOM format"

        total, possible = composite.parse_output(output)

        assert total == 5.0
        assert possible == 10.0

    def test_all_parsers_fail(self):
        """Test composite when all parsers fail."""
        junit_parser = JUnitXMLTestOutputParser()
        regex_parser = RegexTestOutputParser()

        composite = CompositeTestOutputParser([junit_parser, regex_parser])
        output = "Random output with no parseable data"

        total, possible = composite.parse_output(output)

        assert total == 0.0
        assert possible == 0.0

    def test_parser_exception_handling(self):
        """Test composite handles parser exceptions."""

        class FailingParser:
            def parse_output(self, output):
                raise ValueError("Intentional error")

        failing_parser = FailingParser()
        regex_parser = RegexTestOutputParser()

        composite = CompositeTestOutputParser([failing_parser, regex_parser])
        output = "Grade for Test1 (out of possible 10): 8\n"

        total, possible = composite.parse_output(output)

        # Should skip failing parser and use regex parser
        assert total == 8.0
        assert possible == 10.0

    def test_empty_parser_list(self):
        """Test composite with empty parser list."""
        composite = CompositeTestOutputParser([])
        output = "Some output"

        total, possible = composite.parse_output(output)

        assert total == 0.0
        assert possible == 0.0

    def test_single_parser(self):
        """Test composite with single parser."""
        regex_parser = RegexTestOutputParser()
        composite = CompositeTestOutputParser([regex_parser])
        output = "Grade for Test1 (out of possible 10): 8\n"

        total, possible = composite.parse_output(output)

        assert total == 8.0
        assert possible == 10.0


class TestOutputParserIntegration:
    """Integration tests for output parsers."""

    def test_regex_parser_backward_compatibility(self):
        """Test that RegexTestOutputParser matches legacy behavior."""
        from grader._grader import calculate_grade_from_output

        output = """
        Grade for Test1 (out of possible 10): 8
        Grade for Test2 (out of possible 20): 15
        """

        # Legacy function
        legacy_total, legacy_possible = calculate_grade_from_output(output)

        # New parser
        parser = RegexTestOutputParser()
        new_total, new_possible = parser.parse_output(output)

        assert legacy_total == new_total
        assert legacy_possible == new_possible

    def test_real_world_mixed_output(self):
        """Test parsers with realistic mixed output."""
        output = """
        Running tests...
        Test Suite: BasicTests
        Grade for testAddition (out of possible 5): 5
        Grade for testSubtraction (out of possible 5): 4
        Test Suite: AdvancedTests
        Grade for testMultiplication (out of possible 10): 8
        Grade for testDivision (out of possible 10): 0
        
        Total tests run: 4
        """

        parser = RegexTestOutputParser()
        total, possible = parser.parse_output(output)

        assert total == 17.0  # 5 + 4 + 8 + 0
        assert possible == 30.0  # 5 + 5 + 10 + 10

    def test_composite_with_fallback_strategy(self):
        """Test realistic composite parser with fallback."""
        # Try JUnit first (for automated tests), then regex (for custom tests)
        junit_parser = JUnitXMLTestOutputParser(points_per_test=10.0)
        regex_parser = RegexTestOutputParser()

        composite = CompositeTestOutputParser([junit_parser, regex_parser])

        # Test with regex format
        regex_output = "Grade for Test1 (out of possible 100): 85\n"
        total, possible = composite.parse_output(regex_output)
        assert total == 85.0
        assert possible == 100.0

        # Test with JUnit XML format
        junit_output = """<?xml version="1.0"?>
        <testsuite tests="3" failures="1" errors="0">
            <testcase name="test1" />
            <testcase name="test2">
                <failure message="Failed" />
            </testcase>
            <testcase name="test3" />
        </testsuite>"""
        total, possible = composite.parse_output(junit_output)
        assert total == 20.0  # 2 passing * 10 points
        assert possible == 30.0  # 3 tests * 10 points
