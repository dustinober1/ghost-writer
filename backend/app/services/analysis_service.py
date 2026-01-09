"""
Analysis service that orchestrates feature extraction and contrastive model
to generate per-segment AI probability scores for heat map visualization.
Uses Ollama embeddings for improved accuracy.
"""
from typing import List, Dict, Optional
import numpy as np
from app.ml.feature_extraction import extract_feature_vector, extract_all_features
from app.ml.contrastive_model import get_contrastive_model
from app.ml.fingerprint import compare_to_fingerprint
from app.ml.ollama_embeddings import get_ollama_embedding
from app.utils.text_processing import split_into_sentences, split_into_paragraphs


class AnalysisService:
    """Service for analyzing text and generating heat map data"""
    
    def __init__(self):
        self.contrastive_model = get_contrastive_model()
    
    def analyze_text(
        self,
        text: str,
        granularity: str = "sentence",
        user_fingerprint: Optional[Dict] = None,
    ) -> Dict:
        """
        Analyze text and generate heat map data with AI probability scores.
        
        Uses Ollama embeddings in combination with stylometric features
        for more accurate AI probability estimation.
        
        Args:
            text: Text to analyze
            granularity: "sentence" or "paragraph"
            user_fingerprint: Optional user fingerprint for comparison
        
        Returns:
            Dictionary with heat map data and overall AI probability
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
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
                "end_index": end_index
            })
        
        # Calculate overall AI probability
        if segment_results:
            overall_ai_probability = np.mean([s["ai_probability"] for s in segment_results])
        else:
            overall_ai_probability = 0.5  # Default neutral
        
        return {
            "segments": segment_results,
            "overall_ai_probability": float(overall_ai_probability),
            "granularity": granularity
        }
    
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
