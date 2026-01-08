"""
Tests for authentication utilities.
"""
import pytest
from app.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta
from jose import jwt, JWTError
import os


def test_get_password_hash():
    """Test password hashing."""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert len(hashed) > 0
    assert isinstance(hashed, str)


def test_verify_password_correct():
    """Test password verification with correct password."""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed) == True


def test_verify_password_incorrect():
    """Test password verification with incorrect password."""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert verify_password("wrongpassword", hashed) == False


def test_verify_password_empty():
    """Test password verification with empty password."""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert verify_password("", hashed) == False


def test_verify_password_long_password():
    """Test password hashing with long password (>72 bytes)."""
    long_password = "a" * 100
    hashed = get_password_hash(long_password)
    
    assert verify_password(long_password, hashed) == True
    assert verify_password("wrong", hashed) == False


def test_create_access_token():
    """Test creating access token."""
    data = {"sub": "user@example.com"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_with_expiry():
    """Test creating access token with custom expiry."""
    data = {"sub": "user@example.com"}
    expires_delta = timedelta(minutes=60)
    token = create_access_token(data, expires_delta=expires_delta)
    
    # Decode and verify expiry
    secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
    assert decoded["sub"] == "user@example.com"
    assert "exp" in decoded


def test_get_current_user_valid_token(client, test_user, db):
    """Test getting current user with valid token."""
    token = create_access_token({"sub": test_user.email})
    user = get_current_user(token=token, db=db)
    
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


def test_get_current_user_invalid_token(db):
    """Test getting current user with invalid token."""
    with pytest.raises(Exception):  # Should raise HTTPException
        get_current_user(token="invalid_token", db=db)


def test_get_current_user_expired_token(db):
    """Test getting current user with expired token."""
    # Create expired token
    data = {"sub": "user@example.com"}
    expires_delta = timedelta(minutes=-60)  # Negative delta = expired
    token = create_access_token(data, expires_delta=expires_delta)
    
    with pytest.raises(Exception):  # Should raise HTTPException
        get_current_user(token=token, db=db)


def test_get_current_user_no_sub(db):
    """Test getting current user with token missing 'sub'."""
    data = {}  # No 'sub' field
    token = create_access_token(data)
    
    with pytest.raises(Exception):  # Should raise HTTPException
        get_current_user(token=token, db=db)


def test_get_current_user_nonexistent_user(db):
    """Test getting current user that doesn't exist."""
    token = create_access_token({"sub": "nonexistent@example.com"})
    
    with pytest.raises(Exception):  # Should raise HTTPException
        get_current_user(token=token, db=db)