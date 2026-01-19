"""
Analysis service that orchestrates feature extraction and contrastive model
to generate per-segment AI probability scores for heat map visualization.
Uses Ollama embeddings for improved accuracy.
"""
from typing import List, Dict, Optional
import numpy as np
import re
from collections import Counter
from app.ml.feature_extraction import (
    extract_feature_vector,
    extract_all_features,
    calculate_feature_importance,
    generate_feature_interpretation
)
from app.ml.contrastive_model import get_contrastive_model
from app.ml.fingerprint import compare_to_fingerprint
from app.ml.ollama_embeddings import get_ollama_embedding
from app.utils.text_processing import split_into_sentences, split_into_paragraphs
from app.utils.cache import (
    text_hash, get_cached_analysis, cache_analysis_result,
    get_cached_features, cache_features
)
from app.models.schemas import ConfidenceLevel


# Feature pattern descriptions for explanations
FEATURE_PATTERNS = {
    "low_burstiness": "consistent sentence lengths throughout",
    "low_perplexity": "predictable word choices and common phrases",
    "low_unique_words": "repetitive vocabulary",
    "low_rare_word_ratio": "lack of distinctive or uncommon vocabulary",
    "low_noun_ratio": "simplified grammatical structure",
    "low_verb_ratio": "limited action descriptions",
    "low_adjective_ratio": "minimal descriptive language",
    "low_bigram_diversity": "repetitive two-word phrases",
    "low_trigram_diversity": "repetitive three-word patterns",
    "high_bigram_repetition": "formulaic expression patterns",
    "high_trigram_repetition": "template-like phrasing",
    "low_lexical_overlap": "abrupt topic changes",
    "high_topic_consistency": "overly uniform topic focus",
    "low_transition_smoothness": "choppy paragraph transitions",
    "high_comma_ratio": "uniform sentence structures",
    "low_semicolon_ratio": "simplified punctuation patterns",
    "low_question_ratio": "lack of rhetorical variation",
    "high_flesch_reading_ease": "overly simplified readability",
    "low_flesch_kincaid_grade": "consistent complexity level"
}


