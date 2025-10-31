"""Authentication utilities"""

import streamlit as st
import hashlib
from src.database import SessionLocal, User
from datetime import datetime

def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == password_hash

def authenticate_user(email: str, password: str):
    """Authenticate a user with email and password"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user and user.password_hash and verify_password(password, user.password_hash):
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            
            return {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'role': user.role
            }
        return None
    finally:
        db.close()

def authenticate_google_user(google_id: str, email: str, name: str):
    """Authenticate or create a user via Google OAuth"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            (User.google_id == google_id) | (User.email == email)
        ).first()
        
        if user:
            # Update existing user
            user.google_id = google_id
            user.email = email
            user.name = name
            user.last_login = datetime.utcnow()
        else:
            # Create new user
            user = User(
                email=email,
                name=name,
                google_id=google_id,
                password_hash=None,
                role='recruiter',
                last_login=datetime.utcnow()
            )
            db.add(user)
        
        db.commit()
        
        return {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'role': user.role
        }
    finally:
        db.close()

def create_user(email: str, password: str, name: str, role: str = 'recruiter'):
    """Create a new user"""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return None
        
        user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            role=role
        )
        
        db.add(user)
        db.commit()
        
        return {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'role': user.role
        }
    finally:
        db.close()

def get_user_by_id(user_id: int):
    """Get user by ID"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'role': user.role,
                'is_active': user.is_active
            }
        return None
    finally:
        db.close()

def get_all_users():
    """Get all users"""
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()
        return [
            {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'role': user.role,
                'is_active': user.is_active,
                'last_login': user.last_login,
                'created_at': user.created_at
            }
            for user in users
        ]
    finally:
        db.close()

def update_user_role(user_id: int, new_role: str):
    """Update user role"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.role = new_role
            user.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False
    finally:
        db.close()

def toggle_user_status(user_id: int):
    """Toggle user active status"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = not user.is_active
            user.updated_at = datetime.utcnow()
            db.commit()
            return user.is_active
        return None
    finally:
        db.close()

