from pydantic import BaseModel, Field, ConfigDict

# 1. Base Schema: Contains the shared attributes
class PropertyListingBase(BaseModel):
    address: str = Field(..., description="The first line of the address")
    # ADDED REGEX for standard UK postcodes (allows optional space)
    postcode: str = Field(..., pattern=r"^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$", description="A valid UK postcode")
    price: int = Field(..., gt=0, description="The property price in GBP, must be strictly greater than 0")
    property_type: str = Field(..., description="e.g., Detached, Flat, Terraced")
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms, cannot be negative")

# 2. Create Schema: Used specifically when a user sends a POST request to create a new listing
class PropertyListingCreate(PropertyListingBase):
    pass # Inherits everything from the Base schema without adding anything new

# 3. Response Schema: Used when the API sends data back to the user
class PropertyListing(PropertyListingBase):
    id: int
    model_config = ConfigDict(from_attributes=True)