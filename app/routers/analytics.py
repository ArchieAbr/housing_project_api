import os
import json
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from .. import models, schemas, db
from ..db import get_db
from ..models import PropertyListing
router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"]
)

# Configure the Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class SmartSearchRequest(BaseModel):
    query: str

@router.post("/smart-search")
def smart_property_search(request: SmartSearchRequest, db: Session = Depends(get_db)):
    """
    Creative GenAI Feature: Translate a natural language sentence into a database query.
    Example: "I need a detached family home in LS6 with 3 bedrooms for under £350k"
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured on the server.")

    # 1. Advanced Prompt Engineering with Inference Rules
    prompt = f"""
    You are an expert UK property market data extraction tool. Extract search parameters from the user's query.
    
    Inference Rules:
    - If the user asks for a 'house' or 'home', they mean ANY house. Return: ["Detached", "Semi-Detached", "Terraced"]
    - If the user asks for a 'flat' or 'apartment', return: ["Flat"]
    - If the user explicitly asks for a specific type (e.g., 'detached house'), return just that type: ["Detached"]
    - If no property type is mentioned, return null.
    - If no maximum price is mentioned, return null.

    User Query: "{request.query}"
    
    Return ONLY a valid JSON object with these exact keys: 
    "max_price" (integer or null), 
    "min_bedrooms" (integer or null), 
    "property_types" (list of strings or null),
    "postcode_district" (string or null, e.g., 'LS6')
    """

    try:
        # 2. Call the Gemini API
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        # Strip any markdown formatting
        clean_json_string = response.text.replace("```json", "").replace("```", "").strip()
        search_params = json.loads(clean_json_string)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI parsing failed: {str(e)}")

    # 3. Dynamically build the SQLAlchemy query 
    db_query = db.query(PropertyListing)
    
    if search_params.get("max_price"):
        db_query = db_query.filter(PropertyListing.price <= search_params["max_price"])
    if search_params.get("min_bedrooms"):
        db_query = db_query.filter(PropertyListing.bedrooms >= search_params["min_bedrooms"])
        
    # NEW: Handle a list of property types using SQLAlchemy's .in_() operator
    if search_params.get("property_types"):
        db_query = db_query.filter(PropertyListing.property_type.in_(search_params["property_types"]))
        
    if search_params.get("postcode_district"):
        db_query = db_query.filter(PropertyListing.postcode.like(f"{search_params['postcode_district']}%"))

    # 4. Execute and return
    results = db_query.order_by(PropertyListing.price.asc()).limit(20).all()
    
    return {
        "ai_interpretation": search_params,
        "results_count": len(results),
        "properties": results
    }

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