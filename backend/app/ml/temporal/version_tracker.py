"""
Document version tracking for temporal analysis.

Stores document versions with timestamps and AI scores, enabling
comparison between different drafts to detect AI injection and
track writing evolution.
"""

import hashlib
import difflib
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.database import DocumentVersion, get_db


class DocumentNotFound(Exception):
    """Raised when a document has no version history."""
    pass


class VersionTracker:
    """
    Tracks document versions for temporal analysis.

    Stores document snapshots with AI probabilities for each segment,
    enabling comparison across versions to detect AI-generated content
    that was added or modified.
    """

    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize the version tracker.

        Args:
            db_session: Optional database session. If None, creates a new session.
        """
        self.db_session = db_session

    def _get_session(self) -> Session:
        """Get or create a database session."""
        if self.db_session:
            return self.db_session
        return next(get_db())

    def _calculate_content_hash(self, content: str) -> str:
        """
        Calculate SHA-256 hash of content for deduplication.

        Args:
            content: Text content to hash

        Returns:
            Hexadecimal SHA-256 hash
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def store_version(
        self,
        user_id: int,
        document_id: str,
        content: str,
        analysis_result: Dict[str, Any],
        db: Session
    ) -> int:
        """
        Store a new document version in the database.

        Args:
            user_id: ID of the user who owns the document
            document_id: External document identifier (string)
            content: Full document text content
            analysis_result: Full analysis result from ensemble detection
            db: Database session

        Returns:
            version_id: ID of the created version record
        """
        # Calculate content hash for deduplication
        content_hash = self._calculate_content_hash(content)

        # Get the next version number for this document
        last_version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version_number.desc()).first()

        version_number = 1 if last_version is None else last_version.version_number + 1

        # Extract segment AI scores
        segment_ai_scores = []
        segments = analysis_result.get('segments', [])
        for segment in segments:
            segment_ai_scores.append({
                'start_index': segment.get('start_index', 0),
                'end_index': segment.get('end_index', 0),
                'ai_probability': segment.get('ai_probability', 0.5),
                'confidence_level': segment.get('confidence_level', 'MEDIUM')
            })

        # Calculate word count
        word_count = len(content.split())

        # Get overall AI probability
        overall_ai_probability = analysis_result.get('overall_ai_probability', 0.5)

        # Create the version record
        document_version = DocumentVersion(
            user_id=user_id,
            document_id=document_id,
            version_number=version_number,
            content=content,
            content_hash=content_hash,
            segment_ai_scores=segment_ai_scores,
            overall_ai_probability=overall_ai_probability,
            word_count=word_count,
            created_at=datetime.utcnow(),
            analysis_metadata=analysis_result
        )

        db.add(document_version)
        db.commit()
        db.refresh(document_version)

        return document_version.id

    def get_version_history(self, document_id: str, db: Session) -> List[Dict[str, Any]]:
        """
        Get all versions for a document, ordered by creation time.

        Args:
            document_id: External document identifier
            db: Database session

        Returns:
            List of version dictionaries with:
                - version_id: int
                - version_number: int
                - created_at: datetime
                - word_count: int
                - overall_ai_probability: float
                - segment_ai_scores: list of per-segment scores

        Raises:
            DocumentNotFound: If no versions exist for this document
        """
        versions = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.created_at.asc()).all()

        if not versions:
            raise DocumentNotFound(f"No versions found for document: {document_id}")

        return [
            {
                'version_id': v.id,
                'version_number': v.version_number,
                'created_at': v.created_at.isoformat() if v.created_at else None,
                'word_count': v.word_count,
                'overall_ai_probability': v.overall_ai_probability,
                'segment_ai_scores': v.segment_ai_scores or [],
                'content_hash': v.content_hash
            }
            for v in versions
        ]

    def compare_versions(
        self,
        version_a_id: int,
        version_b_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Compare two document versions to find differences.

        Uses difflib.SequenceMatcher to identify added, removed, and
        modified sections between versions.

        Args:
            version_a_id: ID of the first version (earlier)
            version_b_id: ID of the second version (later)
            db: Database session

        Returns:
            Dictionary with:
                - added_sections: list of {text, position, ai_probability}
                - removed_sections: list of {text, position}
                - modified_sections: list of {old_text, new_text, position, delta_ai}
                - similarity_score: float (0-1)
        """
        # Get both versions
        version_a = db.query(DocumentVersion).filter(
            DocumentVersion.id == version_a_id
        ).first()

        version_b = db.query(DocumentVersion).filter(
            DocumentVersion.id == version_b_id
        ).first()

        if not version_a or not version_b:
            raise DocumentNotFound("One or both version IDs not found")

        content_a = version_a.content
        content_b = version_b.content

        # Use SequenceMatcher to find differences
        matcher = difflib.SequenceMatcher(None, content_a, content_b, autojunk=False)

        added_sections = []
        removed_sections = []
        modified_sections = []

        # Get segment AI scores for version B (to annotate additions)
        segment_scores_b = version_b.segment_ai_scores or []

        def get_ai_probability_at_position(position: int) -> float:
            """Get AI probability for text at a given position in version B."""
            for segment in segment_scores_b:
                if segment['start_index'] <= position < segment['end_index']:
                    return segment['ai_probability']
            return 0.5  # Default if no segment matches

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                # Modified section
                old_text = content_a[i1:i2]
                new_text = content_b[j1:j2]

                # Calculate AI probability change
                old_ai = self._estimate_section_ai(old_text, version_a.segment_ai_scores or [], i1, i2)
                new_ai = self._estimate_section_ai(new_text, version_b.segment_ai_scores or [], j1, j2)
                delta_ai = new_ai - old_ai

                modified_sections.append({
                    'old_text': old_text[:200] + '...' if len(old_text) > 200 else old_text,
                    'new_text': new_text[:200] + '...' if len(new_text) > 200 else new_text,
                    'position': j1,
                    'old_position': i1,
                    'delta_ai': delta_ai
                })

            elif tag == 'delete':
                # Removed section
                removed_sections.append({
                    'text': content_a[i1:i2][:200] + '...' if (i2 - i1) > 200 else content_a[i1:i2],
                    'position': i1
                })

            elif tag == 'insert':
                # Added section - get AI probability
                added_text = content_b[j1:j2]
                ai_prob = get_ai_probability_at_position(j1)

                added_sections.append({
                    'text': added_text[:200] + '...' if (j2 - j1) > 200 else added_text,
                    'position': j1,
                    'ai_probability': ai_prob
                })

        # Calculate overall similarity
        similarity_score = matcher.ratio()

        return {
            'added_sections': added_sections,
            'removed_sections': removed_sections,
            'modified_sections': modified_sections,
            'similarity_score': similarity_score,
            'version_a_number': version_a.version_number,
            'version_b_number': version_b.version_number
        }

    def _estimate_section_ai(
        self,
        text: str,
        segment_scores: List[Dict],
        start_pos: int,
        end_pos: int
    ) -> float:
        """
        Estimate average AI probability for a section of text.

        Args:
            text: The text section
            segment_scores: List of segment AI scores
            start_pos: Start position in document
            end_pos: End position in document

        Returns:
            Average AI probability for the section
        """
        if not segment_scores:
            return 0.5

        # Find segments that overlap with this section
        overlapping_probs = []
        for segment in segment_scores:
            seg_start = segment.get('start_index', 0)
            seg_end = segment.get('end_index', 0)

            # Check for overlap
            if not (seg_end <= start_pos or seg_start >= end_pos):
                overlapping_probs.append(segment.get('ai_probability', 0.5))

        if not overlapping_probs:
            return 0.5

        return sum(overlapping_probs) / len(overlapping_probs)

    def get_latest_version(self, document_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Get the most recent version of a document.

        Args:
            document_id: External document identifier
            db: Database session

        Returns:
            Version dictionary or None if no versions exist
        """
        latest = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.created_at.desc()).first()

        if not latest:
            return None

        return {
            'version_id': latest.id,
            'version_number': latest.version_number,
            'created_at': latest.created_at.isoformat() if latest.created_at else None,
            'word_count': latest.word_count,
            'overall_ai_probability': latest.overall_ai_probability,
            'segment_ai_scores': latest.segment_ai_scores or [],
            'content_hash': latest.content_hash
        }

    def get_version_by_number(
        self,
        document_id: str,
        version_number: int,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific version by its version number.

        Args:
            document_id: External document identifier
            version_number: Version number to retrieve
            db: Database session

        Returns:
            Version dictionary or None if not found
        """
        version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version_number
        ).first()

        if not version:
            return None

        return {
            'version_id': version.id,
            'version_number': version.version_number,
            'created_at': version.created_at.isoformat() if version.created_at else None,
            'word_count': version.word_count,
            'overall_ai_probability': version.overall_ai_probability,
            'segment_ai_scores': version.segment_ai_scores or [],
            'content': version.content,
            'content_hash': version.content_hash,
            'analysis_metadata': version.analysis_metadata
        }


def store_version(
    user_id: int,
    document_id: str,
    content: str,
    analysis_result: Dict[str, Any],
    db: Session
) -> int:
    """
    Convenience function to store a document version.

    Args:
        user_id: ID of the user who owns the document
        document_id: External document identifier
        content: Full document text content
        analysis_result: Analysis result from ensemble detection
        db: Database session

    Returns:
        version_id: ID of the created version record
    """
    tracker = VersionTracker()
    return tracker.store_version(user_id, document_id, content, analysis_result, db)


def get_version_history(document_id: str, db: Session) -> List[Dict[str, Any]]:
    """
    Convenience function to get version history.

    Args:
        document_id: External document identifier
        db: Database session

    Returns:
        List of version dictionaries
    """
    tracker = VersionTracker()
    return tracker.get_version_history(document_id, db)


def compare_versions(
    version_a_id: int,
    version_b_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    Convenience function to compare two versions.

    Args:
        version_a_id: ID of the first version
        version_b_id: ID of the second version
        db: Database session

    Returns:
        Comparison result dictionary
    """
    tracker = VersionTracker()
    return tracker.compare_versions(version_a_id, version_b_id, db)
