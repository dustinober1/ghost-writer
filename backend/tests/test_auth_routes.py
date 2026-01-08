"""
Tests for authentication routes.
"""
import pytest
from fastapi import status
from app.models.database import User


def test_register_success(client, db):
    """Test successful user registration."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password" not in data


def test_register_duplicate_email(client, db, test_user):
    """Test registration with duplicate email."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": test_user.email,
            "password": "password123"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"].lower()


def test_register_invalid_email(client, db):
    """Test registration with invalid email."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "notanemail",
            "password": "password123"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_register_short_password(client, db):
    """Test registration with short password."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "user@example.com",
            "password": "short"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(
        "/api/auth/login-json",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    """Test login with wrong password."""
    response = client.post(
        "/api/auth/login-json",
        json={
            "email": test_user.email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorrect" in response.json()["detail"].lower()


def test_login_nonexistent_user(client):
    """Test login with non-existent user."""
    response = client.post(
        "/api/auth/login-json",
        json={
            "email": "nonexistent@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_form_data(client, test_user):
    """Test login with form data (OAuth2PasswordRequestForm)."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_form_data_wrong_password(client, test_user):
    """Test login with form data and wrong password."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user.email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED