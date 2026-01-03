#!/usr/bin/env python3

"""
Demo script showing how to use the grading strategies.

This demonstrates the three main grading strategies:
1. SimpleGradingStrategy - Basic percentage calculation
2. WeightedGradingStrategy - Weighted categories
3. DropLowestGradingStrategy - Drop N lowest scores
"""

from grader.domain import (
    DropLowestGradingStrategy,
    SimpleGradingStrategy,
    WeightedGradingStrategy,
)


def demo_simple_strategy():
    """Demonstrate SimpleGradingStrategy."""
    print("\n" + "=" * 70)
    print("SIMPLE GRADING STRATEGY")
    print("=" * 70)
    print("\nCalculates grade as a simple percentage: (earned / possible) * 100\n")

    strategy = SimpleGradingStrategy()

    # Example: Student earned 85 out of 100 points
    points_earned = 85.0
    points_possible = 100.0

    grade = strategy.apply_strategy(points_earned, points_possible)

    print(f"Points earned: {points_earned}")
    print(f"Points possible: {points_possible}")
    print(f"Final grade: {grade:.1f}%")


def demo_weighted_strategy():
    """Demonstrate WeightedGradingStrategy."""
    print("\n" + "=" * 70)
    print("WEIGHTED GRADING STRATEGY")
    print("=" * 70)
    print("\nApplies different weights to different test categories.\n")

    # Define categories and their weights
    # Example: Labs are 30%, Assignments are 40%, Project is 30%
    weights = {
        "labs": 0.3,
        "assignments": 0.4,
        "project": 0.3,
    }

    # Map category names to categories (self-mapping for clarity)
    category_map = {
        "labs": "labs",
        "assignments": "assignments",
        "project": "project",
    }

    strategy = WeightedGradingStrategy(weights, category_map)

    # For this example, we've already aggregated test results by category
    # In practice, you'd sum up all labs, all assignments, etc.
    # Test results: {category_name: (points_earned, points_possible)}
    test_results = {
        "labs": (19.0, 20.0),  # Combined: Lab1 (10/10) + Lab2 (9/10) = 95%
        "assignments": (
            34.0,
            40.0,
        ),  # Combined: Assign1 (18/20) + Assign2 (16/20) = 85%
        "project": (27.0, 30.0),  # 90%
    }

    grade = strategy.apply_strategy_to_results(test_results)

    print("Category weights:")
    for category, weight in weights.items():
        print(f"  {category}: {weight * 100:.0f}%")

    print("\nAggregated test results by category:")
    for category_name, (earned, possible) in test_results.items():
        percentage = (earned / possible) * 100 if possible > 0 else 0
        print(f"  {category_name}: {earned}/{possible} ({percentage:.1f}%)")

    print(f"\nWeighted final grade: {grade:.1f}%")

    # Show calculation
    print("\nCalculation:")
    print(
        f"  Labs: {19 / 20:.3f} * {weights['labs']} = {(19 / 20) * weights['labs']:.3f}"
    )
    print(
        f"  Assignments: {34 / 40:.3f} * {weights['assignments']} = {(34 / 40) * weights['assignments']:.3f}"
    )
    print(
        f"  Project: {27 / 30:.3f} * {weights['project']} = {(27 / 30) * weights['project']:.3f}"
    )
    print(f"  Total: {grade / 100:.3f} = {grade:.1f}%")


