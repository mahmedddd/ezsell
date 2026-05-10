import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from backend.models.database import SessionLocal, Listing, User
from backend.routers.listings import get_my_listings

def test_endpoints():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            print("No users found.")
            return

        print(f"Testing for user: {user.username}")
        # test get_my_listings
        res = get_my_listings(current_user=user, db=db)
        print("get_my_listings success! found", len(res), "listings")
        
        from backend.routers.favorites import get_favorites
        res2 = get_favorites(current_user_token=user, db=db)
        print("get_favorites success! found", len(res2), "favorites")

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_endpoints()
