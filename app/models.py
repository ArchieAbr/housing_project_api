from sqlalchemy import Column, Integer, String, func
from sqlalchemy import Column, Integer, String
from .db import Base

class PropertyListing(Base):
    __tablename__ = "property_listings"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False)
    postcode = Column(String, index=True, nullable=False)
    # Concrete column for relational SQL joins
    postcode_district = Column(String, index=True, nullable=False) 
    price = Column(Integer, nullable=False)
    property_type = Column(String, nullable=False)
    bedrooms = Column(Integer, nullable=False)

class OfstedSchool(Base):
    __tablename__ = "ofsted_schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    postcode = Column(String, nullable=False)
    postcode_district = Column(String, index=True, nullable=False)
    rating = Column(String, nullable=False)