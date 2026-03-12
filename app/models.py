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
    
    # A dynamic property to extract the district (e.g., 'LS6' from 'LS6 1PF')
    @property
    def postcode_district(self):
        return self.postcode.split(" ")[0] if " " in self.postcode else self.postcode[:-3]

class OfstedSchool(Base):
    __tablename__ = "ofsted_schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    postcode = Column(String, nullable=False)
    postcode_district = Column(String, index=True, nullable=False) # e.g., 'LS6'
    rating = Column(String, nullable=False) # e.g., 'Outstanding', 'Good'