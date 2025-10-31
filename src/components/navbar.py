"""Top Navigation Bar Component"""

import streamlit as st

def render_navbar():
    """Render top navigation bar"""
    # Get user info
    user = st.session_state.get('user', {})
    user_name = user.get('name', 'User')
    user_company = user.get('company', 'test101')
    user_initials = user_name[0].upper() if user_name else 'U'
    
    # Get current page
    current_page = st.session_state.get('page', 'dashboard')
    
    # Determine navigation based on user role
    is_admin = user.get('is_admin', False)
    
    if is_admin:
        # Admin navigation - admins use "Admin Settings", not regular "Settings"
        col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1, 1, 1, 1, 2])
        nav_cols = [col2, col3, col4, col5, col6]
        nav_pages = ['dashboard', 'assessments', 'candidates', 'admin_panel', 'admin_settings']
        nav_labels = ['Dashboard', 'Assessments', 'Candidates', 'Admin Panel', 'Admin Settings']
    else:
        # Regular recruiter navigation
        col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 2])
        nav_cols = [col2, col3, col4, col5]
        nav_pages = ['dashboard', 'assessments', 'candidates', 'settings']
        nav_labels = ['Dashboard', 'Assessments', 'Candidates', 'Settings']
    
    with col1:
        st.markdown(f"**{user_company}**")
    
    for nav_col, page_key, label in zip(nav_cols, nav_pages, nav_labels):
        with nav_col:
            # Use custom CSS for active state
            if current_page == page_key:
                st.markdown("""
                <style>
                .stButton > button[kind="primary"] {
                    background-color: #eff6ff;
                    color: #2563eb;
                }
                </style>
                """, unsafe_allow_html=True)
                button_type = "primary"
            else:
                button_type = "secondary"
            
            if st.button(label, key=f"nav_{page_key}", use_container_width=True, type=button_type):
                st.session_state.page = page_key
                st.rerun()
    
    # User info and logout
    user_col = col7 if is_admin else col6
    with user_col:
        user_col1, user_col2 = st.columns([4, 1])
        with user_col1:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 0.5rem; justify-content: flex-end;">
                <div style="width: 2.5rem; height: 2.5rem; border-radius: 50%; background: #2563eb; color: white; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.875rem;">
                    {user_initials}
                </div>
                <span style="font-weight: 500;">{user_name}</span>
            </div>
            """, unsafe_allow_html=True)
        with user_col2:
            if st.button("Logout", key="nav_logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user = None
                st.session_state.page = 'login'
                st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)