def demo_drop_lowest_strategy():
    """Demonstrate DropLowestGradingStrategy."""
    print("\n" + "=" * 70)
    print("DROP-LOWEST GRADING STRATEGY")
    print("=" * 70)
    print("\nDrops N lowest test scores before calculating the final grade.\n")

    # Drop the lowest test score
    strategy = DropLowestGradingStrategy(drop_count=1)

    # Test results: [(points_earned, points_possible)]
    test_results = [
        (10.0, 10.0),  # Test 1: 100%
        (9.5, 10.0),  # Test 2: 95%
        (5.0, 10.0),  # Test 3: 50% - This will be dropped!
        (9.0, 10.0),  # Test 4: 90%
        (8.5, 10.0),  # Test 5: 85%
    ]

    # Calculate without drop-lowest
    simple_strategy = SimpleGradingStrategy()
    total_earned = sum(r[0] for r in test_results)
    total_possible = sum(r[1] for r in test_results)
    grade_without_drop = simple_strategy.apply_strategy(total_earned, total_possible)

    # Calculate with drop-lowest
    grade_with_drop = strategy.apply_strategy_to_results(test_results)

    print("Test results:")
    for i, (earned, possible) in enumerate(test_results, 1):
        percentage = (earned / possible) * 100 if possible > 0 else 0
        print(f"  Test {i}: {earned}/{possible} ({percentage:.1f}%)")

    print(f"\nWithout drop-lowest: {grade_without_drop:.1f}%")
    print(f"With drop-lowest (drop 1): {grade_with_drop:.1f}%")
    print(f"Improvement: {grade_with_drop - grade_without_drop:.1f} percentage points")


def demo_combined_example():
    """Demonstrate combining strategies for a realistic course grading scenario."""
    print("\n" + "=" * 70)
    print("COMBINED EXAMPLE: REALISTIC COURSE GRADING")
    print("=" * 70)
    print("\nA course with:")
    print("  - 5 Labs (30% of grade, drop lowest)")
    print("  - 2 Assignments (40% of grade)")
    print("  - 1 Final Project (30% of grade)")
    print()

    # Step 1: Calculate lab grade with drop-lowest
    lab_strategy = DropLowestGradingStrategy(drop_count=1)
    lab_results = [
        (10.0, 10.0),  # Lab 1: 100%
        (3.0, 10.0),  # Lab 2: 30% - Student was sick, will be dropped
        (9.0, 10.0),  # Lab 3: 90%
        (10.0, 10.0),  # Lab 4: 100%
        (9.5, 10.0),  # Lab 5: 95%
    ]
    lab_grade_percentage = lab_strategy.apply_strategy_to_results(lab_results)

    # Step 2: Calculate assignment grade
    assignment_strategy = SimpleGradingStrategy()
    assignment_total = (85.0, 100.0)  # Combined assignments
    assignment_grade_percentage = assignment_strategy.apply_strategy(
        assignment_total[0], assignment_total[1]
    )

    # Step 3: Calculate project grade
    project_strategy = SimpleGradingStrategy()
    project_total = (90.0, 100.0)
    project_grade_percentage = project_strategy.apply_strategy(
        project_total[0], project_total[1]
    )

    # Step 4: Combine using weights
    course_weights = {
        "labs": 0.3,
        "assignments": 0.4,
        "project": 0.3,
    }

    overall_grade = (
        (lab_grade_percentage / 100.0) * course_weights["labs"]
        + (assignment_grade_percentage / 100.0) * course_weights["assignments"]
        + (project_grade_percentage / 100.0) * course_weights["project"]
    ) * 100.0

    print("Grade breakdown:")
    print(f"  Labs (30%): {lab_grade_percentage:.1f}%")
    print(f"  Assignments (40%): {assignment_grade_percentage:.1f}%")
    print(f"  Project (30%): {project_grade_percentage:.1f}%")
    print(f"\nFinal course grade: {overall_grade:.1f}%")

    # Show letter grade
    if overall_grade >= 90:
        letter = "A"
    elif overall_grade >= 80:
        letter = "B"
    elif overall_grade >= 70:
        letter = "C"
    elif overall_grade >= 60:
        letter = "D"
    else:
        letter = "F"

    print(f"Letter grade: {letter}")


def main():
    """Run all demonstrations."""
    print("\n")
    print("*" * 70)
    print("GRADING STRATEGIES DEMONSTRATION")
    print("*" * 70)

    demo_simple_strategy()
    demo_weighted_strategy()
    demo_drop_lowest_strategy()
    demo_combined_example()

    print("\n" + "*" * 70)
    print("END OF DEMONSTRATION")
    print("*" * 70 + "\n")


if __name__ == "__main__":
    main()
