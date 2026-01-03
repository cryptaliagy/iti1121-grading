#!/usr/bin/env python3

"""
Demonstration script for student matcher domain services.

This script shows practical examples of using the different student matching
strategies in a grading workflow context.
"""

from grader.domain import (
    Student,
    StudentId,
    ExactStudentMatcher,
    FuzzyStudentMatcher,
    CompositeStudentMatcher,
    normalize_name,
)


def demo_normalize_name():
    """Demonstrate name normalization."""
    print("\n" + "=" * 60)
    print("DEMO 1: Name Normalization")
    print("=" * 60)

    test_names = [
        "José María",
        "François Côté",
        "Václav Dvořák",
        "  Multiple   Spaces  ",
        "UPPERCASE NAME",
    ]

    for name in test_names:
        normalized = normalize_name(name)
        print(f"'{name}' → '{normalized}'")


def demo_exact_matcher():
    """Demonstrate exact matching."""
    print("\n" + "=" * 60)
    print("DEMO 2: Exact Student Matcher")
    print("=" * 60)

    students = [
        Student(StudentId("1", "jdoe"), "John", "Doe"),
        Student(StudentId("2", "jsmith"), "Jane", "Smith"),
        Student(StudentId("3", "jmaria"), "José", "María"),
    ]

    matcher = ExactStudentMatcher()

    test_cases = [
        ("John Doe", "Exact match"),
        ("john doe", "Case insensitive"),
        ("Jose Maria", "Without accents"),
        ("Jon Doe", "Typo (should fail)"),
    ]

    for query, description in test_cases:
        result = matcher.find_match(query, students)
        status = f"✓ Found: {result.full_name}" if result else "✗ Not found"
        print(f"{description:20s} | '{query:15s}' → {status}")


def demo_fuzzy_matcher():
    """Demonstrate fuzzy matching."""
    print("\n" + "=" * 60)
    print("DEMO 3: Fuzzy Student Matcher")
    print("=" * 60)

    students = [
        Student(StudentId("1", "jdoe"), "John", "Doe"),
        Student(StudentId("2", "jsmith"), "Jane", "Smith"),
        Student(StudentId("3", "bwilson"), "Bob", "Wilson"),
    ]

    matcher = FuzzyStudentMatcher()

    test_cases = [
        ("John Doe", 80, "Exact match"),
        ("Jon Doe", 80, "Small typo"),
        ("Jhon Do", 70, "Multiple typos"),
        ("J Doe", 60, "Very short"),
        ("Robert Wilson", 90, "Different first name"),
    ]

    for query, threshold, description in test_cases:
        result = matcher.find_match(query, students, threshold)
        status = f"✓ Found: {result.full_name}" if result else "✗ Not found"
        print(
            f"{description:25s} | '{query:15s}' (threshold={threshold:2d}) → {status}"
        )


def demo_composite_matcher():
    """Demonstrate composite matching strategy."""
    print("\n" + "=" * 60)
    print("DEMO 4: Composite Student Matcher")
    print("=" * 60)

    students = [
        Student(StudentId("1", "cwilson"), "Charlie", "Wilson"),
        Student(StudentId("2", "drodr"), "Dana", "Rodriguez"),
        Student(StudentId("3", "ethom"), "Emma", "Thompson"),
    ]

    # Create composite strategy: exact first, then fuzzy
    exact_matcher = ExactStudentMatcher()
    fuzzy_matcher = FuzzyStudentMatcher()
    composite = CompositeStudentMatcher([exact_matcher, fuzzy_matcher])

    test_cases = [
        ("Charlie Wilson", 80, "Exact → uses ExactMatcher"),
        ("Charle Wilson", 75, "Typo → falls back to FuzzyMatcher"),
        ("Dana Rodriguez", 80, "Exact → uses ExactMatcher"),
        ("Emma Thompsn", 70, "Typo → falls back to FuzzyMatcher"),
    ]

    for query, threshold, description in test_cases:
        result = composite.find_match(query, students, threshold)
        status = f"✓ Found: {result.full_name}" if result else "✗ Not found"
        print(f"{description:40s} | '{query:20s}' → {status}")


def demo_international_names():
    """Demonstrate handling of international names."""
    print("\n" + "=" * 60)
    print("DEMO 5: International Names")
    print("=" * 60)

    students = [
        Student(StudentId("1", "jmaria"), "José", "María"),
        Student(StudentId("2", "fcote"), "François", "Côté"),
        Student(StudentId("3", "vdvorak"), "Václav", "Dvořák"),
        Student(StudentId("4", "bastrom"), "Björn", "Åström"),
    ]

    matcher = FuzzyStudentMatcher()

    # Test with normalized versions (as they might appear in submissions)
    test_cases = [
        ("Jose Maria", "Spanish → normalized"),
        ("Francois Cote", "French → normalized"),
        ("Vaclav Dvorak", "Czech → normalized"),
        ("Bjorn Astrom", "Swedish → normalized"),
    ]

    for query, description in test_cases:
        result = matcher.find_match(query, students)
        status = f"✓ Found: {result.full_name}" if result else "✗ Not found"
        print(f"{description:25s} | '{query:20s}' → {status}")


def demo_performance_comparison():
    """Demonstrate performance difference between matchers."""
    print("\n" + "=" * 60)
    print("DEMO 6: Performance Comparison")
    print("=" * 60)

    import time

    # Create large student list
    students = [
        Student(StudentId(str(i), f"user{i}"), f"First{i}", f"Last{i}")
        for i in range(1000)
    ]

    exact_matcher = ExactStudentMatcher()
    fuzzy_matcher = FuzzyStudentMatcher()

    # Test exact matcher
    start = time.time()
    exact_matcher.find_match("First500 Last500", students)
    exact_time = time.time() - start

    # Test fuzzy matcher (exact match path)
    start = time.time()
    fuzzy_matcher.find_match("First500 Last500", students)
    fuzzy_exact_time = time.time() - start

    # Test fuzzy matcher (fuzzy path)
    start = time.time()
    fuzzy_matcher.find_match("First50 Last50", students, threshold=70)
    fuzzy_fuzzy_time = time.time() - start

    print(f"Dataset: 1000 students")
    print(f"ExactMatcher (exact match):     {exact_time*1000:.2f}ms")
    print(f"FuzzyMatcher (exact path):      {fuzzy_exact_time*1000:.2f}ms")
    print(f"FuzzyMatcher (fuzzy matching):  {fuzzy_fuzzy_time*1000:.2f}ms")
    print(
        f"\nNote: FuzzyMatcher has fast path for exact matches, but is slower for fuzzy matching"
    )


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("STUDENT MATCHER DOMAIN SERVICES - DEMONSTRATION")
    print("=" * 60)

    demo_normalize_name()
    demo_exact_matcher()
    demo_fuzzy_matcher()
    demo_composite_matcher()
    demo_international_names()
    demo_performance_comparison()

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nFor more information, see docs/DomainLayer.md")


if __name__ == "__main__":
    main()
