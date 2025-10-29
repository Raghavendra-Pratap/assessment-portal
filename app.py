"""
Excel Assessment Pro - Streamlit App
Main entry point for the assessment system
"""

import streamlit as st
import sys
import os

# Add the app directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import init_db
from src.utils.auth import check_auth, init_session_state, create_default_admin
import pages.admin_dashboard as admin_dashboard
import pages.admin_assessments as admin_assessments
import pages.admin_sessions as admin_sessions
import pages.admin_settings as admin_settings
import pages.candidate_assessment as candidate_assessment

# Page configuration
st.set_page_config(
    page_title="Excel Assessment Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database
init_db()

# Create default admin if needed
create_default_admin()

# Initialize session state
init_session_state()

# Main app routing
def main():
    # Check URL parameters for candidate assessment
    query_params = st.query_params
    
    # Candidate assessment route (token-based)
    if 'token' in query_params:
        candidate_assessment.render()
        return
    
    # Secret admin panel route - check URL parameter or special path
    if 'admin_panel' in query_params or query_params.get('page') == 'admin_panel':
        from src.utils.admin_auth import check_admin_access
        if check_admin_access():
            import pages.admin_panel as admin_panel
            admin_panel.render()
            return
        else:
            st.error("🚫 Access Denied: Admin privileges required")
            show_login()
            return
    
    # Admin routes
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    
    # Top navigation bar
    if check_auth():
        from src.utils.admin_auth import is_admin_user
        from src.components.navbar import render_navbar
        
        # Check if user is admin
        user_is_admin = is_admin_user(st.session_state.get('user'))
        
        # Render navbar (will show admin panel link if admin)
        render_navbar(user_is_admin)
        
        # Render selected page
        if st.session_state.page == 'admin_panel':
            import pages.admin_panel as admin_panel
            admin_panel.render()
        elif st.session_state.page == 'dashboard':
            admin_dashboard.render()
        elif st.session_state.page == 'assessments':
            admin_assessments.render()
        elif st.session_state.page == 'candidates':
            # For now, redirect to sessions - we'll create candidates page later
            admin_sessions.render()
        elif st.session_state.page == 'settings':
            admin_settings.render()
    else:
        # Login page
        show_login()
    
def show_login():
    """Display login form"""
    st.title("Excel Assessment Pro")
    st.markdown("### Admin Login")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            from src.utils.auth import authenticate_user
            user = authenticate_user(email, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.page = 'dashboard'
                st.rerun()
            else:
                st.error("Invalid email or password")

if __name__ == "__main__":
    main()

