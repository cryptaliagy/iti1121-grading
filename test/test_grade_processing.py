"""Test cases for grade processing utilities."""

from unittest.mock import Mock

from grader.test_runner import JavaTestRunner
from grader.writer import Writer


class TestCalculateGradeFromOutput:
    """Test cases for calculate_grade_from_output function."""

    def test_calculate_grade_single_test(self):
        """Test calculating grade from single test output."""
        runner = JavaTestRunner(writer=Mock(spec=Writer))
        output = """
        Starting test suite...
        Grade for test1 (out of possible 10): 8.5
        Test completed.
        """

        total_points, possible_points = runner._calculate_grade_from_output(output)

        assert total_points == 8.5
        assert possible_points == 10.0

    def test_calculate_grade_multiple_tests(self):
        """Test calculating grade from multiple test outputs."""
        runner = JavaTestRunner(writer=Mock(spec=Writer))
        output = """
        Starting test suite...
        Grade for test1 (out of possible 10): 8.5
        Grade for test2 (out of possible 5): 4.0
        Grade for test3 (out of possible 15): 12.5
        Test completed.
        """

        total_points, possible_points = runner._calculate_grade_from_output(output)

        assert total_points == 25.0  # 8.5 + 4.0 + 12.5
        assert possible_points == 30.0  # 10 + 5 + 15

    def test_calculate_grade_with_a_prefix(self):
        """Test calculating grade with 'a possible' prefix."""
        runner = JavaTestRunner(writer=Mock(spec=Writer))
        output = """
        Starting test suite...
        Grade for test1 (out of a possible 10): 8.5
        Grade for test2 (out of a possible 5): 4.0
        Test completed.
        """

        total_points, possible_points = runner._calculate_grade_from_output(output)

        assert total_points == 12.5  # 8.5 + 4.0
        assert possible_points == 15.0  # 10 + 5

    def test_calculate_grade_decimal_values(self):
        """Test calculating grade with decimal values."""
        runner = JavaTestRunner(writer=Mock(spec=Writer))
        output = """
        Starting test suite...
        Grade for test1 (out of possible 10.5): 8.25
        Grade for test2 (out of possible 5.5): 4.75
        Test completed.
        """

        total_points, possible_points = runner._calculate_grade_from_output(output)

        assert total_points == 13.0  # 8.25 + 4.75
        assert possible_points == 16.0  # 10.5 + 5.5

    def test_calculate_grade_zero_points(self):
        """Test calculating grade with zero points."""
        runner = JavaTestRunner(writer=Mock(spec=Writer))
        output = """
        Starting test suite...
        Grade for test1 (out of possible 10): 0
        Grade for test2 (out of possible 5): 0
        Test completed.
        """

        total_points, possible_points = runner._calculate_grade_from_output(output)

        assert total_points == 0.0
        assert possible_points == 15.0

    def test_calculate_grade_perfect_score(self):
        """Test calculating grade with perfect score."""
        runner = JavaTestRunner(writer=Mock(spec=Writer))
        output = """
        Starting test suite...
        Grade for test1 (out of possible 10): 10
        Grade for test2 (out of possible 5): 5
        Test completed.
        """

        total_points, possible_points = runner._calculate_grade_from_output(output)

        assert total_points == 15.0
        assert possible_points == 15.0

    def test_calculate_grade_no_matches(self):
        """Test calculating grade with no matching grade lines."""
        runner = JavaTestRunner(writer=Mock(spec=Writer))
        output = """
        Starting test suite...
        Some test output without grades...
        Test completed.
        """

        total_points, possible_points = runner._calculate_grade_from_output(output)

        assert total_points == 0.0
        assert possible_points == 0.0

    def test_calculate_grade_empty_output(self):
        """Test calculating grade with empty output."""
        runner = JavaTestRunner(writer=Mock(spec=Writer))
        output = ""

        total_points, possible_points = runner._calculate_grade_from_output(output)

        assert total_points == 0.0
        assert possible_points == 0.0

    def test_calculate_grade_complex_test_names(self):
        """Test calculating grade with complex test names."""
        runner = JavaTestRunner(writer=Mock(spec=Writer))
        output = """
        Starting test suite...
        Grade for testComplexMethod123 (out of possible 10): 8.5
        Grade for test_with_underscores (out of possible 5): 4.0
        Grade for testCamelCase (out of possible 15): 12.5
        Test completed.
        """

        total_points, possible_points = runner._calculate_grade_from_output(output)

        assert total_points == 25.0
        assert possible_points == 30.0

    def test_calculate_grade_multiline_output(self):
        """Test calculating grade with multiline complex output."""
        runner = JavaTestRunner(writer=Mock(spec=Writer))
        output = """Starting test suite...
Running test1...
This is some detailed output
from the test execution
Grade for test1 (out of possible 10): 8.5

Running test2...
More detailed output here
Grade for test2 (out of possible 5): 4.0

Test completed successfully."""

        total_points, possible_points = runner._calculate_grade_from_output(output)

        assert total_points == 12.5
        assert possible_points == 15.0

    def test_calculate_grade_malformed_lines(self):
        """Test calculating grade with some malformed lines."""
        runner = JavaTestRunner(writer=Mock(spec=Writer))
        output = """
        Starting test suite...
        Grade for test1 (out of possible 10): 8.5
        Grade for test2 (out of possible): 4.0  // Missing value
        Grade for test3 (out of possible 5): missing_number
        Grade for test4 (out of possible 7): 5.5
        Test completed.
        """

        total_points, possible_points = runner._calculate_grade_from_output(output)

        # Should only pick up test1 and test4
        assert total_points == 14.0  # 8.5 + 5.5
        assert possible_points == 17.0  # 10 + 7

    def test_calculate_grade_integer_values(self):
        """Test calculating grade with integer values."""
        runner = JavaTestRunner(writer=Mock(spec=Writer))
        output = """
        Starting test suite...
        Grade for test1 (out of possible 10): 8
        Grade for test2 (out of possible 5): 4
        Test completed.
        """

        total_points, possible_points = runner._calculate_grade_from_output(output)

        assert total_points == 12.0
        assert possible_points == 15.0


