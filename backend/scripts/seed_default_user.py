"""
Seed script to create a default user for development/demo purposes.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import SessionLocal, User
from app.utils.auth import get_password_hash


def create_default_user():
    """Create a default demo user"""
    db = SessionLocal()
    
    try:
        # Check if default user already exists
        existing_user = db.query(User).filter(User.email == "demo@ghostwriter.com").first()
        if existing_user:
            print("✓ Default user already exists")
            print(f"   Email: demo@ghostwriter.com")
            print(f"   Password: demo123")
            return
        
        # Create default user
        default_user = User(
            email="demo@ghostwriter.com",
            password_hash=get_password_hash("demo123")
        )
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
        
        print("✓ Default user created successfully!")
        print(f"   Email: demo@ghostwriter.com")
        print(f"   Password: demo123")
        print("\n⚠️  WARNING: This is a default demo account. Change the password in production!")
        
    except Exception as e:
        print(f"❌ Error creating default user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Creating default demo user...")
    create_default_user()
