"""Admin Settings - Google Cloud Console Credentials"""

import streamlit as st
import json
import os

def render():
    """Render admin settings page"""
    
    # Check if user is admin
    user = st.session_state.get('user', {})
    if user.get('role') != 'admin':
        st.error("❌ Access denied. Admin privileges required.")
        st.stop()
    
    st.subheader("Google Cloud Console Settings")
    st.markdown("Configure Google Cloud Console credentials for API integrations.")
    
    # Load existing credentials
    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, 'google_credentials.json')
    
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
                    # Parse and show preview
                    service_json_obj = json.loads(existing_service_json)
                    preview = json.dumps({
                        "type": service_json_obj.get("type", ""),
                        "project_id": service_json_obj.get("project_id", ""),
                        "private_key_id": service_json_obj.get("private_key_id", ""),
                        "client_email": service_json_obj.get("client_email", "")
                    }, indent=2)
                    with st.expander("View current service account details", expanded=False):
                        st.json(service_json_obj)
                    st.info("Service account JSON is configured. Enter new JSON to update.")
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
    
    st.markdown("---")
    
    # Instructions
    with st.expander("📖 Setup Instructions", expanded=False):
        st.markdown("""
        **How to get Google Cloud Console credentials:**
        
        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Create a new project or select an existing one
        3. Enable the APIs you need:
           - Google Sheets API
           - Google Drive API
           - Google OAuth 2.0 API
        4. Create OAuth 2.0 credentials:
           - Go to APIs & Services > Credentials
           - Click "Create Credentials" > "OAuth client ID"
           - Choose "Web application"
           - Add authorized redirect URIs
           - Copy Client ID and Client Secret
        5. Create Service Account:
           - Go to APIs & Services > Credentials
           - Click "Create Credentials" > "Service account"
           - Create a new service account
           - Download the JSON key file
           - Paste the complete JSON content above
        """)
    
    # Current configuration status
    st.markdown("### Configuration Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if existing_creds.get('client_id'):
            st.success("✅ Client ID: Configured")
        else:
            st.warning("⚠️ Client ID: Not configured")
    
    with col2:
        if existing_creds.get('client_secret'):
            st.success("✅ Client Secret: Configured")
        else:
            st.warning("⚠️ Client Secret: Not configured")
    
    with col3:
        if existing_creds.get('service_account_json'):
            st.success("✅ Service Account: Configured")
        else:
            st.warning("⚠️ Service Account: Not configured")

