"""Admin Panel - Manage all recruiters and system settings"""

import streamlit as st
from datetime import datetime
from src.database import SessionLocal, Recruiter, Assessment, Session
from sqlalchemy import func, desc
import pandas as pd

def render():
    """Render admin panel"""
    st.title("🔧 Admin Panel")
    st.markdown("---")
    
    # Check if user is admin
    if not st.session_state.get('user', {}).get('is_admin', False):
        st.error("❌ Access denied. Admin privileges required.")
        return
    
    db = SessionLocal()
    try:
        # Get all recruiters
        recruiters = db.query(Recruiter).order_by(desc(Recruiter.created_at)).all()
        
        # Get system statistics
        total_recruiters = len(recruiters)
        active_recruiters = len([r for r in recruiters if r.status == 'active'])
        total_assessments = db.query(Assessment).count()
        total_sessions = db.query(Session).count()
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Recruiters", total_recruiters)
        with col2:
            st.metric("Active Recruiters", active_recruiters)
        with col3:
            st.metric("Total Assessments", total_assessments)
        with col4:
            st.metric("Total Sessions", total_sessions)
        
        st.markdown("---")
        
        # Recruiters Management Section
        st.subheader("👥 Recruiters Management")
        
        # Add new recruiter button
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("➕ Add New Recruiter", type="primary"):
                st.session_state.show_add_recruiter = True
                st.rerun()
        
        # Show add recruiter form if requested
        if st.session_state.get('show_add_recruiter', False):
            show_add_recruiter_form()
            return
        
        # Recruiters table
        if recruiters:
            # Prepare data for table
            recruiter_data = []
            for recruiter in recruiters:
                # Get recruiter stats
                recruiter_assessments = db.query(Assessment).filter(Assessment.recruiter_id == recruiter.id).count()
                recruiter_sessions = db.query(Session).join(Assessment).filter(Assessment.recruiter_id == recruiter.id).count()
                
                recruiter_data.append({
                    'ID': recruiter.id,
                    'Name': recruiter.name,
                    'Email': recruiter.email,
                    'Company': recruiter.company,
                    'Dashboard Slug': recruiter.dashboard_slug,
                    'Status': recruiter.status,
                    'Assessments': recruiter_assessments,
                    'Sessions': recruiter_sessions,
                    'Created': recruiter.created_at.strftime('%Y/%m/%d') if recruiter.created_at else 'N/A',
                    'Last Login': recruiter.last_login.strftime('%Y/%m/%d %H:%M') if recruiter.last_login else 'Never',
                    'Admin': 'Yes' if recruiter.is_admin else 'No'
                })
            
            # Display table
            df = pd.DataFrame(recruiter_data)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID": st.column_config.NumberColumn("ID", width="small"),
                    "Name": st.column_config.TextColumn("Name", width="medium"),
                    "Email": st.column_config.TextColumn("Email", width="large"),
                    "Company": st.column_config.TextColumn("Company", width="medium"),
                    "Dashboard Slug": st.column_config.TextColumn("Dashboard Slug", width="medium"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Assessments": st.column_config.NumberColumn("Assessments", width="small"),
                    "Sessions": st.column_config.NumberColumn("Sessions", width="small"),
                    "Created": st.column_config.TextColumn("Created", width="small"),
                    "Last Login": st.column_config.TextColumn("Last Login", width="medium"),
                    "Admin": st.column_config.TextColumn("Admin", width="small")
                }
            )
            
            # Action buttons for each recruiter
            st.subheader("Actions")
            for recruiter in recruiters:
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**{recruiter.name}** ({recruiter.email})")
                
                with col2:
                    if st.button(f"View Dashboard", key=f"view_{recruiter.id}"):
                        st.info(f"Dashboard URL: /{recruiter.dashboard_slug}")
                
                with col3:
                    if st.button(f"Edit", key=f"edit_{recruiter.id}"):
                        st.session_state.edit_recruiter_id = recruiter.id
                        st.rerun()
                
                with col4:
                    if recruiter.id != st.session_state.user['id']:  # Don't allow deleting self
                        if st.button(f"Toggle Status", key=f"toggle_{recruiter.id}"):
                            new_status = 'inactive' if recruiter.status == 'active' else 'active'
                            recruiter.status = new_status
                            db.commit()
                            st.success(f"Status changed to {new_status}")
                            st.rerun()
                
                with col5:
                    if recruiter.id != st.session_state.user['id'] and not recruiter.is_admin:  # Don't allow deleting self or other admins
                        if st.button(f"Delete", key=f"delete_{recruiter.id}", type="secondary"):
                            st.session_state.delete_recruiter_id = recruiter.id
                            st.rerun()
                
                st.markdown("---")
        else:
            st.info("No recruiters found.")
        
        # Handle edit recruiter
        if st.session_state.get('edit_recruiter_id'):
            show_edit_recruiter_form(st.session_state.edit_recruiter_id)
            return
        
        # Handle delete recruiter
        if st.session_state.get('delete_recruiter_id'):
            show_delete_recruiter_confirmation(st.session_state.delete_recruiter_id)
            return
            
    finally:
        db.close()

