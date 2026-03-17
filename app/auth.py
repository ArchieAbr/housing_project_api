import os
from fastapi import Header, status
from .exceptions import CustomAPIException

async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key", include_in_schema=True)):
    expected_key = os.getenv("API_KEY")
    
    if not x_api_key or x_api_key != expected_key:
        raise CustomAPIException(
            name="AuthenticationError",
            detail="Invalid or missing API Key",
            status_code=status.HTTP_403_FORBIDDEN
        )
    return x_api_key