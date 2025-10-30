"""Authentication utilities"""

import streamlit as st
import hashlib
from src.database import SessionLocal, Recruiter

def hash_password(password: str) -> str:
    """Hash a password"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password"""
    return hash_password(password) == password_hash

def authenticate_user(email: str, password: str):
    """Authenticate a user"""
    db = SessionLocal()
    try:
        user = db.query(Recruiter).filter(Recruiter.email == email).first()
        if user and verify_password(password, user.password_hash):
            return {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'company': user.company
            }
        return None
    finally:
        db.close()

def check_auth():
    """Check if user is authenticated"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    return st.session_state.authenticated

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'

def create_default_admin():
    """
    Create default admin user if none exists.
    
    WARNING: Default credentials are for initial setup only.
    Change the password immediately after first login!
    
    Default credentials:
    - Email: admin@example.com
    - Password: admin123
    """
    from src.database import safe_query_recruiter
    
    db = SessionLocal()
    try:
        # Use safe query method
        admin = safe_query_recruiter('admin@example.com')
        if not admin:
            # SECURITY NOTE: This is a weak default password for initial setup only
            # Users MUST change this after first login
            admin = Recruiter(
                email='admin@example.com',
                password_hash=hash_password('admin123'),  # TODO: Change immediately after setup!
                name='Admin User',
                company='Excel Assessment Pro',
                dashboard_slug='admin',
                is_admin=True  # Mark as admin
            )
            db.add(admin)
            db.commit()
            return True
        else:
            # Update existing admin user to ensure is_admin is True
            try:
                if not getattr(admin, 'is_admin', False):
                    admin.is_admin = True
                    db.commit()
            except Exception as e:
                print(f"⚠️ Could not update admin flag: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Admin creation warning: {e}")
        return False
    finally:
        db.close()

