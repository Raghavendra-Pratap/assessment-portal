"""Settings - Dashboard customization for admins and recruiters"""

import streamlit as st
import json
import os
import re
import hashlib
from datetime import datetime
from src.database import SessionLocal, Recruiter
from src.utils.auth import hash_password

def generate_dashboard_slug(company_name):
    """
    Generate a unique dashboard slug based on company name
    One dashboard per organization
    """
    if not company_name:
        return ''
    
    # Convert to lowercase, replace spaces/special chars with hyphens
    slug = company_name.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)  # Replace non-alphanumeric with hyphens
    slug = re.sub(r'-+', '-', slug)  # Replace multiple hyphens with single
    slug = slug.strip('-')  # Remove leading/trailing hyphens
    
    # Ensure uniqueness within the organization
    return slug

def save_uploaded_logo(uploaded_file, company_name):
    """Save uploaded logo file"""
    if not uploaded_file:
        return None
    
    # Create uploads directory
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'logos')
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Generate filename based on company name
    file_ext = os.path.splitext(uploaded_file.name)[1]
    safe_company = re.sub(r'[^a-zA-Z0-9]+', '_', company_name.lower())
    filename = f"{safe_company}_{int(datetime.now().timestamp())}{file_ext}"
    filepath = os.path.join(uploads_dir, filename)
    
    # Save file
    with open(filepath, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    # Return relative path for URL
    return f"/static/logos/{filename}"

def render():
    """Render settings page for dashboard customization"""
    st.title("⚙️ Settings")
    st.markdown("---")
    
    # Get current user (both admins and recruiters)
    user = st.session_state.get('user', {})
    user_id = user.get('id')
    
    if not user_id:
        st.error("❌ User not found.")
        return
    
    db = SessionLocal()
    try:
        recruiter = db.query(Recruiter).filter(Recruiter.id == user_id).first()
        if not recruiter:
            st.error("❌ User not found.")
            return
        
        # Combined Profile and Branding Settings in one form
        with st.form("dashboard_settings_form"):
            # Profile Section
            st.subheader("📋 Profile")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Name *", value=recruiter.name, placeholder="Enter your name")
            
            with col2:
                email = st.text_input("Email *", value=recruiter.email, placeholder="your.email@company.com")
            
            company = st.text_input("Company *", value=recruiter.company or '', placeholder="Enter your company name")
            
            # Auto-generate dashboard slug from company name
            # One dashboard per organization - all users with same company share the same dashboard
            if company:
                auto_slug = generate_dashboard_slug(company)
                
                # Check if another user from the same organization already has this slug
                existing_org = db.query(Recruiter).filter(
                    Recruiter.company == company,
                    Recruiter.id != user_id
                ).first()
                
                if existing_org:
                    # Use the existing organization's dashboard slug
                    auto_slug = existing_org.dashboard_slug
                # If no existing org member, use the generated slug
            else:
                auto_slug = recruiter.dashboard_slug or ''
            
            # Dashboard URL (read-only, auto-generated)
            if auto_slug:
                dashboard_url = f"/dashboard/{auto_slug}"
                st.info(f"**Dashboard URL:** `{dashboard_url}`")
                st.caption("This URL is automatically generated from your company name. **All users in the same organization share this dashboard.** One dashboard per organization.")
                
                # Show if sharing with other users
                org_members = db.query(Recruiter).filter(
                    Recruiter.company == company,
                    Recruiter.id != user_id
                ).count()
                
                if org_members > 0:
                    st.success(f"✅ Sharing dashboard with {org_members} other user(s) from {company}")
            else:
                st.warning("⚠️ Enter a company name to generate your dashboard URL")
            
            st.markdown("---")
            
            # Branding Section
            st.subheader("🎨 Branding")
            
            # Load existing branding settings
            branding = recruiter.branding_settings or {}
            
            # Logo upload
            st.markdown("#### Logo")
            logo_url = branding.get('logo_url', '')
            
            # Display current logo if exists
            if logo_url:
                col1, col2 = st.columns([1, 3])
                with col1:
                    if logo_url.startswith('/static/'):
                        # Local file
                        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), logo_url.lstrip('/'))
                        if os.path.exists(logo_path):
                            st.image(logo_path, width=200)
                        else:
                            st.info("Logo not found")
                    else:
                        # External URL
                        st.image(logo_url, width=200)
                with col2:
                    st.caption(f"Current logo: {logo_url}")
            else:
                st.info("No logo uploaded")
            
            # Logo file uploader
            uploaded_logo = st.file_uploader(
                "Choose logo file",
                type=['png', 'jpg', 'jpeg', 'svg'],
                help="Upload a logo image (PNG, JPG, SVG). Recommended size: 200x100px or similar aspect ratio."
            )
            
            if uploaded_logo:
                st.caption(f"Selected file: {uploaded_logo.name}")
                # Preview uploaded logo
                if uploaded_logo.type.startswith('image/'):
                    st.image(uploaded_logo, width=200)
            
            # Colors
            col1, col2 = st.columns(2)
            
            with col1:
                primary_color = st.color_picker(
                    "Primary Color",
                    value=branding.get('primary_color', '#667eea'),
                    help="Main color for your dashboard"
                )
            
            with col2:
                secondary_color = st.color_picker(
                    "Secondary Color",
                    value=branding.get('secondary_color', '#764ba2'),
                    help="Secondary color for your dashboard"
                )
            
            # Action buttons
            col1, col2 = st.columns([1, 4])
            with col1:
                submitted = st.form_submit_button("💾 Save Settings", type="primary", use_container_width=True)
            with col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.rerun()
            
            if submitted:
                errors = []
                
                # Validate required fields
                if not name:
                    errors.append("Name is required.")
                if not email:
                    errors.append("Email is required.")
                if not company:
                    errors.append("Company name is required to generate dashboard URL.")
                
                # Check if email already exists
                if email != recruiter.email:
                    existing = db.query(Recruiter).filter(Recruiter.email == email, Recruiter.id != user_id).first()
                    if existing:
                        errors.append("Email already taken by another user.")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # Recalculate dashboard slug based on final company name
                    # One dashboard per organization - all users with same company share same dashboard
                    final_slug = generate_dashboard_slug(company)
                    
                    # Check if another user from the same organization already exists
                    existing_org_user = db.query(Recruiter).filter(
                        Recruiter.company == company,
                        Recruiter.id != user_id
                    ).first()
                    
                    if existing_org_user:
                        # Join existing organization's dashboard
                        final_slug = existing_org_user.dashboard_slug
                    # If no existing org member, use the generated slug
                    
                    # Save logo if uploaded
                    new_logo_url = logo_url
                    if uploaded_logo:
                        saved_logo_path = save_uploaded_logo(uploaded_logo, company)
                        if saved_logo_path:
                            new_logo_url = saved_logo_path
                    
                    # Update recruiter
                    recruiter.name = name
                    recruiter.email = email
                    recruiter.company = company
                    recruiter.dashboard_slug = final_slug  # Auto-generated from company, shared with org
                    
                    # Update branding settings
                    branding_settings = {
                        'primary_color': primary_color,
                        'secondary_color': secondary_color,
                        'logo_url': new_logo_url,
                        'favicon_url': branding.get('favicon_url', ''),
                        'welcome_message': branding.get('welcome_message', '')
                    }
                    recruiter.branding_settings = branding_settings
                    
                    db.commit()
                    
                    # Update session state
                    st.session_state.user['name'] = name
                    st.session_state.user['email'] = email
                    st.session_state.user['company'] = company
                    st.session_state.user['dashboard_slug'] = final_slug
                    
                    # Show organization sharing info
                    org_members_count = db.query(Recruiter).filter(
                        Recruiter.company == company,
                        Recruiter.id != user_id
                    ).count()
                    
                    st.success("✅ Settings saved successfully!")
                    st.info(f"📊 Your dashboard is available at: `/dashboard/{final_slug}`")
                    
                    if org_members_count > 0:
                        st.success(f"✅ Sharing dashboard with {org_members_count} other user(s) from {company}")
                    else:
                        st.info(f"ℹ️ You're the first user from {company}. Other users from your organization will automatically join this dashboard.")
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
