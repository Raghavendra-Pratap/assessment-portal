"""Admin Settings - System-wide configuration including Google Sheets API"""

import streamlit as st
import json
import os
from src.database import SessionLocal, Recruiter

def render():
    """Render admin settings page"""
    st.title("⚙️ Admin Settings")
    st.markdown("---")
    
    # Check if user is admin
    if not st.session_state.get('user', {}).get('is_admin', False):
        st.error("❌ Access denied. Admin privileges required.")
        return
    
    # System Configuration Section
    st.subheader("🔧 System Configuration")
    
    # Google Sheets API Configuration
    st.markdown("### 📊 Google Sheets API Configuration")
    st.markdown("Configure Google Sheets integration for all recruiters.")
    
    with st.expander("Google Sheets API Setup", expanded=True):
        st.markdown("""
        **Setup Instructions:**
        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Create a new project or select existing one
        3. Enable Google Sheets API
        4. Create a Service Account
        5. Download the JSON credentials file
        6. Upload the credentials file below
        """)
        
        # File upload for service account JSON
        uploaded_file = st.file_uploader(
            "Upload Service Account JSON",
            type=['json'],
            help="Upload the service account JSON file downloaded from Google Cloud Console"
        )
        
        if uploaded_file:
            try:
                # Read and validate JSON
                credentials_data = json.load(uploaded_file)
                
                # Validate required fields
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'client_id']
                missing_fields = [field for field in required_fields if field not in credentials_data]
                
                if missing_fields:
                    st.error(f"Invalid JSON file. Missing fields: {', '.join(missing_fields)}")
                else:
                    # Save credentials to environment or config file
                    credentials_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'google_credentials.json')
                    os.makedirs(os.path.dirname(credentials_path), exist_ok=True)
                    
                    with open(credentials_path, 'w') as f:
                        json.dump(credentials_data, f, indent=2)
                    
                    st.success("✅ Google Sheets credentials saved successfully!")
                    st.info(f"Credentials saved to: `{credentials_path}`")
                    
                    # Display service account info
                    st.markdown("**Service Account Information:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text(f"Project ID: {credentials_data.get('project_id', 'N/A')}")
                        st.text(f"Client Email: {credentials_data.get('client_email', 'N/A')}")
                    with col2:
                        st.text(f"Type: {credentials_data.get('type', 'N/A')}")
                        st.text(f"Client ID: {credentials_data.get('client_id', 'N/A')}")
                    
            except json.JSONDecodeError:
                st.error("Invalid JSON file. Please upload a valid service account JSON file.")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
    
    st.markdown("---")
    
    # Default Assessment Settings
    st.subheader("📝 Default Assessment Settings")
    
    with st.expander("Default Assessment Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            default_duration = st.number_input(
                "Default Duration (minutes)",
                min_value=5,
                max_value=480,
                value=60,
                help="Default time limit for new assessments"
            )
            
            default_attempts = st.number_input(
                "Default Max Attempts",
                min_value=1,
                max_value=10,
                value=1,
                help="Default maximum attempts allowed for assessments"
            )
        
        with col2:
            default_proctoring = st.selectbox(
                "Default Proctoring Level",
                ['basic', 'standard', 'strict'],
                index=1,
                help="Default proctoring settings for new assessments"
            )
            
            default_grading = st.selectbox(
                "Default Grading Mode",
                ['auto', 'manual', 'hybrid'],
                index=0,
                help="Default grading mode for new assessments"
            )
        
        if st.button("Save Default Settings", type="primary"):
            # Save to config file or database
            config = {
                'default_duration': default_duration,
                'default_attempts': default_attempts,
                'default_proctoring': default_proctoring,
                'default_grading': default_grading
            }
            
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'default_settings.json')
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            st.success("✅ Default settings saved successfully!")
    
    st.markdown("---")
    
    # Security Settings
    st.subheader("🔒 Security Settings")
    
    with st.expander("Security Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            session_timeout = st.number_input(
                "Session Timeout (minutes)",
                min_value=5,
                max_value=480,
                value=120,
                help="Auto-logout after inactivity"
            )
            
            password_min_length = st.number_input(
                "Minimum Password Length",
                min_value=6,
                max_value=20,
                value=8,
                help="Minimum password length for new accounts"
            )
        
        with col2:
            enable_2fa = st.checkbox(
                "Enable Two-Factor Authentication",
                value=False,
                help="Require 2FA for admin accounts"
            )
            
            enable_audit_log = st.checkbox(
                "Enable Audit Logging",
                value=True,
                help="Log all admin actions for security"
            )
        
        if st.button("Save Security Settings", type="primary"):
            security_config = {
                'session_timeout': session_timeout,
                'password_min_length': password_min_length,
                'enable_2fa': enable_2fa,
                'enable_audit_log': enable_audit_log
            }
            
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'security_settings.json')
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(security_config, f, indent=2)
            
            st.success("✅ Security settings saved successfully!")
    
    st.markdown("---")
    
    # System Information
    st.subheader("ℹ️ System Information")
    
    with st.expander("System Details", expanded=False):
        db = SessionLocal()
        try:
            # Get system stats
            total_recruiters = db.query(Recruiter).count()
            admin_recruiters = db.query(Recruiter).filter(Recruiter.is_admin == True).count()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Recruiters", total_recruiters)
            with col2:
                st.metric("Admin Users", admin_recruiters)
            with col3:
                st.metric("Regular Recruiters", total_recruiters - admin_recruiters)
            
            # Database info
            st.markdown("**Database Information:**")
            st.text(f"Database Path: {os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'assessments.db')}")
            st.text(f"Database Size: {get_db_size()}")
            
            # Application info
            st.markdown("**Application Information:**")
            st.text(f"Version: 1.0.0")
            st.text(f"Python Version: {os.sys.version}")
            
        finally:
            db.close()
    
    st.markdown("---")
    
    # Danger Zone
    st.subheader("⚠️ Danger Zone")
    
    with st.expander("Dangerous Operations", expanded=False):
        st.warning("⚠️ These operations are irreversible and can cause data loss!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Reset All Settings", type="secondary"):
                st.session_state.reset_settings = True
                st.rerun()
        
        with col2:
            if st.button("Clear All Data", type="secondary"):
                st.session_state.clear_data = True
                st.rerun()
        
        # Handle reset settings
        if st.session_state.get('reset_settings', False):
            st.error("Are you sure you want to reset all settings? This will remove all configuration files.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Reset Settings", type="primary"):
                    reset_all_settings()
                    st.session_state.reset_settings = False
                    st.success("Settings reset successfully!")
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.session_state.reset_settings = False
                    st.rerun()
        
        # Handle clear data
        if st.session_state.get('clear_data', False):
            st.error("Are you sure you want to clear ALL data? This will delete all recruiters, assessments, and sessions!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Clear All Data", type="primary"):
                    clear_all_data()
                    st.session_state.clear_data = False
                    st.success("All data cleared successfully!")
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.session_state.clear_data = False
                    st.rerun()

def get_db_size():
    """Get database file size"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'assessments.db')
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
        return "Not found"
    except:
        return "Unknown"

def reset_all_settings():
    """Reset all configuration files"""
    try:
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        if os.path.exists(config_dir):
            import shutil
            shutil.rmtree(config_dir)
        st.success("All settings reset successfully!")
    except Exception as e:
        st.error(f"Error resetting settings: {str(e)}")

def clear_all_data():
    """Clear all data from database"""
    try:
        from src.database import Base, engine
        # Drop all tables and recreate
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        st.success("All data cleared successfully!")
    except Exception as e:
        st.error(f"Error clearing data: {str(e)}")