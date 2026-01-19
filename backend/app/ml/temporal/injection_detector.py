"""
AI injection detection across document versions.

Identifies when AI-generated content has been inserted into a document
between versions, detecting suspicious additions and modifications.
"""

import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.ml.temporal.version_tracker import VersionTracker, DocumentNotFound


class InjectionDetector:
    """
    Detect AI-generated content injected between document versions.

    Analyzes version differences to identify suspicious additions
    and modifications that suggest AI-generated content was added.
    """

    # Default threshold for considering content as "high AI probability"
    DEFAULT_THRESHOLD = 0.7

    # Threshold for considering a modification as "significant AI change"
    DELTA_THRESHOLD = 0.3

    def __init__(
        self,
        version_tracker: Optional[VersionTracker] = None,
        threshold: float = DEFAULT_THRESHOLD
    ):
        """
        Initialize the injection detector.

        Args:
            version_tracker: Optional VersionTracker instance
            threshold: AI probability above which content is flagged
        """
        self.version_tracker = version_tracker or VersionTracker()
        self.threshold = threshold

    def detect_injections(self, document_id: str, db: Session) -> List[Dict[str, Any]]:
        """
        Detect AI injection events across all versions of a document.

        Compares each adjacent version pair to identify when high-AI
        content was added or when AI probability significantly increased.

        Args:
            document_id: External document identifier
            db: Database session

        Returns:
            List of injection events with:
                - version: version number where injection occurred
                - version_id: database ID of the version
                - timestamp: when the version was created
                - position: position in document
                - text: text snippet (truncated to 100 chars)
                - ai_probability: AI probability score
                - type: 'addition' or 'modification'
        """
        # Get version history
        try:
            versions = self.version_tracker.get_version_history(document_id, db)
        except DocumentNotFound:
            return []

        if len(versions) < 2:
            return []

        injection_events = []

        # Compare each adjacent pair
        for i in range(len(versions) - 1):
            version_a_id = versions[i]['version_id']
            version_b_id = versions[i + 1]['version_id']

            comparison = self.version_tracker.compare_versions(
                version_a_id, version_b_id, db
            )

            # Check added sections
            for addition in comparison.get('added_sections', []):
                if addition['ai_probability'] >= self.threshold:
                    injection_events.append({
                        'version': versions[i + 1]['version_number'],
                        'version_id': versions[i + 1]['version_id'],
                        'timestamp': versions[i + 1]['created_at'],
                        'position': addition['position'],
                        'text': self._truncate_text(addition['text'], 100),
                        'ai_probability': addition['ai_probability'],
                        'type': 'addition',
                        'severity': self._get_severity(addition['ai_probability'])
                    })

            # Check modified sections with significant AI increase
            for modification in comparison.get('modified_sections', []):
                delta_ai = modification.get('delta_ai', 0)
                if delta_ai >= self.DELTA_THRESHOLD:
                    injection_events.append({
                        'version': versions[i + 1]['version_number'],
                        'version_id': versions[i + 1]['version_id'],
                        'timestamp': versions[i + 1]['created_at'],
                        'position': modification['position'],
                        'old_text': self._truncate_text(modification['old_text'], 100),
                        'new_text': self._truncate_text(modification['new_text'], 100),
                        'delta_ai': delta_ai,
                        'ai_probability': min(1.0, modification.get('old_position', 0) + delta_ai),
                        'type': 'modification',
                        'severity': self._get_severity(delta_ai)
                    })

        # Sort by AI probability (highest first)
        injection_events.sort(
            key=lambda e: e.get('ai_probability', 0),
            reverse=True
        )

        return injection_events

    def find_suspicious_additions(
        self,
        versions: List[Dict[str, Any]],
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Filter and rank added sections by AI probability.

        Args:
            versions: List of version dictionaries from get_version_history
            top_n: Maximum number of suspicious additions to return

        Returns:
            Top N most suspicious additions
        """
        suspicious = []

        for i in range(len(versions) - 1):
            version = versions[i + 1]
            segment_scores = version.get('segment_ai_scores', [])

            for segment in segment_scores:
                ai_prob = segment.get('ai_probability', 0.5)
                if ai_prob >= self.threshold:
                    suspicious.append({
                        'version': version['version_number'],
                        'version_id': version['version_id'],
                        'position': segment.get('start_index', 0),
                        'ai_probability': ai_prob,
                        'confidence_level': segment.get('confidence_level', 'MEDIUM'),
                        'timestamp': version['created_at']
                    })

        # Sort by AI probability and take top N
        suspicious.sort(key=lambda s: s['ai_probability'], reverse=True)
        return suspicious[:top_n]

    def calculate_injection_score(self, document_id: str, db: Session) -> float:
        """
        Calculate overall injection severity score for a document.

        The score represents the proportion of the document that
        appears to be AI-injected content.

        Formula: (sum of injection AI probabilities) / (total words across all versions)

        Args:
            document_id: External document identifier
            db: Database session

        Returns:
            Injection score from 0-1
        """
        injection_events = self.detect_injections(document_id, db)

        if not injection_events:
            return 0.0

        # Get latest version for word count
        latest = self.version_tracker.get_latest_version(document_id, db)
        if not latest:
            return 0.0

        total_words = latest['word_count']
        if total_words == 0:
            return 0.0

        # Sum AI probabilities of injection events
        # Weight by estimated proportion of document (simplified)
        injection_sum = sum(e.get('ai_probability', 0) for e in injection_events)

        # Normalize by number of events to prevent overcounting
        if injection_events:
            injection_sum /= len(injection_events)

        # Apply to proportion of suspicious events
        suspicious_ratio = min(1.0, len(injection_events) / 5.0)

        return round(injection_sum * suspicious_ratio, 4)

    def detect_mixed_authorship_indicators(
        self,
        versions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect patterns indicating mixed human-AI authorship.

        Looks for:
        - High variance in AI probability between segments
        - Sudden changes in burstiness/coherence metrics
        - Inconsistent writing patterns

        Args:
            versions: List of version dictionaries

        Returns:
            List of indicator dictionaries with type, description, severity
        """
        if not versions:
            return []

        indicators = []
        latest_version = versions[-1]
        segment_scores = latest_version.get('segment_ai_scores', [])

        if not segment_scores:
            return []

        # Calculate variance in AI probabilities
        ai_probs = [s.get('ai_probability', 0.5) for s in segment_scores]
        if len(ai_probs) > 1:
            prob_variance = float(np.var(ai_probs))

            # High variance suggests mixed authorship
            if prob_variance > 0.1:
                indicators.append({
                    'type': 'variance_discrepancy',
                    'description': f'High variance in AI probability ({prob_variance:.3f}) suggests mixed authorship',
                    'value': round(prob_variance, 4),
                    'severity': 'high' if prob_variance > 0.2 else 'medium',
                    'version': latest_version['version_number']
                })

        # Check for probability spikes (suspicious transitions)
        for i in range(1, len(ai_probs)):
            diff = abs(ai_probs[i] - ai_probs[i - 1])
            if diff > 0.5:
                indicators.append({
                    'type': 'probability_spike',
                    'description': f'Sudden AI probability change ({diff:.2f}) between segments suggests style injection',
                    'value': round(diff, 4),
                    'severity': 'high' if diff > 0.7 else 'medium',
                    'version': latest_version['version_number'],
                    'segment_index': i
                })

        # Check version-to-version probability shifts
        if len(versions) >= 2:
            for i in range(1, len(versions)):
                prev_prob = versions[i - 1].get('overall_ai_probability', 0.5)
                curr_prob = versions[i].get('overall_ai_probability', 0.5)
                shift = abs(curr_prob - prev_prob)

                if shift > 0.3:
                    indicators.append({
                        'type': 'version_shift',
                        'description': f'Large AI probability shift ({shift:.2f}) from version {i} to {i + 1}',
                        'value': round(shift, 4),
                        'severity': 'high' if shift > 0.5 else 'medium',
                        'from_version': versions[i - 1]['version_number'],
                        'to_version': versions[i]['version_number']
                    })

        return indicators

    def get_injection_summary(
        self,
        document_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get a comprehensive summary of AI injections for a document.

        Args:
            document_id: External document identifier
            db: Database session

        Returns:
            Summary dictionary with injection events, score, and indicators
        """
        injection_events = self.detect_injections(document_id, db)
        injection_score = self.calculate_injection_score(document_id, db)

        # Get versions for mixed authorship detection
        try:
            versions = self.version_tracker.get_version_history(document_id, db)
        except DocumentNotFound:
            versions = []

        mixed_authorship_indicators = self.detect_mixed_authorship_indicators(versions)

        # Categorize injection events
        additions = [e for e in injection_events if e['type'] == 'addition']
        modifications = [e for e in injection_events if e['type'] == 'modification']

        # Get severity breakdown
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}
        for event in injection_events:
            severity = event.get('severity', 'low')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            'injection_events': injection_events,
            'injection_score': injection_score,
            'total_injections': len(injection_events),
            'additions_count': len(additions),
            'modifications_count': len(modifications),
            'severity_breakdown': severity_counts,
            'mixed_authorship_indicators': mixed_authorship_indicators,
            'overall_risk': self._calculate_overall_risk(injection_score, severity_counts)
        }

    def _calculate_overall_risk(
        self,
        injection_score: float,
        severity_counts: Dict[str, int]
    ) -> str:
        """
        Calculate overall risk level based on injection metrics.

        Args:
            injection_score: Overall injection score
            severity_counts: Count of events by severity

        Returns:
            Risk level: 'high', 'medium', 'low', 'none'
        """
        if severity_counts.get('high', 0) >= 3:
            return 'high'
        if injection_score > 0.5:
            return 'high'
        if severity_counts.get('high', 0) >= 1 or severity_counts.get('medium', 0) >= 3:
            return 'medium'
        if injection_score > 0.2:
            return 'medium'
        if severity_counts.get('medium', 0) >= 1 or injection_score > 0:
            return 'low'
        return 'none'

    def _truncate_text(self, text: str, max_length: int) -> str:
        """
        Truncate text to maximum length, adding ellipsis if needed.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text
        """
        if not text:
            return ''
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + '...'

    def _get_severity(self, ai_probability: float) -> str:
        """
        Get severity level from AI probability.

        Args:
            ai_probability: AI probability score

        Returns:
            Severity: 'high', 'medium', or 'low'
        """
        if ai_probability >= 0.8:
            return 'high'
        elif ai_probability >= 0.6:
            return 'medium'
        else:
            return 'low'


def detect_injections(document_id: str, db: Session) -> List[Dict[str, Any]]:
    """
    Convenience function to detect injections for a document.

    Args:
        document_id: External document identifier
        db: Database session

    Returns:
        List of injection events
    """
    detector = InjectionDetector()
    return detector.detect_injections(document_id, db)


def find_suspicious_additions(
    versions: List[Dict[str, Any]],
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Convenience function to find suspicious additions.

    Args:
        versions: List of version dictionaries
        top_n: Maximum number to return

    Returns:
        Top N suspicious additions
    """
    detector = InjectionDetector()
    return detector.find_suspicious_additions(versions, top_n)
