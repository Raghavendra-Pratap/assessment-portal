"""
Secure Admin Page (Develop branch reset)

This app exposes ONLY an `admin` page which is protected by a TOTP code
from an authenticator app (Google Authenticator, Authy, 1Password, etc.).

Access policy:
- No username/password, no alternate route. A valid TOTP code is required.
- The TOTP secret must be provisioned via environment variable or a local
  config file before any access is possible.
"""

import os
import json
import time
import streamlit as st
import pyotp


CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'admin_totp.json')


def load_totp_secret():
    """Load TOTP configuration from env or local config. Returns (secret, issuer, account)."""
    secret = os.getenv('ADMIN_TOTP_SECRET')
    issuer = os.getenv('ADMIN_TOTP_ISSUER', 'ExcelAssessment')
    account = os.getenv('ADMIN_TOTP_ACCOUNT', 'admin')

    if secret:
        return secret.strip(), issuer.strip(), account.strip()

    # Fallback to config file if present
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
            s = data.get('secret', '').strip()
            if s:
                return s, data.get('issuer', issuer).strip(), data.get('account', account).strip()
    except Exception:
        pass
    return None, None, None


def ensure_session_state():
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    if 'last_verified_at' not in st.session_state:
        st.session_state.last_verified_at = 0


def guard_configured():
    """Render a hard stop if TOTP secret is not configured yet."""
    st.title('Admin Access Locked')
    st.error('TOTP secret is not configured. Access is disabled until an admin provisions the secret.')
    st.markdown('''
1. Generate a secret on a secure machine:
   - Linux/macOS: `python -c "import pyotp; print(pyotp.random_base32())"`
2. Deploy the secret as an environment variable on your host:
   - `ADMIN_TOTP_SECRET=YOUR_GENERATED_SECRET`
   - Optionally set `ADMIN_TOTP_ISSUER` and `ADMIN_TOTP_ACCOUNT`
3. Alternatively, place a local file (not committed to git):
   - `config/admin_totp.json` with:
     `{ "secret": "YOUR_GENERATED_SECRET", "issuer": "ExcelAssessment", "account": "admin" }`
''')
    st.stop()


def render_admin_page():
    st.title('🔧 Admin')
    st.success('Authenticated via TOTP')
    st.write('This space is intentionally minimal until dedicated roles/creds are added.')
    st.write('You can place sensitive admin operations here.')
    if st.button('Logout'):
        st.session_state.admin_authenticated = False
        st.rerun()


def render_totp_login(secret: str, issuer: str, account: str):
    st.title('Admin Authentication')
    st.caption('Enter the 6-digit code from your authenticator app')

    totp = pyotp.TOTP(secret)
    code = st.text_input('TOTP Code', max_chars=6)
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button('Verify', type='primary'):
            if code and totp.verify(code.strip(), valid_window=1):
                st.session_state.admin_authenticated = True
                st.session_state.last_verified_at = int(time.time())
                st.success('Verified')
                st.rerun()
            else:
                st.error('Invalid or expired code')
    with col2:
        # Show time remaining in current TOTP step (UX only, no QR exposure)
        try:
            remaining = totp.interval - (int(time.time()) % totp.interval)
            st.info(f"Time remaining: {remaining}s")
        except Exception:
            pass

    with st.expander('Having trouble?'):
        st.markdown('''
- Ensure the device time is accurate (auto time sync on).
- Code changes every 30 seconds; enter promptly.
- If you lost access, rotate the TOTP secret in deployment.
''')


def main():
    st.set_page_config(page_title='Secure Admin', page_icon='🔒', layout='wide', initial_sidebar_state='collapsed')
    ensure_session_state()

    secret, issuer, account = load_totp_secret()
    if not secret:
        guard_configured()

    # Only route is the admin page guarded by TOTP
    if st.session_state.admin_authenticated:
        render_admin_page()
    else:
        render_totp_login(secret, issuer, account)


if __name__ == '__main__':
    main()

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
import pages.admin_panel as admin_panel
import pages.recruiter_settings as recruiter_settings
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
        elif st.session_state.page == 'candidates':
            # For now, redirect to sessions - we'll create candidates page later
            admin_sessions.render()
        elif st.session_state.page == 'settings':
            # Show different settings based on user role
            if st.session_state.get('user', {}).get('is_admin', False):
                admin_settings.render()
            else:
                recruiter_settings.render()
        elif st.session_state.page == 'admin_panel':
            # Only admins can access admin panel
            if st.session_state.get('user', {}).get('is_admin', False):
                admin_panel.render()
            else:
                st.error("❌ Access denied. Admin privileges required.")
        elif st.session_state.page == 'admin_settings':
            # Only admins can access admin settings
            if st.session_state.get('user', {}).get('is_admin', False):
                admin_settings.render()
            else:
                st.error("❌ Access denied. Admin privileges required.")
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