def show_add_recruiter_form():
    """Show form to add new recruiter"""
    st.subheader("➕ Add New Recruiter")
    
    with st.form("add_recruiter_form"):
        name = st.text_input("Name *", placeholder="Enter recruiter name")
        email = st.text_input("Email *", placeholder="Enter email address")
        company = st.text_input("Company", placeholder="Enter company name")
        password = st.text_input("Password *", type="password", placeholder="Enter password")
        is_admin = st.checkbox("Admin privileges", help="Give admin access to this recruiter")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Create Recruiter", type="primary")
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state.show_add_recruiter = False
                st.rerun()
        
        if submitted:
            if not name or not email or not password:
                st.error("Please fill in all required fields.")
                return
            
            # Check if email already exists
            db = SessionLocal()
            try:
                existing = db.query(Recruiter).filter(Recruiter.email == email).first()
                if existing:
                    st.error("Email already exists.")
                    return
                
                # Create recruiter
                from src.utils.auth import hash_password
                recruiter = Recruiter(
                    name=name,
                    email=email,
                    company=company or '',
                    password_hash=hash_password(password),
                    dashboard_slug=email.split('@')[0].replace('.', '-').replace('_', '-'),
                    is_admin=is_admin,
                    status='active'
                )
                
                db.add(recruiter)
                db.commit()
                st.success(f"Recruiter {name} created successfully!")
                st.session_state.show_add_recruiter = False
                st.rerun()
                
            finally:
                db.close()

def show_edit_recruiter_form(recruiter_id):
    """Show form to edit recruiter"""
    db = SessionLocal()
    try:
        recruiter = db.query(Recruiter).filter(Recruiter.id == recruiter_id).first()
        if not recruiter:
            st.error("Recruiter not found.")
            return
        
        st.subheader(f"✏️ Edit Recruiter: {recruiter.name}")
        
        with st.form("edit_recruiter_form"):
            name = st.text_input("Name *", value=recruiter.name)
            email = st.text_input("Email *", value=recruiter.email)
            company = st.text_input("Company", value=recruiter.company or '')
            dashboard_slug = st.text_input("Dashboard Slug", value=recruiter.dashboard_slug)
            status = st.selectbox("Status", ['active', 'inactive'], index=0 if recruiter.status == 'active' else 1)
            is_admin = st.checkbox("Admin privileges", value=recruiter.is_admin)
            
            st.markdown("**Change Password (leave blank to keep current)**")
            new_password = st.text_input("New Password", type="password", placeholder="Enter new password")
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Update Recruiter", type="primary")
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.edit_recruiter_id = None
                    st.rerun()
            
            if submitted:
                if not name or not email:
                    st.error("Please fill in all required fields.")
                    return
                
                # Update recruiter
                recruiter.name = name
                recruiter.email = email
                recruiter.company = company
                recruiter.dashboard_slug = dashboard_slug
                recruiter.status = status
                recruiter.is_admin = is_admin
                
                if new_password:
                    from src.utils.auth import hash_password
                    recruiter.password_hash = hash_password(new_password)
                
                db.commit()
                st.success(f"Recruiter {name} updated successfully!")
                st.session_state.edit_recruiter_id = None
                st.rerun()
                
    finally:
        db.close()

def show_delete_recruiter_confirmation(recruiter_id):
    """Show confirmation dialog for deleting recruiter"""
    db = SessionLocal()
    try:
        recruiter = db.query(Recruiter).filter(Recruiter.id == recruiter_id).first()
        if not recruiter:
            st.error("Recruiter not found.")
            return
        
        st.subheader(f"🗑️ Delete Recruiter: {recruiter.name}")
        st.warning(f"Are you sure you want to delete recruiter '{recruiter.name}' ({recruiter.email})?")
        st.error("⚠️ This action cannot be undone!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Delete", type="primary"):
                # Delete associated data first
                db.query(Assessment).filter(Assessment.recruiter_id == recruiter_id).delete()
                db.query(Session).join(Assessment).filter(Assessment.recruiter_id == recruiter_id).delete()
                
                # Delete recruiter
                db.query(Recruiter).filter(Recruiter.id == recruiter_id).delete()
                db.commit()
                
                st.success(f"Recruiter {recruiter.name} deleted successfully!")
                st.session_state.delete_recruiter_id = None
                st.rerun()
        
        with col2:
            if st.button("Cancel"):
                st.session_state.delete_recruiter_id = None
                st.rerun()
                
    finally:
        db.close()
