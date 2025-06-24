#!/usr/bin/env python3

import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from grader.bulk_grader import (
    GradingResult,
    StudentRecord,
    Submission,
    extract_submissions,
    find_best_name_match,
    find_latest_submissions,
    load_grading_list,
    normalize_name,
    parse_submission_folder_name,
    prepare_grading_directory,
    save_results_to_csv,
)
from grader._grader import Writer


class TestCSVProcessing:
    """Test CSV loading and processing functions."""

    def test_load_grading_list(self, tmp_path):
        """Test loading grading list CSV."""
        csv_file = tmp_path / "grading_list.csv"
        content = """OrgDefinedId,Username,Last Name,First Name,End-of-Line Indicator
300069634,ASMITH001,Smith,Alice,#
#300167116,#BJONES002,Jones,Bob,#
300167116,BJONES002,Jones,Bob,#"""

        csv_file.write_text(content)

        df = load_grading_list(csv_file)

        # Should not filter out rows starting with #
        assert len(df) == 3
        assert "ASMITH001" in df["Username"].values
        assert "BJONES002" in df["Username"].values
        assert "#BJONES002" in df["Username"].values


class TestNameMatching:
    """Test name normalization and matching functions."""

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
            ("Žofia Čech", "zofia cech"),
            ("Łukasz Wróbel", "lukasz wrobel"),
            # Spanish characters
            ("Peña Niño", "pena nino"),
            ("Señor Corazón", "senor corazon"),
            # Portuguese characters
            ("João São", "joao sao"),
            ("Conceição", "conceicao"),
            # German umlauts and eszett
            ("Schöne Größe", "schone grosse"),
            ("Weiß", "weiss"),
            # Nordic characters
            ("Björn Åström", "bjorn astrom"),
            ("Øyvind Næss", "oyvind naess"),
            # Eastern European characters
            ("Václav Dvořák", "vaclav dvorak"),
            ("István Gábor", "istvan gabor"),
            ("Ştefan Ţuţu", "stefan tutu"),
            # Mixed case with special characters
            ("D'Angelo O'Brien", "d'angelo o'brien"),
            ("Van Der Berg", "van der berg"),
            ("MacLeod-Smith", "macleod-smith"),
            # Numbers and punctuation (should be preserved)
            ("John Smith III", "john smith iii"),
            ("Mary-Jane O'Connor", "mary-jane o'connor"),
            # Edge cases
            ("", ""),
            ("   ", ""),
            ("A", "a"),
            # Complex combinations
            ("María José Fernández-González", "maria jose fernandez-gonzalez"),
            ("Björn-Åke Sørensen", "bjorn-ake sorensen"),
        ],
    )
    def test_normalize_name_basic(self, input_name, expected):
        """Test basic name normalization cases."""
        assert normalize_name(input_name) == expected

    @pytest.mark.parametrize(
        "input_name,expected",
        [
            # Cyrillic characters
            ("Александр Иванов", "aleksandr ivanov"),
            ("Дмитрий Петров", "dmitrii petrov"),
            # Greek characters
            ("Αλέξανδρος Παπαδόπουλος", "alexandros papadopoulos"),
            ("Μαρία Γεωργίου", "maria georgiou"),
            # Arabic characters (RTL script)
            ("محمد الأحمد", "mhmd l'hmd"),
            # Chinese characters
            ("李小明", "li xiao ming"),
            ("王美麗", "wang mei li"),
            # Japanese characters (Hiragana and Katakana)
            ("たなか ひろし", "tanaka hiroshi"),
            ("サトウ ユキ", "satou yuki"),
            # Korean characters
            ("김철수", "gimceolsu"),
            ("박영희", "bagyeonghyi"),
            # Mixed scripts
            ("John 李", "john li"),
            ("María Мария", "maria mariia"),
            # Special diacritics and combined characters
            ("Naïve café", "naive cafe"),
            ("Montréal Québec", "montreal quebec"),
            ("Håkon Ångström", "hakon angstrom"),
            # Vietnamese tonal marks
            ("Nguyễn Thị Hoa", "nguyen thi hoa"),
            ("Trần Văn Phúc", "tran van phuc"),
            # Turkish specific characters
            ("İstanbul Öğretmen", "istanbul ogretmen"),
            ("Çağlar Şimşek", "caglar simsek"),
            # Combined diacritical marks
            ("Zoë Chloë", "zoe chloe"),
            ("Noël Citroën", "noel citroen"),
            # Ligatures and special combinations
            ("æther Œuvre", "aether oeuvre"),
            ("ﬁle ﬂag", "file flag"),
        ],
    )
    def test_normalize_name_unicode(self, input_name, expected):
        """Test name normalization with unicode characters."""
        assert normalize_name(input_name) == expected

    @pytest.mark.parametrize(
        "query,candidates,expected",
        [
            # Exact match
            (
                "Charlie Wilson",
                ["Charlie Wilson", "Dana Rodriguez", "Emma Thompson"],
                "Charlie Wilson",
            ),
            # Case insensitive
            (
                "charlie wilson",
                ["Charlie Wilson", "Dana Rodriguez", "Emma Thompson"],
                "Charlie Wilson",
            ),
            # With accents - exact match
            (
                "José María",
                ["José María", "François Côté", "Dana Rodriguez"],
                "José María",
            ),
            # With accents - without accents input
            (
                "Jose Maria",
                ["José María", "François Côté", "Dana Rodriguez"],
                "José María",
            ),
            # No good match
            (
                "Completely Different Name",
                ["Charlie Wilson", "Dana Rodriguez", "Emma Thompson"],
                None,
            ),
        ],
    )
    def test_find_best_name_match_basic(self, query, candidates, expected):
        """Test basic fuzzy name matching."""
        assert find_best_name_match(query, candidates) == expected

    @pytest.mark.parametrize(
        "query,candidates,threshold,expected",
        [
            # Partial match above threshold
            (
                "Charlie",
                ["Charlie Wilson", "Dana Rodriguez", "Emma Thompson"],
                50,
                "Charlie Wilson",
            ),
            # Partial match below threshold
            ("Char", ["Charlie Wilson", "Dana Rodriguez", "Emma Thompson"], 60, None),
            # International partial matches
            (
                "José María",
                ["José María González", "François Müller", "Björn Åström"],
                60,
                "José María González",
            ),
            (
                "Dvorak",
                ["José María González", "François Müller", "Václav Dvořák"],
                60,
                "Václav Dvořák",
            ),
        ],
    )
    def test_find_best_name_match_with_threshold(
        self, query, candidates, threshold, expected
    ):
        """Test fuzzy name matching with custom threshold."""
        assert find_best_name_match(query, candidates, threshold=threshold) == expected

    @pytest.mark.parametrize(
        "query,candidates,expected",
        [
            # International exact matches with accents
            (
                "José María González",
                [
                    "José María González",
                    "François Müller",
                    "Björn Åström",
                    "Václav Dvořák",
                ],
                "José María González",
            ),
            # International matches without accents
            (
                "Jose Maria Gonzalez",
                [
                    "José María González",
                    "François Müller",
                    "Björn Åström",
                    "Václav Dvořák",
                ],
                "José María González",
            ),
            (
                "Francois Muller",
                [
                    "José María González",
                    "François Müller",
                    "Björn Åström",
                    "Václav Dvořák",
                ],
                "François Müller",
            ),
            (
                "Bjorn Astrom",
                [
                    "José María González",
                    "François Müller",
                    "Björn Åström",
                    "Václav Dvořák",
                ],
                "Björn Åström",
            ),
            (
                "Vaclav Dvorak",
                [
                    "José María González",
                    "François Müller",
                    "Björn Åström",
                    "Václav Dvořák",
                ],
                "Václav Dvořák",
            ),
            # Case variations
            (
                "JOSÉ MARÍA GONZÁLEZ",
                [
                    "José María González",
                    "François Müller",
                    "Björn Åström",
                    "Václav Dvořák",
                ],
                "José María González",
            ),
            (
                "françois müller",
                [
                    "José María González",
                    "François Müller",
                    "Björn Åström",
                    "Václav Dvořák",
                ],
                "François Müller",
            ),
            # Hyphenated and compound names
            (
                "van der berg",
                ["Van Der Berg", "O'Connor-Smith", "MacLeod", "de la Cruz"],
                "Van Der Berg",
            ),
            (
                "macleod",
                ["Van Der Berg", "O'Connor-Smith", "MacLeod", "de la Cruz"],
                "MacLeod",
            ),
            (
                "de la cruz",
                ["Van Der Berg", "O'Connor-Smith", "MacLeod", "de la Cruz"],
                "de la Cruz",
            ),
        ],
    )
    def test_find_best_name_match_international(self, query, candidates, expected):
        """Test fuzzy name matching with international names."""
        assert find_best_name_match(query, candidates) == expected

    @pytest.mark.parametrize(
        "query,candidates,threshold,expected",
        [
            # Compound name with threshold and partial similarity
            (
                "O'Connor Smith",
                ["Van Der Berg", "O'Connor-Smith", "MacLeod", "de la Cruz"],
                80,
                "O'Connor-Smith",
            ),
        ],
    )
    def test_find_best_name_match_compound_with_threshold(
        self, query, candidates, threshold, expected
    ):
        """Test fuzzy name matching with compound names and threshold."""
        assert find_best_name_match(query, candidates, threshold=threshold) == expected


