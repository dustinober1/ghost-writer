"""
Timeline analysis for tracking AI probability evolution across document versions.

Analyzes document version history to identify trends in AI probability over time,
detecting patterns that indicate AI-generated content was added or modified.
"""

import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.ml.temporal.version_tracker import VersionTracker, DocumentNotFound


class TimelineAnalyzer:
    """
    Analyze document evolution across versions.

    Tracks how AI probability changes over time, identifying trends
    that suggest AI-generated content was added or the document
    was increasingly written with AI assistance.
    """

    # Trend threshold - minimum probability difference to indicate a trend
    TREND_THRESHOLD = 0.2

    def __init__(self, version_tracker: Optional[VersionTracker] = None):
        """
        Initialize the timeline analyzer.

        Args:
            version_tracker: Optional VersionTracker instance
        """
        self.version_tracker = version_tracker or VersionTracker()

    def analyze_timeline(self, document_id: str, db: Session) -> Dict[str, Any]:
        """
        Analyze the complete timeline of a document's evolution.

        Args:
            document_id: External document identifier
            db: Database session

        Returns:
            Dictionary with:
                - timeline: list of version stats
                - overall_trend: 'increasing', 'decreasing', 'stable', 'insufficient_data'
                - ai_velocity: rate of AI probability change per version
                - total_versions: number of versions
        """
        # Get version history
        try:
            versions = self.version_tracker.get_version_history(document_id, db)
        except DocumentNotFound:
            return {
                'timeline': [],
                'overall_trend': 'no_data',
                'ai_velocity': 0.0,
                'total_versions': 0,
                'error': 'No version history found for this document'
            }

        if len(versions) < 2:
            return {
                'timeline': self._calculate_version_stats(versions),
                'overall_trend': 'insufficient_data',
                'ai_velocity': 0.0,
                'total_versions': len(versions)
            }

        # Calculate stats for each version
        timeline = self._calculate_version_stats(versions)

        # Determine overall trend
        overall_trend = self.detect_trend(timeline)

        # Calculate AI velocity (rate of change)
        ai_velocity = self._calculate_ai_velocity(timeline)

        return {
            'timeline': timeline,
            'overall_trend': overall_trend,
            'ai_velocity': ai_velocity,
            'total_versions': len(versions)
        }

    def _calculate_version_stats(self, versions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate statistics for each version in the timeline.

        Args:
            versions: List of version dictionaries

        Returns:
            List of version dictionaries with added statistics
        """
        stats = []
        for version in versions:
            segment_scores = version.get('segment_ai_scores', [])

            # Calculate statistics from segment scores
            if segment_scores:
                ai_probs = [s.get('ai_probability', 0.5) for s in segment_scores]
                avg_ai_prob = float(np.mean(ai_probs))
                max_ai_prob = float(np.max(ai_probs))
                min_ai_prob = float(np.min(ai_probs))
                std_ai_prob = float(np.std(ai_probs)) if len(ai_probs) > 1 else 0.0

                # Count high-confidence segments
                high_confidence_count = sum(1 for s in segment_scores
                                            if s.get('ai_probability', 0.5) > 0.7)
                medium_confidence_count = sum(1 for s in segment_scores
                                              if 0.4 <= s.get('ai_probability', 0.5) <= 0.7)
                low_confidence_count = sum(1 for s in segment_scores
                                           if s.get('ai_probability', 0.5) < 0.4)
            else:
                # Fall back to overall probability if no segment data
                avg_ai_prob = version.get('overall_ai_probability', 0.5)
                max_ai_prob = avg_ai_prob
                min_ai_prob = avg_ai_prob
                std_ai_prob = 0.0
                high_confidence_count = 0
                medium_confidence_count = 0
                low_confidence_count = 0

            stats.append({
                'version_id': version['version_id'],
                'version_number': version['version_number'],
                'timestamp': version['created_at'],
                'word_count': version['word_count'],
                'avg_ai_prob': round(avg_ai_prob, 4),
                'max_ai_prob': round(max_ai_prob, 4),
                'min_ai_prob': round(min_ai_prob, 4),
                'std_ai_prob': round(std_ai_prob, 4),
                'high_confidence_count': high_confidence_count,
                'medium_confidence_count': medium_confidence_count,
                'low_confidence_count': low_confidence_count,
                'overall_ai_probability': version.get('overall_ai_probability', avg_ai_prob)
            })

        return stats

    def detect_trend(self, timeline_data: List[Dict[str, Any]]) -> str:
        """
        Detect the overall trend in AI probability across versions.

        Compares the first and last average AI probabilities to determine
        if AI usage is increasing, decreasing, or stable.

        Args:
            timeline_data: List of version statistics

        Returns:
            Trend: 'increasing', 'decreasing', 'stable', or 'insufficient_data'
        """
        if len(timeline_data) < 2:
            return 'insufficient_data'

        first_avg = timeline_data[0]['avg_ai_prob']
        last_avg = timeline_data[-1]['avg_ai_prob']
        diff = last_avg - first_avg

        # Also check for consistent directional movement
        # (more than half of the changes in the same direction)
        if len(timeline_data) >= 3:
            changes = []
            for i in range(1, len(timeline_data)):
                change = timeline_data[i]['avg_ai_prob'] - timeline_data[i-1]['avg_ai_prob']
                changes.append(change)

            positive_changes = sum(1 for c in changes if c > 0)
            negative_changes = sum(1 for c in changes if c < 0)

            if positive_changes > len(changes) / 2 and diff > 0.05:
                return 'increasing'
            elif negative_changes > len(changes) / 2 and diff < -0.05:
                return 'decreasing'

        # Use simple threshold comparison
        if diff > self.TREND_THRESHOLD:
            return 'increasing'
        elif diff < -self.TREND_THRESHOLD:
            return 'decreasing'
        else:
            return 'stable'

    def _calculate_ai_velocity(self, timeline_data: List[Dict[str, Any]]) -> float:
        """
        Calculate the rate of AI probability change per version.

        Args:
            timeline_data: List of version statistics

        Returns:
            Average change in AI probability per version
        """
        if len(timeline_data) < 2:
            return 0.0

        total_change = timeline_data[-1]['avg_ai_prob'] - timeline_data[0]['avg_ai_prob']
        num_transitions = len(timeline_data) - 1

        return round(total_change / num_transitions, 4)

    def detect_significant_changes(
        self,
        timeline_data: List[Dict[str, Any]],
        threshold: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        Detect significant changes in AI probability between consecutive versions.

        Args:
            timeline_data: List of version statistics
            threshold: Minimum probability difference to flag as significant

        Returns:
            List of significant change events
        """
        if len(timeline_data) < 2:
            return []

        significant_changes = []
        for i in range(1, len(timeline_data)):
            prev = timeline_data[i - 1]
            curr = timeline_data[i]

            diff = curr['avg_ai_prob'] - prev['avg_ai_prob']

            if abs(diff) >= threshold:
                significant_changes.append({
                    'from_version': prev['version_number'],
                    'to_version': curr['version_number'],
                    'change': round(diff, 4),
                    'from_probability': prev['avg_ai_prob'],
                    'to_probability': curr['avg_ai_prob'],
                    'type': 'increase' if diff > 0 else 'decrease',
                    'timestamp': curr['timestamp']
                })

        return significant_changes

    def get_version_comparison_summary(
        self,
        document_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get a summary comparing all versions of a document.

        Args:
            document_id: External document identifier
            db: Database session

        Returns:
            Summary dictionary with key comparisons
        """
        timeline_result = self.analyze_timeline(document_id, db)
        timeline = timeline_result.get('timeline', [])

        if not timeline:
            return {'error': 'No timeline data available'}

        # Find min/max probability versions
        min_prob_version = min(timeline, key=lambda v: v['avg_ai_prob'])
        max_prob_version = max(timeline, key=lambda v: v['avg_ai_prob'])

        # Word count change
        first_wc = timeline[0]['word_count']
        last_wc = timeline[-1]['word_count']
        wc_change = last_wc - first_wc

        return {
            'total_versions': len(timeline),
            'overall_trend': timeline_result.get('overall_trend'),
            'ai_velocity': timeline_result.get('ai_velocity'),
            'lowest_ai_probability_version': {
                'version_number': min_prob_version['version_number'],
                'avg_ai_prob': min_prob_version['avg_ai_prob'],
                'timestamp': min_prob_version['timestamp']
            },
            'highest_ai_probability_version': {
                'version_number': max_prob_version['version_number'],
                'avg_ai_prob': max_prob_version['avg_ai_prob'],
                'timestamp': max_prob_version['timestamp']
            },
            'word_count_change': wc_change,
            'first_word_count': first_wc,
            'last_word_count': last_wc,
            'significant_changes': self.detect_significant_changes(timeline)
        }


def analyze_timeline(document_id: str, db: Session) -> Dict[str, Any]:
    """
    Convenience function to analyze document timeline.

    Args:
        document_id: External document identifier
        db: Database session

    Returns:
        Timeline analysis result
    """
    analyzer = TimelineAnalyzer()
    return analyzer.analyze_timeline(document_id, db)


def detect_trend(timeline_data: List[Dict[str, Any]]) -> str:
    """
    Convenience function to detect trend from timeline data.

    Args:
        timeline_data: List of version statistics

    Returns:
        Trend: 'increasing', 'decreasing', 'stable', or 'insufficient_data'
    """
    analyzer = TimelineAnalyzer()
    return analyzer.detect_trend(timeline_data)
