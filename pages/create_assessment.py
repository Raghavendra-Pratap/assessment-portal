"""Create Assessment Page - Dedicated page for assessment creation with Google Sheets integration"""

import streamlit as st
import json
from datetime import datetime
from src.database import SessionLocal, Assessment, Question
from src.utils.auth import check_auth
from src.services.google_sheets import get_google_sheets_service
import re

def extract_sheet_id(sheet_url_or_id):
    """
    Extract Google Sheet ID from URL or return the ID if it's already just an ID
    """
    if not sheet_url_or_id:
        return None
    
    sheet_url_or_id = sheet_url_or_id.strip()
    
    # If it contains /d/, it's a full URL
    if '/d/' in sheet_url_or_id:
        # Extract ID from URL pattern: /d/SHEET_ID/
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', sheet_url_or_id)
        if match:
            return match.group(1)
    else:
        # Assume it's just the sheet ID (alphanumeric, dash, underscore)
        if re.match(r'^[a-zA-Z0-9-_]+$', sheet_url_or_id):
            return sheet_url_or_id
    
    return None

def render():
    """Render the dedicated assessment creation page"""
    
    if not check_auth():
        st.error("Please login first")
        return
    
    st.title("📝 Create Assessment")
    
    db = SessionLocal()
    try:
        user_id = st.session_state.user['id']
        
        # Draft state in session
        if 'assessment_draft' not in st.session_state:
            st.session_state.assessment_draft = {
                'title': '',
                'questions': []
            }
        
        draft = st.session_state.assessment_draft
        
        # Top bar: title input and actions
        top_left, top_right = st.columns([4, 2])
        with top_left:
            draft['title'] = st.text_input(
                "Enter assessment name...", 
                value=draft.get('title', ''), 
                placeholder="New Assessment",
                key="assessment_title_input"
            )
        with top_right:
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                st.button("Import", key="import_btn", disabled=True, use_container_width=True)
            with c2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.assessment_draft = {'title': '', 'questions': []}
                    if 'current_sheet_url' in st.session_state:
                        del st.session_state.current_sheet_url
                    if 'preview_sheet_url' in st.session_state:
                        del st.session_state.preview_sheet_url
                    st.session_state.page = 'assessments'
                    st.rerun()
            with c3:
                if st.button("💾 Save Assessment", type="primary", use_container_width=True):
                    if not draft['title']:
                        st.error("Assessment name is required")
                    elif not draft['questions']:
                        st.warning("Please add at least one question before saving")
                    else:
                        # Persist assessment and questions
                        assessment = Assessment(
                            recruiter_id=user_id,
                            title=draft['title'],
                            description='',
                            duration_minutes=60,
                            settings={}
                        )
                        db.add(assessment)
                        db.commit()

                        for idx, q in enumerate(draft['questions'], start=1):
                            question = Question(
                                assessment_id=assessment.id,
                                type=q['type'],
                                question_text=q['text'],
                                section_name=q.get('section') or None,
                                sheet_template_url=q.get('sheet_url') or None,
                                answer_key=q.get('answer_key') or {},
                                points=q['score'],
                                display_order=idx
                            )
                            db.add(question)
                        db.commit()

                        st.session_state.assessment_draft = {'title': '', 'questions': []}
                        if 'current_sheet_url' in st.session_state:
                            del st.session_state.current_sheet_url
                        if 'preview_sheet_url' in st.session_state:
                            del st.session_state.preview_sheet_url
                        st.success("✅ Assessment created successfully!")
                        st.session_state.page = 'assessments'
                        st.rerun()

        st.divider()

        # Two-column layout: left panel (1/4) - question editor; right (3/4) - Google Sheet
        left, right = st.columns([1, 3])

        with left:
            st.markdown("#### Question Settings")
            
            # Google Sheets Integration Section
            st.markdown("**Google Sheets Integration**")
            google_sheets_service = get_google_sheets_service()
            
            if not google_sheets_service or not google_sheets_service.is_configured():
                st.warning("⚠️ Google Sheets API not configured. Please configure credentials in Admin Settings.")
                with st.expander("📋 Configure Google Sheets", expanded=False):
                    st.info("Go to **Admin Settings** page to upload your Google Cloud Console Service Account JSON file.")
            else:
                # Google Sheets Quick Actions
                sheets_col1, sheets_col2 = st.columns(2)
                with sheets_col1:
                    if st.button("➕ Create New", use_container_width=True, help="Create a new Google Sheet"):
                        st.session_state.show_create_sheet = not st.session_state.get('show_create_sheet', False)
                with sheets_col2:
                    if st.button("📋 List Sheets", use_container_width=True, help="View all your Google Sheets"):
                        st.session_state.show_sheets_list = not st.session_state.get('show_sheets_list', False)
                
                # Create new sheet form
                if st.session_state.get('show_create_sheet', False):
                    with st.expander("➕ Create New Google Sheet", expanded=True):
                        with st.form("create_sheet_form"):
                            sheet_title = st.text_input(
                                "Sheet Title", 
                                value=f"Assessment Sheet - {datetime.now().strftime('%Y%m%d_%H%M%S')}", 
                                key="new_sheet_title"
                            )
                            col1, col2 = st.columns(2)
                            with col1:
                                create_btn = st.form_submit_button("✅ Create", use_container_width=True)
                            with col2:
                                cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)
                            
                            if cancel_btn:
                                st.session_state.show_create_sheet = False
                                st.rerun()
                            
                            if create_btn:
                                if sheet_title:
                                    result = google_sheets_service.create_sheet(sheet_title)
                                    if result.get('success'):
                                        st.session_state.preview_sheet_url = result['url']
                                        st.session_state.current_sheet_url = result['url']
                                        st.session_state.show_create_sheet = False
                                        st.success(f"✅ Sheet created: {result['title']}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Error creating sheet: {result.get('error', 'Unknown error')}")
                                else:
                                    st.warning("⚠️ Please enter a sheet title")
                
                # Show sheets list if requested
                if st.session_state.get('show_sheets_list', False):
                    with st.expander("📋 My Google Sheets", expanded=True):
                        with st.spinner("Loading sheets..."):
                            sheets = google_sheets_service.list_sheets(max_results=20)
                            if sheets:
                                for sheet in sheets:
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.write(f"**{sheet['name']}**")
                                        st.caption(f"Created: {sheet['created'][:10] if sheet['created'] else 'N/A'}")
                                    with col2:
                                        if st.button("Use", key=f"use_sheet_{sheet['id']}", use_container_width=True):
                                            st.session_state.preview_sheet_url = sheet['url']
                                            st.session_state.current_sheet_url = sheet['url']
                                            st.session_state.show_sheets_list = False
                                            st.success(f"✅ Loaded: {sheet['name']}")
                                            st.rerun()
                            else:
                                st.info("No Google Sheets found.")
                
                # Copy from template section
                with st.expander("📄 Copy from Template", expanded=False):
                    template_sheet_url = st.text_input(
                        "Template Sheet URL", 
                        placeholder="Paste Google Sheet URL to copy from...", 
                        key="template_url"
                    )
                    new_sheet_name = st.text_input(
                        "New Sheet Name", 
                        placeholder="Name for the copied sheet...", 
                        key="template_name"
                    )
                    if st.button("📋 Copy Template", use_container_width=True):
                        if template_sheet_url and new_sheet_name:
                            template_id = extract_sheet_id(template_sheet_url)
                            if template_id:
                                with st.spinner("Copying sheet..."):
                                    result = google_sheets_service.copy_sheet(template_id, new_sheet_name)
                                    if result.get('success'):
                                        st.session_state.preview_sheet_url = result['url']
                                        st.session_state.current_sheet_url = result['url']
                                        st.success(f"✅ Sheet copied: {new_sheet_name}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Error copying sheet: {result.get('error', 'Unknown error')}")
                            else:
                                st.error("❌ Invalid template sheet URL")
                        else:
                            st.warning("⚠️ Please provide both template URL and new sheet name")
            
            st.markdown("---")
            
            # Question form
            question_number = len(draft['questions']) + 1
            with st.form("question_builder_form"):
                st.markdown(f"**Question {question_number:02d}**")
                section_name = st.text_input("Section Name", placeholder="e.g., Excel Basics, Advanced Formulas")
                question_type = st.selectbox("Question Type *", ["formula", "data-entry", "mcq", "scenario"], index=0)
                question_text = st.text_area("Question Text *", placeholder="Enter your question...", height=100)
                score = st.number_input("Score *", min_value=1, value=10)
                mandatory = st.toggle("Mandatory Question", value=True)
                time_bound = st.toggle("Time Bound", value=False)
                negative_marking = st.toggle("Enable Negative Marking", value=False)
                instructions = st.text_area("Instructions (if any)", placeholder="Additional instructions for the candidate...", height=60)
                
                # Auto-populate sheet URL from session state if available
                default_sheet_url = st.session_state.get('preview_sheet_url', '') or st.session_state.get('current_sheet_url', '')
                sheet_url = st.text_input(
                    "Google Sheet ID or URL", 
                    placeholder="Enter Google Sheet ID or paste full URL...", 
                    key="sheet_url_input", 
                    value=default_sheet_url
                )
                
                # Preview and Save buttons
                preview_col1, preview_col2 = st.columns([1, 1])
                with preview_col1:
                    preview_btn = st.form_submit_button("👁️ Preview", use_container_width=True)
                with preview_col2:
                    add_q = st.form_submit_button("💾 Save Question", use_container_width=True, type="primary")
                
                # Preview sheet without saving
                if preview_btn:
                    if sheet_url:
                        sheet_id = extract_sheet_id(sheet_url)
                        if sheet_id:
                            st.session_state.current_sheet_url = sheet_url
                            st.session_state.preview_sheet_url = sheet_url
                            st.success("✅ Sheet loaded! Check the workspace on the right.")
                            st.rerun()
                        else:
                            st.error("❌ Invalid Google Sheet URL. Please enter a valid URL or ID.")
                    else:
                        st.warning("⚠️ Please enter a Google Sheet URL or ID first.")

                # Save question
                if add_q:
                    if not question_text:
                        st.error("Question text is required")
                    elif not sheet_url:
                        st.warning("⚠️ Please add a Google Sheet URL for this question")
                    else:
                        sheet_id = extract_sheet_id(sheet_url)
                        if not sheet_id:
                            st.error("❌ Invalid Google Sheet URL. Please enter a valid URL or ID.")
                        else:
                            draft['questions'].append({
                                'type': question_type,
                                'text': question_text,
                                'section': section_name,
                                'score': int(score),
                                'mandatory': mandatory,
                                'time_bound': time_bound,
                                'negative_marking': negative_marking,
                                'instructions': instructions,
                                'sheet_url': sheet_url,
                                'answer_key': {}
                            })
                            # Store sheet URL for display in workspace
                            st.session_state.current_sheet_url = sheet_url
                            st.session_state.preview_sheet_url = sheet_url
                            st.success("✅ Question saved! Sheet loaded in workspace.")
                            st.rerun()

        with right:
            st.markdown("#### Google Sheet Workspace")
            
            # Determine which sheet to display
            current_sheet_url = None
            sheet_id = None
            
            # First check if there's a current/preview sheet URL
            if st.session_state.get('current_sheet_url'):
                current_sheet_url = st.session_state.get('current_sheet_url')
            elif st.session_state.get('preview_sheet_url'):
                current_sheet_url = st.session_state.get('preview_sheet_url')
            # Then check if there are questions with sheet URLs
            elif draft.get('questions'):
                # Get the latest question's sheet URL
                for q in reversed(draft['questions']):
                    if q.get('sheet_url'):
                        current_sheet_url = q['sheet_url']
                        break
            
            # Extract sheet ID if URL is available
            if current_sheet_url:
                sheet_id = extract_sheet_id(current_sheet_url)
            
            if current_sheet_url and sheet_id:
                # Get sheet info
                sheet_title = None
                if google_sheets_service and google_sheets_service.is_configured():
                    sheet_info = google_sheets_service.get_sheet_info(sheet_id)
                    if sheet_info:
                        sheet_title = sheet_info['title']
                        st.markdown(f"**📊 {sheet_title}**")
                    else:
                        st.markdown(f"**📊 Google Sheet**")
                else:
                    st.markdown(f"**📊 Google Sheet**")
                
                # Create embed URL - using edit mode for better integration
                embed_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit?usp=sharing&rm=minimal&widget=true&headers=false"
                
                # Quick actions
                action_col1, action_col2, action_col3, action_col4 = st.columns(4)
                with action_col1:
                    if st.button("🔄 Refresh", key="refresh_sheet", use_container_width=True):
                        st.rerun()
                with action_col2:
                    if st.button("✏️ Open in New Tab", key="open_new_tab", use_container_width=True):
                        st.markdown(f'<script>window.open("{embed_url}", "_blank");</script>', unsafe_allow_html=True)
                with action_col3:
                    st.markdown(f"**Sheet ID:** `{sheet_id[:12]}...`")
                with action_col4:
                    if st.button("🔗 Copy URL", key="copy_url", use_container_width=True):
                        st.session_state.copied_url = embed_url
                        st.success("URL copied! Paste it below or in your browser.")
                        st.code(embed_url, language=None)
                
                # Display copied URL if available
                if st.session_state.get('copied_url'):
                    st.info(f"**Copied URL:** {st.session_state.copied_url}")
                
                # Create iframe with proper styling - full height for assessment workspace
                # Use the embed URL which is more reliable for iframes
                embed_public_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/preview"
                
                st.markdown(f"""
                <div style="width: 100%; height: 75vh; border: 2px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin-top: 10px; background-color: #ffffff;">
                    <iframe 
                        src="{embed_url}" 
                        width="100%" 
                        height="100%" 
                        frameborder="0"
                        style="border: none; min-height: 600px;"
                        allow="clipboard-read; clipboard-write"
                        allowfullscreen="true">
                    </iframe>
                </div>
                """, unsafe_allow_html=True)
                
                # Fallback link in case iframe doesn't load
                st.markdown(f"""
                <div style="text-align: center; margin-top: 10px;">
                    <a href="{embed_url}" target="_blank" style="color: #64748b; text-decoration: none; font-size: 0.9em;">
                        🔗 Open in New Window
                    </a>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Show placeholder when no sheet is loaded
                st.markdown("""
                <div style="width: 100%; height: 75vh; border: 2px dashed #e2e8f0; border-radius: 8px; 
                            display: flex; flex-direction: column; align-items: center; justify-content: center;
                            background-color: #f8f9fa; margin-top: 10px;">
                    <div style="text-align: center; color: #64748b; padding: 20px;">
                        <h3 style="color: #64748b; margin-bottom: 10px;">No Questions Yet</h3>
                        <p style="color: #94a3b8;">Add a question on the left to get started with Google Sheets integration</p>
                        <p style="color: #94a3b8; margin-top: 10px; font-size: 0.9em;">
                            Or create a new sheet, select from your existing sheets, or paste a sheet URL
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
    finally:
        db.close()

