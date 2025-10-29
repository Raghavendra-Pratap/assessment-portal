"""Admin Settings Page"""

import streamlit as st
import json
from src.database import SessionLocal, Recruiter

def render():
    st.title("⚙️ Settings")
    
    if not st.session_state.get('authenticated'):
        st.error("Please login first")
        return
    
    db = SessionLocal()
    try:
        user_id = st.session_state.user['id']
        recruiter = db.query(Recruiter).filter(Recruiter.id == user_id).first()
        
        if not recruiter:
            st.error("User not found")
            return
        
        # Profile Settings
        st.subheader("Profile Settings")
        
        with st.form("profile_form"):
            name = st.text_input("Name", value=recruiter.name)
            company = st.text_input("Company", value=recruiter.company or "")
            
            if st.form_submit_button("Update Profile", use_container_width=True):
                recruiter.name = name
                recruiter.company = company
                db.commit()
                st.success("Profile updated!")
                st.rerun()
        
        st.divider()
        
        # Google Sheets API Configuration
        st.subheader("Google Sheets API Configuration")
        
        storage_config = recruiter.storage_config or {}
        google_service_account = storage_config.get('google_service_account', '')
        
        google_json = st.text_area(
            "Google Service Account JSON",
            value=google_service_account,
            height=200,
            placeholder='{"type": "service_account", "project_id": "...", ...}'
        )
        
        if st.button("Save Google Sheets Config", use_container_width=True):
            try:
                # Validate JSON
                if google_json:
                    json.loads(google_json)
                
                if not storage_config:
                    storage_config = {}
                
                storage_config['google_service_account'] = google_json
                recruiter.storage_config = storage_config
                
                db.commit()
                
                # Update session state
                if 'settings' not in st.session_state:
                    st.session_state.settings = {}
                st.session_state.settings['google_service_account'] = google_json
                
                st.success("Google Sheets API configuration saved!")
            except json.JSONDecodeError:
                st.error("Invalid JSON format!")
        
        # Test connection
        if google_json:
            if st.button("Test Connection"):
                from src.services.google_sheets import GoogleSheetsAPI
                try:
                    service = GoogleSheetsAPI(google_json)
                    if service.service:
                        st.success("✅ Google Sheets API connection successful!")
                    else:
                        st.error("❌ Failed to initialize Google Sheets API")
                except Exception as e:
                    st.error(f"❌ Connection error: {str(e)}")
        
        st.divider()
        
        # Branding Settings
        st.subheader("Branding Settings")
        
        branding_settings = recruiter.branding_settings or {}
        
        col1, col2 = st.columns(2)
        with col1:
            primary_color = st.color_picker("Primary Color", value=branding_settings.get('primary_color', '#667eea'))
        with col2:
            secondary_color = st.color_picker("Secondary Color", value=branding_settings.get('secondary_color', '#764ba2'))
        
        if st.button("Save Branding", use_container_width=True):
            branding_settings['primary_color'] = primary_color
            branding_settings['secondary_color'] = secondary_color
            recruiter.branding_settings = branding_settings
            db.commit()
            st.success("Branding updated!")
        
        st.divider()
        
        # Change Password
        st.subheader("Change Password")
        
        with st.form("password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Change Password", use_container_width=True):
                from src.utils.auth import verify_password, hash_password
                
                if not verify_password(current_password, recruiter.password_hash):
                    st.error("Current password is incorrect!")
                elif new_password != confirm_password:
                    st.error("New passwords do not match!")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters!")
                else:
                    recruiter.password_hash = hash_password(new_password)
                    db.commit()
                    st.success("Password changed successfully!")
            
    finally:
        db.close()