class TestSubmissionParsing:
    """Test submission folder parsing functions."""

    def test_parse_submission_folder_name(self):
        """Test parsing submission folder names."""
        # Standard format
        folder_name = "152711-351765 - Charlie Wilson - May 18, 2025 1224 PM"
        name, timestamp = parse_submission_folder_name(folder_name)

        assert name == "Charlie Wilson"
        assert timestamp == datetime(2025, 5, 18, 12, 24)

        # AM time
        folder_name = "123456-789012 - Dana Rodriguez - June 15, 2025 930 AM"
        name, timestamp = parse_submission_folder_name(folder_name)

        assert name == "Dana Rodriguez"
        assert timestamp == datetime(2025, 6, 15, 9, 30)

        # 12 PM (noon)
        folder_name = "123456-789012 - Test Student - July 4, 2025 1200 PM"
        name, timestamp = parse_submission_folder_name(folder_name)

        assert timestamp == datetime(2025, 7, 4, 12, 0)

        # 12 AM (midnight)
        folder_name = "123456-789012 - Test Student - July 4, 2025 1200 AM"
        name, timestamp = parse_submission_folder_name(folder_name)

        assert timestamp == datetime(2025, 7, 4, 0, 0)

    def test_parse_submission_folder_name_invalid(self):
        """Test parsing invalid folder names."""
        with pytest.raises(ValueError):
            parse_submission_folder_name("Invalid folder name")

        with pytest.raises(ValueError):
            parse_submission_folder_name(
                "123-456 - Name - InvalidMonth 1, 2025 1200 PM"
            )


