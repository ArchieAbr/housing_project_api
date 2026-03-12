import os
import csv
import random
from .db import SessionLocal
from .models import PropertyListing, OfstedSchool

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

def get_postcode_district(postcode: str) -> str:
    """Extract the district (e.g., 'LS6') from a full postcode (e.g., 'LS6 1PF')."""
    postcode = postcode.strip()
    return postcode.split(" ")[0] if " " in postcode else postcode[:-3]

def parse_ofsted_rating(row: dict) -> str:
    """Intelligently extract and normalise the rating from Gov CSV data."""
    graded = row.get('Latest OEIF overall effectiveness', '').strip().lower()
    ungraded = row.get('Ungraded inspection overall outcome', '').strip().lower()
    
    if graded in ['1', 'outstanding']: return 'Outstanding'
    if graded in ['2', 'good']: return 'Good'
    if graded in ['3', 'requires improvement']: return 'Requires Improvement'
    if graded in ['4', 'inadequate']: return 'Inadequate'
    
    if 'outstanding' in ungraded: return 'Outstanding'
    if 'good' in ungraded or 'standards maintained' in ungraded: return 'Good'
    if 'serious weaknesses' in ungraded or 'inadequate' in ungraded: return 'Inadequate'
    
    return 'Not Rated / Unknown'

def find_csv_file(filename: str) -> str:
    """Find the specified CSV data file in various possible locations."""
    csv_paths = [
        f"/code/{filename}",
        filename,
        os.path.join(os.path.dirname(__file__), "..", filename),
    ]
    for path in csv_paths:
        if os.path.exists(path):
            return path
    return None

def seed_schools(database):
    """Seed the database with real Ofsted school data from CSV."""
    if database.query(OfstedSchool).count() > 0:
        return

    csv_path = find_csv_file("leeds_ofsted_data.csv")
    if not csv_path:
        print("WARNING: leeds_ofsted_data.csv not found.")
        return

    print(f"Seeding schools from {csv_path}...")
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            schools_to_add = []
            
            for row in reader:
                name = row.get('School name')
                postcode = row.get('Postcode')
                
                if not name or not postcode:
                    continue
                    
                school = OfstedSchool(
                    name=name.strip(),
                    postcode=postcode.strip(),
                    postcode_district=get_postcode_district(postcode),
                    rating=parse_ofsted_rating(row)
                )
                schools_to_add.append(school)
            
            database.bulk_save_objects(schools_to_add)
            database.commit()
            print(f"Successfully seeded database with {len(schools_to_add)} schools.")
    except Exception as e:
        database.rollback()
        print(f"Error seeding schools: {e}")

def seed_properties(database):
    """Seed the database with Land Registry property data from CSV."""
    if database.query(PropertyListing).count() > 0:
        return
    
    csv_path = find_csv_file("leeds_housing_data.csv")
    if not csv_path:
        print("WARNING: leeds_housing_data.csv not found.")
        return
    
    print(f"Seeding properties from {csv_path}...")
    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            listings_to_add = []
            
            for row in reader:
                if not row.get('price_paid') or not row.get('postcode'):
                    continue
                    
                raw_type = row.get('property_type', 'O')
                postcode = row['postcode'].strip()
                
                listing = PropertyListing(
                    address=build_address(row),
                    postcode=postcode,
                    postcode_district=get_postcode_district(postcode),
                    price=int(row['price_paid']),
                    property_type=PROPERTY_TYPE_MAP.get(raw_type, 'Other'),
                    bedrooms=generate_mock_bedrooms(raw_type)
                )
                listings_to_add.append(listing)
            
            database.bulk_save_objects(listings_to_add)
            database.commit()
            print(f"Successfully seeded database with {len(listings_to_add)} listings.")
    except Exception as e:
        database.rollback()
        print(f"Error seeding properties: {e}")

def seed_database_if_empty():
    """Main seeder function called on app lifespan startup."""
    database = SessionLocal()
    try:
        seed_schools(database)
        seed_properties(database)
    finally:
        database.close()