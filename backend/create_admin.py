"""
Run this script on the EC2 server to create or reset the admin user.
Usage: python create_admin.py
"""
import sys
import os

# Make sure we can import from the backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal, User, Base, engine
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_EMAIL    = "admin@ezsell.com"
ADMIN_NAME     = "EzSell Admin"

def create_or_reset_admin():
    Base.metadata.create_all(bind=engine)  # ensure tables exist
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        hashed = pwd_context.hash(ADMIN_PASSWORD)

        if user:
            user.hashed_password = hashed
            user.is_admin        = True
            user.is_active       = True
            user.is_verified     = True
            db.commit()
            print(f"✅ Admin user '{ADMIN_USERNAME}' password reset successfully.")
        else:
            new_admin = User(
                username        = ADMIN_USERNAME,
                email           = ADMIN_EMAIL,
                full_name       = ADMIN_NAME,
                hashed_password = hashed,
                is_admin        = True,
                is_active       = True,
                is_verified     = True,
            )
            db.add(new_admin)
            db.commit()
            print(f"✅ Admin user '{ADMIN_USERNAME}' created successfully.")

        print(f"   Username : {ADMIN_USERNAME}")
        print(f"   Password : {ADMIN_PASSWORD}")
        print(f"   Email    : {ADMIN_EMAIL}")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_or_reset_admin()
