#!/usr/bin/env python3

"""Integration tests for grading strategies."""

import pytest

from grader.domain import (
    DropLowestGradingStrategy,
    SimpleGradingStrategy,
    TestResult,
    TestRunOutput,
    WeightedGradingStrategy,
)


class TestGradingStrategyIntegration:
    """Integration tests demonstrating grading strategy usage patterns."""

    def test_simple_strategy_with_test_result(self):
        """Test SimpleGradingStrategy with TestResult model."""
        strategy = SimpleGradingStrategy()
        
        # Create test output
        output = TestRunOutput(
            stdout="Test passed",
            stderr="",
            exit_code=0,
            execution_time=1.5
        )
        
        # Create test result
        test_result = TestResult(
            points_earned=85.0,
            points_possible=100.0,
            output=output,
            success=True
        )
        
        # Calculate grade using strategy
        grade = strategy.apply_strategy(
            test_result.points_earned,
            test_result.points_possible
        )
        
        assert grade == 85.0
        assert test_result.percentage == 85.0

    def test_weighted_strategy_multiple_test_categories(self):
        """Test WeightedGradingStrategy with multiple test categories."""
        # Define test categories and weights
        weights = {
            "basics": 0.2,      # 20% of grade
            "intermediate": 0.3, # 30% of grade
            "advanced": 0.5     # 50% of grade
        }
        
        category_map = {
            "TestBasics": "basics",
            "TestIntermediate": "intermediate",
            "TestAdvanced": "advanced"
        }
        
        strategy = WeightedGradingStrategy(weights, category_map)
        
        # Test results from different categories
        test_results = {
            "TestBasics": (20.0, 20.0),        # 100% in basics
            "TestIntermediate": (24.0, 30.0),  # 80% in intermediate
            "TestAdvanced": (40.0, 50.0),      # 80% in advanced
        }
        
        # Expected: (1.0 * 0.2) + (0.8 * 0.3) + (0.8 * 0.5) = 0.2 + 0.24 + 0.4 = 0.84 = 84%
        grade = strategy.apply_strategy_to_results(test_results)
        assert grade == pytest.approx(84.0)

    def test_drop_lowest_strategy_with_multiple_tests(self):
        """Test DropLowestGradingStrategy dropping one bad test."""
        strategy = DropLowestGradingStrategy(drop_count=1)
        
        # Student had one bad test day
        test_results = [
            (10.0, 10.0),  # Test 1: 100%
            (9.5, 10.0),   # Test 2: 95%
            (5.0, 10.0),   # Test 3: 50% - this will be dropped
            (9.0, 10.0),   # Test 4: 90%
        ]
        
        # After dropping 5/10: (10 + 9.5 + 9) / (10 + 10 + 10) = 28.5/30 = 95%
        grade = strategy.apply_strategy_to_results(test_results)
        assert grade == pytest.approx(95.0)

    def test_drop_multiple_lowest_scores(self):
        """Test dropping multiple lowest scores for more flexibility."""
        strategy = DropLowestGradingStrategy(drop_count=2)
        
        test_results = [
            (10.0, 10.0),  # 100%
            (9.0, 10.0),   # 90%
            (8.0, 10.0),   # 80%
            (6.0, 10.0),   # 60% - dropped
            (5.0, 10.0),   # 50% - dropped
        ]
        
        # After dropping two lowest: (10 + 9 + 8) / (10 + 10 + 10) = 27/30 = 90%
        grade = strategy.apply_strategy_to_results(test_results)
        assert grade == pytest.approx(90.0)

    def test_real_world_scenario_lab_grading(self):
        """Test a realistic lab grading scenario."""
        # Student completed 5 labs with varying success
        simple_strategy = SimpleGradingStrategy()
        
        lab_results = [
            (10.0, 10.0),   # Lab 1: Perfect
            (9.5, 10.0),    # Lab 2: Almost perfect
            (8.0, 10.0),    # Lab 3: Good
            (10.0, 10.0),   # Lab 4: Perfect
            (9.0, 10.0),    # Lab 5: Excellent
        ]
        
        total_earned = sum(r[0] for r in lab_results)
        total_possible = sum(r[1] for r in lab_results)
        
        grade = simple_strategy.apply_strategy(total_earned, total_possible)
        
        # Expected: 46.5 / 50 = 93%
        assert grade == pytest.approx(93.0)

    def test_real_world_scenario_weighted_assignment_categories(self):
        """Test weighted grading for different assignment categories."""
        # Course has labs (30%), assignments (40%), and project (30%)
        weights = {
            "labs": 0.3,
            "assignments": 0.4,
            "project": 0.3
        }
        
        # Map each test to its category
        category_map = {
            "labs": "labs",
            "assignments": "assignments",
            "project": "project"
        }
        
        strategy = WeightedGradingStrategy(weights, category_map)
        
        # Aggregate results from each category
        category_results = {
            "labs": (45.0, 50.0),          # 90% on labs
            "assignments": (36.0, 40.0),   # 90% on assignments
            "project": (27.0, 30.0),       # 90% on project
        }
        
        grade = strategy.apply_strategy_to_results(category_results)
        
        # All 90%, so weighted average is 90%
        assert grade == pytest.approx(90.0)

    def test_real_world_scenario_labs_with_drop_lowest(self):
        """Test lab grading with drop-lowest policy."""
        # Course allows dropping the lowest lab grade
        drop_strategy = DropLowestGradingStrategy(drop_count=1)
        
        # Student had one really bad lab but recovered
        lab_results = [
            (10.0, 10.0),  # Lab 1: 100%
            (3.0, 10.0),   # Lab 2: 30% - sick that week, will be dropped
            (9.0, 10.0),   # Lab 3: 90%
            (10.0, 10.0),  # Lab 4: 100%
            (9.5, 10.0),   # Lab 5: 95%
        ]
        
        # Without drop: 41.5/50 = 83%
        simple_grade = SimpleGradingStrategy().apply_strategy(
            sum(r[0] for r in lab_results),
            sum(r[1] for r in lab_results)
        )
        assert simple_grade == pytest.approx(83.0)
        
        # With drop-lowest: (10 + 9 + 10 + 9.5) / (10 + 10 + 10 + 10) = 38.5/40 = 96.25%
        drop_grade = drop_strategy.apply_strategy_to_results(lab_results)
        assert drop_grade == pytest.approx(96.25)

    def test_combining_strategies_conceptually(self):
        """
        Demonstrate how strategies could be combined in a real grading system.
        
        This shows the pattern for using different strategies for different
        parts of the grade calculation.
        """
        # Category 1: Labs with drop-lowest
        lab_strategy = DropLowestGradingStrategy(drop_count=1)
        lab_results = [
            (10.0, 10.0),
            (5.0, 10.0),   # This will be dropped
            (9.0, 10.0),
            (10.0, 10.0),
        ]
        lab_grade_percentage = lab_strategy.apply_strategy_to_results(lab_results)
        # (10 + 9 + 10) / (10 + 10 + 10) = 96.67%
        
        # Category 2: Assignments (simple average)
        assignment_strategy = SimpleGradingStrategy()
        assignment_total = (85.0, 100.0)
        assignment_grade_percentage = assignment_strategy.apply_strategy(
            assignment_total[0],
            assignment_total[1]
        )
        # 85%
        
        # Category 3: Final project
        project_strategy = SimpleGradingStrategy()
        project_total = (90.0, 100.0)
        project_grade_percentage = project_strategy.apply_strategy(
            project_total[0],
            project_total[1]
        )
        # 90%
        
        # Overall course grade with weights
        course_weights = {
            "labs": 0.3,
            "assignments": 0.4,
            "project": 0.3
        }
        
        # Convert percentages to proportions and apply weights
        overall_grade = (
            (lab_grade_percentage / 100.0) * course_weights["labs"] +
            (assignment_grade_percentage / 100.0) * course_weights["assignments"] +
            (project_grade_percentage / 100.0) * course_weights["project"]
        ) * 100.0
        
        # Expected: (0.9667 * 0.3) + (0.85 * 0.4) + (0.90 * 0.3)
        #         = 0.29 + 0.34 + 0.27 = 0.90 = 90%
        assert overall_grade == pytest.approx(90.0, abs=0.1)

    def test_edge_case_all_zeros(self):
        """Test strategies handle all zero scores gracefully."""
        simple_strategy = SimpleGradingStrategy()
        drop_strategy = DropLowestGradingStrategy(drop_count=1)
        
        # All tests failed
        test_results = [
            (0.0, 10.0),
            (0.0, 10.0),
            (0.0, 10.0),
        ]
        
        simple_grade = simple_strategy.apply_strategy(0.0, 30.0)
        assert simple_grade == 0.0
        
        drop_grade = drop_strategy.apply_strategy_to_results(test_results)
        assert drop_grade == 0.0

    def test_edge_case_perfect_scores(self):
        """Test strategies with all perfect scores."""
        simple_strategy = SimpleGradingStrategy()
        drop_strategy = DropLowestGradingStrategy(drop_count=1)
        
        # All tests perfect
        test_results = [
            (10.0, 10.0),
            (10.0, 10.0),
            (10.0, 10.0),
        ]
        
        simple_grade = simple_strategy.apply_strategy(30.0, 30.0)
        assert simple_grade == 100.0
        
        # Even dropping one perfect score gives 100%
        drop_grade = drop_strategy.apply_strategy_to_results(test_results)
        assert drop_grade == 100.0
