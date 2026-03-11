import os
# Force the script to connect via localhost since it is running outside Docker
os.environ["DATABASE_URL"] = "postgresql://user:password@localhost:5432/housing_db"

import csv
import random
from app.db import SessionLocal, engine, Base
from app.models import PropertyListing

Base.metadata.create_all(bind=engine)

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
    return random.randint(1, 3) # For 'Other' or unknown

def build_address(row: dict) -> str:
    """Combine available address parts into a single string."""
    parts = [row.get('saon', ''), row.get('paon', ''), row.get('street', '')]
    # Filter out empty strings and join with a comma
    clean_parts = [p.strip() for p in parts if p and p.strip()]
    return ", ".join(clean_parts)

def import_csv_to_db(filepath: str):
    """Read Land Registry CSV data and bulk insert into PostgreSQL."""
    database = SessionLocal()
    
    try:
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            listings_to_add = []
            
            for row in reader:
                # Skip rows missing crucial data like price or postcode
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
                
            # Bulk save for better performance
            database.bulk_save_objects(listings_to_add)
            database.commit()
            print(f"Successfully imported {len(listings_to_add)} records from Leeds.")
            
    except Exception as e:
        database.rollback()
        print(f"Error importing data: {e}")
        
    finally:
        database.close()

if __name__ == "__main__":
    import_csv_to_db('leeds_housing_data.csv')