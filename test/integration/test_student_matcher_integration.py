#!/usr/bin/env python3

"""Integration tests for student matcher domain services in bulk grading workflow."""

import pytest

from grader.domain import (
    Student,
    StudentId,
    FuzzyStudentMatcher,
    ExactStudentMatcher,
    CompositeStudentMatcher,
)
from grader.bulk_grader import find_best_name_match


class TestStudentMatcherIntegrationWithBulkGrader:
    """Test student matchers in realistic bulk grading scenarios."""

    def test_fuzzy_matcher_with_real_student_list(self):
        """Test FuzzyStudentMatcher with realistic student data."""
        # Simulate students from a CSV grading list
        students = [
            Student(StudentId("300069634", "cwils001"), "Charlie", "Wilson"),
            Student(StudentId("300173416", "drodr002"), "Dana", "Rodriguez"),
            Student(StudentId("300234567", "ethom003"), "Emma", "Thompson"),
            Student(StudentId("300345678", "jmari004"), "José", "María"),
            Student(StudentId("300456789", "fcote005"), "François", "Côté"),
        ]

        matcher = FuzzyStudentMatcher()

        # Test exact matches
        result = matcher.find_match("Charlie Wilson", students)
        assert result is not None
        assert result.student_id.username == "cwils001"

        # Test case-insensitive
        result = matcher.find_match("DANA RODRIGUEZ", students)
        assert result is not None
        assert result.student_id.username == "drodr002"

        # Test accent-insensitive
        result = matcher.find_match("Jose Maria", students)
        assert result is not None
        assert result.student_id.username == "jmari004"

        result = matcher.find_match("Francois Cote", students)
        assert result is not None
        assert result.student_id.username == "fcote005"

        # Test with submission-like name (from folder name parsing)
        result = matcher.find_match("Emma Thompson", students)
        assert result is not None
        assert result.student_id.username == "ethom003"

    def test_exact_matcher_for_performance(self):
        """Test ExactStudentMatcher for fast exact matching."""
        students = [
            Student(StudentId("1", "student1"), "John", "Doe"),
            Student(StudentId("2", "student2"), "Jane", "Smith"),
            Student(StudentId("3", "student3"), "Bob", "Wilson"),
        ] * 100  # Large list to test performance

        matcher = ExactStudentMatcher()

        # Should find exact matches quickly
        result = matcher.find_match("John Doe", students)
        assert result is not None
        assert result.student_id.org_defined_id == "1"

        # Should not find partial matches
        result = matcher.find_match("John", students)
        assert result is None

    def test_composite_matcher_workflow(self):
        """Test CompositeStudentMatcher in bulk grading workflow."""
        students = [
            Student(StudentId("300069634", "cwils001"), "Charlie", "Wilson"),
            Student(StudentId("300173416", "drodr002"), "Dana", "Rodriguez"),
            Student(StudentId("300234567", "ethom003"), "Emma", "Thompson"),
        ]

        # Typical production setup: exact first, then fuzzy
        matcher = CompositeStudentMatcher([
            ExactStudentMatcher(),
            FuzzyStudentMatcher(),
        ])

        # Exact match (uses fast ExactStudentMatcher)
        result = matcher.find_match("Charlie Wilson", students)
        assert result is not None
        assert result.student_id.username == "cwils001"

        # Fuzzy match with typo (falls back to FuzzyStudentMatcher)
        result = matcher.find_match("Charle Wilson", students, threshold=75)
        assert result is not None
        assert result.student_id.username == "cwils001"

        # No match if too different
        result = matcher.find_match("Unknown Student", students, threshold=80)
        assert result is None

    def test_backward_compatibility_with_bulk_grader(self):
        """Test that bulk_grader wrapper functions still work."""
        # Test normalize_name wrapper
        from grader.bulk_grader import normalize_name as bulk_normalize_name

        assert bulk_normalize_name("José María") == "jose maria"
        assert bulk_normalize_name("François Côté") == "francois cote"

        # Test find_best_name_match wrapper
        candidate_names = [
            "Charlie Wilson",
            "Dana Rodriguez",
            "Emma Thompson",
        ]

        result = find_best_name_match("Charlie Wilson", candidate_names)
        assert result == "Charlie Wilson"

        result = find_best_name_match("charlie wilson", candidate_names)
        assert result == "Charlie Wilson"

        result = find_best_name_match("Jose Maria", candidate_names)
        assert result is None  # Not in list

    def test_multiple_submissions_same_student(self):
        """Test matching when student has multiple submissions."""
        students = [
            Student(StudentId("300069634", "cwils001"), "Charlie", "Wilson"),
        ]

        matcher = FuzzyStudentMatcher()

        # Different variations from submission folder names
        variations = [
            "Charlie Wilson",
            "charlie wilson",
            "CHARLIE WILSON",
            "Charlie  Wilson",  # Extra space
        ]

        for variation in variations:
            result = matcher.find_match(variation, students)
            assert result is not None
            assert result.student_id.username == "cwils001"

    def test_international_student_names(self):
        """Test matching with diverse international names."""
        students = [
            Student(StudentId("1", "vdvorak"), "Václav", "Dvořák"),
            Student(StudentId("2", "bastrom"), "Björn", "Åström"),
            Student(StudentId("3", "nguyen"), "Nguyễn", "Văn"),
            Student(StudentId("4", "wang"), "王", "美麗"),
        ]

        matcher = FuzzyStudentMatcher()

        # Test with normalized versions
        result = matcher.find_match("Vaclav Dvorak", students)
        assert result is not None
        assert result.student_id.username == "vdvorak"

        result = matcher.find_match("Bjorn Astrom", students)
        assert result is not None
        assert result.student_id.username == "bastrom"

        result = matcher.find_match("Nguyen Van", students)
        assert result is not None
        assert result.student_id.username == "nguyen"

    def test_edge_cases_in_bulk_grading(self):
        """Test edge cases that might occur in bulk grading."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
            Student(StudentId("2", "jsmith"), "Jane", "Smith"),
        ]

        matcher = FuzzyStudentMatcher()

        # Empty name
        result = matcher.find_match("", students)
        assert result is None

        # Single word
        result = matcher.find_match("John", students, threshold=50)
        assert result is not None  # Should match with low threshold

        # Empty candidate list
        result = matcher.find_match("John Doe", [])
        assert result is None

        # Special characters
        students_with_special = [
            Student(StudentId("1", "moconnor"), "Mary-Jane", "O'Connor"),
        ]
        matcher2 = FuzzyStudentMatcher()
        result = matcher2.find_match("Mary-Jane O'Connor", students_with_special)
        assert result is not None

    def test_threshold_sensitivity(self):
        """Test how threshold affects matching results."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
        ]

        matcher = FuzzyStudentMatcher()

        # High threshold - requires close match
        result = matcher.find_match("J D", students, threshold=90)
        assert result is None

        # Medium threshold - typo should still match
        result = matcher.find_match("Jon Doe", students, threshold=80)
        assert result is not None

        # Low threshold - very lenient, allows partial match
        result = matcher.find_match("Jo", students, threshold=20)
        assert result is not None