class TestDisplayGradeSummary:
    """Test cases for display_grade_summary function."""

    def test_display_grade_summary_normal_case(self):
        """Test displaying grade summary with normal values."""
        mock_writer = Mock(spec=Writer)
        runner = JavaTestRunner(writer=mock_writer)

        runner._display_grade_summary(8.5, 10.0)

        # Check that always_echo was called multiple times
        assert mock_writer.always_echo.call_count >= 4

        # Check that the calls include the expected information
        calls = [call[0][0] for call in mock_writer.always_echo.call_args_list]
        summary_text = " ".join(calls)

        assert "Final Grade Summary" in summary_text
        assert "8.5" in summary_text
        assert "10.0" in summary_text
        assert "85.0%" in summary_text

    def test_display_grade_summary_zero_possible_points(self):
        """Test displaying grade summary with zero possible points."""
        mock_writer = Mock(spec=Writer)
        runner = JavaTestRunner(writer=mock_writer)

        runner._display_grade_summary(0.0, 0.0)

        # Should not display anything when possible_points is 0
        mock_writer.always_echo.assert_not_called()

    def test_display_grade_summary_perfect_score(self):
        """Test displaying grade summary with perfect score."""
        mock_writer = Mock(spec=Writer)
        runner = JavaTestRunner(writer=mock_writer)

        runner._display_grade_summary(10.0, 10.0)

        # Check that always_echo was called
        assert mock_writer.always_echo.call_count >= 4

        # Check that 100% is displayed
        calls = [call[0][0] for call in mock_writer.always_echo.call_args_list]
        summary_text = " ".join(calls)
        assert "100.0%" in summary_text

    def test_display_grade_summary_zero_score(self):
        """Test displaying grade summary with zero score."""
        mock_writer = Mock(spec=Writer)
        runner = JavaTestRunner(writer=mock_writer)

        runner._display_grade_summary(0.0, 10.0)

        # Check that always_echo was called
        assert mock_writer.always_echo.call_count >= 4

        # Check that 0% is displayed
        calls = [call[0][0] for call in mock_writer.always_echo.call_args_list]
        summary_text = " ".join(calls)
        assert "0.0%" in summary_text

    def test_display_grade_summary_decimal_values(self):
        """Test displaying grade summary with decimal values."""
        mock_writer = Mock(spec=Writer)
        runner = JavaTestRunner(writer=mock_writer)

        runner._display_grade_summary(8.75, 12.5)

        # Check that always_echo was called
        assert mock_writer.always_echo.call_count >= 4

        # Check that the correct values are displayed
        calls = [call[0][0] for call in mock_writer.always_echo.call_args_list]
        summary_text = " ".join(calls)

        assert "8.8" in summary_text  # 8.75 rounded to 1 decimal
        assert "12.5" in summary_text
        assert "70.0%" in summary_text  # (8.75/12.5)*100

    def test_display_grade_summary_formatting(self):
        """Test that grade summary has proper formatting."""
        mock_writer = Mock(spec=Writer)
        runner = JavaTestRunner(writer=mock_writer)

        runner._display_grade_summary(7.5, 10.0)

        # Check that formatting includes separators
        calls = [call[0][0] for call in mock_writer.always_echo.call_args_list]

        # Should have separator lines
        separator_calls = [call for call in calls if "=" in call]
        assert len(separator_calls) >= 2  # At least opening and closing separators

    def test_display_grade_summary_negative_possible_points(self):
        """Test displaying grade summary with negative possible points."""
        mock_writer = Mock(spec=Writer)
        runner = JavaTestRunner(writer=mock_writer)

        runner._display_grade_summary(5.0, -1.0)

        # Should not display anything when possible_points is negative
        mock_writer.always_echo.assert_not_called()

    def test_display_grade_summary_very_small_values(self):
        """Test displaying grade summary with very small values."""
        mock_writer = Mock(spec=Writer)
        runner = JavaTestRunner(writer=mock_writer)

        runner._display_grade_summary(0.1, 0.5)

        # Check that always_echo was called
        assert mock_writer.always_echo.call_count >= 4

        # Check that the percentage is calculated correctly
        calls = [call[0][0] for call in mock_writer.always_echo.call_args_list]
        summary_text = " ".join(calls)
        assert "20.0%" in summary_text  # (0.1/0.5)*100