class AnalysisService:
    """Service for analyzing text and generating heat map data"""
    
    def __init__(self):
        self.contrastive_model = get_contrastive_model()
    
    def analyze_text(
        self,
        text: str,
        granularity: str = "sentence",
        user_fingerprint: Optional[Dict] = None,
        user_id: int = None,
        use_cache: bool = True,
    ) -> Dict:
        """
        Analyze text and generate heat map data with AI probability scores.
        
        Uses Ollama embeddings in combination with stylometric features
        for more accurate AI probability estimation.
        
        Args:
            text: Text to analyze
            granularity: "sentence" or "paragraph"
            user_fingerprint: Optional user fingerprint for comparison
            user_id: Optional user ID for cache key
            use_cache: Whether to use caching (default: True)
        
        Returns:
            Dictionary with heat map data and overall AI probability
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Check cache first
        if use_cache:
            cache_key = text_hash(text + granularity)
            cached = get_cached_analysis(cache_key, user_id)
            if cached:
                return cached
        
        # Split text into segments
        if granularity == "sentence":
            segments = split_into_sentences(text)
        elif granularity == "paragraph":
            segments = split_into_paragraphs(text)
        else:
            raise ValueError(f"Invalid granularity: {granularity}. Must be 'sentence' or 'paragraph'")
        
        # Analyze each segment
        segment_results = []
        current_index = 0

        for segment in segments:
            if not segment.strip():
                continue

            # Extract stylometric features (used for heuristics and fingerprint path)
            segment_features = extract_feature_vector(segment)

            # Get Ollama embedding for this segment
            ollama_embedding = get_ollama_embedding(segment)

            # Calculate AI probability
            if user_fingerprint:
                # Compare to user's fingerprint
                similarity = compare_to_fingerprint(segment, user_fingerprint)
                # High similarity = human-like (low AI probability)
                # Low similarity = AI-like (high AI probability)
                ai_probability = 1.0 - similarity
            else:
                # Base stylometric heuristic
                base_ai_prob = self._estimate_ai_probability(segment_features)

                # Use Ollama embedding if available
                if ollama_embedding is not None:
                    # Use Ollama embedding magnitude as an additional signal
                    emb_norm = float(np.linalg.norm(ollama_embedding))
                    # Map norm to [0, 1] where smaller norm => more AI-like
                    norm_score = 1.0 / (1.0 + emb_norm)
                    # Blend stylometric heuristic with embedding-based score
                    ai_probability = float(
                        max(0.0, min(1.0, 0.7 * base_ai_prob + 0.3 * norm_score))
                    )
                else:
                    # Fallback to stylometric only if Ollama unavailable
                    ai_probability = base_ai_prob

            # Calculate feature attribution
            feature_attribution = self._generate_feature_attribution(
                segment, float(ai_probability)
            )

            # Find segment position in original text
            start_index = text.find(segment, current_index)
            if start_index == -1:
                start_index = current_index
            end_index = start_index + len(segment)
            current_index = end_index

            segment_results.append({
                "text": segment,
                "ai_probability": float(ai_probability),
                "start_index": start_index,
                "end_index": end_index,
                "confidence_level": self._calculate_confidence_level(float(ai_probability)),
                "feature_attribution": feature_attribution
            })
        
        # Calculate overall AI probability
        if segment_results:
            overall_ai_probability = np.mean([s["ai_probability"] for s in segment_results])
        else:
            overall_ai_probability = 0.5  # Default neutral

        # Calculate confidence distribution
        confidence_distribution = {
            "HIGH": sum(1 for s in segment_results if s["confidence_level"] == ConfidenceLevel.HIGH),
            "MEDIUM": sum(1 for s in segment_results if s["confidence_level"] == ConfidenceLevel.MEDIUM),
            "LOW": sum(1 for s in segment_results if s["confidence_level"] == ConfidenceLevel.LOW)
        }

        # Detect overused patterns
        overused_patterns = self.detect_overused_patterns(text, segment_results)

        # Build result dictionary
        result = {
            "segments": segment_results,
            "overall_ai_probability": float(overall_ai_probability),
            "confidence_distribution": confidence_distribution,
            "overused_patterns": overused_patterns,
            "granularity": granularity
        }

        # Generate document-level explanation
        result["document_explanation"] = self.generate_document_explanation(result)
        
        # Cache the result
        if use_cache:
            cache_analysis_result(cache_key, result, user_id)
        
        return result
    
    def _estimate_ai_probability(self, features: np.ndarray) -> float:
        """
        Estimate AI probability from features using heuristics.
        This is a fallback when no user fingerprint is available.

        Args:
            features: Feature vector

        Returns:
            AI probability (0 to 1)
        """
        # Simple heuristic based on feature values
        # Lower burstiness and perplexity = more AI-like
        # This is a simplified approach; in production, use the trained model

        # Normalize features to 0-1 range for this heuristic
        # Features: [burstiness, perplexity, rare_word_ratio, unique_word_ratio, ...]

        if len(features) < 2:
            return 0.5

        burstiness = features[0] if len(features) > 0 else 0.5
        perplexity = features[1] if len(features) > 1 else 0.5

        # AI text tends to have lower burstiness and more predictable patterns
        # Combine these into an AI probability score
        ai_score = (1.0 - burstiness) * 0.6 + (1.0 - min(perplexity / 100.0, 1.0)) * 0.4

        # Clamp to [0, 1]
        ai_probability = max(0.0, min(1.0, ai_score))

        return float(ai_probability)

    def _calculate_confidence_level(self, probability: float) -> ConfidenceLevel:
        """
        Calculate confidence level category from AI probability.

        Args:
            probability: AI probability (0 to 1)

        Returns:
            ConfidenceLevel enum value (HIGH, MEDIUM, or LOW)
        """
        if probability > 0.7:
            return ConfidenceLevel.HIGH
        elif probability >= 0.4:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def _generate_feature_attribution(
        self,
        segment: str,
        ai_probability: float
    ) -> List[Dict[str, any]]:
        """
        Generate feature attribution for a text segment.

        This identifies which stylometric features contributed most to the AI detection score
        and provides human-readable interpretations.

        Args:
            segment: The text segment (sentence or paragraph)
            ai_probability: The AI probability score for this segment

        Returns:
            List of feature attribution dicts with feature_name, importance, and interpretation
            Returns top 5 features by importance.
        """
        # Calculate feature importance
        importance_scores = calculate_feature_importance(segment, ai_probability)

        if not importance_scores:
            return []

        # Get top 5 features and generate interpretations
        feature_attribution = []
        for feature_name, importance in list(importance_scores.items())[:5]:
            # Extract raw feature value for interpretation
            all_features = extract_all_features(segment)
            feature_value = all_features.get(feature_name, 0.0)

            # Generate human-readable interpretation
            interpretation = generate_feature_interpretation(feature_name, feature_value)

            feature_attribution.append({
                "feature_name": feature_name,
                "importance": float(importance),
                "interpretation": interpretation
            })

        return feature_attribution

    def detect_overused_patterns(
        self,
        text: str,
        segments: List[Dict]
    ) -> List[Dict]:
        """
        Detect overused phrases and patterns in the text.

        Analyzes text for repetitive patterns across multiple dimensions:
        - Repeated phrases (2-4 word n-grams)
        - Sentence structure patterns (repeated starts)
        - Word repetition patterns (high-frequency words)

        Args:
            text: Full text to analyze
            segments: List of segment dictionaries with start_index/end_index

        Returns:
            List of detected patterns with locations, counts, and severity
        """
        patterns = []

        # Common stopwords to exclude from word repetition analysis
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can',
            'that', 'this', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how'
        }

        # 1. Detect repeated phrases (n-grams)
        patterns.extend(self._detect_repeated_phrases(text))

        # 2. Detect sentence structure patterns (repeated starts)
        patterns.extend(self._detect_sentence_starts(text, segments))

        # 3. Detect word repetition patterns
        patterns.extend(self._detect_word_repetition(text, stopwords))

        # Sort by severity (HIGH first) then by count
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        patterns.sort(key=lambda p: (severity_order.get(p['severity'], 3), -p['count']))

        return patterns

    def _detect_repeated_phrases(self, text: str) -> List[Dict]:
        """Detect repeated 2-4 word phrases appearing 3+ times."""
        patterns = []

        # Clean and tokenize text
        text_clean = text.lower()
        # Replace punctuation with spaces for phrase extraction
        text_clean = re.sub(r'[^\w\s]', ' ', text_clean)
        words = text_clean.split()

        if len(words) < 6:
            return patterns

        # Extract n-grams
        all_ngrams = []

        # 2-word phrases
        for i in range(len(words) - 1):
            phrase = ' '.join(words[i:i+2])
            # Find original position in text
            original_phrase = ' '.join(text.lower().split()[i:i+2])
            start_idx = text.lower().find(original_phrase)
            if start_idx != -1:
                all_ngrams.append((phrase, start_idx))

        # 3-word phrases
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            original_phrase = ' '.join(text.lower().split()[i:i+3])
            start_idx = text.lower().find(original_phrase)
            if start_idx != -1:
                all_ngrams.append((phrase, start_idx))

        # 4-word phrases
        for i in range(len(words) - 3):
            phrase = ' '.join(words[i:i+4])
            original_phrase = ' '.join(text.lower().split()[i:i+4])
            start_idx = text.lower().find(original_phrase)
            if start_idx != -1:
                all_ngrams.append((phrase, start_idx))

        # Count phrase occurrences
        phrase_counter = Counter([phrase for phrase, _ in all_ngrams])

        # Find phrases appearing 3+ times
        for phrase, count in phrase_counter.items():
            if count >= 3:
                # Get all locations
                locations = []
                text_lower = text.lower()
                start = 0
                while True:
                    idx = text_lower.find(phrase, start)
                    if idx == -1:
                        break
                    locations.append(idx)
                    start = idx + 1

                # Determine severity based on count
                if count >= 5:
                    severity = 'HIGH'
                elif count >= 3:
                    severity = 'MEDIUM'
                else:
                    severity = 'LOW'

                patterns.append({
                    'pattern_type': 'repeated_phrase',
                    'pattern': phrase,
                    'count': count,
                    'locations': locations[:10],  # Limit to 10 locations
                    'severity': severity,
                    'percentage': None,
                    'examples': None
                })

        return patterns

    def _detect_sentence_starts(self, text: str, segments: List[Dict]) -> List[Dict]:
        """Detect repeated sentence start patterns (>30% same start)."""
        patterns = []

        if not segments:
            return patterns

        # Extract first words from each segment
        first_words = []
        for segment in segments:
            segment_text = segment.get('text', '').strip()
            if segment_text:
                # Get first word (lowercase, remove punctuation)
                words = segment_text.split()
                if words:
                    first_word = re.sub(r'[^\w]', '', words[0].lower())
                    first_words.append(first_word)

        if not first_words:
            return patterns

        total_sentences = len(first_words)

        # Count first word occurrences
        word_counter = Counter(first_words)

        # Find words that start >30% of sentences
        for word, count in word_counter.items():
            percentage = count / total_sentences

            if percentage > 0.30:
                # Determine severity
                if percentage >= 0.50:
                    severity = 'HIGH'
                elif percentage >= 0.35:
                    severity = 'MEDIUM'
                else:
                    severity = 'LOW'

                # Get examples (first 3)
                examples = []
                for segment in segments:
                    segment_text = segment.get('text', '').strip()
                    if segment_text:
                        first_word_match = re.sub(r'[^\w]', '', segment_text.split()[0].lower())
                        if first_word_match == word and len(examples) < 3:
                            examples.append(segment_text[:50] + '...' if len(segment_text) > 50 else segment_text)

                patterns.append({
                    'pattern_type': 'sentence_start',
                    'pattern': word,
                    'count': count,
                    'locations': [],  # Sentence starts don't need specific locations
                    'severity': severity,
                    'percentage': round(percentage, 3),
                    'examples': examples
                })

        return patterns

    def _detect_word_repetition(self, text: str, stopwords: set) -> List[Dict]:
        """Detect words used >5% of total word count (excluding stopwords)."""
        patterns = []

        # Clean and tokenize
        text_clean = text.lower()
        text_clean = re.sub(r'[^\w\s]', ' ', text_clean)
        words = [w for w in text_clean.split() if w not in stopwords and len(w) > 2]

        if not words:
            return patterns

        total_words = len(words)
        word_counter = Counter(words)

        # Find words appearing >5% of the time
        for word, count in word_counter.items():
            percentage = count / total_words

            if percentage > 0.05:
                # Determine severity
                if percentage >= 0.10:
                    severity = 'HIGH'
                elif percentage >= 0.07:
                    severity = 'MEDIUM'
                else:
                    severity = 'LOW'

                # Get all locations
                locations = []
                text_lower = text.lower()
                start = 0
                while True:
                    idx = text_lower.find(f' {word} ', start)  # Look for whole words
                    if idx == -1:
                        # Try at start of text
                        if text_lower.startswith(word + ' '):
                            idx = 0
                        else:
                            break
                    locations.append(idx)
                    start = idx + len(word) + 1

                patterns.append({
                    'pattern_type': 'word_repetition',
                    'pattern': word,
                    'count': count,
                    'locations': locations[:10],  # Limit to 10 locations
                    'severity': severity,
                    'percentage': round(percentage, 3),
                    'examples': None
                })

        return patterns

    def generate_document_explanation(self, result: Dict) -> str:
        """
        Generate document-level explanation summarizing overall AI assessment.

        Creates a 2-3 sentence natural language explanation that references
        specific feature patterns and confidence distribution.

        Args:
            result: Full analysis result with segments, overall probability, and distribution

        Returns:
            Natural language explanation string (2-3 sentences)
        """
        overall_prob = result.get("overall_ai_probability", 0.5)
        segments = result.get("segments", [])
        confidence_distribution = result.get("confidence_distribution", {})

        high_count = confidence_distribution.get("HIGH", 0)
        medium_count = confidence_distribution.get("MEDIUM", 0)
        low_count = confidence_distribution.get("LOW", 0)
        total_segments = len(segments)

        # Identify dominant feature patterns across high-confidence segments
        feature_patterns = self._analyze_document_feature_patterns(segments)

        # Build explanation based on overall probability
        if overall_prob > 0.7:
            # High AI probability
            explanation = (
                f"This document shows strong indicators of AI-generated content. "
            )
            if feature_patterns:
                explanation += f"Key patterns include {feature_patterns}. "
            explanation += (
                f"Approximately {high_count} of {total_segments} sentences are flagged "
                f"as high-confidence AI-generated."
            )
        elif overall_prob >= 0.4:
            # Medium AI probability (mixed signals)
            explanation = (
                f"This document contains mixed signals - some sections appear AI-generated "
                f"while others seem human-written. "
            )
            if feature_patterns:
                explanation += f"{feature_patterns.capitalize()}. "
            explanation += (
                f"Overall, {high_count} of {total_segments} sentences show strong AI patterns, "
                f"while {low_count} appear primarily human-written."
            )
        else:
            # Low AI probability (human-like)
            explanation = (
                f"This document primarily shows human-like writing patterns. "
            )
            if feature_patterns:
                explanation += f"{feature_patterns.capitalize()}. "
            explanation += (
                f"Only {high_count} of {total_segments} sentences are flagged as potentially AI-generated."
            )

        return explanation

    def _analyze_document_feature_patterns(self, segments: List[Dict]) -> str:
        """
        Analyze which features are most important across high-confidence segments.

        Args:
            segments: List of segment dictionaries with feature_attribution

        Returns:
            Comma-separated feature pattern descriptions (e.g., "consistent sentence lengths, predictable word choices")
        """
        # Count feature occurrences across high-confidence segments
        high_conf_segments = [s for s in segments if s.get("confidence_level") == ConfidenceLevel.HIGH]

        if not high_conf_segments:
            # If no high-confidence segments, look at medium
            high_conf_segments = [s for s in segments if s.get("confidence_level") == ConfidenceLevel.MEDIUM]

        if not high_conf_segments:
            return ""

        # Aggregate feature importance across segments
        feature_pattern_counts = {}

        for segment in high_conf_segments:
            feature_attribution = segment.get("feature_attribution", [])
            for feature in feature_attribution:
                feature_name = feature.get("feature_name", "")
                importance = feature.get("importance", 0)

                # Only count high-importance features (>0.5)
                if importance > 0.5:
                    # Map feature name to pattern description
                    pattern_key = self._feature_to_pattern_key(feature_name, feature)
                    if pattern_key:
                        feature_pattern_counts[pattern_key] = feature_pattern_counts.get(pattern_key, 0) + importance

        # Sort by count and get top 2-3 patterns
        sorted_patterns = sorted(feature_pattern_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        if not sorted_patterns:
            return ""

        # Convert to pattern descriptions
        pattern_descriptions = [FEATURE_PATTERNS.get(pattern, pattern) for pattern, _ in sorted_patterns]
        pattern_descriptions = [p for p in pattern_descriptions if p]  # Filter out None

        if len(pattern_descriptions) == 1:
            return pattern_descriptions[0]
        elif len(pattern_descriptions) == 2:
            return f"{pattern_descriptions[0]} and {pattern_descriptions[1]}"
        else:
            return f"{pattern_descriptions[0]}, {pattern_descriptions[1]}, and {pattern_descriptions[2]}"

    def _feature_to_pattern_key(self, feature_name: str, feature: Dict) -> Optional[str]:
        """
        Map feature name and value to pattern key for explanation lookup.

        Args:
            feature_name: Name of the feature
            feature: Feature dict with importance and potentially interpretation

        Returns:
            Pattern key for FEATURE_PATTERNS lookup (e.g., "low_burstiness")
        """
        interpretation = feature.get("interpretation", "").lower()

        # Parse interpretation to determine if value is high/low/normal
        if "very low" in interpretation or "low" in interpretation:
            level = "low"
        elif "very high" in interpretation or "high" in interpretation:
            level = "high"
        else:
            level = "normal"

        # Map feature names to pattern keys
        feature_name_lower = feature_name.lower().replace(" ", "_")

        # Common mappings
        if "burstiness" in feature_name_lower:
            return f"{level}_burstiness" if level != "normal" else None
        elif "perplexity" in feature_name_lower:
            return f"{level}_perplexity" if level != "normal" else None
        elif "unique_word" in feature_name_lower:
            return f"{level}_unique_words"
        elif "rare_word" in feature_name_lower:
            return f"{level}_rare_word_ratio"
        elif "noun_ratio" in feature_name_lower:
            return f"{level}_noun_ratio" if level != "normal" else None
        elif "verb_ratio" in feature_name_lower:
            return f"{level}_verb_ratio" if level != "normal" else None
        elif "adjective_ratio" in feature_name_lower:
            return f"{level}_adjective_ratio" if level != "normal" else None
        elif "bigram_diversity" in feature_name_lower:
            return f"{level}_bigram_diversity"
        elif "trigram_diversity" in feature_name_lower:
            return f"{level}_trigram_diversity"
        elif "bigram_repetition" in feature_name_lower:
            return f"{level}_bigram_repetition" if level != "normal" else None
        elif "trigram_repetition" in feature_name_lower:
            return f"{level}_trigram_repetition" if level != "normal" else None
        elif "lexical_overlap" in feature_name_lower:
            return f"{level}_lexical_overlap" if level != "normal" else None
        elif "topic_consistency" in feature_name_lower:
            return f"{level}_topic_consistency" if level != "normal" else None
        elif "transition_smoothness" in feature_name_lower:
            return f"{level}_transition_smoothness" if level != "normal" else None
        elif "comma_ratio" in feature_name_lower:
            return f"{level}_comma_ratio" if level != "normal" else None
        elif "semicolon_ratio" in feature_name_lower:
            return f"{level}_semicolon_ratio" if level != "normal" else None
        elif "question_ratio" in feature_name_lower:
            return f"{level}_question_ratio" if level != "normal" else None
        elif "flesch_reading_ease" in feature_name_lower:
            return f"{level}_flesch_reading_ease" if level != "normal" else None
        elif "flesch_kincaid_grade" in feature_name_lower:
            return f"{level}_flesch_kincaid_grade" if level != "normal" else None

        return None

    def analyze_with_fingerprint(
        self,
        text: str,
        user_fingerprint: Dict,
        granularity: str = "sentence"
    ) -> Dict:
        """
        Analyze text comparing against user's fingerprint.
        
        Args:
            text: Text to analyze
            user_fingerprint: User's fingerprint dictionary
            granularity: "sentence" or "paragraph"
        
        Returns:
            Dictionary with heat map data
        """
        return self.analyze_text(text, granularity, user_fingerprint)


# Global service instance
_analysis_service = None


def get_analysis_service() -> AnalysisService:
    """Get or create the global analysis service instance"""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service
