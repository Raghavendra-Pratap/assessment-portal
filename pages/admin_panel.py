"""Admin Panel - Super Admin Only Page"""

import streamlit as st
from datetime import datetime
from src.database import SessionLocal, Recruiter, Assessment
from src.utils.admin_auth import check_admin_access

def render():
    if not check_admin_access():
        st.error("🚫 Access Denied: Admin privileges required")
        st.info("Only super admin users can access this page.")
        return
    
    st.title("🔐 Admin Panel")
    st.markdown("**Super Admin Control Panel** - Manage all recruiters, assessments, and global settings")
    
    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Recruiters", "All Assessments", "Global Settings", "System Info"])
    
    with tab1:
        render_recruiters_management()
    
    with tab2:
        render_all_assessments()
    
    with tab3:
        render_global_settings()
    
    with tab4:
        render_system_info()

def render_recruiters_management():
    """Manage all recruiters"""
    st.subheader("Recruiters Management")
    
    db = SessionLocal()
    try:
        # Get all recruiters
        recruiters = db.query(Recruiter).order_by(Recruiter.created_at.desc()).all()
        
        # Add new recruiter button
        if st.button("➕ Add New Recruiter", type="primary"):
            st.session_state.show_add_recruiter = True
        
        if st.session_state.get('show_add_recruiter'):
            with st.form("add_recruiter_form"):
                st.markdown("### Add New Recruiter")
                name = st.text_input("Name *")
                email = st.text_input("Email *")
                company = st.text_input("Company")
                password = st.text_input("Password *", type="password")
                is_admin_check = st.checkbox("Grant Admin Access")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Create Recruiter", use_container_width=True):
                        if name and email and password:
                            from src.utils.auth import hash_password
                            import uuid
                            
                            # Check if email exists
                            existing = db.query(Recruiter).filter(Recruiter.email == email).first()
                            if existing:
                                st.error("Email already exists!")
                            else:
                                # Generate unique slug
                                slug = email.split('@')[0].lower().replace('.', '-')
                                counter = 1
                                while db.query(Recruiter).filter(Recruiter.dashboard_slug == slug).first():
                                    slug = f"{slug}-{counter}"
                                    counter += 1
                                
                                recruiter = Recruiter(
                                    email=email,
                                    password_hash=hash_password(password),
                                    name=name,
                                    company=company or '',
                                    dashboard_slug=slug,
                                    is_admin=is_admin_check,
                                    status='active'
                                )
                                db.add(recruiter)
                                db.commit()
                                st.success("Recruiter created successfully!")
                                st.session_state.show_add_recruiter = False
                                st.rerun()
                        else:
                            st.error("Name, Email, and Password are required!")
                
                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.show_add_recruiter = False
                        st.rerun()
        
        # Recruiters table
        if recruiters:
            st.markdown("### All Recruiters")
            
            for recruiter in recruiters:
                with st.expander(f"{recruiter.name} ({recruiter.email}) {'[ADMIN]' if recruiter.is_admin else ''}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Company:** {recruiter.company or 'N/A'}")
                        st.write(f"**Dashboard Slug:** {recruiter.dashboard_slug}")
                        st.write(f"**Status:** {recruiter.status}")
                        st.write(f"**Created:** {recruiter.created_at.strftime('%Y-%m-%d %H:%M') if recruiter.created_at else 'N/A'}")
                        if recruiter.last_login:
                            st.write(f"**Last Login:** {recruiter.last_login.strftime('%Y-%m-%d %H:%M')}")
                    
                    with col2:
                        if recruiter.is_admin:
                            st.warning("🔐 Admin User")
                        
                        # Edit button
                        if st.button("Edit", key=f"edit_recruiter_{recruiter.id}"):
                            st.session_state.edit_recruiter_id = recruiter.id
                            st.rerun()
                        
                        # Delete button
                        if st.button("Delete", key=f"delete_recruiter_{recruiter.id}", type="secondary"):
                            if recruiter.id == st.session_state.user['id']:
                                st.error("Cannot delete your own account!")
                            else:
                                db.delete(recruiter)
                                db.commit()
                                st.success("Recruiter deleted!")
                                st.rerun()
                    
                    # Edit form
                    if st.session_state.get('edit_recruiter_id') == recruiter.id:
                        st.divider()
                        with st.form(f"edit_recruiter_{recruiter.id}_form"):
                            st.markdown("### Edit Recruiter")
                            edit_name = st.text_input("Name", value=recruiter.name)
                            edit_company = st.text_input("Company", value=recruiter.company or "")
                            edit_email = st.text_input("Email", value=recruiter.email)
                            edit_slug = st.text_input("Dashboard Slug", value=recruiter.dashboard_slug)
                            edit_status = st.selectbox("Status", ["active", "inactive"], index=0 if recruiter.status == 'active' else 1)
                            edit_is_admin = st.checkbox("Admin Access", value=recruiter.is_admin)
                            
                            new_password = st.text_input("New Password (leave empty to keep current)", type="password")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Save Changes", use_container_width=True):
                                    recruiter.name = edit_name
                                    recruiter.company = edit_company
                                    recruiter.email = edit_email
                                    recruiter.dashboard_slug = edit_slug
                                    recruiter.status = edit_status
                                    recruiter.is_admin = edit_is_admin
                                    
                                    if new_password:
                                        from src.utils.auth import hash_password
                                        recruiter.password_hash = hash_password(new_password)
                                    
                                    db.commit()
                                    st.success("Recruiter updated!")
                                    del st.session_state.edit_recruiter_id
                                    st.rerun()
                            
                            with col2:
                                if st.form_submit_button("Cancel", use_container_width=True, type="secondary"):
                                    del st.session_state.edit_recruiter_id
                                    st.rerun()
        else:
            st.info("No recruiters found.")
            
    finally:
        db.close()

