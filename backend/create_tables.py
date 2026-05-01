"""
Create database tables in Supabase
Run this script once to initialize the database
"""
from models.database import Base, engine

def create_tables():
    print("Creating tables in Supabase...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")
    print("\nTables created:")
    print("- users (enhanced with phone, bio, location, last_login)")
    print("- listings (enhanced with brand, model, additional_images, is_featured, likes_count)")
    print("- reviews (user ratings and comments)")
    print("- favorites (saved listings)")
    print("- messages (user-to-user messaging)")
    print("\n✅ All tables are interconnected with foreign keys and CASCADE delete")

if __name__ == "__main__":
    create_tables()
