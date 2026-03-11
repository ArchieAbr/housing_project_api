import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 1. Set up mock environment variables BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["API_KEY"] = "test_super_secret_key"

from app.main import app
from app.db import Base, get_db

# 2. Setup an in-memory SQLite database for isolated testing
engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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

# 3. Reusable test assets
AUTH_HEADERS = {"X-API-Key": "test_super_secret_key"}
MOCK_LISTING = {
    "address": "100 Test Avenue",
    "postcode": "LS1 9ZZ",
    "price": 300000,
    "property_type": "Semi-Detached",
    "bedrooms": 3
}

# --- AUTHENTICATION & SECURITY TESTS ---

def test_unauthorised_access():
    """Ensure protected endpoints reject requests without a valid API key."""
    response = client.post("/api/listings/", json=MOCK_LISTING)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"

def test_invalid_api_key():
    """Ensure protected endpoints reject requests with an incorrect API key."""
    response = client.post(
        "/api/listings/", 
        json=MOCK_LISTING, 
        headers={"X-API-Key": "wrong_key"}
    )
    assert response.status_code == 403

# --- CRUD ENDPOINT TESTS ---

def test_create_listing():
    """Test creating a new property listing with valid headers."""
    response = client.post("/api/listings/", json=MOCK_LISTING, headers=AUTH_HEADERS)
    assert response.status_code == 201
    assert response.json()["address"] == "100 Test Avenue"
    assert "id" in response.json()

def test_get_all_listings_pagination():
    """Test the GET all endpoint and its pagination logic."""
    response = client.get("/api/listings/?skip=0&limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_listing_success():
    """Test retrieving an existing listing (created in the previous test)."""
    response = client.get("/api/listings/1")
    assert response.status_code == 200
    assert response.json()["postcode"] == "LS1 9ZZ"

def test_get_listing_not_found():
    """Test error handling for a non-existent listing ID."""
    response = client.get("/api/listings/999")
    assert response.status_code == 404

def test_update_listing():
    """Test updating an existing listing."""
    updated_data = MOCK_LISTING.copy()
    updated_data["price"] = 350000
    
    response = client.put("/api/listings/1", json=updated_data, headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["price"] == 350000

def test_delete_listing():
    """Test deleting an existing listing."""
    response = client.delete("/api/listings/1", headers=AUTH_HEADERS)
    assert response.status_code == 204
    
    # Verify it was actually deleted
    verify_response = client.get("/api/listings/1")
    assert verify_response.status_code == 404

# --- DATA VALIDATION TESTS ---

def test_invalid_data_payload():
    """Test Pydantic validation (e.g., negative price)."""
    invalid_data = MOCK_LISTING.copy()
    invalid_data["price"] = -50000  # Should trigger a 422 Unprocessable Entity
    
    response = client.post("/api/listings/", json=invalid_data, headers=AUTH_HEADERS)
    assert response.status_code == 422

# --- ANALYTICS TESTS ---

def test_affordability_calculator():
    """Test the analytics endpoint filtering logic."""
    # First, inject a test listing so the database isn't empty
    client.post("/api/listings/", json=MOCK_LISTING, headers=AUTH_HEADERS)
    
    response = client.get("/api/analytics/affordability?max_price=350000&min_bedrooms=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["price"] <= 350000