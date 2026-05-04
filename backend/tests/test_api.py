"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models import Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health_check():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user():
    """Test user registration."""
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_login_user():
    """Test user login."""
    # Register first
    client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "testpass123"}
    )
    
    # Login
    response = client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "testpass123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_get_me():
    """Test get current user."""
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "me@example.com", "password": "testpass123"}
    )
    login_response = client.post(
        "/auth/login",
        json={"email": "me@example.com", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    
    # Get user info
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_unauthorized_access():
    """Test unauthorized access to protected endpoint."""
    response = client.get("/intel/items")
    assert response.status_code == 403
