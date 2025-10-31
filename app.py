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
import pages.create_assessment as create_assessment
import pages.admin_sessions as admin_sessions
import pages.admin_settings as admin_settings
import pages.admin_panel as admin_panel
import pages.recruiter_settings as recruiter_settings
import pages.candidate_assessment as candidate_assessment

# Page configuration
st.set_page_config(
    page_title="Excel Assessment Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None  # Hide menu items
)

# Hide sidebar completely using CSS
hide_sidebar_css = """
<style>
    /* Hide the entire sidebar */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Adjust main content area when sidebar is hidden */
    [data-testid="stSidebar"] ~ div {
        margin-left: 0 !important;
    }
    
    /* Hide hamburger menu button that toggles sidebar */
    button[data-testid="baseButton-header"] {
        display: none !important;
    }
    
    /* Hide Streamlit's default navigation menu */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Ensure main content takes full width */
    .main .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
    
    /* Hide footer menu */
    footer {
        display: none !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {
        visibility: hidden;
    }
</style>
"""
st.markdown(hide_sidebar_css, unsafe_allow_html=True)

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
    
    # Admin routes
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    
    # Top navigation bar
    if check_auth():
        from src.components.navbar import render_navbar
        render_navbar()
        
        # Render selected page based on user role
        if st.session_state.page == 'dashboard':
            admin_dashboard.render()
        elif st.session_state.page == 'assessments':
            admin_assessments.render()
        elif st.session_state.page == 'create_assessment':
            create_assessment.render()
        elif st.session_state.page == 'candidates':
            # For now, redirect to sessions - we'll create candidates page later
            admin_sessions.render()
        elif st.session_state.page == 'settings':
            # Settings page is for dashboard customization - accessible to both admins and recruiters
            recruiter_settings.render()
        elif st.session_state.page == 'admin_panel':
            # Only admins can access admin panel - redirect non-admins
            if not st.session_state.get('user', {}).get('is_admin', False):
                st.error("❌ Access denied. Admin privileges required.")
                st.warning("Redirecting to dashboard...")
                st.session_state.page = 'dashboard'
                st.rerun()
            admin_panel.render()
        elif st.session_state.page == 'admin_settings':
            # Only admins can access admin settings - redirect non-admins
            if not st.session_state.get('user', {}).get('is_admin', False):
                st.error("❌ Access denied. Admin privileges required.")
                st.warning("Redirecting to settings...")
                st.session_state.page = 'settings'
                st.rerun()
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

