import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 1. Mock Environment
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["API_KEY"] = "test_super_secret_key"

from app.main import app
from app.db import Base, get_db
from app.models import PropertyListing

# 2. Database Setup for Testing
engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Dependency override
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# 3. Test Constants
AUTH_HEADERS = {"X-API-Key": "test_super_secret_key"}
MOCK_LISTING = {
    "address": "100 Test Avenue",
    "postcode": "LS1 2BH",
    "price": 300000,
    "property_type": "Semi-Detached",
    "bedrooms": 3
}

@pytest.fixture(autouse=True)
def setup_db():
    """Wipe and recreate tables for every test to ensure isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

# --- SECURITY & AUTHENTICATION TESTS ---

def test_unauthorised_access():
    """Ensure protected endpoints return correct CustomAPIException structure."""
    response = client.post("/api/listings/", json=MOCK_LISTING)
    assert response.status_code == 403
    data = response.json()
    assert data["error"] == "AuthenticationError"
    assert "message" in data # Fixes the KeyError: 'detail'

def test_invalid_api_key():
    response = client.post("/api/listings/", json=MOCK_LISTING, headers={"X-API-Key": "wrong"})
    assert response.status_code == 403

def test_security_on_update_and_delete():
    """Verify PUT and DELETE also require auth."""
    client.post("/api/listings/", json=MOCK_LISTING, headers=AUTH_HEADERS)
    assert client.put("/api/listings/1", json=MOCK_LISTING).status_code == 403
    assert client.delete("/api/listings/1").status_code == 403

# --- CRUD & FUNCTIONALITY TESTS ---

def test_create_listing_integrity():
    """Verify listing is actually in the DB after POST."""
    response = client.post("/api/listings/", json=MOCK_LISTING, headers=AUTH_HEADERS)
    assert response.status_code == 201
    
    db = TestingSessionLocal()
    listing = db.query(PropertyListing).first()
    assert listing.address == "100 Test Avenue"
    db.close()

def test_get_listing_not_found():
    response = client.get("/api/listings/999")
    assert response.status_code == 404
    assert response.json()["error"] == "ListingNotFoundError"

def test_pagination_logic():
    """Test skip and limit functionality."""
    for i in range(5):
        client.post("/api/listings/", json=MOCK_LISTING, headers=AUTH_HEADERS)
    
    response = client.get("/api/listings/?skip=2&limit=2")
    assert len(response.json()) == 2

# --- DATA VALIDATION TESTS ---

def test_invalid_postcode_regex():
    invalid_data = MOCK_LISTING.copy()
    invalid_data["postcode"] = "NOT A PC"
    response = client.post("/api/listings/", json=invalid_data, headers=AUTH_HEADERS)
    assert response.status_code == 422

def test_negative_price_rejected():
    invalid_data = MOCK_LISTING.copy()
    invalid_data["price"] = -100
    response = client.post("/api/listings/", json=invalid_data, headers=AUTH_HEADERS)
    assert response.status_code == 422