def render_all_assessments():
    """View all assessments from all recruiters"""
    st.subheader("All Assessments (All Recruiters)")
    
    db = SessionLocal()
    try:
        # Get all assessments with recruiter info
        assessments = db.query(Assessment).join(Recruiter).order_by(Assessment.created_at.desc()).all()
        
        if assessments:
            for assessment in assessments:
                with st.expander(f"{assessment.title} - {assessment.recruiter.name} ({assessment.recruiter.email})", expanded=False):
                    st.write(f"**Recruiter:** {assessment.recruiter.name} ({assessment.recruiter.company})")
                    st.write(f"**Duration:** {assessment.duration_minutes} minutes")
                    st.write(f"**Created:** {assessment.created_at.strftime('%Y-%m-%d %H:%M') if assessment.created_at else 'N/A'}")
                    if assessment.description:
                        st.write(f"**Description:** {assessment.description[:200]}")
                    
                    if st.button("View Details", key=f"view_assessment_{assessment.id}"):
                        st.session_state.view_assessment_id = assessment.id
                        st.session_state.page = 'assessments'
                        st.rerun()
        else:
            st.info("No assessments found.")
    finally:
        db.close()

def render_global_settings():
    """Global settings - Google Service Account JSON for all recruiters"""
    st.subheader("Global Settings")
    st.markdown("Configure global settings that apply to all recruiters")
    
    db = SessionLocal()
    try:
        # Global Google Service Account JSON
        st.markdown("### Google Service Account Configuration")
        st.info("This Google Service Account JSON will be used by all recruiters unless they have their own configuration.")
        
        # Store in a special admin config or update all recruiters
        # For now, we'll create a simple global config approach
        
        st.text_area(
            "Google Service Account JSON",
            key="global_google_json",
            height=200,
            placeholder='{"type": "service_account", "project_id": "...", ...}'
        )
        
        if st.button("Save Global Google Sheets Config", type="primary"):
            # Update all recruiters' storage_config with global setting
            # Or create a separate global_settings table - for now update all
            global_json = st.session_state.get('global_google_json', '')
            if global_json:
                try:
                    import json
                    json.loads(global_json)  # Validate
                    
                    recruiters = db.query(Recruiter).all()
                    for recruiter in recruiters:
                        if not recruiter.storage_config:
                            recruiter.storage_config = {}
                        if isinstance(recruiter.storage_config, str):
                            try:
                                recruiter.storage_config = json.loads(recruiter.storage_config)
                            except:
                                recruiter.storage_config = {}
                        
                        recruiter.storage_config['google_service_account'] = global_json
                        recruiter.storage_config['use_global_config'] = True
                    
                    db.commit()
                    st.success("Global Google Sheets API configuration saved for all recruiters!")
                except json.JSONDecodeError:
                    st.error("Invalid JSON format!")
            else:
                st.error("Please enter Google Service Account JSON")
        
        st.divider()
        st.markdown("### System Configuration")
        st.info("Additional system-wide settings will be available here.")
        
    finally:
        db.close()

def render_system_info():
    """System information"""
    st.subheader("System Information")
    
    db = SessionLocal()
    try:
        from src.database import Recruiter, Assessment, Session, Question
        
        total_recruiters = db.query(Recruiter).count()
        admin_count = db.query(Recruiter).filter(Recruiter.is_admin == True).count()
        total_assessments = db.query(Assessment).count()
        total_sessions = db.query(Session).count()
        total_questions = db.query(Question).count()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Recruiters", total_recruiters)
            st.metric("Admin Users", admin_count)
        
        with col2:
            st.metric("Total Assessments", total_assessments)
            st.metric("Total Sessions", total_sessions)
        
        with col3:
            st.metric("Total Questions", total_questions)
        
        st.divider()
        st.markdown("### Database Information")
        from src.database import DB_PATH
        st.write(f"**Database Path:** `{DB_PATH}`")
        
    finally:
        db.close()

