"""Admin Page - User Management and Role Assignment"""

import streamlit as st
import json
import os
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
    tab1, tab2 = st.tabs(["👥 User Management", "📊 Statistics"])
    
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
    
    # Settings Section - Google Cloud Console Credentials
    st.markdown("---")
    st.markdown("### ⚙️ Google Cloud Console Settings")
    
    with st.expander("🔑 Configure Google Cloud API Credentials", expanded=False):
        # Load existing credentials
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'google_credentials.json')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        existing_config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    existing_config = json.load(f)
            except:
                existing_config = {}
        
        # Form for credentials
        with st.form("google_credentials_form"):
            st.markdown("#### OAuth 2.0 Client Credentials")
            
            client_id = st.text_input(
                "Client ID",
                value=existing_config.get('client_id', ''),
                placeholder="e.g., 417402972310-nec398pa3d60ipq7304h4gu8cn9f1",
                help="From Google Cloud Console > APIs & Services > Credentials"
            )
            
            client_secret = st.text_input(
                "Client Secret",
                value=existing_config.get('client_secret', ''),
                type="password",
                placeholder="Enter your Google OAuth 2.0 Client Secret",
                help="Your Google OAuth 2.0 Client Secret"
            )
            
            st.markdown("---")
            st.markdown("#### Service Account JSON")
            
            service_account_json = st.text_area(
                "Service Account JSON",
                value=json.dumps(existing_config.get('service_account', {}), indent=2) if existing_config.get('service_account') else '',
                height=200,
                placeholder='{\n  "type": "service_account",\n  "project_id": "your-project-id",\n  ...\n}',
                help="Paste the complete JSON key file content"
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                save_button = st.form_submit_button("💾 Save Credentials", type="primary", use_container_width=True)
            
            if save_button:
                config = {
                    'client_id': client_id.strip(),
                    'client_secret': client_secret.strip()
                }
                
                # Validate and parse service account JSON
                if service_account_json.strip():
                    try:
                        service_account_data = json.loads(service_account_json)
                        config['service_account'] = service_account_data
                    except json.JSONDecodeError:
                        st.error("❌ Invalid JSON format for Service Account. Please check your JSON syntax.")
                        return
                elif existing_config.get('service_account'):
                    # Keep existing service account if new one is empty
                    config['service_account'] = existing_config.get('service_account')
                
                # Save to config file
                try:
                    with open(config_path, 'w') as f:
                        json.dump(config, f, indent=2)
                    st.success("✅ Google Cloud credentials saved successfully!")
                    
                    # Display saved configuration summary
                    if client_id:
                        st.info(f"**Client ID:** {client_id[:20]}... (saved)")
                    if client_secret:
                        st.info("**Client Secret:** ******** (saved)")
                    if config.get('service_account'):
                        project_id = config['service_account'].get('project_id', 'N/A')
                        client_email = config['service_account'].get('client_email', 'N/A')
                        st.info(f"**Service Account:** {project_id} | {client_email}")
                except Exception as e:
                    st.error(f"❌ Error saving credentials: {str(e)}")
        
        # Display current configuration status
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    current_config = json.load(f)
                    
                st.markdown("---")
                st.markdown("#### Current Configuration Status")
                
                status_cols = st.columns(3)
                with status_cols[0]:
                    if current_config.get('client_id'):
                        st.success("✅ Client ID configured")
                    else:
                        st.warning("⚠️ Client ID not set")
                
                with status_cols[1]:
                    if current_config.get('client_secret'):
                        st.success("✅ Client Secret configured")
                    else:
                        st.warning("⚠️ Client Secret not set")
                
                with status_cols[2]:
                    if current_config.get('service_account'):
                        st.success("✅ Service Account configured")
                    else:
                        st.warning("⚠️ Service Account not set")
            except:
                st.warning("⚠️ Could not read configuration file")

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

