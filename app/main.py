from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas, db

# Automatically creates the tables PostgreSQL database based on the models.py file
models.Base.metadata.create_all(bind=db.engine)

app = FastAPI(
    title="UK Housing Market API",
    description="An API providing insights and data on the UK housing market.",
    version="1.0.0"
)

# Dependency: This function provides a fresh database session for each request securely closes it afterwards.
def get_db():
    database = db.SessionLocal()
    try:
        yield database
    finally:
        database.close()

# --- CREATE (POST) ---
@app.post("/api/listings", response_model=schemas.PropertyListing, status_code=status.HTTP_201_CREATED)
def create_listing(listing: schemas.PropertyListingCreate, database: Session = Depends(get_db)):
    """
    Add a new property listing to the database.
    """
    # Convert the validated Pydantic schema into a SQLAlchemy model
    db_listing = models.PropertyListing(**listing.model_dump())
    
    # Add to the database and commit the transaction
    database.add(db_listing)
    database.commit()
    database.refresh(db_listing)
    
    return db_listing

# --- READ (GET Single Item) ---
@app.get("/api/listings/{listing_id}", response_model=schemas.PropertyListing)
def get_listing(listing_id: int, database: Session = Depends(get_db)):
    """
    Retrieve a specific property listing by its ID.
    """
    # Query the database for the specific ID
    db_listing = database.query(models.PropertyListing).filter(models.PropertyListing.id == listing_id).first()
    
    # If it doesn't exist, return 404 error
    if db_listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property listing not found")
        
    return db_listing

# --- UPDATE (PUT) ---
@app.put("/api/listings/{listing_id}", response_model=schemas.PropertyListing)
def update_listing(listing_id: int, updated_listing: schemas.PropertyListingCreate, database: Session = Depends(get_db)):
    """Update an existing property listing."""
    listing_query = database.query(models.PropertyListing).filter(models.PropertyListing.id == listing_id)
    db_listing = listing_query.first()
    
    if not db_listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
        
    listing_query.update(updated_listing.model_dump(), synchronize_session=False)
    database.commit()
    
    return listing_query.first()

# --- DELETE (DELETE) ---
@app.delete("/api/listings/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(listing_id: int, database: Session = Depends(get_db)):
    """Remove a property listing from the database."""
    listing_query = database.query(models.PropertyListing).filter(models.PropertyListing.id == listing_id)
    db_listing = listing_query.first()
    
    if not db_listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
        
    listing_query.delete(synchronize_session=False)
    database.commit()
    
    return None