#!/usr/bin/env python3

"""Unit tests for grading strategies."""

import pytest

from grader.domain import (
    DropLowestGradingStrategy,
    SimpleGradingStrategy,
    WeightedGradingStrategy,
)


class TestSimpleGradingStrategy:
    """Test the SimpleGradingStrategy class."""

    def test_perfect_score(self):
        """Test perfect score calculation."""
        strategy = SimpleGradingStrategy()
        result = strategy.apply_strategy(100.0, 100.0)
        assert result == 100.0

    def test_partial_score(self):
        """Test partial score calculation."""
        strategy = SimpleGradingStrategy()
        result = strategy.apply_strategy(85.0, 100.0)
        assert result == 85.0

    def test_decimal_scores(self):
        """Test with decimal values."""
        strategy = SimpleGradingStrategy()
        result = strategy.apply_strategy(42.5, 50.0)
        assert result == 85.0

    def test_zero_points_earned(self):
        """Test when student earns zero points."""
        strategy = SimpleGradingStrategy()
        result = strategy.apply_strategy(0.0, 100.0)
        assert result == 0.0

    def test_zero_points_possible(self):
        """Test when points possible is zero."""
        strategy = SimpleGradingStrategy()
        result = strategy.apply_strategy(0.0, 0.0)
        assert result == 0.0

    def test_various_percentages(self):
        """Test various percentage calculations."""
        strategy = SimpleGradingStrategy()
        
        assert strategy.apply_strategy(75.0, 100.0) == 75.0
        assert strategy.apply_strategy(50.0, 100.0) == 50.0
        assert strategy.apply_strategy(25.0, 100.0) == 25.0
        assert strategy.apply_strategy(90.0, 100.0) == 90.0

    def test_different_max_values(self):
        """Test with different maximum possible values."""
        strategy = SimpleGradingStrategy()
        
        assert strategy.apply_strategy(45.0, 50.0) == 90.0
        assert strategy.apply_strategy(30.0, 40.0) == 75.0
        assert strategy.apply_strategy(18.0, 20.0) == 90.0


