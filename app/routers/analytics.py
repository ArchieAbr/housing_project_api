import requests
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, db

router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"]
)

@router.get("/market-summary")
def get_market_summary(database: Session = Depends(db.get_db)):
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
    return [{"property_type": row.property_type, "total_listings": row.total_listings, "average_price": row.average_price} for row in summary]

@router.get("/affordability", response_model=List[schemas.PropertyListing])
def calculate_affordability(max_price: int, min_bedrooms: int = 1, database: Session = Depends(db.get_db)):
    affordable_properties = (
        database.query(models.PropertyListing)
        .filter(models.PropertyListing.price <= max_price)
        .filter(models.PropertyListing.bedrooms >= min_bedrooms)
        .order_by(models.PropertyListing.bedrooms.desc(), models.PropertyListing.price.asc())
        .limit(10)
        .all()
    )
    if not affordable_properties:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No properties found matching these criteria")
    return affordable_properties

@router.get("/radius-search", response_model=List[schemas.PropertyListing])
def search_properties_by_radius(
    postcode: str = Query(..., description="The central UK postcode to search around"),
    radius_miles: float = Query(5.0, gt=0, description="Search radius in miles"),
    max_price: int = Query(None, description="Optional maximum price filter"),
    min_bedrooms: int = Query(None, description="Optional minimum bedrooms filter"),
    database: Session = Depends(db.get_db)
):
    """Find properties within a specific radius of a given UK postcode."""
    
    # 1. Geocode the target postcode using the free postcodes.io API
    clean_postcode = postcode.replace(" ", "").lower()
    geo_response = requests.get(f"https://api.postcodes.io/postcodes/{clean_postcode}")
    
    if geo_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid or unrecognised UK postcode provided")
        
    target_data = geo_response.json()["result"]
    target_lat = target_data["latitude"]
    target_lon = target_data["longitude"]

    # 2. Construct the Haversine formula in SQLAlchemy to calculate distance in miles
    # Earth's radius is roughly 3959 miles
    distance_calc = (
        3959 * func.acos(
            func.cos(func.radians(target_lat)) * func.cos(func.radians(models.PropertyListing.latitude)) *
            func.cos(func.radians(models.PropertyListing.longitude) - func.radians(target_lon)) +
            func.sin(func.radians(target_lat)) * func.sin(func.radians(models.PropertyListing.latitude))
        )
    )

    # 3. Build the query
    query = database.query(models.PropertyListing).filter(
        models.PropertyListing.latitude.isnot(None),
        models.PropertyListing.longitude.isnot(None),
        distance_calc <= radius_miles
    )
    
    # 4. Apply optional filters dynamically
    if max_price:
        query = query.filter(models.PropertyListing.price <= max_price)
    if min_bedrooms:
        query = query.filter(models.PropertyListing.bedrooms >= min_bedrooms)

    results = query.order_by(distance_calc.asc()).limit(50).all()
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No properties found within {radius_miles} miles of {postcode}")
        
    return results