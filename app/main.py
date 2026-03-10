from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security.api_key import APIKeyHeader
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

# --- READ (Analytics: Market Summary) ---
@app.get("/api/analytics/market-summary", tags=["Analytics"])
def get_market_summary(database: Session = Depends(get_db)):
    """Retrieve aggregate market statistics grouped by property type."""
    summary = (
        database.query(
            models.PropertyListing.property_type,
            func.count(models.PropertyListing.id).label("total_listings"),
            func.round(func.avg(models.PropertyListing.price)).label("average_price")
        )
        .group_by(models.PropertyListing.property_type)
        .all()
    )
    
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No listing data available for analysis")

    # Format the raw database rows into a clean list of dictionaries
    return [
        {
            "property_type": row.property_type, 
            "total_listings": row.total_listings, 
            "average_price": row.average_price
        } 
        for row in summary
    ]
    
# --- READ (Analytics: Affordability Calculator) ---
@app.get("/api/analytics/affordability", response_model=List[schemas.PropertyListing], tags=["Analytics"])
def calculate_affordability(
    max_price: int, 
    min_bedrooms: int = 1, 
    database: Session = Depends(get_db)
):
    """Find the top 10 largest properties within a specific budget."""
    
    # Query properties matching budget and bedroom criteria
    affordable_properties = (
        database.query(models.PropertyListing)
        .filter(models.PropertyListing.price <= max_price)
        .filter(models.PropertyListing.bedrooms >= min_bedrooms)
        # Sort by largest first, then lowest price
        .order_by(models.PropertyListing.bedrooms.desc(), models.PropertyListing.price.asc())
        # Restrict payload size
        .limit(10)
        .all()
    )
    
    # Handle empty result sets
    if not affordable_properties:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No properties found matching these criteria"
        )
        
    return affordable_properties