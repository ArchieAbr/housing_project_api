from fastapi import APIRouter, Depends, HTTPException, status
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