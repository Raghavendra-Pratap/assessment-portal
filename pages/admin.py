"""Admin Page - User Management and Role Assignment"""

import streamlit as st
from src.database import SessionLocal, User
from src.utils.auth import get_all_users, update_user_role, toggle_user_status, get_user_by_id
from datetime import datetime

def render():
    """Render admin page"""
    
    # Check if user is admin
    user = st.session_state.get('user', {})
    if user.get('role') != 'admin':
        st.error("❌ Access denied. Admin privileges required.")
        st.stop()
    
    st.title("🔧 Admin Dashboard")
    st.markdown("---")
    
    # Page tabs
    tab1, tab2, tab3 = st.tabs(["👥 User Management", "📊 Statistics", "⚙️ Settings"])
    
    with tab1:
        st.subheader("User Management")
        
        # Get all users
        users = get_all_users()
        
        if not users:
            st.info("No users found.")
            return
        
        # Display user statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Users", len(users))
        with col2:
            admins = len([u for u in users if u['role'] == 'admin'])
            st.metric("Admins", admins)
        with col3:
            recruiters = len([u for u in users if u['role'] == 'recruiter'])
            st.metric("Recruiters", recruiters)
        with col4:
            active = len([u for u in users if u['is_active']])
            st.metric("Active Users", active)
        
        st.markdown("---")
        
        # Users table
        st.markdown("### All Users")
        
        for user_data in users:
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1.5, 1.5, 1.5, 1.5])
                
                with col1:
                    st.write(f"**{user_data['name']}**")
                    st.caption(user_data['email'])
                
                with col2:
                    if user_data['last_login']:
                        st.write(f"Last Login: {user_data['last_login'].strftime('%Y-%m-%d %H:%M')}")
                    else:
                        st.write("Last Login: Never")
                    st.caption(f"Joined: {user_data['created_at'].strftime('%Y-%m-%d')}")
                
                with col3:
                    # Role selector
                    current_role = user_data['role']
                    if user_data['id'] == st.session_state.user['id']:
                        st.write(f"**Role:** {current_role}")
                        st.caption("(Your account)")
                    else:
                        new_role = st.selectbox(
                            "Role",
                            ['admin', 'recruiter', 'candidate'],
                            index=['admin', 'recruiter', 'candidate'].index(current_role),
                            key=f"role_{user_data['id']}",
                            label_visibility="collapsed"
                        )
                        if new_role != current_role:
                            if update_user_role(user_data['id'], new_role):
                                st.success(f"Role updated to {new_role}")
                                st.rerun()
                
                with col4:
                    # Status toggle
                    status_text = "Active" if user_data['is_active'] else "Inactive"
                    status_color = "🟢" if user_data['is_active'] else "🔴"
                    
                    if user_data['id'] == st.session_state.user['id']:
                        st.write(f"{status_color} {status_text}")
                        st.caption("(Your account)")
                    else:
                        if st.button(
                            f"{status_color} {status_text}",
                            key=f"status_{user_data['id']}",
                            use_container_width=True
                        ):
                            new_status = toggle_user_status(user_data['id'])
                            if new_status is not None:
                                st.success(f"Status updated to {'Active' if new_status else 'Inactive'}")
                                st.rerun()
                
                with col5:
                    # View Details button
                    if st.button("View", key=f"view_{user_data['id']}", use_container_width=True):
                        st.session_state.selected_user_id = user_data['id']
                        show_user_details(user_data)
                
                with col6:
                    # Delete button (disable for self)
                    if user_data['id'] == st.session_state.user['id']:
                        st.button("Delete", key=f"delete_{user_data['id']}", disabled=True, use_container_width=True)
                    else:
                        if st.button("Delete", key=f"delete_{user_data['id']}", use_container_width=True, type="secondary"):
                            if confirm_delete_user(user_data['id']):
                                delete_user(user_data['id'])
                                st.rerun()
                
                st.markdown("---")
    
    with tab2:
        st.subheader("Statistics")
        
        # User statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### User Roles Distribution")
            role_counts = {
                'admin': len([u for u in users if u['role'] == 'admin']),
                'recruiter': len([u for u in users if u['role'] == 'recruiter']),
                'candidate': len([u for u in users if u['role'] == 'candidate'])
            }
            st.bar_chart(role_counts)
        
        with col2:
            st.markdown("### User Status")
            status_counts = {
                'Active': len([u for u in users if u['is_active']]),
                'Inactive': len([u for u in users if not u['is_active']])
            }
            st.bar_chart(status_counts)
        
        # Recent activity
        st.markdown("### Recent Logins")
        recent_users = sorted(
            [u for u in users if u['last_login']],
            key=lambda x: x['last_login'],
            reverse=True
        )[:10]
        
        if recent_users:
            for u in recent_users:
                st.write(f"**{u['name']}** ({u['email']}) - {u['last_login'].strftime('%Y-%m-%d %H:%M')}")
        else:
            st.info("No recent logins")
    
    with tab3:
        st.subheader("Google Cloud Console Settings")
        st.markdown("Configure Google Cloud Console credentials for API integrations.")
        
        # Load existing credentials
        import json
        import os
        
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'google_credentials.json')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        existing_creds = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    existing_creds = json.load(f)
            except:
                existing_creds = {}
        
        # Form for credentials
        with st.form("google_credentials_form"):
            st.markdown("### OAuth 2.0 Credentials")
            
            # Client ID
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("**Client ID:**")
                st.caption("From Google Cloud Console > APIs & Services > Credentials")
            with col2:
                client_id = st.text_input(
                    "Client ID",
                    value=existing_creds.get('client_id', ''),
                    label_visibility="collapsed",
                    placeholder="Enter your Google OAuth 2.0 Client ID"
                )
            
            # Client Secret
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("**Client Secret:**")
                st.caption("Your Google OAuth 2.0 Client Secret")
            with col2:
                # Show existing secret partially if available
                existing_secret = existing_creds.get('client_secret', '')
                if existing_secret:
                    secret_display = existing_secret[:4] + '*' * (len(existing_secret) - 8) + existing_secret[-4:] if len(existing_secret) > 8 else '*' * len(existing_secret)
                    st.info(f"Current secret: {secret_display}")
                
                client_secret = st.text_input(
                    "Client Secret",
                    value='',  # Always empty for security
                    type="password",
                    label_visibility="collapsed",
                    placeholder="Enter your Google OAuth 2.0 Client Secret"
                )
            
            st.markdown("---")
            
            # Service Account JSON
            st.markdown("### Service Account JSON")
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("**Service Account JSON:**")
                st.caption("Paste the complete JSON key file content")
            with col2:
                existing_service_json = existing_creds.get('service_account_json', '')
                if existing_service_json:
                    try:
                        # Parse and show first few lines
                        service_json_obj = json.loads(existing_service_json)
                        preview = json.dumps({
                            "type": service_json_obj.get("type", ""),
                            "project_id": service_json_obj.get("project_id", ""),
                            "private_key_id": service_json_obj.get("private_key_id", ""),
                            "client_email": service_json_obj.get("client_email", "")
                        }, indent=2)
                        with st.expander("View current service account details", expanded=False):
                            st.json(service_json_obj)
                    except:
                        st.info("Service account JSON is configured")
                
                service_account_json = st.text_area(
                    "Service Account JSON",
                    value='',  # Always empty for security
                    label_visibility="collapsed",
                    height=200,
                    placeholder='Paste your complete service account JSON here...'
                )
            
            # Submit button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                submitted = st.form_submit_button("💾 Save Credentials", type="primary", use_container_width=True)
            
            if submitted:
                # Validate and save credentials
                errors = []
                
                # Validate Client ID
                if not client_id or len(client_id) < 10:
                    errors.append("Client ID is required and must be valid")
                
                # Validate Client Secret (only if new one provided)
                if client_secret:
                    if len(client_secret) < 10:
                        errors.append("Client Secret must be valid")
                    else:
                        existing_creds['client_secret'] = client_secret
                elif not existing_creds.get('client_secret'):
                    errors.append("Client Secret is required")
                
                # Validate Service Account JSON (only if new one provided)
                if service_account_json:
                    try:
                        json_obj = json.loads(service_account_json)
                        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'client_id']
                        missing = [f for f in required_fields if f not in json_obj]
                        if missing:
                            errors.append(f"Service Account JSON missing required fields: {', '.join(missing)}")
                        else:
                            existing_creds['service_account_json'] = service_account_json
                    except json.JSONDecodeError:
                        errors.append("Service Account JSON is not valid JSON")
                elif not existing_creds.get('service_account_json'):
                    errors.append("Service Account JSON is required")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # Save credentials
                    existing_creds['client_id'] = client_id
                    
                    try:
                        with open(config_path, 'w') as f:
                            json.dump(existing_creds, f, indent=2)
                        st.success("✅ Credentials saved successfully!")
                        st.info(f"Credentials saved to: `{config_path}`")
                        
                        # Show summary
                        with st.expander("Credentials Summary", expanded=True):
                            st.markdown(f"**Client ID:** `{client_id[:20]}...`")
                            if service_account_json or existing_creds.get('service_account_json'):
                                try:
                                    sa_json = json.loads(service_account_json or existing_creds.get('service_account_json', '{}'))
                                    st.markdown(f"**Project ID:** `{sa_json.get('project_id', 'N/A')}`")
                                    st.markdown(f"**Client Email:** `{sa_json.get('client_email', 'N/A')}`")
                                except:
                                    st.markdown("**Service Account:** ✅ Configured")
                    except Exception as e:
                        st.error(f"Error saving credentials: {str(e)}")

def show_user_details(user_data):
    """Show detailed user information"""
    st.subheader(f"User Details: {user_data['name']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Email:** {user_data['email']}")
        st.markdown(f"**Role:** {user_data['role']}")
        st.markdown(f"**Status:** {'Active' if user_data['is_active'] else 'Inactive'}")
    
    with col2:
        st.markdown(f"**Created:** {user_data['created_at'].strftime('%Y-%m-%d %H:%M')}")
        if user_data['last_login']:
            st.markdown(f"**Last Login:** {user_data['last_login'].strftime('%Y-%m-%d %H:%M')}")
        else:
            st.markdown("**Last Login:** Never")

def confirm_delete_user(user_id):
    """Show confirmation dialog for deleting user"""
    user = get_user_by_id(user_id)
    if user:
        return st.confirm(f"Are you sure you want to delete {user['name']} ({user['email']})?")
    return False

def delete_user(user_id):
    """Delete a user"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
            st.success(f"User {user.name} deleted successfully")
            return True
        return False
    finally:
        db.close()