class TestMatcherPerformance:
    """Test performance characteristics of matchers."""

    def test_exact_matcher_scales_linearly(self):
        """Test that ExactStudentMatcher has O(n) performance."""
        import time

        # Create large student list
        students_100 = [
            Student(StudentId(str(i), f"user{i}"), f"First{i}", f"Last{i}")
            for i in range(100)
        ]
        students_1000 = [
            Student(StudentId(str(i), f"user{i}"), f"First{i}", f"Last{i}")
            for i in range(1000)
        ]

        matcher = ExactStudentMatcher()

        # Test with smaller list
        start = time.time()
        matcher.find_match("First50 Last50", students_100)
        time_100 = time.time() - start

        # Test with larger list
        start = time.time()
        matcher.find_match("First500 Last500", students_1000)
        time_1000 = time.time() - start

        # Should scale roughly linearly (allow for some variance)
        # 1000 students should take at most 20x as long as 100 students
        assert time_1000 < time_100 * 20

    def test_composite_matcher_early_exit(self):
        """Test that CompositeStudentMatcher exits early on first match."""
        students = [
            Student(StudentId("1", "jdoe"), "John", "Doe"),
        ]

        call_count = [0]

        class CountingMatcher:
            def find_match(self, target_name, candidates, threshold=80):
                call_count[0] += 1
                return candidates[0] if candidates else None

        # Create composite with multiple counting matchers
        matcher = CompositeStudentMatcher([
            CountingMatcher(),
            CountingMatcher(),
            CountingMatcher(),
        ])

        matcher.find_match("John Doe", students)

        # Should only call first matcher (early exit)
        assert call_count[0] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
