"""Login Page - Sign In and Sign Up"""

import streamlit as st
from src.utils.auth import authenticate_user, create_user, authenticate_google_user

def render():
    """Render login page"""
    
    # Custom CSS for the gradient background and card design
    st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    .login-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        max-width: 450px;
        margin: 0 auto;
    }
    
    .testing-banner {
        background: #fef3c7;
        border-left: 4px solid #10b981;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .testing-banner-icon {
        color: #10b981;
        display: inline-block;
        margin-right: 0.5rem;
    }
    
    .tab-container {
        display: flex;
        gap: 1rem;
        margin: 1.5rem 0;
        border-bottom: 2px solid #e5e7eb;
    }
    
    .tab {
        padding: 0.5rem 1rem;
        cursor: pointer;
        border: none;
        background: none;
        color: #6b7280;
        font-weight: 500;
    }
    
    .tab.active {
        color: #2563eb;
        border-bottom: 2px solid #2563eb;
    }
    
    .gradient-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
        cursor: pointer;
    }
    
    .google-button {
        background: white;
        border: 1px solid #e5e7eb;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        width: 100%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    
    .divider {
        text-align: center;
        margin: 1.5rem 0;
        position: relative;
    }
    
    .divider::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        width: 45%;
        height: 1px;
        background: #e5e7eb;
    }
    
    .divider::after {
        content: '';
        position: absolute;
        right: 0;
        top: 50%;
        width: 45%;
        height: 1px;
        background: #e5e7eb;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Center the login card
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        # Header
        st.markdown("## Recruiter Portal")
        st.markdown("<p style='color: #6b7280; text-align: center; margin-top: -10px;'>Access your assessment dashboard</p>", unsafe_allow_html=True)
        
        # Testing Mode Banner
        st.markdown("""
        <div class="testing-banner">
            <span class="testing-banner-icon">✓</span>
            <strong>Testing Mode Active</strong><br>
            <small style="color: #6b7280;">Any email/password combination will work for testing purposes.</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize tab state
        if 'login_tab' not in st.session_state:
            st.session_state.login_tab = 'signin'
        
        # Tabs
        tab1, tab2 = st.columns(2)
        with tab1:
            if st.button("Sign In", key="tab_signin", use_container_width=True, type="primary" if st.session_state.login_tab == 'signin' else "secondary"):
                st.session_state.login_tab = 'signin'
                st.rerun()
        with tab2:
            if st.button("Sign Up", key="tab_signup", use_container_width=True, type="primary" if st.session_state.login_tab == 'signup' else "secondary"):
                st.session_state.login_tab = 'signup'
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Sign In Form
        if st.session_state.login_tab == 'signin':
            with st.form("signin_form"):
                email = st.text_input("Work Email", placeholder="your.email@company.com")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
                
                if submitted:
                    if not email or not password:
                        st.error("Please enter both email and password")
                    else:
                        # In testing mode, any email/password works
                        # Otherwise, authenticate normally
                        user = authenticate_user(email, password)
                        
                        if user or (email and password):  # Testing mode: accept any credentials
                            if not user:
                                # Create a test user in testing mode
                                from src.utils.auth import create_user
                                user = create_user(email, password, email.split('@')[0], role='recruiter')
                            
                            if user:
                                st.session_state.authenticated = True
                                st.session_state.user = user
                                st.session_state.page = 'admin' if user['role'] == 'admin' else 'dashboard'
                                st.rerun()
                            else:
                                st.error("Authentication failed")
        
        # Sign Up Form
        elif st.session_state.login_tab == 'signup':
            with st.form("signup_form"):
                name = st.text_input("Full Name", placeholder="John Doe")
                email = st.text_input("Work Email", placeholder="your.email@company.com")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                
                submitted = st.form_submit_button("Sign Up", use_container_width=True, type="primary")
                
                if submitted:
                    if not name or not email or not password:
                        st.error("Please fill in all fields")
                    elif password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        user = create_user(email, password, name, role='recruiter')
                        if user:
                            st.success("Account created successfully! Please sign in.")
                            st.session_state.login_tab = 'signin'
                            st.rerun()
                        else:
                            st.error("Email already exists")
        
        # Divider
        st.markdown('<div class="divider"><span style="background: white; padding: 0 1rem; color: #6b7280;">or</span></div>', unsafe_allow_html=True)
        
        # Google OAuth Button
        if st.button("🔴 Continue with Google", use_container_width=True, type="secondary"):
            # For now, show a message - Google OAuth integration will be added
            st.info("Google OAuth integration coming soon!")
            # TODO: Implement Google OAuth
            # user = authenticate_google_user(google_id, email, name)
        
        # Forgot Password Link
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p style="text-align: center;"><a href="#" style="color: #2563eb; text-decoration: none;">Forgot Password?</a></p>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