class TestWeightedGradingStrategy:
    """Test the WeightedGradingStrategy class."""

    def test_initialization_valid_weights(self):
        """Test initialization with valid weights."""
        weights = {"basics": 0.3, "advanced": 0.7}
        strategy = WeightedGradingStrategy(weights)
        assert strategy.category_weights == weights

    def test_initialization_invalid_weights_sum(self):
        """Test initialization fails with invalid weight sum."""
        weights = {"basics": 0.3, "advanced": 0.6}  # Sum = 0.9, not 1.0
        with pytest.raises(ValueError, match="must sum to 1.0"):
            WeightedGradingStrategy(weights)

    def test_initialization_weights_sum_too_high(self):
        """Test initialization fails when weights sum > 1.0."""
        weights = {"basics": 0.6, "advanced": 0.7}  # Sum = 1.3
        with pytest.raises(ValueError, match="must sum to 1.0"):
            WeightedGradingStrategy(weights)

    def test_simple_weighted_calculation(self):
        """Test simple weighted grade calculation with multiple tests."""
        weights = {"basics": 0.4, "advanced": 0.6}
        category_map = {"Test1": "basics", "Test2": "advanced"}
        strategy = WeightedGradingStrategy(weights, category_map)
        
        test_results = {
            "Test1": (10.0, 10.0),  # 100% in basics (weight 0.4)
            "Test2": (15.0, 20.0),  # 75% in advanced (weight 0.6)
        }
        
        # Expected: (1.0 * 0.4) + (0.75 * 0.6) = 0.4 + 0.45 = 0.85 = 85%
        result = strategy.apply_strategy_to_results(test_results)
        assert result == pytest.approx(85.0)

    def test_weighted_all_perfect_scores(self):
        """Test weighted calculation with all perfect scores."""
        weights = {"category1": 0.5, "category2": 0.5}
        category_map = {"Test1": "category1", "Test2": "category2"}
        strategy = WeightedGradingStrategy(weights, category_map)
        
        test_results = {
            "Test1": (50.0, 50.0),  # 100%
            "Test2": (100.0, 100.0),  # 100%
        }
        
        result = strategy.apply_strategy_to_results(test_results)
        assert result == pytest.approx(100.0)

    def test_weighted_unequal_weights(self):
        """Test weighted calculation with unequal weights."""
        weights = {"basics": 0.3, "intermediate": 0.3, "advanced": 0.4}
        category_map = {
            "Test1": "basics",
            "Test2": "intermediate",
            "Test3": "advanced",
        }
        strategy = WeightedGradingStrategy(weights, category_map)
        
        test_results = {
            "Test1": (10.0, 10.0),  # 100% in basics (weight 0.3)
            "Test2": (8.0, 10.0),   # 80% in intermediate (weight 0.3)
            "Test3": (6.0, 10.0),   # 60% in advanced (weight 0.4)
        }
        
        # Expected: (1.0 * 0.3) + (0.8 * 0.3) + (0.6 * 0.4) = 0.3 + 0.24 + 0.24 = 0.78 = 78%
        result = strategy.apply_strategy_to_results(test_results)
        assert result == pytest.approx(78.0)

    def test_weighted_with_zero_points_in_category(self):
        """Test weighted calculation when one category has zero points possible."""
        weights = {"basics": 0.5, "advanced": 0.5}
        category_map = {"Test1": "basics", "Test2": "advanced"}
        strategy = WeightedGradingStrategy(weights, category_map)
        
        test_results = {
            "Test1": (10.0, 10.0),  # 100% in basics
            "Test2": (0.0, 0.0),    # 0 points possible in advanced
        }
        
        # Expected: (1.0 * 0.5) + (0.0 * 0.5) = 0.5 = 50%
        result = strategy.apply_strategy_to_results(test_results)
        assert result == pytest.approx(50.0)

    def test_weighted_no_test_results(self):
        """Test weighted calculation with no test results."""
        weights = {"basics": 0.5, "advanced": 0.5}
        strategy = WeightedGradingStrategy(weights)
        
        result = strategy.apply_strategy_to_results({})
        assert result == 0.0

    def test_weighted_default_category(self):
        """Test weighted calculation with unmapped test using default category."""
        weights = {"default": 0.4, "advanced": 0.6}
        category_map = {"Test2": "advanced"}  # Test1 not mapped
        strategy = WeightedGradingStrategy(weights, category_map)
        
        test_results = {
            "Test1": (10.0, 10.0),  # 100% in default (weight 0.4)
            "Test2": (12.0, 20.0),  # 60% in advanced (weight 0.6)
        }
        
        # Expected: (1.0 * 0.4) + (0.6 * 0.6) = 0.4 + 0.36 = 0.76 = 76%
        result = strategy.apply_strategy_to_results(test_results)
        assert result == pytest.approx(76.0)

    def test_apply_strategy_single_test(self):
        """Test simple apply_strategy method with single test."""
        weights = {"basics": 1.0}
        strategy = WeightedGradingStrategy(weights)
        
        result = strategy.apply_strategy(85.0, 100.0)
        assert result == 85.0


