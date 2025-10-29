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
    """Create default admin user if none exists"""
    db = SessionLocal()
    try:
        admin = db.query(Recruiter).filter(Recruiter.email == 'admin@example.com').first()
        if not admin:
            from src.utils.auth import hash_password
            admin = Recruiter(
                email='admin@example.com',
                password_hash=hash_password('admin123'),
                name='Admin User',
                company='Excel Assessment Pro',
                dashboard_slug='admin'
            )
            db.add(admin)
            db.commit()
            return True
        return False
    finally:
        db.close()

