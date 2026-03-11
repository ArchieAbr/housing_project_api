# app/routers/listings.py
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

@router.get("/{listing_id}", response_model=schemas.PropertyListing)
def get_listing(listing_id: int, database: Session = Depends(db.get_db)):
    db_listing = database.query(models.PropertyListing).filter(models.PropertyListing.id == listing_id).first()
    if db_listing is None:
        raise CustomAPIException(
            name="NotFoundError",
            detail="Property listing not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return db_listing

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