class TestFileOperations:
    """Test file extraction and preparation functions."""

    def test_extract_submissions(self, tmp_path):
        """Test extracting submissions ZIP file."""
        # Create a test ZIP file with submission folders
        zip_path = tmp_path / "submissions.zip"

        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr(
                "152711-351765 - Charlie Wilson - May 18, 2025 1224 PM/Test.java",
                "// Java code",
            )
            zip_file.writestr(
                "123456-789012 - Dana Rodriguez - June 15, 2025 930 AM/Test.java",
                "// Java code",
            )

        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        submissions_dir = extract_submissions(zip_path, temp_dir)

        assert submissions_dir.exists()
        assert (
            submissions_dir / "152711-351765 - Charlie Wilson - May 18, 2025 1224 PM"
        ).exists()
        assert (
            submissions_dir / "123456-789012 - Dana Rodriguez - June 15, 2025 930 AM"
        ).exists()

    def test_prepare_grading_directory_with_java_files(self, tmp_path):
        """Test preparing grading directory with Java files."""
        submission_dir = tmp_path / "submission"
        submission_dir.mkdir()

        # Create test Java files
        (submission_dir / "Test.java").write_text("public class Test {}")
        (submission_dir / "Helper.java").write_text("public class Helper {}")

        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        writer = Writer(verbose=False)
        grading_dir = prepare_grading_directory(submission_dir, temp_dir, writer)

        assert grading_dir.exists()
        assert (grading_dir / "Test.java").exists()
        assert (grading_dir / "Helper.java").exists()

    def test_prepare_grading_directory_with_zip_files(self, tmp_path):
        """Test preparing grading directory with ZIP files."""
        submission_dir = tmp_path / "submission"
        submission_dir.mkdir()

        # Create a ZIP file with Java files
        zip_path = submission_dir / "code.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("src/Test.java", "public class Test {}")
            zip_file.writestr("src/Helper.java", "public class Helper {}")
            zip_file.writestr("README.txt", "Not a Java file")

        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        writer = Writer(verbose=False)
        grading_dir = prepare_grading_directory(submission_dir, temp_dir, writer)

        assert grading_dir.exists()
        assert (grading_dir / "Test.java").exists()
        assert (grading_dir / "Helper.java").exists()
        assert not (
            grading_dir / "README.txt"
        ).exists()  # Should only extract Java files


