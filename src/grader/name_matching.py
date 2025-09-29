"""Name normalization and matching utilities."""

from thefuzz import fuzz, process
from unidecode import unidecode


class Matcher:
    def __init__(self, threshold: int = 80):
        """
        Initialize the matcher with a threshold for fuzzy matching.

        Args:
            threshold: Minimum match score (0-100)
        """
        self.threshold = threshold

    def normalize_name(self, name: str) -> str:
        """
        Normalize a name for comparison by removing accents and converting to lowercase.

        Args:
            name: The name to normalize

        Returns:
            Normalized name
        """
        # Convert unicode characters to ASCII equivalents
        normalized = unidecode(name)
        # Convert to lowercase and remove extra whitespace
        normalized = " ".join(normalized.lower().split())
        return normalized

    def find_best_name_match(
        self, target_name: str, candidate_names: list[str]
    ) -> str | None:
        """
        Find the best matching name using fuzzy string matching.

        Args:
            target_name: The name to match against
            candidate_names: List of candidate names

        Returns:
            Best matching name or None if no good match found
        """
        normalized_target = self.normalize_name(target_name)
        normalized_candidates = [self.normalize_name(name) for name in candidate_names]

        # Try exact match first
        if normalized_target in normalized_candidates:
            idx = normalized_candidates.index(normalized_target)
            return candidate_names[idx]

        # Try fuzzy matching
        result = process.extractOne(  # type: ignore
            normalized_target, normalized_candidates, scorer=fuzz.ratio
        )
        if result and result[1] >= self.threshold:
            idx = normalized_candidates.index(result[0])
            return candidate_names[idx]

        return None
