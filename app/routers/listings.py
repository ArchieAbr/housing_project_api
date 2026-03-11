import requests
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, db
from ..auth import verify_api_key
from ..exceptions import CustomAPIException

router = APIRouter(
    prefix="/api/listings",
    tags=["Listings"]
)

@router.post("/", response_model=schemas.PropertyListing, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
def create_listing(listing: schemas.PropertyListingCreate, database: Session = Depends(db.get_db)):
    db_listing = models.PropertyListing(**listing.model_dump())
    database.add(db_listing)
    database.commit()
    database.refresh(db_listing)
    return db_listing

@router.get("/", response_model=List[schemas.PropertyListing])
def get_all_listings(skip: int = 0, limit: int = 100, database: Session = Depends(db.get_db)):
    """Retrieve all listings with pagination to prevent database overload."""
    return database.query(models.PropertyListing).offset(skip).limit(limit).all()

def get_dynamic_crime_date():
    """Returns a string for the date 2 months ago (YYYY-MM) to account for Police API lag."""
    # UK Police data is usually delayed by ~2 months
    target_date = datetime.now() - relativedelta(months=2)
    return target_date.strftime("%Y-%m")

@router.get("/{listing_id}", response_model=schemas.PropertyListing)
def get_listing(listing_id: int, database: Session = Depends(db.get_db)):
    """Retrieve a single listing enriched with dynamic live crime data."""
    db_listing = database.query(models.PropertyListing).filter(models.PropertyListing.id == listing_id).first()
    
    if db_listing is None:
        raise CustomAPIException(
            name="ListingNotFoundError", 
            detail="Property listing not found", 
            status_code=status.HTTP_404_NOT_FOUND
        )

    # Convert SQLAlchemy object to dict via Pydantic for modification
    listing_data = schemas.PropertyListing.model_validate(db_listing).model_dump()

    # Dynamic date calculation
    crime_date = get_dynamic_crime_date()

    if db_listing.latitude and db_listing.longitude:
        try:
            police_url = "https://data.police.uk/api/crimes-street/all-crime"
            params = {
                "lat": db_listing.latitude,
                "lng": db_listing.longitude,
                "date": crime_date
            }
            response = requests.get(police_url, params=params, timeout=5)
            
            if response.status_code == 200:
                crimes = response.json()[:10]
                listing_data["local_crime"] = [
                    {
                        "category": c["category"].replace("-", " ").title(), 
                        "location_type": c["location_type"], 
                        "month": c["month"]
                    }
                    for c in crimes
                ]
        except Exception as e:
            # Log error internally but don't break the user experience
            print(f"External API Error: {e}")
            listing_data["local_crime"] = []

    return listing_data

@router.put("/{listing_id}", response_model=schemas.PropertyListing, dependencies=[Depends(verify_api_key)])
def update_listing(listing_id: int, updated_listing: schemas.PropertyListingCreate, database: Session = Depends(db.get_db)):
    listing_query = database.query(models.PropertyListing).filter(models.PropertyListing.id == listing_id)
    if not listing_query.first():
        raise CustomAPIException(
            name="NotFoundError",
            detail="Listing not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    listing_query.update(updated_listing.model_dump(), synchronize_session=False)
    database.commit()
    return listing_query.first()

@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_api_key)])
def delete_listing(listing_id: int, database: Session = Depends(db.get_db)):
    listing_query = database.query(models.PropertyListing).filter(models.PropertyListing.id == listing_id)
    if not listing_query.first():
        raise CustomAPIException(
            name="NotFoundError",
            detail="Listing not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    listing_query.delete(synchronize_session=False)
    database.commit()
    return None