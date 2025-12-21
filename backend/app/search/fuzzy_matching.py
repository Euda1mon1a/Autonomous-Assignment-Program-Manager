"""
Fuzzy matching service for text similarity and deduplication.

Provides multiple fuzzy matching algorithms:
- Levenshtein distance for edit distance similarity
- Soundex for phonetic matching
- Metaphone for advanced phonetic matching
- N-gram similarity for partial string matching
- Combined scoring using weighted algorithms
"""

import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.person import Person
from app.schemas.fuzzy_matching import (
    BatchFuzzyMatchRequest,
    BatchFuzzyMatchResponse,
    BatchFuzzyMatchResult,
    DeduplicationRequest,
    DeduplicationResponse,
    DuplicateGroup,
    FuzzyMatchAlgorithm,
    FuzzyMatchConfig,
    FuzzyMatchRequest,
    FuzzyMatchResponse,
    FuzzyMatchResult,
    MatchConfidenceBreakdown,
    NameMatchRequest,
    NameMatchResponse,
    NameMatchResult,
)


class FuzzyMatcher:
    """
    Comprehensive fuzzy matching service.

    Implements multiple string similarity algorithms with configurable
    thresholds, weights, and matching strategies. Optimized for name
    matching and deduplication use cases.
    """

    def __init__(self, config: Optional[FuzzyMatchConfig] = None):
        """
        Initialize the fuzzy matcher.

        Args:
            config: Optional configuration for matching behavior.
                   Uses defaults if not provided.
        """
        self.config = config or FuzzyMatchConfig()
        self._validate_config()

        # Common nickname mappings for name matching
        self.nickname_map = {
            'robert': ['bob', 'rob', 'bobby'],
            'william': ['bill', 'will', 'billy'],
            'james': ['jim', 'jimmy'],
            'richard': ['dick', 'rick', 'ricky'],
            'michael': ['mike', 'mikey'],
            'david': ['dave', 'davy'],
            'joseph': ['joe', 'joey'],
            'thomas': ['tom', 'tommy'],
            'christopher': ['chris'],
            'matthew': ['matt'],
            'elizabeth': ['liz', 'beth', 'betsy', 'lizzy'],
            'jennifer': ['jen', 'jenny'],
            'katherine': ['kate', 'katie', 'kathy'],
            'margaret': ['maggie', 'meg', 'peggy'],
            'patricia': ['pat', 'patty', 'tricia'],
            'susan': ['sue', 'susie'],
            'barbara': ['barb', 'babs'],
            'charles': ['charlie', 'chuck'],
            'daniel': ['dan', 'danny'],
            'anthony': ['tony'],
            'nicholas': ['nick'],
            'alexander': ['alex'],
        }

    def _validate_config(self) -> None:
        """Validate configuration weights sum appropriately."""
        total_weight = (
            self.config.levenshtein_weight +
            self.config.soundex_weight +
            self.config.metaphone_weight +
            self.config.ngram_weight
        )
        if not (0.99 <= total_weight <= 1.01):  # Allow small floating point error
            raise ValueError(
                f"Algorithm weights must sum to 1.0, got {total_weight}. "
                f"Adjust levenshtein_weight, soundex_weight, metaphone_weight, and ngram_weight."
            )

    def match(self, request: FuzzyMatchRequest) -> FuzzyMatchResponse:
        """
        Perform fuzzy matching on a query against candidate strings.

        Args:
            request: Fuzzy match request with query, candidates, and options

        Returns:
            FuzzyMatchResponse with matched results and metadata
        """
        start_time = time.time()

        # Normalize inputs
        query = self._normalize(request.query) if not request.case_sensitive else request.query
        candidates = [
            self._normalize(c) if not request.case_sensitive else c
            for c in request.candidates
        ]

        # Compute matches
        matches = []
        for candidate in candidates:
            score, algorithm_scores = self._compute_similarity(
                query,
                candidate,
                request.algorithm
            )

            if score >= request.threshold:
                confidence = self._compute_confidence(
                    query,
                    candidate,
                    score,
                    algorithm_scores
                )

                matches.append({
                    'value': candidate,
                    'score': score,
                    'confidence': confidence,
                    'algorithm_scores': algorithm_scores,
                })

        # Sort by score (descending)
        matches.sort(key=lambda x: x['score'], reverse=True)

        # Limit results
        matches = matches[:request.max_results]

        # Add rank
        ranked_matches = [
            FuzzyMatchResult(rank=idx + 1, **match)
            for idx, match in enumerate(matches)
        ]

        execution_time = (time.time() - start_time) * 1000  # Convert to ms

        return FuzzyMatchResponse(
            query=request.query,
            matches=ranked_matches,
            total_candidates=len(candidates),
            total_matches=len(ranked_matches),
            algorithm=request.algorithm,
            threshold=request.threshold,
            execution_time_ms=execution_time,
        )

    def match_names(
        self,
        db: Session,
        request: NameMatchRequest
    ) -> NameMatchResponse:
        """
        Match person names with specialized name matching logic.

        Includes support for nickname matching, phonetic similarity,
        and partial name matching (first/last name separately).

        Args:
            db: Database session
            request: Name match request

        Returns:
            NameMatchResponse with matched person entities
        """
        start_time = time.time()

        # Normalize query
        query = self._normalize(request.query)
        query_tokens = query.split()

        # Build database query
        db_query = db.query(Person)

        # Filter by entity type
        if request.entity_type == 'faculty':
            db_query = db_query.filter(Person.type == 'faculty')
        elif request.entity_type == 'resident':
            db_query = db_query.filter(Person.type == 'resident')

        # Get all persons
        persons = db_query.all()

        matches = []

        for person in persons:
            name = self._normalize(person.name)
            name_tokens = name.split()

            # Try different matching strategies
            match_type = None
            score = 0.0
            algorithm_scores = {}

            # 1. Exact match
            if query == name:
                match_type = 'exact'
                score = 1.0
                algorithm_scores = {'exact': 1.0}

            # 2. Fuzzy match on full name
            elif not match_type:
                score, algorithm_scores = self._compute_similarity(
                    query,
                    name,
                    FuzzyMatchAlgorithm.COMBINED
                )
                if score >= request.threshold:
                    match_type = 'fuzzy'

            # 3. Phonetic match (if enabled)
            if request.include_phonetic and score < request.threshold:
                phonetic_score = self._phonetic_similarity(query, name)
                if phonetic_score >= request.threshold:
                    match_type = 'phonetic'
                    score = phonetic_score
                    algorithm_scores = {'phonetic': phonetic_score}

            # 4. Nickname match (if enabled)
            if request.include_nicknames and score < request.threshold:
                nickname_score = self._nickname_similarity(query_tokens, name_tokens)
                if nickname_score >= request.threshold:
                    match_type = 'nickname'
                    score = nickname_score
                    algorithm_scores = {'nickname': nickname_score}

            # 5. Partial name match (first or last name)
            if score < request.threshold and len(query_tokens) == 1:
                # Check if query matches any part of the name
                for token in name_tokens:
                    token_score, token_algo_scores = self._compute_similarity(
                        query,
                        token,
                        FuzzyMatchAlgorithm.COMBINED
                    )
                    if token_score >= request.threshold:
                        match_type = 'partial'
                        score = token_score * 0.9  # Slight penalty for partial match
                        algorithm_scores = token_algo_scores
                        break

            # Add match if score meets threshold
            if score >= request.threshold and match_type:
                confidence = self._compute_confidence(
                    query,
                    name,
                    score,
                    algorithm_scores
                )

                matches.append(
                    NameMatchResult(
                        id=person.id,
                        name=person.name,
                        score=score,
                        confidence=confidence,
                        entity_type=person.type,
                        match_type=match_type,
                        metadata={
                            'email': person.email,
                            'pgy_level': person.pgy_level,
                            'faculty_role': person.faculty_role,
                        }
                    )
                )

        # Sort by score
        matches.sort(key=lambda x: x.score, reverse=True)

        # Limit results
        matches = matches[:request.max_results]

        execution_time = (time.time() - start_time) * 1000

        return NameMatchResponse(
            query=request.query,
            matches=matches,
            total_matches=len(matches),
            execution_time_ms=execution_time,
        )

    def deduplicate(self, request: DeduplicationRequest) -> DeduplicationResponse:
        """
        Perform fuzzy deduplication on a list of items.

        Identifies and removes duplicates based on similarity threshold,
        keeping either the first occurrence or highest quality item.

        Args:
            request: Deduplication request with items and options

        Returns:
            DeduplicationResponse with deduplicated items and duplicate groups
        """
        start_time = time.time()

        if not request.items:
            return DeduplicationResponse(
                original_count=0,
                deduplicated_count=0,
                duplicates_removed=0,
                unique_items=[],
                duplicate_groups=[],
                execution_time_ms=0.0,
            )

        # Normalize items
        items = [self._normalize(item) for item in request.items]

        # Track unique items and duplicate groups
        unique_items = []
        duplicate_groups = []
        processed_indices = set()

        for i, item in enumerate(items):
            if i in processed_indices:
                continue

            # This item becomes a canonical representative
            duplicates = []
            similarity_scores = {}

            # Check remaining items for duplicates
            for j in range(i + 1, len(items)):
                if j in processed_indices:
                    continue

                score, _ = self._compute_similarity(
                    item,
                    items[j],
                    request.algorithm
                )

                if score >= request.threshold:
                    duplicates.append(items[j])
                    similarity_scores[items[j]] = score
                    processed_indices.add(j)

            # Add to unique items
            unique_items.append(item)
            processed_indices.add(i)

            # Record duplicate group if duplicates were found
            if duplicates:
                duplicate_groups.append(
                    DuplicateGroup(
                        canonical=item,
                        duplicates=duplicates,
                        similarity_scores=similarity_scores,
                    )
                )

        execution_time = (time.time() - start_time) * 1000

        return DeduplicationResponse(
            original_count=len(items),
            deduplicated_count=len(unique_items),
            duplicates_removed=len(items) - len(unique_items),
            unique_items=unique_items,
            duplicate_groups=duplicate_groups,
            execution_time_ms=execution_time,
        )

    def batch_match(
        self,
        request: BatchFuzzyMatchRequest
    ) -> BatchFuzzyMatchResponse:
        """
        Perform batch fuzzy matching for multiple queries.

        Efficiently matches multiple queries against a set of candidates,
        returning results for each query with performance statistics.

        Args:
            request: Batch fuzzy match request

        Returns:
            BatchFuzzyMatchResponse with results for all queries
        """
        start_time = time.time()

        results = []
        total_matches = 0
        successful_queries = 0

        for query in request.queries:
            # Create individual match request
            match_request = FuzzyMatchRequest(
                query=query,
                candidates=request.candidates,
                algorithm=request.algorithm,
                threshold=request.threshold,
                max_results=request.max_results_per_query,
            )

            # Perform match
            match_response = self.match(match_request)

            # Determine best match
            best_match = match_response.matches[0] if match_response.matches else None

            # Track statistics
            if match_response.matches:
                successful_queries += 1
                total_matches += len(match_response.matches)

            results.append(
                BatchFuzzyMatchResult(
                    query=query,
                    matches=match_response.matches,
                    best_match=best_match,
                )
            )

        execution_time = (time.time() - start_time) * 1000
        avg_time = execution_time / len(request.queries) if request.queries else 0.0

        return BatchFuzzyMatchResponse(
            results=results,
            total_queries=len(request.queries),
            total_matches=total_matches,
            successful_queries=successful_queries,
            failed_queries=len(request.queries) - successful_queries,
            execution_time_ms=execution_time,
            avg_time_per_query_ms=avg_time,
        )

    # ===== PRIVATE HELPER METHODS =====

    def _normalize(self, text: str) -> str:
        """
        Normalize text for comparison.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        if self.config.normalize_whitespace:
            text = ' '.join(text.split())

        if self.config.remove_punctuation:
            text = re.sub(r'[^\w\s]', '', text)

        if not self.config.case_sensitive:
            text = text.lower()

        return text.strip()

    def _compute_similarity(
        self,
        str1: str,
        str2: str,
        algorithm: str
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute similarity score using specified algorithm.

        Args:
            str1: First string
            str2: Second string
            algorithm: Algorithm to use

        Returns:
            Tuple of (overall_score, algorithm_scores_dict)
        """
        algorithm_scores = {}

        if algorithm == FuzzyMatchAlgorithm.LEVENSHTEIN:
            score = self._levenshtein_similarity(str1, str2)
            algorithm_scores['levenshtein'] = score
            return score, algorithm_scores

        elif algorithm == FuzzyMatchAlgorithm.SOUNDEX:
            score = self._soundex_similarity(str1, str2)
            algorithm_scores['soundex'] = score
            return score, algorithm_scores

        elif algorithm == FuzzyMatchAlgorithm.METAPHONE:
            score = self._metaphone_similarity(str1, str2)
            algorithm_scores['metaphone'] = score
            return score, algorithm_scores

        elif algorithm == FuzzyMatchAlgorithm.NGRAM:
            score = self._ngram_similarity(str1, str2)
            algorithm_scores['ngram'] = score
            return score, algorithm_scores

        elif algorithm == FuzzyMatchAlgorithm.COMBINED:
            # Compute all scores
            lev_score = self._levenshtein_similarity(str1, str2)
            soundex_score = self._soundex_similarity(str1, str2)
            metaphone_score = self._metaphone_similarity(str1, str2)
            ngram_score = self._ngram_similarity(str1, str2)

            algorithm_scores = {
                'levenshtein': lev_score,
                'soundex': soundex_score,
                'metaphone': metaphone_score,
                'ngram': ngram_score,
            }

            # Weighted combination
            combined_score = (
                lev_score * self.config.levenshtein_weight +
                soundex_score * self.config.soundex_weight +
                metaphone_score * self.config.metaphone_weight +
                ngram_score * self.config.ngram_weight
            )

            algorithm_scores['combined'] = combined_score
            return combined_score, algorithm_scores

        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    def _levenshtein_similarity(self, str1: str, str2: str) -> float:
        """
        Compute Levenshtein distance-based similarity.

        Uses dynamic programming to compute edit distance, then
        normalizes to similarity score (0.0-1.0).

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score (0.0-1.0)
        """
        if str1 == str2:
            return 1.0

        if not str1 or not str2:
            return 0.0

        # Compute Levenshtein distance
        len1, len2 = len(str1), len(str2)
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j

        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if str1[i - 1] == str2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],      # Deletion
                        dp[i][j - 1],      # Insertion
                        dp[i - 1][j - 1]   # Substitution
                    )

        distance = dp[len1][len2]
        max_len = max(len1, len2)

        # Convert distance to similarity
        similarity = 1.0 - (distance / max_len) if max_len > 0 else 0.0

        return max(0.0, min(1.0, similarity))

    def _soundex(self, text: str) -> str:
        """
        Compute Soundex phonetic encoding.

        Soundex is a phonetic algorithm that indexes names by sound,
        as pronounced in English.

        Args:
            text: Text to encode

        Returns:
            Soundex code (e.g., "S530" for "Smith")
        """
        if not text:
            return ""

        text = text.upper()

        # Remove non-alphabetic characters
        text = re.sub(r'[^A-Z]', '', text)

        if not text:
            return ""

        # Soundex digit mapping
        soundex_map = {
            'B': '1', 'F': '1', 'P': '1', 'V': '1',
            'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
            'D': '3', 'T': '3',
            'L': '4',
            'M': '5', 'N': '5',
            'R': '6'
        }

        # Keep first letter
        soundex = text[0]

        # Process remaining letters
        prev_code = soundex_map.get(text[0], '0')

        for char in text[1:]:
            code = soundex_map.get(char, '0')

            # Skip vowels and duplicate codes
            if code != '0' and code != prev_code:
                soundex += code
                prev_code = code

            if len(soundex) == 4:
                break

        # Pad with zeros if needed
        soundex = soundex.ljust(4, '0')

        return soundex[:4]

    def _soundex_similarity(self, str1: str, str2: str) -> float:
        """
        Compute similarity based on Soundex encoding.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score (1.0 if soundex codes match, 0.0 otherwise)
        """
        # Only use soundex for strings of sufficient length
        if len(str1) < self.config.min_length_for_phonetic or \
           len(str2) < self.config.min_length_for_phonetic:
            return 0.0

        soundex1 = self._soundex(str1)
        soundex2 = self._soundex(str2)

        if soundex1 == soundex2:
            return 1.0

        # Partial match on soundex codes
        matches = sum(c1 == c2 for c1, c2 in zip(soundex1, soundex2))
        return matches / 4.0

    def _metaphone(self, text: str) -> str:
        """
        Compute Metaphone phonetic encoding.

        Metaphone is more accurate than Soundex for English words,
        especially for matching names.

        Args:
            text: Text to encode

        Returns:
            Metaphone code
        """
        if not text:
            return ""

        text = text.upper()
        text = re.sub(r'[^A-Z]', '', text)

        if not text:
            return ""

        # Simplified Metaphone implementation
        # (Full implementation is complex; this is a basic version)
        metaphone = ""

        # Handle leading characters
        if text.startswith('KN'):
            text = text[1:]
        elif text.startswith('GN'):
            text = text[1:]
        elif text.startswith('PN'):
            text = text[1:]
        elif text.startswith('AE'):
            text = 'E' + text[2:]
        elif text.startswith('WR'):
            text = text[1:]
        elif text.startswith('X'):
            text = 'S' + text[1:]

        prev_char = ''
        for i, char in enumerate(text):
            if len(metaphone) >= 4:
                break

            # Skip duplicate letters (except C)
            if char == prev_char and char != 'C':
                continue

            # Vowels
            if char in 'AEIOU':
                if i == 0:
                    metaphone += char
            # Consonants
            elif char == 'B':
                if i == len(text) - 1 and prev_char == 'M':
                    pass  # Silent B
                else:
                    metaphone += 'B'
            elif char == 'C':
                if i + 1 < len(text) and text[i + 1] in 'IEY':
                    metaphone += 'S'
                elif i + 1 < len(text) and text[i:i + 2] == 'CH':
                    metaphone += 'X'
                else:
                    metaphone += 'K'
            elif char == 'D':
                if i + 2 < len(text) and text[i:i + 3] in ['DGE', 'DGI', 'DGY']:
                    metaphone += 'J'
                else:
                    metaphone += 'T'
            elif char == 'G':
                if i + 1 < len(text) and text[i + 1] in 'IEY':
                    metaphone += 'J'
                elif i + 1 < len(text) and text[i + 1] == 'H':
                    pass  # Silent GH
                else:
                    metaphone += 'K'
            elif char == 'H':
                if i == 0 or text[i - 1] not in 'AEIOU':
                    metaphone += 'H'
            elif char == 'K':
                if i > 0 and text[i - 1] != 'C':
                    metaphone += 'K'
            elif char == 'P':
                if i + 1 < len(text) and text[i + 1] == 'H':
                    metaphone += 'F'
                else:
                    metaphone += 'P'
            elif char == 'Q':
                metaphone += 'K'
            elif char == 'S':
                if i + 2 < len(text) and text[i:i + 3] in ['SIO', 'SIA']:
                    metaphone += 'X'
                elif i + 1 < len(text) and text[i + 1] == 'H':
                    metaphone += 'X'
                else:
                    metaphone += 'S'
            elif char == 'T':
                if i + 2 < len(text) and text[i:i + 3] in ['TIO', 'TIA']:
                    metaphone += 'X'
                elif i + 1 < len(text) and text[i + 1] == 'H':
                    metaphone += '0'
                elif i + 1 < len(text) and text[i:i + 2] != 'TCH':
                    metaphone += 'T'
            elif char == 'V':
                metaphone += 'F'
            elif char == 'W':
                if i + 1 < len(text) and text[i + 1] in 'AEIOU':
                    metaphone += 'W'
            elif char == 'X':
                metaphone += 'KS'
            elif char == 'Y':
                if i + 1 < len(text) and text[i + 1] in 'AEIOU':
                    metaphone += 'Y'
            elif char == 'Z':
                metaphone += 'S'
            elif char in 'FLJMNR':
                metaphone += char

            prev_char = char

        return metaphone[:4]

    def _metaphone_similarity(self, str1: str, str2: str) -> float:
        """
        Compute similarity based on Metaphone encoding.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score (0.0-1.0)
        """
        # Only use metaphone for strings of sufficient length
        if len(str1) < self.config.min_length_for_phonetic or \
           len(str2) < self.config.min_length_for_phonetic:
            return 0.0

        metaphone1 = self._metaphone(str1)
        metaphone2 = self._metaphone(str2)

        if not metaphone1 or not metaphone2:
            return 0.0

        if metaphone1 == metaphone2:
            return 1.0

        # Partial match on metaphone codes
        max_len = max(len(metaphone1), len(metaphone2))
        matches = sum(
            c1 == c2
            for c1, c2 in zip(metaphone1, metaphone2)
        )
        return matches / max_len if max_len > 0 else 0.0

    def _ngram_similarity(self, str1: str, str2: str) -> float:
        """
        Compute N-gram similarity (Dice coefficient).

        Computes similarity based on shared character n-grams,
        useful for partial string matching and typos.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score (0.0-1.0)
        """
        if str1 == str2:
            return 1.0

        if not str1 or not str2:
            return 0.0

        # Generate n-grams
        ngrams1 = self._generate_ngrams(str1, self.config.ngram_size)
        ngrams2 = self._generate_ngrams(str2, self.config.ngram_size)

        if not ngrams1 or not ngrams2:
            return 0.0

        # Dice coefficient
        intersection = ngrams1.intersection(ngrams2)
        dice = (2.0 * len(intersection)) / (len(ngrams1) + len(ngrams2))

        return dice

    def _generate_ngrams(self, text: str, n: int) -> Set[str]:
        """
        Generate character n-grams from text.

        Args:
            text: Input text
            n: Size of n-grams

        Returns:
            Set of n-grams
        """
        # Pad text for edge n-grams
        padded = ' ' * (n - 1) + text + ' ' * (n - 1)

        ngrams = set()
        for i in range(len(padded) - n + 1):
            ngrams.add(padded[i:i + n])

        return ngrams

    def _phonetic_similarity(self, str1: str, str2: str) -> float:
        """
        Combined phonetic similarity (Soundex + Metaphone).

        Args:
            str1: First string
            str2: Second string

        Returns:
            Average phonetic similarity score
        """
        soundex_score = self._soundex_similarity(str1, str2)
        metaphone_score = self._metaphone_similarity(str1, str2)

        return (soundex_score + metaphone_score) / 2.0

    def _nickname_similarity(
        self,
        query_tokens: List[str],
        name_tokens: List[str]
    ) -> float:
        """
        Check for nickname matches in names.

        Args:
            query_tokens: Query name tokens
            name_tokens: Candidate name tokens

        Returns:
            Similarity score (1.0 if nickname match found, 0.0 otherwise)
        """
        for query_token in query_tokens:
            query_lower = query_token.lower()

            # Check if query is a nickname of any name token
            for name_token in name_tokens:
                name_lower = name_token.lower()

                # Direct match
                if query_lower == name_lower:
                    return 1.0

                # Check nickname map
                if name_lower in self.nickname_map:
                    if query_lower in self.nickname_map[name_lower]:
                        return 0.95  # High score but not perfect

                # Reverse check (query is full name, name is nickname)
                if query_lower in self.nickname_map:
                    if name_lower in self.nickname_map[query_lower]:
                        return 0.95

        return 0.0

    def _compute_confidence(
        self,
        query: str,
        candidate: str,
        base_score: float,
        algorithm_scores: Dict[str, float]
    ) -> float:
        """
        Compute confidence score for a match.

        Confidence considers multiple factors beyond base similarity:
        - Length difference penalty
        - Phonetic bonus
        - Prefix matching bonus
        - Exact token matching bonus

        Args:
            query: Query string
            candidate: Candidate string
            base_score: Base similarity score
            algorithm_scores: Individual algorithm scores

        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = base_score

        # Length penalty
        len_diff = abs(len(query) - len(candidate))
        max_len = max(len(query), len(candidate))
        if max_len > 0:
            len_penalty = (len_diff / max_len) * 0.1
            confidence -= len_penalty

        # Phonetic bonus
        phonetic_score = (
            algorithm_scores.get('soundex', 0.0) +
            algorithm_scores.get('metaphone', 0.0)
        ) / 2.0
        if phonetic_score >= 0.8:
            confidence += 0.05

        # Prefix bonus
        min_len = min(len(query), len(candidate))
        if min_len >= 3:
            prefix_len = 0
            for i in range(min_len):
                if query[i] == candidate[i]:
                    prefix_len += 1
                else:
                    break
            if prefix_len >= 3:
                prefix_bonus = (prefix_len / min_len) * 0.1
                confidence += prefix_bonus

        # Exact token bonus
        query_tokens = set(query.split())
        candidate_tokens = set(candidate.split())
        common_tokens = query_tokens.intersection(candidate_tokens)
        if common_tokens:
            token_ratio = len(common_tokens) / max(len(query_tokens), len(candidate_tokens))
            confidence += token_ratio * 0.1

        # Ensure confidence is in valid range
        return max(0.0, min(1.0, confidence))


# Singleton instance for dependency injection
_fuzzy_matcher_instance: Optional[FuzzyMatcher] = None


def get_fuzzy_matcher(config: Optional[FuzzyMatchConfig] = None) -> FuzzyMatcher:
    """
    Get singleton instance of FuzzyMatcher.

    Args:
        config: Optional configuration (only used on first call)

    Returns:
        FuzzyMatcher instance
    """
    global _fuzzy_matcher_instance

    if _fuzzy_matcher_instance is None:
        _fuzzy_matcher_instance = FuzzyMatcher(config)

    return _fuzzy_matcher_instance
