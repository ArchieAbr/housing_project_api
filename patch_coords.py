import os
import time
import requests

# Connect to your local database
os.environ["DATABASE_URL"] = "postgresql://user:password@localhost:5432/housing_db"

from app.db import SessionLocal
from app.models import PropertyListing

def patch_coordinates():
    database = SessionLocal()
    try:
        # 1. Get all listings where latitude is NULL
        listings = database.query(PropertyListing).filter(PropertyListing.latitude.is_(None)).all()
        print(f"Found {len(listings)} records missing coordinates.")
        
        if not listings:
            print("No records to update! Everything is fully geocoded.")
            return

        # 2. Extract unique postcodes to drastically reduce API calls
        postcode_map = {}
        for listing in listings:
            clean_pc = listing.postcode.strip()
            if clean_pc not in postcode_map:
                postcode_map[clean_pc] = []
            postcode_map[clean_pc].append(listing)

        unique_postcodes = list(postcode_map.keys())
        print(f"Extracted {len(unique_postcodes)} unique postcodes to look up.")

        # 3. Batch query the postcodes.io API
        batch_size = 100
        updated_count = 0

        for i in range(0, len(unique_postcodes), batch_size):
            batch = unique_postcodes[i:i + batch_size]
            
            print(f"Fetching batch {i//batch_size + 1} of {(len(unique_postcodes)//batch_size) + 1}...")
            response = requests.post("https://api.postcodes.io/postcodes", json={"postcodes": batch})
            
            if response.status_code == 200:
                results = response.json().get("result", [])
                for res in results:
                    query_pc = res.get("query")
                    data = res.get("result")
                    
                    # If the API found coordinates for this postcode...
                    if data and query_pc in postcode_map:
                        lat = data.get("latitude")
                        lon = data.get("longitude")
                        
                        # Update every single property in our database that shares this postcode
                        for listing in postcode_map[query_pc]:
                            listing.latitude = lat
                            listing.longitude = lon
                            updated_count += 1
            else:
                # If it fails this time, it will print the exact reason!
                print(f"API Error {response.status_code}: {response.text}")
                
            time.sleep(0.5) # Polite delay to avoid rate limiting
            
        # 4. Commit the updates to PostgreSQL
        database.commit()
        print(f"Successfully updated {updated_count} records with new coordinates!")

    except Exception as e:
        database.rollback()
        print(f"Error during patch: {e}")
    finally:
        database.close()

if __name__ == "__main__":
    patch_coordinates()