class TestGradingWorkflow:
    """Test the complete grading workflow functions."""

    def test_find_latest_submissions(self, tmp_path):
        """Test finding latest submissions for students."""
        # Create test submissions directory
        submissions_dir = tmp_path / "submissions"
        submissions_dir.mkdir()

        # Create submission folders with different timestamps
        (
            submissions_dir / "152711-351765 - Charlie Wilson - May 18, 2025 1224 PM"
        ).mkdir()
        (
            submissions_dir / "152711-351765 - Charlie Wilson - May 18, 2025 1130 PM"
        ).mkdir()  # Later
        (
            submissions_dir / "123456-789012 - Dana Rodriguez - June 15, 2025 930 AM"
        ).mkdir()

        # Create test DataFrame
        grading_data = {
            "OrgDefinedId": ["300069634", "300173416"],
            "Username": ["CWILS001", "DRODR002"],
            "Last Name": ["Wilson", "Rodriguez"],
            "First Name": ["Charlie", "Dana"],
            "Lab Grade": ["", ""],
        }
        grading_df = pd.DataFrame(grading_data)

        writer = Writer(verbose=False)
        latest_submissions = find_latest_submissions(
            submissions_dir, grading_df, writer
        )

        # Should find 2 students
        assert len(latest_submissions) == 2

        # Should pick the later submission for Charlie
        charlie_submission = None
        for _, (record, path) in latest_submissions.items():
            if record.first_name == "Charlie":
                charlie_submission = path
                break

        assert charlie_submission is not None
        assert "1130 PM" in charlie_submission.name  # Later time

    def test_save_results_to_csv(self, tmp_path):
        """Test saving results to CSV."""
        # Create original DataFrame
        original_data = {
            "OrgDefinedId": ["300069634", "300173416"],
            "Username": ["CWILS001", "DRODR002"],
            "Last Name": ["Wilson", "Rodriguez"],
            "First Name": ["Charlie", "Dana"],
            "Lab Grade": ["", ""],
            "End-of-Line Indicator": ["#", "#"],
        }
        original_df = pd.DataFrame(original_data)

        # Create test results
        student1 = StudentRecord("300069634", "CWILS001", "Wilson", "Charlie")
        student2 = StudentRecord("300173416", "DRODR002", "Rodriguez", "Dana")

        results = [
            GradingResult(student1, 0.85, success=True),
            GradingResult(
                student2, 0.0, error_message="Compilation failed", success=False
            ),
        ]

        output_path = tmp_path / "results.csv"

        # Test with failure as 0
        save_results_to_csv(results, original_df, output_path, failure_is_null=False)

        with open(output_path, "r") as f:
            content = f.read()

        assert "0.850" in content  # Charlie's grade
        assert "0.000" in content  # Dana's failed grade

        # Test with failure as null
        save_results_to_csv(results, original_df, output_path, failure_is_null=True)

        with open(output_path, "r") as f:
            lines = f.readlines()

        # Dana's grade should be empty
        dana_line = [line for line in lines if "DRODR002" in line][0]
        parts = dana_line.split(",")
        grade_index = 2  # Lab Grade column
        assert parts[grade_index] == ""


class TestDataStructures:
    """Test data structure classes."""

    def test_student_record(self):
        """Test StudentRecord dataclass."""
        record = StudentRecord(
            org_defined_id="300069634",
            username="CWILS001",
            last_name="Wilson",
            first_name="Charlie",
        )

        assert record.org_defined_id == "300069634"
        assert record.username == "CWILS001"
        assert record.original_grade is None

    def test_submission(self):
        """Test Submission dataclass."""
        timestamp = datetime(2025, 5, 18, 12, 24)
        path = Path("/test/path")

        submission = Submission("Charlie Wilson", timestamp, path)

        assert submission.student_name == "Charlie Wilson"
        assert submission.timestamp == timestamp
        assert submission.folder_path == path

    def test_grading_result(self):
        """Test GradingResult dataclass."""
        student = StudentRecord(
            "300069634", "CWILS001", "Wilson", "Charlie", "cwils001@example.edu"
        )

        # Successful result
        result = GradingResult(student, 0.85, success=True)
        assert result.grade == 0.85
        assert result.success is True
        assert result.error_message is None

        # Failed result
        result = GradingResult(student, 0.0, error_message="Failed", success=False)
        assert result.grade == 0.0
        assert result.success is False
        assert result.error_message == "Failed"


# Integration tests would require actual test files and more complex setup
class TestIntegration:
    """Integration tests for the bulk grader."""

    @pytest.mark.integration
    def test_end_to_end_workflow(self, tmp_path):
        """Test the complete end-to-end workflow."""
        # This test would require setting up:
        # 1. A complete submissions ZIP file
        # 2. Test files
        # 3. A grading list CSV
        # 4. Running the complete grading process
        #
        # Due to complexity, this is marked as an integration test
        # and would be implemented when the actual test files are available
        pytest.skip("Integration test requires full test setup")


if __name__ == "__main__":
    pytest.main([__file__])
