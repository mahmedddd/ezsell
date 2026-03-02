
import json
from sqlalchemy.orm import Session
from main import app
from models.database import SessionLocal, Listing, User
from schemas.schemas import ListingResponse
from typing import List

def check_api_output():
    db = SessionLocal()
    try:
        # Mimic my-listings logic
        user = db.query(User).filter(User.username == 'ahmed').first()
        if not user:
            print("User 'ahmed' not found")
            return
            
        listings = db.query(Listing).filter(Listing.owner_id == user.id).all()
        print(f"Found {len(listings)} listings for user {user.username}")
        
        # Manually serialize using the Pydantic model
        serialized = [ListingResponse.from_orm(l).dict() for l in listings]
        
        if serialized:
            print(f"Keys found in serialized output: {list(serialized[0].keys())}")
            print(f"ID: {serialized[0]['id']}")
            print(f"is_active: {serialized[0].get('is_active')}")
            print(f"approval_status: {serialized[0].get('approval_status')}")
            print(f"is_sold: {serialized[0].get('is_sold')}")
            
        # Check raw JSON string
        print("\nRaw JSON for first listing:")
        if serialized:
            # Handle datetime sterilization
            def datetime_handler(x):
                if hasattr(x, 'isoformat'):
                    return x.isoformat()
                raise TypeError
            print(json.dumps(serialized[0], default=datetime_handler, indent=2))
            
    finally:
        db.close()

if __name__ == "__main__":
    check_api_output()
