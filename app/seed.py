# app/seed.py
import os
import csv
import random
from .db import SessionLocal
from .models import PropertyListing

# Map Land Registry property types to readable strings
PROPERTY_TYPE_MAP = {
    'D': 'Detached',
    'S': 'Semi-Detached',
    'T': 'Terraced',
    'F': 'Flat',
    'O': 'Other'
}

def generate_mock_bedrooms(property_type: str) -> int:
    """Mock bedroom counts based on the type of property."""
    if property_type == 'F': return random.randint(1, 2)
    if property_type == 'T': return random.randint(2, 3)
    if property_type == 'S': return random.randint(3, 4)
    if property_type == 'D': return random.randint(4, 5)
    return random.randint(1, 3)

def build_address(row: dict) -> str:
    """Combine available address parts into a single string."""
    parts = [row.get('saon', ''), row.get('paon', ''), row.get('street', '')]
    clean_parts = [p.strip() for p in parts if p and p.strip()]
    return ", ".join(clean_parts)

def find_csv_file() -> str:
    """Find the CSV data file in various possible locations."""
    csv_paths = [
        "/code/leeds_housing_data.csv",     # Docker container path
        "leeds_housing_data.csv",           # Root working directory
        os.path.join(os.path.dirname(__file__), "..", "leeds_housing_data.csv"),
    ]
    
    for path in csv_paths:
        if os.path.exists(path):
            return path
    return None

def seed_database_if_empty():
    """
    Check if database is empty and seed with CSV data if so.
    This function is idempotent - it will only seed once.
    """
    database = SessionLocal()
    
    try:
        # Check if data already exists
        existing_count = database.query(PropertyListing).count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} listings. Skipping seed.")
            return
        
        # Find CSV file
        csv_path = find_csv_file()
        if not csv_path:
            print("WARNING: CSV data file not found. Database will remain empty.")
            return
        
        print(f"Seeding database from {csv_path}...")
        
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            listings_to_add = []
            
            for row in reader:
                if not row.get('price_paid') or not row.get('postcode'):
                    continue
                    
                raw_type = row.get('property_type', 'O')
                mapped_type = PROPERTY_TYPE_MAP.get(raw_type, 'Other')
                
                listing = PropertyListing(
                    address=build_address(row),
                    postcode=row['postcode'],
                    price=int(row['price_paid']),
                    property_type=mapped_type,
                    bedrooms=generate_mock_bedrooms(raw_type)
                )
                listings_to_add.append(listing)
            
            database.bulk_save_objects(listings_to_add)
            database.commit()
            print(f"Successfully seeded database with {len(listings_to_add)} listings.")
            
    except Exception as e:
        database.rollback()
        print(f"Error seeding database: {e}")
        
    finally:
        database.close()
