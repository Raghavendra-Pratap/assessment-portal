"""
Setup script to initialize the application
"""

from src.database import init_db, SessionLocal, Recruiter
from src.utils.auth import hash_password, create_default_admin

def setup():
    """Initialize database and create default admin"""
    print("Initializing database...")
    init_db()
    print("Database initialized!")
    
    print("Creating default admin user...")
    create_default_admin()
    print("Setup complete!")
    print("\nDefault credentials:")
    print("Email: admin@example.com")
    print("Password: admin123")
    print("\nPlease change the default password after first login!")

if __name__ == "__main__":
    setup()

