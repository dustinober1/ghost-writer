"""
Fingerprint service for managing user writing samples and fingerprints.
Handles storage, generation, and fine-tuning of user fingerprints.
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.models.database import User, WritingSample, Fingerprint
from app.ml.fingerprint import generate_fingerprint, update_fingerprint
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


# Global service instance
_fingerprint_service = None


def get_fingerprint_service() -> FingerprintService:
    """Get or create the global fingerprint service instance"""
    global _fingerprint_service
    if _fingerprint_service is None:
        _fingerprint_service = FingerprintService()
    return _fingerprint_service
