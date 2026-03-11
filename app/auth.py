import os
from fastapi import Security, status
from fastapi.security.api_key import APIKeyHeader
from .exceptions import CustomAPIException  # Import it here

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    expected_key = os.getenv("API_KEY")
    
    if not api_key or api_key != expected_key:
        raise CustomAPIException(
            name="AuthenticationError",
            detail="Invalid or missing API Key",
            status_code=status.HTTP_403_FORBIDDEN
        )
    return api_key