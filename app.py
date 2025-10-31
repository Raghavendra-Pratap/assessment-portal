"""
Recruiter Portal - Main Application
"""

import streamlit as st
import sys
import os

# Add the app directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import init_db
from src.utils.auth import create_user, hash_password
from src.database import SessionLocal, User
import pages.login as login_page
import pages.admin as admin_page

# Page configuration
st.set_page_config(
    page_title="Recruiter Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database
init_db()

# Create default admin user if none exists
def create_default_admin():
    """Create default admin user"""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == 'admin@example.com').first()
        if not admin:
            admin = User(
                email='admin@example.com',
                password_hash=hash_password('admin123'),
                name='Admin User',
                role='admin',
                is_active=True
            )
            db.add(admin)
            db.commit()
            return True
        return False
    finally:
        db.close()

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# Create default admin
try:
    create_default_admin()
except:
    pass  # Admin might already exist

# Main routing
def main():
    """Main application routing"""
    
    if not st.session_state.authenticated:
        # Show login page
        login_page.render()
    else:
        # Show page based on user role
        user = st.session_state.get('user', {})
        role = user.get('role', 'recruiter')
        
        if role == 'admin':
            # Show admin page
            admin_page.render()
        else:
            # Show recruiter dashboard (placeholder for now)
            st.title("Recruiter Dashboard")
            st.write(f"Welcome, {user.get('name', 'User')}!")
            st.info("Recruiter dashboard coming soon...")
            
            # Logout button
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.user = None
                st.session_state.page = 'login'
                st.rerun()

if __name__ == "__main__":
    main()

