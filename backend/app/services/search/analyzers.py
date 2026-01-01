"""Text analyzers for search preprocessing and tokenization.

Analyzers transform raw text into searchable tokens, handling:
- Tokenization (splitting text into words)
- Normalization (lowercasing, accent removal)
- Stemming (reducing words to root forms)
- Stopword removal (filtering common words)
- Domain-specific processing (medical terms, names)
"""

import re
from abc import ABC, abstractmethod
from typing import List, Set


class SearchAnalyzer(ABC):
    """Abstract base class for text analyzers."""

    @abstractmethod
    def analyze(self, text: str) -> list[str]:
        """
        Analyze text and return list of tokens.

        Args:
            text: Raw input text to analyze

        Returns:
            List of processed tokens suitable for searching
        """
        pass

    def _normalize(self, text: str) -> str:
        """
        Normalize text (lowercase, remove extra whitespace).

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _tokenize(self, text: str) -> list[str]:
        """
        Tokenize text into words.

        Args:
            text: Text to tokenize

        Returns:
            List of word tokens
        """
        # Split on word boundaries, keeping alphanumeric and hyphens
        tokens = re.findall(r"\b[\w-]+\b", text)
        return [t for t in tokens if len(t) > 0]


class StandardAnalyzer(SearchAnalyzer):
    """
    Standard analyzer with basic text processing.

    Features:
    - Lowercasing
    - Tokenization on word boundaries
    - Stopword removal
    - Minimum token length filtering
    """

    # Common English stopwords
    STOPWORDS: set[str] = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "he",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "that",
        "the",
        "to",
        "was",
        "will",
        "with",
    }

    def __init__(self, min_token_length: int = 2, remove_stopwords: bool = True) -> None:
        """
        Initialize standard analyzer.

        Args:
            min_token_length: Minimum length for tokens to keep
            remove_stopwords: Whether to remove stopwords
        """
        self.min_token_length = min_token_length
        self.remove_stopwords = remove_stopwords

    def analyze(self, text: str) -> list[str]:
        """
        Analyze text with standard processing.

        Args:
            text: Raw input text

        Returns:
            List of processed tokens
        """
        # Normalize and tokenize
        normalized = self._normalize(text)
        tokens = self._tokenize(normalized)

        # Filter by length
        tokens = [t for t in tokens if len(t) >= self.min_token_length]

        # Remove stopwords if enabled
        if self.remove_stopwords:
            tokens = [t for t in tokens if t not in self.STOPWORDS]

        return tokens


class PersonNameAnalyzer(SearchAnalyzer):
    """
    Specialized analyzer for person names.

    Features:
    - Preserves name structure (first, middle, last)
    - Handles prefixes (Dr., Col., etc.)
    - Generates n-grams for partial matching
    - Case-insensitive matching
    """

    # Common name prefixes to preserve
    PREFIXES: set[str] = {
        "dr",
        "md",
        "do",
        "col",
        "lt",
        "maj",
        "capt",
        "cpt",
        "ltc",
        "cdr",
        "lcdr",
        "lt col",
        "lt cdr",
    }

    def __init__(self, generate_ngrams: bool = True) -> None:
        """
        Initialize person name analyzer.

        Args:
            generate_ngrams: Whether to generate character n-grams for fuzzy matching
        """
        self.generate_ngrams = generate_ngrams

    def analyze(self, text: str) -> list[str]:
        """
        Analyze person name.

        Args:
            text: Person name text

        Returns:
            List of name tokens and n-grams
        """
        # Normalize
        normalized = self._normalize(text)
        tokens = self._tokenize(normalized)

        result = []

        # Add full tokens (preserve all parts of name)
        result.extend(tokens)

        # Add n-grams for fuzzy matching
        if self.generate_ngrams:
            for token in tokens:
                # Skip very short tokens and prefixes
                if len(token) >= 3 and token not in self.PREFIXES:
                    # Generate 3-grams for fuzzy matching
                    ngrams = self._generate_ngrams(token, n=3)
                    result.extend(ngrams)

        return result

    def _generate_ngrams(self, text: str, n: int = 3) -> list[str]:
        """
        Generate character n-grams from text.

        Args:
            text: Text to generate n-grams from
            n: N-gram size

        Returns:
            List of n-grams
        """
        if len(text) < n:
            return [text]

        ngrams = []
        for i in range(len(text) - n + 1):
            ngrams.append(text[i : i + n])
        return ngrams


class MedicalTermAnalyzer(SearchAnalyzer):
    """
    Specialized analyzer for medical and scheduling terms.

    Features:
    - Preserves medical abbreviations
    - Handles rotation names and specialty terms
    - Recognizes PGY levels, block types
    - Acronym expansion
    """

    # Medical and scheduling abbreviations to preserve
    MEDICAL_TERMS: set[str] = {
        "pgy",
        "pgy1",
        "pgy2",
        "pgy3",
        "fmit",
        "fm",
        "im",
        "obgyn",
        "peds",
        "psych",
        "er",
        "icu",
        "nicu",
        "picu",
        "acgme",
        "rrc",
        "cler",
        "clinic",
        "inpatient",
        "procedure",
        "conference",
        "am",
        "pm",
        "call",
        "tdy",
        "leave",
    }

    # Acronym expansions
    EXPANSIONS: dict = {
        "pgy": "post graduate year",
        "fmit": "family medicine inpatient training",
        "fm": "family medicine",
        "im": "internal medicine",
        "obgyn": "obstetrics gynecology",
        "peds": "pediatrics",
        "psych": "psychiatry",
        "er": "emergency room",
        "icu": "intensive care unit",
        "acgme": "accreditation council graduate medical education",
    }

    def __init__(self, expand_acronyms: bool = True) -> None:
        """
        Initialize medical term analyzer.

        Args:
            expand_acronyms: Whether to expand medical acronyms
        """
        self.expand_acronyms = expand_acronyms

    def analyze(self, text: str) -> list[str]:
        """
        Analyze medical/scheduling text.

        Args:
            text: Medical or scheduling term text

        Returns:
            List of processed tokens
        """
        # Normalize and tokenize
        normalized = self._normalize(text)
        tokens = self._tokenize(normalized)

        result = []

        for token in tokens:
            # Always include the original token
            result.append(token)

            # Expand acronyms if enabled and found
            if self.expand_acronyms and token in self.EXPANSIONS:
                expansion_tokens = self.EXPANSIONS[token].split()
                result.extend(expansion_tokens)

            # Handle PGY levels specially
            pgy_match = re.match(r"pgy-?(\d)", token)
            if pgy_match:
                level = pgy_match.group(1)
                result.extend(["pgy", level, f"pgy{level}"])

        return result


class FuzzyAnalyzer(SearchAnalyzer):
    """
    Analyzer with fuzzy matching capabilities.

    Features:
    - Phonetic encoding (Soundex)
    - Edit distance tolerance
    - Typo correction suggestions
    """

    def analyze(self, text: str) -> list[str]:
        """
        Analyze text with fuzzy matching support.

        Args:
            text: Raw input text

        Returns:
            List of tokens including fuzzy variants
        """
        # Normalize and tokenize
        normalized = self._normalize(text)
        tokens = self._tokenize(normalized)

        result = []

        for token in tokens:
            # Include original token
            result.append(token)

            # Add soundex encoding for phonetic matching
            if len(token) >= 3:
                soundex = self._soundex(token)
                if soundex:
                    result.append(soundex)

        return result

    def _soundex(self, word: str) -> str:
        """
        Generate Soundex phonetic encoding.

        Args:
            word: Word to encode

        Returns:
            Soundex code
        """
        if not word:
            return ""

        word = word.upper()

        # Soundex mapping
        soundex_map = {
            "B": "1",
            "F": "1",
            "P": "1",
            "V": "1",
            "C": "2",
            "G": "2",
            "J": "2",
            "K": "2",
            "Q": "2",
            "S": "2",
            "X": "2",
            "Z": "2",
            "D": "3",
            "T": "3",
            "L": "4",
            "M": "5",
            "N": "5",
            "R": "6",
        }

        # Keep first letter
        soundex = word[0]

        # Convert remaining letters
        for char in word[1:]:
            code = soundex_map.get(char, "0")
            if code != "0" and code != soundex[-1]:
                soundex += code

        # Pad with zeros to length 4
        soundex = (soundex + "000")[:4]

        return soundex