class TestDropLowestGradingStrategy:
    """Test the DropLowestGradingStrategy class."""

    def test_initialization_valid_drop_count(self):
        """Test initialization with valid drop count."""
        strategy = DropLowestGradingStrategy(drop_count=2)
        assert strategy.drop_count == 2

    def test_initialization_default_drop_count(self):
        """Test initialization with default drop count."""
        strategy = DropLowestGradingStrategy()
        assert strategy.drop_count == 1

    def test_initialization_negative_drop_count(self):
        """Test initialization fails with negative drop count."""
        with pytest.raises(ValueError, match="must be non-negative"):
            DropLowestGradingStrategy(drop_count=-1)

    def test_drop_one_lowest(self):
        """Test dropping one lowest score."""
        strategy = DropLowestGradingStrategy(drop_count=1)
        
        test_results = [
            (10.0, 10.0),  # 100%
            (5.0, 10.0),   # 50% - should be dropped
            (9.0, 10.0),   # 90%
        ]
        
        # After dropping 5/10: (10 + 9) / (10 + 10) = 19/20 = 95%
        result = strategy.apply_strategy_to_results(test_results)
        assert result == pytest.approx(95.0)

    def test_drop_two_lowest(self):
        """Test dropping two lowest scores."""
        strategy = DropLowestGradingStrategy(drop_count=2)
        
        test_results = [
            (10.0, 10.0),  # 100%
            (5.0, 10.0),   # 50% - should be dropped
            (6.0, 10.0),   # 60% - should be dropped
            (9.0, 10.0),   # 90%
        ]
        
        # After dropping 5/10 and 6/10: (10 + 9) / (10 + 10) = 19/20 = 95%
        result = strategy.apply_strategy_to_results(test_results)
        assert result == pytest.approx(95.0)

    def test_drop_all_scores_returns_zero(self):
        """Test dropping all scores returns zero."""
        strategy = DropLowestGradingStrategy(drop_count=3)
        
        test_results = [
            (10.0, 10.0),
            (8.0, 10.0),
            (9.0, 10.0),
        ]
        
        result = strategy.apply_strategy_to_results(test_results)
        assert result == 0.0

    def test_drop_more_than_available_returns_zero(self):
        """Test dropping more scores than available returns zero."""
        strategy = DropLowestGradingStrategy(drop_count=5)
        
        test_results = [
            (10.0, 10.0),
            (8.0, 10.0),
        ]
        
        result = strategy.apply_strategy_to_results(test_results)
        assert result == 0.0

    def test_drop_none(self):
        """Test with drop_count of 0 (no dropping)."""
        strategy = DropLowestGradingStrategy(drop_count=0)
        
        test_results = [
            (10.0, 10.0),  # 100%
            (5.0, 10.0),   # 50%
            (8.0, 10.0),   # 80%
        ]
        
        # No drops: (10 + 5 + 8) / (10 + 10 + 10) = 23/30 = 76.67%
        result = strategy.apply_strategy_to_results(test_results)
        assert result == pytest.approx(76.666666, rel=1e-5)

    def test_drop_with_different_max_scores(self):
        """Test dropping lowest with different maximum scores."""
        strategy = DropLowestGradingStrategy(drop_count=1)
        
        test_results = [
            (20.0, 20.0),  # 100%
            (10.0, 20.0),  # 50% - should be dropped
            (30.0, 40.0),  # 75%
        ]
        
        # After dropping 10/20: (20 + 30) / (20 + 40) = 50/60 = 83.33%
        result = strategy.apply_strategy_to_results(test_results)
        assert result == pytest.approx(83.333333, rel=1e-5)

    def test_drop_with_zero_possible_points(self):
        """Test dropping lowest when a test has zero possible points."""
        strategy = DropLowestGradingStrategy(drop_count=1)
        
        test_results = [
            (10.0, 10.0),  # 100%
            (0.0, 0.0),    # 0% (zero possible) - should be dropped
            (8.0, 10.0),   # 80%
        ]
        
        # After dropping 0/0: (10 + 8) / (10 + 10) = 18/20 = 90%
        result = strategy.apply_strategy_to_results(test_results)
        assert result == pytest.approx(90.0)

    def test_empty_test_results(self):
        """Test with empty test results."""
        strategy = DropLowestGradingStrategy(drop_count=1)
        
        result = strategy.apply_strategy_to_results([])
        assert result == 0.0

    def test_single_test_with_drop_one(self):
        """Test single test with drop count of 1."""
        strategy = DropLowestGradingStrategy(drop_count=1)
        
        test_results = [(10.0, 10.0)]
        
        # Dropping the only test returns 0
        result = strategy.apply_strategy_to_results(test_results)
        assert result == 0.0

    def test_all_perfect_scores_drop_one(self):
        """Test all perfect scores with drop one."""
        strategy = DropLowestGradingStrategy(drop_count=1)
        
        test_results = [
            (10.0, 10.0),  # 100%
            (20.0, 20.0),  # 100%
            (30.0, 30.0),  # 100%
        ]
        
        # After dropping one perfect score: still 100%
        result = strategy.apply_strategy_to_results(test_results)
        assert result == pytest.approx(100.0)

    def test_apply_strategy_single_test(self):
        """Test simple apply_strategy method with single test."""
        strategy = DropLowestGradingStrategy(drop_count=1)
        
        result = strategy.apply_strategy(85.0, 100.0)
        assert result == 85.0

    def test_decimal_scores(self):
        """Test with decimal scores."""
        strategy = DropLowestGradingStrategy(drop_count=1)
        
        test_results = [
            (8.5, 10.0),   # 85%
            (4.25, 10.0),  # 42.5% - should be dropped
            (9.75, 10.0),  # 97.5%
        ]
        
        # After dropping 4.25/10: (8.5 + 9.75) / (10 + 10) = 18.25/20 = 91.25%
        result = strategy.apply_strategy_to_results(test_results)
        assert result == pytest.approx(91.25)
