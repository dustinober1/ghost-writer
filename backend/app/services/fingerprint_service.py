"""
Fingerprint service for managing user writing samples and fingerprints.
Handles storage, generation, and fine-tuning of user fingerprints.
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.models.database import User, WritingSample, Fingerprint, FingerprintSample, EnhancedFingerprint
from app.ml.fingerprint import generate_fingerprint, update_fingerprint
from app.ml.fingerprint.corpus_builder import FingerprintCorpusBuilder
from app.ml.feature_extraction import extract_feature_vector
from datetime import datetime


class FingerprintService:
    """Service for managing user fingerprints"""
    
    def upload_writing_sample(
        self,
        db: Session,
        user_id: int,
        text_content: str,
        source_type: str = "upload"
    ) -> WritingSample:
        """
        Upload a writing sample for a user.
        
        Args:
            db: Database session
            user_id: User ID
            text_content: Text content of the sample
            source_type: Type of source ("upload", "manual", "api")
        
        Returns:
            Created WritingSample object
        """
        writing_sample = WritingSample(
            user_id=user_id,
            text_content=text_content,
            source_type=source_type
        )
        db.add(writing_sample)
        db.commit()
        db.refresh(writing_sample)
        return writing_sample
    
    def get_user_samples(self, db: Session, user_id: int) -> List[WritingSample]:
        """Get all writing samples for a user"""
        return db.query(WritingSample).filter(WritingSample.user_id == user_id).all()
    
    def generate_user_fingerprint(
        self,
        db: Session,
        user_id: int
    ) -> Fingerprint:
        """
        Generate or update fingerprint for a user based on their writing samples.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Fingerprint object
        """
        # Get all writing samples
        samples = self.get_user_samples(db, user_id)
        
        if not samples:
            raise ValueError("No writing samples found. Please upload samples first.")
        
        # Extract text content
        text_samples = [sample.text_content for sample in samples]
        
        # Check if fingerprint already exists
        existing_fingerprint = db.query(Fingerprint).filter(
            Fingerprint.user_id == user_id
        ).first()
        
        if existing_fingerprint:
            # Update existing fingerprint
            fingerprint_dict = {
                "feature_vector": existing_fingerprint.feature_vector,
                "sample_count": len(samples),
                "model_version": existing_fingerprint.model_version
            }
            updated_fingerprint_dict = generate_fingerprint(text_samples)
            existing_fingerprint.feature_vector = updated_fingerprint_dict["feature_vector"]
            existing_fingerprint.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_fingerprint)
            return existing_fingerprint
        else:
            # Create new fingerprint
            fingerprint_dict = generate_fingerprint(text_samples)
            fingerprint = Fingerprint(
                user_id=user_id,
                feature_vector=fingerprint_dict["feature_vector"],
                model_version=fingerprint_dict.get("model_version", "1.0")
            )
            db.add(fingerprint)
            db.commit()
            db.refresh(fingerprint)
            return fingerprint
    
    def get_user_fingerprint(
        self,
        db: Session,
        user_id: int
    ) -> Optional[Fingerprint]:
        """Get user's fingerprint if it exists"""
        return db.query(Fingerprint).filter(Fingerprint.user_id == user_id).first()
    
    def fine_tune_fingerprint(
        self,
        db: Session,
        user_id: int,
        new_samples: List[str],
        weight: float = 0.3
    ) -> Fingerprint:
        """
        Fine-tune user's fingerprint with new samples.
        
        Args:
            db: Database session
            user_id: User ID
            new_samples: List of new text samples
            weight: Weight for new samples (0.0 to 1.0)
        
        Returns:
            Updated Fingerprint object
        """
        # Get existing fingerprint
        fingerprint = self.get_user_fingerprint(db, user_id)
        
        if not fingerprint:
            # No existing fingerprint, generate new one
            for sample_text in new_samples:
                self.upload_writing_sample(db, user_id, sample_text, "manual")
            return self.generate_user_fingerprint(db, user_id)
        
        # Upload new samples
        for sample_text in new_samples:
            self.upload_writing_sample(db, user_id, sample_text, "manual")
        
        # Update fingerprint
        fingerprint_dict = {
            "feature_vector": fingerprint.feature_vector,
            "sample_count": len(self.get_user_samples(db, user_id)),
            "model_version": fingerprint.model_version
        }
        
        updated_fingerprint_dict = update_fingerprint(
            fingerprint_dict,
            new_samples,
            weight
        )
        
        fingerprint.feature_vector = updated_fingerprint_dict["feature_vector"]
        fingerprint.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(fingerprint)
        
        return fingerprint
    
    def get_fingerprint_status(
        self,
        db: Session,
        user_id: int
    ) -> Dict:
        """
        Get fingerprint status for a user.
        
        Returns:
            Dictionary with has_fingerprint, fingerprint, and sample_count
        """
        fingerprint = self.get_user_fingerprint(db, user_id)
        samples = self.get_user_samples(db, user_id)
        
        from app.models.schemas import FingerprintResponse
        
        return {
            "has_fingerprint": fingerprint is not None,
            "fingerprint": FingerprintResponse.model_validate(fingerprint) if fingerprint else None,
            "sample_count": len(samples)
        }

    # ============= Corpus Management Methods =============

    def add_corpus_sample(
        self,
        db: Session,
        user_id: int,
        text_content: str,
        source_type: str = "manual",
        written_at: Optional[datetime] = None
    ) -> FingerprintSample:
        """
        Add a writing sample to the corpus for enhanced fingerprint generation.

        Args:
            db: Database session
            user_id: User ID
            text_content: Text content of the sample
            source_type: Type of source (email, essay, blog, academic, document, manual)
            written_at: When the text was originally written (for time-weighted aggregation)

        Returns:
            Created FingerprintSample object
        """
        # Extract features from text
        features = extract_feature_vector(text_content)
        features_list = features.tolist() if hasattr(features, 'tolist') else list(features)

        # Create fingerprint sample
        fingerprint_sample = FingerprintSample(
            user_id=user_id,
            text_content=text_content,
            source_type=source_type,
            features=features_list,
            word_count=len(text_content.split()),
            written_at=written_at
        )
        db.add(fingerprint_sample)
        db.commit()
        db.refresh(fingerprint_sample)
        return fingerprint_sample

    def get_corpus_status(
        self,
        db: Session,
        user_id: int
    ) -> Dict:
        """
        Get corpus summary status for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dictionary with sample_count, total_words, source_distribution,
            ready_for_fingerprint, samples_needed, oldest_sample, newest_sample
        """
        # Query all fingerprint samples for user
        samples = db.query(FingerprintSample).filter(
            FingerprintSample.user_id == user_id
        ).all()

        sample_count = len(samples)
        total_words = sum(s.word_count for s in samples)

        # Calculate source distribution
        source_distribution: Dict[str, int] = {}
        for sample in samples:
            source = sample.source_type
            source_distribution[source] = source_distribution.get(source, 0) + 1

        # Get oldest and newest sample timestamps
        oldest_sample = None
        newest_sample = None
        if samples:
            oldest_sample = min(s.created_at for s in samples)
            newest_sample = max(s.created_at for s in samples)

        ready_for_fingerprint = sample_count >= FingerprintCorpusBuilder.MIN_SAMPLES_FOR_FINGERPRINT
        samples_needed = max(0, FingerprintCorpusBuilder.MIN_SAMPLES_FOR_FINGERPRINT - sample_count)

        return {
            "sample_count": sample_count,
            "total_words": total_words,
            "source_distribution": source_distribution,
            "ready_for_fingerprint": ready_for_fingerprint,
            "samples_needed": samples_needed,
            "oldest_sample": oldest_sample,
            "newest_sample": newest_sample
        }

    def list_corpus_samples(
        self,
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> List[FingerprintSample]:
        """
        List corpus samples with pagination.

        Args:
            db: Database session
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            List of FingerprintSample objects
        """
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20

        offset = (page - 1) * page_size
        samples = db.query(FingerprintSample).filter(
            FingerprintSample.user_id == user_id
        ).order_by(FingerprintSample.created_at.desc()).offset(offset).limit(page_size).all()

        return samples

    def delete_corpus_sample(
        self,
        db: Session,
        user_id: int,
        sample_id: int
    ) -> bool:
        """
        Delete a corpus sample.

        Args:
            db: Database session
            user_id: User ID
            sample_id: ID of sample to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If sample doesn't exist or doesn't belong to user
        """
        sample = db.query(FingerprintSample).filter(
            FingerprintSample.id == sample_id
        ).first()

        if not sample:
            raise ValueError("Sample not found")

        if sample.user_id != user_id:
            raise ValueError("Sample does not belong to this user")

        db.delete(sample)
        db.commit()
        return True

    def generate_enhanced_fingerprint(
        self,
        db: Session,
        user_id: int,
        method: str = "time_weighted",
        alpha: float = 0.3
    ) -> EnhancedFingerprint:
        """
        Generate an enhanced fingerprint from the corpus.

        Args:
            db: Database session
            user_id: User ID
            method: Aggregation method ('time_weighted', 'average', 'source_weighted')
            alpha: EMA smoothing parameter for time_weighted method

        Returns:
            Created or updated EnhancedFingerprint object

        Raises:
            ValueError: If insufficient samples or invalid method
        """
        # Validate method
        valid_methods = ["time_weighted", "average", "source_weighted"]
        if method not in valid_methods:
            raise ValueError(
                f"Invalid method: {method}. Must be one of: {', '.join(valid_methods)}"
            )

        # Get all user's fingerprint samples
        samples = db.query(FingerprintSample).filter(
            FingerprintSample.user_id == user_id
        ).all()

        if len(samples) < FingerprintCorpusBuilder.MIN_SAMPLES_FOR_FINGERPRINT:
            raise ValueError(
                f"Need at least {FingerprintCorpusBuilder.MIN_SAMPLES_FOR_FINGERPRINT} samples. "
                f"Have {len(samples)}."
            )

        # Build corpus and generate fingerprint
        builder = FingerprintCorpusBuilder(min_samples=FingerprintCorpusBuilder.MIN_SAMPLES_FOR_FINGERPRINT)

        for sample in samples:
            timestamp = sample.written_at or sample.created_at
            builder.samples.append({
                "features": sample.features,
                "timestamp": timestamp,
                "source_type": sample.source_type,
                "word_count": sample.word_count
            })

        # Generate fingerprint
        fingerprint_data = builder.build_fingerprint(method=method, alpha=alpha)

        # Check if enhanced fingerprint already exists
        existing_fingerprint = db.query(EnhancedFingerprint).filter(
            EnhancedFingerprint.user_id == user_id
        ).first()

        if existing_fingerprint:
            # Update existing fingerprint
            existing_fingerprint.feature_vector = fingerprint_data["feature_vector"]
            existing_fingerprint.feature_statistics = fingerprint_data.get("feature_statistics")
            existing_fingerprint.corpus_size = fingerprint_data["sample_count"]
            existing_fingerprint.method = fingerprint_data["method"]
            existing_fingerprint.alpha = fingerprint_data.get("alpha", alpha)
            existing_fingerprint.source_distribution = fingerprint_data.get("source_distribution")
            existing_fingerprint.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_fingerprint)
            return existing_fingerprint
        else:
            # Create new enhanced fingerprint
            enhanced_fingerprint = EnhancedFingerprint(
                user_id=user_id,
                feature_vector=fingerprint_data["feature_vector"],
                feature_statistics=fingerprint_data.get("feature_statistics"),
                corpus_size=fingerprint_data["sample_count"],
                method=fingerprint_data["method"],
                alpha=fingerprint_data.get("alpha", alpha),
                source_distribution=fingerprint_data.get("source_distribution")
            )
            db.add(enhanced_fingerprint)
            db.commit()
            db.refresh(enhanced_fingerprint)
            return enhanced_fingerprint


# Global service instance
_fingerprint_service = None


def get_fingerprint_service() -> FingerprintService:
    """Get or create the global fingerprint service instance"""
    global _fingerprint_service
    if _fingerprint_service is None:
        _fingerprint_service = FingerprintService()
    return _fingerprint_service
