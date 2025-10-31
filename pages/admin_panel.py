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
        
        # Tabs for different management sections
        tab1, tab2 = st.tabs(["👥 User Management", "📊 System Overview"])
        
        with tab1:
            render_user_management(db, recruiters)
        
        with tab2:
            render_system_overview(db, recruiters, total_assessments, total_sessions)
    
def render_user_management(db, recruiters):
    """Render user management section with all features"""
    st.subheader("👥 User Management")
    st.markdown("Manage all users logged in through admin login page")
    
    # Add new user button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("➕ Add New User", type="primary"):
            st.session_state.show_add_recruiter = True
            st.rerun()
    
    # Show add user form if requested
    if st.session_state.get('show_add_recruiter', False):
        show_add_recruiter_form()
        return
    
    # User statistics
    if recruiters:
        active_count = len([r for r in recruiters if r.status == 'active'])
        admin_count = len([r for r in recruiters if r.is_admin])
        recruiter_count = len([r for r in recruiters if not r.is_admin])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Users", len(recruiters))
        with col2:
            st.metric("Active Users", active_count)
        with col3:
            st.metric("Admins", admin_count)
        with col4:
            st.metric("Recruiters", recruiter_count)
        
        st.markdown("---")
        
        # Search and filter
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_term = st.text_input("🔍 Search users", placeholder="Search by name, email, or company...")
        with col2:
            status_filter = st.selectbox("Status", ["All", "Active", "Inactive"], index=0)
        with col3:
            role_filter = st.selectbox("Role", ["All", "Admin", "Recruiter"], index=0)
        
        # Filter recruiters
        filtered_recruiters = recruiters
        if search_term:
            search_lower = search_term.lower()
            filtered_recruiters = [r for r in filtered_recruiters if 
                                 search_lower in r.name.lower() or 
                                 search_lower in r.email.lower() or 
                                 (r.company and search_lower in r.company.lower())]
        
        if status_filter != "All":
            filtered_recruiters = [r for r in filtered_recruiters if 
                                 r.status == status_filter.lower()]
        
        if role_filter != "All":
            is_admin_filter = role_filter == "Admin"
            filtered_recruiters = [r for r in filtered_recruiters if r.is_admin == is_admin_filter]
        
        st.markdown(f"**Showing {len(filtered_recruiters)} of {len(recruiters)} users**")
        st.markdown("---")
        
        # Users table with enhanced display
        for recruiter in filtered_recruiters:
            with st.container():
                # User card
                col1, col2, col3, col4, col5 = st.columns([3, 2, 1.5, 1.5, 2])
                
                with col1:
                    # User info
                    status_icon = "🟢" if recruiter.status == 'active' else "🔴"
                    role_badge = "👑 Admin" if recruiter.is_admin else "👤 Recruiter"
                    st.markdown(f"""
                    **{recruiter.name}** {status_icon}
                    <br>
                    <small style="color: #6b7280;">{recruiter.email}</small>
                    <br>
                    <small>{role_badge} | {recruiter.company or 'No company'}</small>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Login info
                    if recruiter.last_login:
                        st.caption(f"**Last Login:** {recruiter.last_login.strftime('%Y-%m-%d %H:%M')}")
                    else:
                        st.caption("**Last Login:** Never")
                    st.caption(f"**Created:** {recruiter.created_at.strftime('%Y-%m-%d') if recruiter.created_at else 'N/A'}")
                
                with col3:
                    # Role selector
                    if recruiter.id == st.session_state.user['id']:
                        st.write(f"**{role_badge}**")
                        st.caption("(Your account)")
                    else:
                        current_role = "admin" if recruiter.is_admin else "recruiter"
                        new_role = st.selectbox(
                            "Role",
                            ['admin', 'recruiter'],
                            index=0 if recruiter.is_admin else 1,
                            key=f"role_{recruiter.id}",
                            label_visibility="collapsed"
                        )
                        if new_role != current_role:
                            recruiter.is_admin = (new_role == 'admin')
                            db.commit()
                            st.success(f"✅ Role changed to {new_role}")
                            st.rerun()
                
                with col4:
                    # Status toggle
                    if recruiter.id == st.session_state.user['id']:
                        st.write(f"**{status_icon} {recruiter.status.title()}**")
                        st.caption("(Your account)")
                    else:
                        status_text = "Active" if recruiter.status == 'active' else "Inactive"
                        button_type = "primary" if recruiter.status == 'active' else "secondary"
                        if st.button(
                            f"{status_icon} {status_text}",
                            key=f"status_{recruiter.id}",
                            use_container_width=True,
                            type=button_type
                        ):
                            new_status = 'inactive' if recruiter.status == 'active' else 'active'
                            recruiter.status = new_status
                            db.commit()
                            st.success(f"✅ Status changed to {new_status}")
                            st.rerun()
                
                with col5:
                    # Action buttons
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        if st.button("✏️ Edit", key=f"edit_{recruiter.id}", use_container_width=True):
                            st.session_state.edit_recruiter_id = recruiter.id
                            st.rerun()
                    
                    with action_col2:
                        if st.button("🔑 Creds", key=f"creds_{recruiter.id}", use_container_width=True):
                            st.session_state.view_creds_id = recruiter.id
                            st.rerun()
                    
                    with action_col3:
                        if recruiter.id == st.session_state.user['id']:
                            st.button("🗑️ Delete", key=f"delete_{recruiter.id}", disabled=True, use_container_width=True)
                        elif recruiter.is_admin and recruiter.id != st.session_state.user['id']:
                            st.button("🗑️ Delete", key=f"delete_{recruiter.id}", disabled=True, use_container_width=True, help="Cannot delete other admins")
                        else:
                            if st.button("🗑️ Delete", key=f"delete_{recruiter.id}", type="secondary", use_container_width=True):
                                st.session_state.delete_recruiter_id = recruiter.id
                                st.rerun()
                
                st.markdown("---")
        
        if not filtered_recruiters:
            st.info("No users found matching your search criteria.")
    
    else:
        st.info("No users found.")
    
    # Handle edit user
    if st.session_state.get('edit_recruiter_id'):
        show_edit_recruiter_form(st.session_state.edit_recruiter_id)
        return
    
    # Handle view credentials
    if st.session_state.get('view_creds_id'):
        show_user_credentials(st.session_state.view_creds_id)
        return
    
    # Handle delete user
    if st.session_state.get('delete_recruiter_id'):
        show_delete_recruiter_confirmation(st.session_state.delete_recruiter_id)
        return

def render_system_overview(db, recruiters, total_assessments, total_sessions):
    """Render system overview section"""
    st.subheader("📊 System Overview")
    
    # Get all recruiters for display
    recruiter_data = []
    for recruiter in recruiters:
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
    if recruiter_data:
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
    else:
        st.info("No users found.")
        
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
        
    finally:
        db.close()

def show_user_credentials(recruiter_id):
    """Show and manage user credentials"""
    db = SessionLocal()
    try:
        recruiter = db.query(Recruiter).filter(Recruiter.id == recruiter_id).first()
        if not recruiter:
            st.error("User not found.")
            st.session_state.view_creds_id = None
            st.rerun()
            return
        
        st.subheader(f"🔑 Credentials Management: {recruiter.name}")
        st.markdown("---")
        
        # Current credentials info
        st.markdown("### Current Credentials")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Email:** {recruiter.email}")
            st.info(f"**Dashboard Slug:** `{recruiter.dashboard_slug}`")
            st.info(f"**Status:** {recruiter.status.title()}")
            st.info(f"**Role:** {'Admin' if recruiter.is_admin else 'Recruiter'}")
        
        with col2:
            if recruiter.last_login:
                st.info(f"**Last Login:** {recruiter.last_login.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                st.info("**Last Login:** Never")
            st.info(f"**Created:** {recruiter.created_at.strftime('%Y-%m-%d %H:%M') if recruiter.created_at else 'N/A'}")
            st.info(f"**Password Set:** {'Yes' if recruiter.password_hash else 'No'}")
        
        st.markdown("---")
        
        # Update credentials
        st.markdown("### Update Credentials")
        with st.form("update_credentials_form"):
            st.markdown("#### Change Email")
            new_email = st.text_input("New Email", value=recruiter.email, placeholder="Enter new email")
            
            st.markdown("---")
            st.markdown("#### Change Password")
            st.markdown("**Leave blank to keep current password**")
            new_password = st.text_input("New Password", type="password", placeholder="Enter new password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm new password")
            
            st.markdown("---")
            st.markdown("#### Update Dashboard Slug")
            new_slug = st.text_input("Dashboard Slug", value=recruiter.dashboard_slug, placeholder="Enter dashboard slug")
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("💾 Update Credentials", type="primary", use_container_width=True)
            with col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.view_creds_id = None
                    st.rerun()
            
            if submitted:
                errors = []
                
                # Validate email
                if new_email != recruiter.email:
                    # Check if email already exists
                    existing = db.query(Recruiter).filter(Recruiter.email == new_email, Recruiter.id != recruiter_id).first()
                    if existing:
                        errors.append("Email already exists. Please choose a different email.")
                    else:
                        recruiter.email = new_email
                
                # Validate password
                if new_password:
                    if len(new_password) < 6:
                        errors.append("Password must be at least 6 characters long.")
                    elif new_password != confirm_password:
                        errors.append("Passwords do not match.")
                    else:
                        from src.utils.auth import hash_password
                        recruiter.password_hash = hash_password(new_password)
                
                # Validate slug
                if new_slug != recruiter.dashboard_slug:
                    # Check if slug already exists
                    existing = db.query(Recruiter).filter(Recruiter.dashboard_slug == new_slug, Recruiter.id != recruiter_id).first()
                    if existing:
                        errors.append("Dashboard slug already exists. Please choose a different slug.")
                    else:
                        recruiter.dashboard_slug = new_slug
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    db.commit()
                    st.success("✅ Credentials updated successfully!")
                    st.info("**Note:** User will need to log in again if password was changed.")
                    st.session_state.view_creds_id = None
                    st.rerun()
        
        st.markdown("---")
        
        # Back button
        if st.button("← Back to User Management"):
            st.session_state.view_creds_id = None
            st.rerun()
            
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
