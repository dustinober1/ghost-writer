"""
Database connection check utility.
"""
from typing import Tuple
from sqlalchemy import text
from app.models.database import engine, SessionLocal


def check_db_connection() -> Tuple[bool, str]:
    """
    Check if database connection is available.
    
    Returns:
        (is_connected, message)
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Database connection successful"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"


def is_db_available() -> bool:
    """Quick check if database is available"""
    is_connected, _ = check_db_connection()
    return is_connected
