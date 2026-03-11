from sqlalchemy import Column, Integer, String, func
from .db import Base

class PropertyListing(Base):
    __tablename__ = "property_listings"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False)
    postcode = Column(String, index=True, nullable=False)
    price = Column(Integer, nullable=False)
    property_type = Column(String, nullable=False)
    bedrooms = Column(Integer, nullable=False)
    
    # NEW GEOSPATIAL COLUMNS
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)