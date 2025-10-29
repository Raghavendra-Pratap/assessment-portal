"""Admin Authentication Utilities"""

import streamlit as st
from src.database import SessionLocal, Recruiter
from src.utils.auth import verify_password

def is_admin_user(user):
    """Check if user is an admin"""
    if not user:
        return False
    db = SessionLocal()
    try:
        recruiter = db.query(Recruiter).filter(Recruiter.id == user['id']).first()
        return recruiter.is_admin if recruiter else False
    finally:
        db.close()

def check_admin_access():
    """Check if current user has admin access"""
    if not st.session_state.get('authenticated'):
        return False
    return is_admin_user(st.session_state.get('user'))

