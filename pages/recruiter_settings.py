"""Recruiter Settings - Personal settings for recruiters"""

import streamlit as st
import json
import os
from src.database import SessionLocal, Recruiter
from src.utils.auth import hash_password

def render():
    """Render recruiter settings page"""
    st.title("⚙️ Settings")
    st.markdown("---")
    
    # Get current user
    user = st.session_state.get('user', {})
    user_id = user.get('id')
    
    if not user_id:
        st.error("❌ User not found.")
        return
    
    db = SessionLocal()
    try:
        recruiter = db.query(Recruiter).filter(Recruiter.id == user_id).first()
        if not recruiter:
            st.error("❌ Recruiter not found.")
            return
        
        # Personal Information Section
        st.subheader("👤 Personal Information")
        
        with st.expander("Profile Settings", expanded=True):
            with st.form("profile_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("Name *", value=recruiter.name)
                    email = st.text_input("Email *", value=recruiter.email)
                
                with col2:
                    company = st.text_input("Company", value=recruiter.company or '')
                    dashboard_slug = st.text_input("Dashboard Slug", value=recruiter.dashboard_slug)
                
                if st.form_submit_button("Update Profile", type="primary"):
                    if not name or not email:
                        st.error("Please fill in all required fields.")
                    else:
                        # Check if email is already taken by another user
                        existing = db.query(Recruiter).filter(Recruiter.email == email, Recruiter.id != user_id).first()
                        if existing:
                            st.error("Email already taken by another user.")
                        else:
                            recruiter.name = name
                            recruiter.email = email
                            recruiter.company = company
                            recruiter.dashboard_slug = dashboard_slug
                            db.commit()
                            st.success("Profile updated successfully!")
                            # Update session state
                            st.session_state.user['name'] = name
                            st.session_state.user['email'] = email
                            st.session_state.user['company'] = company
                            st.session_state.user['dashboard_slug'] = dashboard_slug
                            st.rerun()
        
        st.markdown("---")
        
        # Password Change Section
        st.subheader("🔒 Security")
        
        with st.expander("Change Password", expanded=True):
            with st.form("password_form"):
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                
                if st.form_submit_button("Change Password", type="primary"):
                    if not current_password or not new_password or not confirm_password:
                        st.error("Please fill in all fields.")
                    elif new_password != confirm_password:
                        st.error("New passwords do not match.")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    else:
                        # Verify current password
                        from src.utils.auth import verify_password
                        if not verify_password(current_password, recruiter.password_hash):
                            st.error("Current password is incorrect.")
                        else:
                            recruiter.password_hash = hash_password(new_password)
                            db.commit()
                            st.success("Password changed successfully!")
        
        st.markdown("---")
        
        # Branding Settings Section
        st.subheader("🎨 Branding")
        
        with st.expander("Customize Your Branding", expanded=True):
            # Load existing branding settings
            branding = recruiter.branding_settings or {}
            
            col1, col2 = st.columns(2)
            
            with col1:
                primary_color = st.color_picker(
                    "Primary Color",
                    value=branding.get('primary_color', '#2563eb'),
                    help="Main color for your assessment interface"
                )
                
                logo_url = st.text_input(
                    "Logo URL",
                    value=branding.get('logo_url', ''),
                    help="URL to your company logo"
                )
            
            with col2:
                secondary_color = st.color_picker(
                    "Secondary Color",
                    value=branding.get('secondary_color', '#64748b'),
                    help="Secondary color for your assessment interface"
                )
                
                favicon_url = st.text_input(
                    "Favicon URL",
                    value=branding.get('favicon_url', ''),
                    help="URL to your favicon"
                )
            
            welcome_message = st.text_area(
                "Welcome Message",
                value=branding.get('welcome_message', ''),
                help="Custom message shown to candidates",
                height=100
            )
            
            if st.button("Save Branding Settings", type="primary"):
                branding_settings = {
                    'primary_color': primary_color,
                    'secondary_color': secondary_color,
                    'logo_url': logo_url,
                    'favicon_url': favicon_url,
                    'welcome_message': welcome_message
                }
                
                recruiter.branding_settings = branding_settings
                db.commit()
                st.success("Branding settings saved successfully!")
        
        st.markdown("---")
        
        # Assessment Preferences Section
        st.subheader("📝 Assessment Preferences")
        
        with st.expander("Default Assessment Settings", expanded=True):
            # Load existing storage config
            storage_config = recruiter.storage_config or {}
            
            col1, col2 = st.columns(2)
            
            with col1:
                default_duration = st.number_input(
                    "Default Duration (minutes)",
                    min_value=5,
                    max_value=480,
                    value=storage_config.get('default_duration', 60),
                    help="Default time limit for your assessments"
                )
                
                default_attempts = st.number_input(
                    "Default Max Attempts",
                    min_value=1,
                    max_value=10,
                    value=storage_config.get('default_attempts', 1),
                    help="Default maximum attempts for your assessments"
                )
            
            with col2:
                default_proctoring = st.selectbox(
                    "Default Proctoring Level",
                    ['basic', 'standard', 'strict'],
                    index=['basic', 'standard', 'strict'].index(storage_config.get('default_proctoring', 'standard')),
                    help="Default proctoring settings for your assessments"
                )
                
                default_grading = st.selectbox(
                    "Default Grading Mode",
                    ['auto', 'manual', 'hybrid'],
                    index=['auto', 'manual', 'hybrid'].index(storage_config.get('default_grading', 'auto')),
                    help="Default grading mode for your assessments"
                )
            
            if st.button("Save Assessment Preferences", type="primary"):
                storage_config.update({
                    'default_duration': default_duration,
                    'default_attempts': default_attempts,
                    'default_proctoring': default_proctoring,
                    'default_grading': default_grading
                })
                
                recruiter.storage_config = storage_config
                db.commit()
                st.success("Assessment preferences saved successfully!")
        
        st.markdown("---")
        
        # Account Information Section
        st.subheader("ℹ️ Account Information")
        
        with st.expander("Account Details", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Account Status", recruiter.status.title())
            with col2:
                st.metric("Created", recruiter.created_at.strftime('%Y-%m-%d') if recruiter.created_at else 'N/A')
            with col3:
                st.metric("Last Login", recruiter.last_login.strftime('%Y-%m-%d %H:%M') if recruiter.last_login else 'Never')
            
            # Get assessment stats
            from src.database import Assessment, Session
            total_assessments = db.query(Assessment).filter(Assessment.recruiter_id == user_id).count()
            total_sessions = db.query(Session).join(Assessment).filter(Assessment.recruiter_id == user_id).count()
            
            st.markdown("**Assessment Statistics:**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Assessments", total_assessments)
            with col2:
                st.metric("Total Sessions", total_sessions)
        
        st.markdown("---")
        
        # Danger Zone
        st.subheader("⚠️ Danger Zone")
        
        with st.expander("Dangerous Operations", expanded=False):
            st.warning("⚠️ These operations are irreversible!")
            
            if st.button("Delete My Account", type="secondary"):
                st.session_state.show_delete_account = True
                st.rerun()
        
        # Handle delete account confirmation
        if st.session_state.get('show_delete_account', False):
            st.error("Are you sure you want to delete your account? This will remove all your assessments, sessions, and data!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete My Account", type="primary"):
                    # Delete associated data
                    db.query(Assessment).filter(Assessment.recruiter_id == user_id).delete()
                    db.query(Session).join(Assessment).filter(Assessment.recruiter_id == user_id).delete()
                    
                    # Delete recruiter
                    db.query(Recruiter).filter(Recruiter.id == user_id).delete()
                    db.commit()
                    
                    st.success("Account deleted successfully!")
                    st.session_state.authenticated = False
                    st.session_state.user = None
                    st.session_state.page = 'login'
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.session_state.show_delete_account = False
                    st.rerun()
                    
    finally:
        db.close()
