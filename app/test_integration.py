"""
Integration Test Suite for Leeds Housing Market API

This module tests the deployed Azure API endpoints to validate
that everything is working correctly in production.

Setup:
    1. Copy .env.example to .env in the project root
    2. Fill in your TEST_API_KEY value
    3. Load the environment variables before running tests

Usage (PowerShell):
    # Load environment variables from .env
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#][^=]*)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
        }
    }
    
    # Run integration tests
    pytest app/test_integration.py -v

Usage (Bash):
    export $(grep -v '^#' .env | xargs)
    pytest app/test_integration.py -v

Note: These tests run against the LIVE deployed API.
      Never commit your .env file - it contains secrets!
"""

import os
import pytest
import httpx
from typing import Generator

# =============================================================================
# CONFIGURATION
# =============================================================================

API_URL = os.getenv("TEST_API_URL", "https://housing-project-api-bda2hwf3fzfvg0bb.francecentral-01.azurewebsites.net")
API_KEY = os.getenv("TEST_API_KEY", "")

# Skip all tests if API key is not configured
pytestmark = pytest.mark.skipif(
    not API_KEY,
    reason="TEST_API_KEY environment variable not set"
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def client() -> Generator[httpx.Client, None, None]:
    """Create a reusable HTTP client for all tests."""
    with httpx.Client(base_url=API_URL, timeout=30.0) as c:
        yield c


@pytest.fixture
def auth_headers() -> dict:
    """Headers with valid API key for authenticated requests."""
    return {"X-API-Key": API_KEY}


@pytest.fixture
def test_listing() -> dict:
    """Sample listing data for testing."""
    return {
        "address": "INTEGRATION TEST - 999 Test Lane",
        "postcode": "LS1 1AA",
        "price": 999999,
        "property_type": "Test-Property",
        "bedrooms": 99
    }


# =============================================================================
# HEALTH & CONNECTIVITY TESTS
# =============================================================================

class TestConnectivity:
    """Verify the API is reachable and responding."""

    def test_api_root_responds(self, client: httpx.Client):
        """API root should return a response (docs redirect or health check)."""
        response = client.get("/")
        assert response.status_code in [200, 307, 404], \
            f"API root returned unexpected status: {response.status_code}"

    def test_swagger_docs_available(self, client: httpx.Client):
        """Swagger UI documentation should be accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()

    def test_openapi_schema_available(self, client: httpx.Client):
        """OpenAPI JSON schema should be accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert data["info"]["title"] == "UK Housing Market API"


# =============================================================================
# AUTHENTICATION TESTS
# =============================================================================

class TestAuthentication:
    """Verify API key authentication is working correctly."""

    def test_protected_endpoint_rejects_missing_key(self, client: httpx.Client, test_listing: dict):
        """POST without API key should return 403."""
        response = client.post("/api/listings/", json=test_listing)
        assert response.status_code == 403
        data = response.json()
        assert data["error"] == "AuthenticationError"
        assert "Invalid or missing API Key" in data["message"]

    def test_protected_endpoint_rejects_invalid_key(self, client: httpx.Client, test_listing: dict):
        """POST with wrong API key should return 403."""
        response = client.post(
            "/api/listings/",
            json=test_listing,
            headers={"X-API-Key": "completely_wrong_key_12345"}
        )
        assert response.status_code == 403
        data = response.json()
        assert data["error"] == "AuthenticationError"

    def test_protected_endpoint_accepts_valid_key(self, client: httpx.Client, test_listing: dict, auth_headers: dict):
        """POST with correct API key should succeed."""
        response = client.post("/api/listings/", json=test_listing, headers=auth_headers)
        assert response.status_code == 201
        
        # Clean up: delete the created listing
        listing_id = response.json()["id"]
        client.delete(f"/api/listings/{listing_id}", headers=auth_headers)


# =============================================================================
# LISTINGS CRUD TESTS
# =============================================================================

class TestListingsCRUD:
    """Test full Create, Read, Update, Delete lifecycle."""

    def test_full_crud_lifecycle(self, client: httpx.Client, test_listing: dict, auth_headers: dict):
        """Test complete CRUD operations on a single listing."""
        
        # CREATE
        create_response = client.post("/api/listings/", json=test_listing, headers=auth_headers)
        assert create_response.status_code == 201, f"Create failed: {create_response.text}"
        created = create_response.json()
        listing_id = created["id"]
        assert created["address"] == test_listing["address"]
        assert created["price"] == test_listing["price"]
        
        # READ (single)
        read_response = client.get(f"/api/listings/{listing_id}")
        assert read_response.status_code == 200
        assert read_response.json()["id"] == listing_id
        
        # UPDATE
        updated_data = test_listing.copy()
        updated_data["price"] = 888888
        update_response = client.put(
            f"/api/listings/{listing_id}",
            json=updated_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["price"] == 888888
        
        # DELETE
        delete_response = client.delete(f"/api/listings/{listing_id}", headers=auth_headers)
        assert delete_response.status_code == 204
        
        # VERIFY DELETION
        verify_response = client.get(f"/api/listings/{listing_id}")
        assert verify_response.status_code == 404

    def test_get_all_listings_returns_list(self, client: httpx.Client):
        """GET /api/listings/ should return a list."""
        response = client.get("/api/listings/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_pagination_parameters(self, client: httpx.Client):
        """Pagination with skip and limit should work."""
        response = client.get("/api/listings/?skip=0&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_get_nonexistent_listing_returns_404(self, client: httpx.Client):
        """Getting a non-existent listing should return 404."""
        response = client.get("/api/listings/999999999")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "ListingNotFoundError"


# =============================================================================
# DATA VALIDATION TESTS
# =============================================================================

class TestDataValidation:
    """Verify request validation is working correctly."""

    def test_invalid_postcode_rejected(self, client: httpx.Client, auth_headers: dict):
        """Invalid UK postcode format should be rejected."""
        invalid_listing = {
            "address": "Test Address",
            "postcode": "NOT A VALID POSTCODE",
            "price": 100000,
            "property_type": "Flat",
            "bedrooms": 2
        }
        response = client.post("/api/listings/", json=invalid_listing, headers=auth_headers)
        assert response.status_code == 422  # Validation error

    def test_negative_price_rejected(self, client: httpx.Client, auth_headers: dict):
        """Negative price should be rejected."""
        invalid_listing = {
            "address": "Test Address",
            "postcode": "LS1 1AA",
            "price": -50000,
            "property_type": "Flat",
            "bedrooms": 2
        }
        response = client.post("/api/listings/", json=invalid_listing, headers=auth_headers)
        assert response.status_code == 422

    def test_zero_price_rejected(self, client: httpx.Client, auth_headers: dict):
        """Zero price should be rejected (price must be > 0)."""
        invalid_listing = {
            "address": "Test Address",
            "postcode": "LS1 1AA",
            "price": 0,
            "property_type": "Flat",
            "bedrooms": 2
        }
        response = client.post("/api/listings/", json=invalid_listing, headers=auth_headers)
        assert response.status_code == 422

    def test_negative_bedrooms_rejected(self, client: httpx.Client, auth_headers: dict):
        """Negative bedroom count should be rejected."""
        invalid_listing = {
            "address": "Test Address",
            "postcode": "LS1 1AA",
            "price": 100000,
            "property_type": "Flat",
            "bedrooms": -1
        }
        response = client.post("/api/listings/", json=invalid_listing, headers=auth_headers)
        assert response.status_code == 422

    def test_missing_required_field_rejected(self, client: httpx.Client, auth_headers: dict):
        """Missing required fields should be rejected."""
        incomplete_listing = {
            "address": "Test Address",
            # Missing: postcode, price, property_type, bedrooms
        }
        response = client.post("/api/listings/", json=incomplete_listing, headers=auth_headers)
        assert response.status_code == 422


# =============================================================================
# ANALYTICS ENDPOINT TESTS
# =============================================================================

class TestAnalytics:
    """Test analytics endpoints."""

    def test_market_summary_returns_data(self, client: httpx.Client):
        """Market summary should return aggregated data."""
        response = client.get("/api/analytics/market-summary")
        # Could be 200 (with data) or 404 (no data)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            if len(data) > 0:
                assert "property_type" in data[0]
                assert "total_listings" in data[0]
                assert "average_price" in data[0]

    def test_affordability_with_valid_params(self, client: httpx.Client):
        """Affordability search with valid parameters."""
        response = client.get("/api/analytics/affordability?max_price=500000&min_bedrooms=2")
        # Could be 200 (found properties) or 404 (none match)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            # Verify all returned properties meet criteria
            for listing in data:
                assert listing["price"] <= 500000
                assert listing["bedrooms"] >= 2

    def test_affordability_requires_max_price(self, client: httpx.Client):
        """Affordability search requires max_price parameter."""
        response = client.get("/api/analytics/affordability")
        assert response.status_code == 422  # Missing required param
    def test_smart_search_valid_query(self, client: httpx.Client):
        """Smart search should successfully parse a natural language string using Gemini."""
        payload = {"query": "Find me a detached family home in LS6 for under 350000"}
        response = client.post("/api/analytics/smart-search", json=payload)
        
        # If the GEMINI_API_KEY is missing on Azure, it raises a 500 error. 
        # If configured, it should return 200.
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}. Response: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            assert "ai_interpretation" in data
            assert "results_count" in data
            assert "properties" in data
            assert isinstance(data["properties"], list)
            
            # Verify the AI correctly extracted the parameters from the sentence
            interpretation = data["ai_interpretation"]
            assert interpretation.get("property_type") == "Detached"
            assert interpretation.get("postcode_district") == "LS6"
            assert interpretation.get("max_price") == 350000

    def test_smart_search_missing_query(self, client: httpx.Client):
        """Smart search should reject requests without a query string."""
        response = client.post("/api/analytics/smart-search", json={})
        assert response.status_code == 422

# =============================================================================
# RESPONSE FORMAT TESTS
# =============================================================================

class TestResponseFormat:
    """Verify response formats match expected schemas."""

    def test_listing_response_schema(self, client: httpx.Client, test_listing: dict, auth_headers: dict):
        """Verify listing response contains all expected fields."""
        # Create a listing
        response = client.post("/api/listings/", json=test_listing, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        
        # Verify all expected fields are present
        expected_fields = ["id", "address", "postcode", "price", "property_type", "bedrooms"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify types
        assert isinstance(data["id"], int)
        assert isinstance(data["address"], str)
        assert isinstance(data["postcode"], str)
        assert isinstance(data["price"], int)
        assert isinstance(data["property_type"], str)
        assert isinstance(data["bedrooms"], int)
        
        # Clean up
        client.delete(f"/api/listings/{data['id']}", headers=auth_headers)

    def test_error_response_schema(self, client: httpx.Client):
        """Verify error responses have consistent format."""
        response = client.get("/api/listings/999999999")
        assert response.status_code == 404
        data = response.json()
        
        # Custom errors should have 'error' and 'message' keys
        assert "error" in data
        assert "message" in data


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Basic performance sanity checks."""

    def test_listings_endpoint_responds_quickly(self, client: httpx.Client):
        """Listings endpoint should respond within acceptable time."""
        import time
        start = time.time()
        response = client.get("/api/listings/?limit=10")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 5.0, f"Response took {elapsed:.2f}s, expected < 5s"

    def test_analytics_endpoint_responds_quickly(self, client: httpx.Client):
        """Analytics endpoint should respond within acceptable time."""
        import time
        start = time.time()
        response = client.get("/api/analytics/market-summary")
        elapsed = time.time() - start
        
        assert response.status_code in [200, 404]
        assert elapsed < 10.0, f"Response took {elapsed:.2f}s, expected < 10s"
    
    def test_smart_search_responds_within_llm_limits(self, client: httpx.Client):
        """Smart search (LLM call) should respond within acceptable time limit."""
        import time
        start = time.time()
        payload = {"query": "I am looking for a flat in LS1"}
        response = client.post("/api/analytics/smart-search", json=payload)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            # LLM API calls typically take 1-4 seconds. We allow up to 10s for network variance.
            assert elapsed < 10.0, f"LLM API response took {elapsed:.2f}s, expected < 10s"


# =============================================================================
# CLEANUP HELPER
# =============================================================================

@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data(client: httpx.Client):
    """Clean up any test data after all tests complete."""
    yield
    
    # After all tests, try to delete any leftover test listings
    if API_KEY:
        headers = {"X-API-Key": API_KEY}
        try:
            response = client.get("/api/listings/?limit=1000")
            if response.status_code == 200:
                for listing in response.json():
                    if "INTEGRATION TEST" in listing.get("address", ""):
                        client.delete(f"/api/listings/{listing['id']}", headers=headers)
        except Exception:
            pass  # Best effort cleanup
