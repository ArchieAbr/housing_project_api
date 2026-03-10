import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# FIX: Force a dummy SQLite URL before main.py is imported so it doesn't crash trying to find the Docker 'db' hostname.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.main import app, get_db
from app.models import Base

# 1. Setup an in-memory SQLite database specifically for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the test database tables
Base.metadata.create_all(bind=engine)

# 2. Override the get_db dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# 3. Initialise the test client
client = TestClient(app)

# --- TESTS ---

def test_create_listing():
    """Test creating a new property listing."""
    response = client.post(
        "/api/listings",
        json={
            "address": "100 Test Avenue",
            "postcode": "LS1 9ZZ",
            "price": 300000,
            "property_type": "Semi-Detached",
            "bedrooms": 3
        },
    )
    assert response.status_code == 201
    assert response.json()["address"] == "100 Test Avenue"
    assert response.json()["id"] == 1

def test_get_listing():
    """Test retrieving an existing listing."""
    response = client.get("/api/listings/1")
    assert response.status_code == 200
    assert response.json()["postcode"] == "LS1 9ZZ"

def test_get_listing_not_found():
    """Test error handling for a non-existent listing."""
    response = client.get("/api/listings/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Property listing not found"

def test_affordability_calculator():
    """Test the analytics endpoint filtering logic."""
    response = client.get("/api/analytics/affordability?max_price=350000&min_bedrooms=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["price"] <= 350000
    assert data[0]["bedrooms"] >= 2